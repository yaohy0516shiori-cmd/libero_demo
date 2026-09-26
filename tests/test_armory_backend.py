import os
import sys,time,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
ARMORY=Path(os.environ.get("ARMORY_ROOT","/root/work/armory"))
sys.path[:0]=[str(ROOT/"demo"),str(ARMORY/"src"),str(ARMORY/"armory-client/src")]
import model_runtime
from armory_backend import Pi05Policy
from armory.backends.types import warmup_request
from armory.serving.rtc import InferType
from dataclasses import replace

class FakeRuntime:
    metadata={"test_only":True}
    def infer(self,observation,seed=0):
        assert observation["images"][0].shape in [(224,224,3),(256,256,3)]
        return np.full((50,7),seed,dtype=np.float32),{"inference_ms":0}

class AdapterTests(unittest.TestCase):
    def test_preserves_each_robot_and_shape(self):
        with tempfile.TemporaryDirectory(dir=ROOT/"results") as d,patch.object(model_runtime,"Runtime",FakeRuntime):
            policy=Pi05Policy(d)
            base=policy.make_infer_request()
            a=policy.infer_batch([replace(base,robot_id="robot_0",observation_step=12)])[0]
            b=policy.infer_batch([replace(base,robot_id="robot_3",observation_step=24)])[0]
            self.assertEqual(a["actions"].shape,(50,7))
            self.assertEqual(float(a["actions"][0,0]),1012)
            self.assertEqual(float(b["actions"][0,0]),31024)
            self.assertIsNone(a["noise"])
            self.assertTrue((a["rtc_prev_actions"]==a["actions"]).all())
    def test_rejects_unsupported_batch(self):
        with tempfile.TemporaryDirectory(dir=ROOT/"results") as d,patch.object(model_runtime,"Runtime",FakeRuntime):
            policy=Pi05Policy(d)
            with self.assertRaises(ValueError):policy.warmup(4)
            with self.assertRaises(ValueError):policy.infer_batch([policy.make_infer_request()]*2)
if __name__=="__main__":unittest.main()
