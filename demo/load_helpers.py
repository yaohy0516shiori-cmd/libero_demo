"""Rebuild only nonpersistent buffers omitted by safetensors, using upstream initializers."""
import torch

def restore_nonpersistent_buffers(model):
    restored=[]
    for name,module in model.named_modules():
        for key,buffer in list(module.named_buffers(recurse=False)):
            if buffer.device.type!="meta":continue
            if type(module).__name__=="SiglipVisionEmbeddings" and key=="position_ids":
                module.position_ids=torch.arange(module.num_positions,device="cpu").expand((1,-1))
            elif type(module).__name__=="GemmaRotaryEmbedding" and key=="inv_freq":
                module.inv_freq,module.attention_scaling=module.rope_init_fn(module.config,torch.device("cpu"))
                module.original_inv_freq=module.inv_freq
            else:
                raise RuntimeError(f"Unsupported missing buffer {name}.{key}")
            restored.append(name+"."+key)
    return restored
