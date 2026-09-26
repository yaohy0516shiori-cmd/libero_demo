"""Native LeRobot Pi0.5 inference; strict checkpoint load, no compilation or quantization."""
import gc
import json
import time
from pathlib import Path
import numpy as np
import torch
from safetensors.torch import load_file
from load_helpers import restore_nonpersistent_buffers
from transformers import GemmaTokenizer
from lerobot.configs.policies import PreTrainedConfig
from lerobot.policies.pi05.modeling_pi05 import PI05Policy
import lerobot.policies.pi05.processor_pi05  # register the saved processor steps
from lerobot.processor import PolicyProcessorPipeline
from lerobot.processor.converters import (batch_to_transition, transition_to_batch,
    policy_action_to_transition, transition_to_policy_action)

ROOT = Path(__file__).resolve().parents[1]
MODEL_ID = "lerobot/pi05_libero_finetuned"
REVISION = "8e174154ef5f6c60a8da12ae99c303d8963138c1"

class Runtime:
    def __init__(self):
        started = time.perf_counter()
        torch.set_num_threads(4)
        model_dir = ROOT / "models/pi05_finetuned"
        cfg = PreTrainedConfig.from_pretrained(model_dir)
        cfg.device = "meta"
        cfg.compile_model = False
        cfg.gradient_checkpointing = False
        with torch.device("meta"):
            self.policy = PI05Policy(cfg)
        state = load_file(str(model_dir / "model.safetensors"))
        expected = set(self.policy.state_dict())
        aliases = {}
        # Safetensors removes tied storage. Restore only the documented Gemma tie.
        for missing in expected - state.keys():
            if missing.endswith("paligemma.model.language_model.embed_tokens.weight"):
                other = missing.replace("model.language_model.embed_tokens.weight", "lm_head.weight")
            elif missing.endswith("paligemma.lm_head.weight"):
                other = missing.replace("lm_head.weight", "model.language_model.embed_tokens.weight")
            else:
                raise RuntimeError(f"Unexpected missing checkpoint key: {missing}")
            state[missing] = state[other]
            aliases[missing] = other
        self.policy.load_state_dict(state, strict=True, assign=True)
        self.policy.model.paligemma_with_expert.paligemma.tie_weights()
        restored_buffers=restore_nonpersistent_buffers(self.policy)
        del state
        gc.collect()
        cfg.device = "cuda"
        self.policy.to("cuda").eval()
        self.cfg = cfg
        tok_dir = ROOT / "models/tokenizer"
        tok_dir.mkdir(exist_ok=True)
        tok = GemmaTokenizer(vocab_file=str(ROOT / "models/paligemma_tokenizer.model"),
                            add_bos_token=True, add_eos_token=False)
        tok.save_pretrained(tok_dir)
        self.pre = PolicyProcessorPipeline.from_pretrained(
            model_dir, config_filename="policy_preprocessor.json",
            overrides={"tokenizer_processor": {"tokenizer_name": str(tok_dir)},
                       "device_processor": {"device": "cuda"}},
            to_transition=batch_to_transition, to_output=transition_to_batch)
        self.post = PolicyProcessorPipeline.from_pretrained(
            model_dir, config_filename="policy_postprocessor.json",
            to_transition=policy_action_to_transition, to_output=transition_to_policy_action)
        torch.cuda.synchronize()
        self.metadata = dict(model=MODEL_ID, revision=REVISION, dtype=cfg.dtype,
            compile=False, quantization=False, action_chunk=cfg.chunk_size,
            model_load_s=time.perf_counter()-started, restored_tied_keys=aliases,
            restored_nonpersistent_buffers=restored_buffers,
            parameter_bytes=sum(p.numel()*p.element_size() for p in self.policy.parameters()),
            torch=torch.__version__, gpu=torch.cuda.get_device_name())
        self.stage = {}
        # These nested measurements cover embedding construction and denoising.
        # embed_prefix does not include the full prefix transformer pass.
        # Synchronization gives actual GPU completion times rather than enqueue times.
        for name in ("embed_prefix", "denoise_step"):
            original = getattr(self.policy.model, name)
            def measured(*args, _fn=original, _name=name, **kwargs):
                torch.cuda.synchronize(); t = time.perf_counter()
                value = _fn(*args, **kwargs)
                torch.cuda.synchronize()
                self.stage[_name+"_ms"] = self.stage.get(_name+"_ms", 0.) + (time.perf_counter()-t)*1000
                return value
            setattr(self.policy.model, name, measured)

    def infer(self, observation, seed=0):
        self.stage = {}
        torch.manual_seed(seed)
        torch.cuda.reset_peak_memory_stats()
        t0 = time.perf_counter()
        batch = {"task": observation["task"],
                 "observation.state": torch.tensor(observation["state"], dtype=torch.float32)}
        for key, image in zip(("image","image2"), observation["images"]):
            array = np.asarray(image, dtype=np.uint8)
            if array.shape not in ((224,224,3),(256,256,3)):
                raise ValueError(f"Unexpected image shape: {array.shape}")
            batch["observation.images."+key] = torch.from_numpy(array.copy()).permute(2,0,1).float()/255
        batch = self.pre(batch)
        torch.cuda.synchronize(); t1 = time.perf_counter()
        # No select_action queue is shared across robots.
        with torch.inference_mode():
            normalized = self.policy.predict_action_chunk(batch)
        torch.cuda.synchronize(); t2 = time.perf_counter()
        actions = self.post(normalized)[0].cpu().numpy()
        torch.cuda.synchronize(); t3 = time.perf_counter()
        if actions.shape != (50,7) or not np.isfinite(actions).all():
            raise RuntimeError("Invalid model actions")
        times = dict(preprocess_ms=(t1-t0)*1000, inference_ms=(t2-t1)*1000,
            postprocess_ms=(t3-t2)*1000, **self.stage,
            peak_allocated_mib=torch.cuda.max_memory_allocated()/2**20,
            peak_reserved_mib=torch.cuda.max_memory_reserved()/2**20)
        return actions, times

if __name__ == "__main__":
    runtime = Runtime()
    path = ROOT / "assets/warmup/observation.npz"
    with np.load(path) as sample:
        observation = {"state":sample["state"], "images":[sample["image"],sample["image2"]],
                       "task":str(sample["task"])}
    results=[]
    for index in range(2):
        actions,timing=runtime.infer(observation,seed=1000+index)
        results.append(dict(iteration=index, **timing, action_min=float(actions.min()),
                            action_max=float(actions.max())))
        print(results[-1],flush=True)
    (ROOT/"verification/pi05_real_inference.json").write_text(json.dumps(
        dict(metadata=runtime.metadata, calls=results),indent=2))
    np.save(ROOT/"verification/smoke_actions.npy",actions)
