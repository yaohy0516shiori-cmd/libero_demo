"""Uses the existing simulation environment, separately from inference dependencies."""
import os
os.environ.setdefault("MUJOCO_GL","egl")
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
ARMORY=Path(os.environ.get("ARMORY_ROOT","/root/work/armory"))
sys.path[:0]=[str(ARMORY/"third_party/libero"),str(ROOT/"libero_test/audit")]
import numpy as np
from PIL import Image
from common import create,restore,AuditConfig
from robosuite.utils.transform_utils import quat2axisangle
p=Path(__file__).resolve().parents[1]/"assets/warmup";p.mkdir(parents=True,exist_ok=True)
cfg=AuditConfig(suite="libero_spatial",task=0,init=0)
env,suite,task,_=create(cfg,resolution=256)
obs,_=restore(env,suite,0,0)
for _ in range(50):obs,*_=env.step([0,0,0,0,0,0,-1])
np.savez(p/"observation.npz",state=np.concatenate([obs["robot0_eef_pos"],
    quat2axisangle(obs["robot0_eef_quat"].copy()),obs["robot0_gripper_qpos"]]),
    image=obs["agentview_image"][::-1,::-1],image2=obs["robot0_eye_in_hand_image"][::-1,::-1],
    task=task.language)
Image.fromarray(obs["agentview_image"][::-1]).save(p/"initial_scene.png")
print(task.language,flush=True)
env.close()
