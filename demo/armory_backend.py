"""Armory ServingPolicy adapter for the official LeRobot Pi0.5 LIBERO checkpoint."""
import json
import time
from pathlib import Path
import numpy as np
from armory.backends.types import warmup_request
from armory.serving.rtc import InferType

class Pi05Factory:
    def __init__(self,output):self.output=str(output)
    def __call__(self):return Pi05Policy(self.output)

class Pi05Policy:
    def __init__(self,output):
        from model_runtime import Runtime,ROOT
        self.runtime=Runtime()
        self.output=Path(output);self.output.mkdir(parents=True,exist_ok=True)
        with np.load(ROOT/"assets/warmup/observation.npz") as s:
            self.example={"state":s["state"],"image":s["image"],"wrist_image":s["image2"],"prompt":str(s["task"])}
        (self.output/"model.json").write_text(json.dumps(self.runtime.metadata,indent=2))

    def make_infer_request(self):
        return warmup_request(self.example)

    def warmup(self,max_batch_size):
        if max_batch_size!=1:raise ValueError("This unbatched 8 GB baseline requires max_batch_size=1")
        for _ in range(2):self.infer_batch([self.make_infer_request()])

    def infer_batch(self,requests):
        if len(requests)!=1:raise ValueError("Native baseline supports one GPU request at a time")
        request=requests[0]
        if request.infer_type!=InferType.SYNC:
            raise ValueError("RTC is not enabled for this baseline adapter")
        obs=request.observation
        robot_number=int(request.robot_id.split("_")[-1]) if request.robot_id.startswith("robot_") else 0
        started=time.time();started_mono=time.perf_counter()
        actions,timing=self.runtime.infer(
            {"state":obs["state"],"images":[obs["image"],obs["wrist_image"]],"task":obs["prompt"]},
            seed=1000+robot_number*10000+request.observation_step)
        finished=time.time();finished_mono=time.perf_counter()
        row=dict(robot_id=request.robot_id,request_id=request.request_id,
            observation_step=request.observation_step,action_index_start=request.action_index_start,
            request_timestamp=request.request_timestamp,arrival_timestamp=request.arrival_timestamp,
            inference_entry_timestamp=started,inference_exit_timestamp=finished,
            inference_entry_mono_s=started_mono,inference_exit_mono_s=finished_mono,
            observation_mono_s=obs.get("demo_observation_mono_s"),
            observation_episode=obs.get("demo_episode"),
            arrival_to_backend_ms=(started-request.arrival_timestamp)*1000,**timing)
        with (self.output/"model_stages.jsonl").open("a") as f:f.write(json.dumps(row)+"\n")
        return [{"actions":actions.astype(np.float32),"noise":None,"rtc_prev_actions":actions}]
