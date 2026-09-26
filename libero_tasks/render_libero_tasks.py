"""Dump every LIBERO task (suite, id, language, scene) and render the first frame of init state 0.

Run inside the Armory venv; output defaults to this folder (libero_tasks/):
  MUJOCO_GL=egl $ARMORY_ROOT/.venv/bin/python render_libero_tasks.py [out_dir]
rerender.sh wraps this and restarts it after the occasional SIGFPE crash.
"""

import json
import pathlib
import sys

import numpy as np
from PIL import Image

from libero.libero import get_libero_path
from libero.libero.benchmark import get_benchmark_dict
from libero.libero.envs import OffScreenRenderEnv

SUITES = ["libero_spatial", "libero_object", "libero_goal", "libero_10", "libero_90"]
RES = 256
DUMMY = [0.0] * 6 + [-1.0]
# LIBERO 官方评测空跑 5 步、Armory 空跑 10 步；全量实测场景首次静止的
# 中位是 13 步、最长 29 步（libero_test/audit/results_all_tasks）。10 步拍照时 17 个
# 任务的物体仍在半空，图里会整个漏掉物体（libero_test/audit/results_render_check/wait_10_vs_30.png）。
WAIT = 30

out = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else pathlib.Path(__file__).resolve().parent
(out / "img").mkdir(parents=True, exist_ok=True)
bench = get_benchmark_dict()
rows = []
BDDL_ROOT = pathlib.Path(get_libero_path("bddl_files"))


def retry(fn, tries=5):
    # LIBERO re-reads its yaml config on every path lookup; that read fails intermittently.
    for i in range(tries):
        try:
            return fn()
        except TypeError:
            if i == tries - 1:
                raise


for suite_name in SUITES:
    suite = bench[suite_name]()
    for tid in range(suite.n_tasks):
        task = suite.get_task(tid)
        init_states = retry(lambda: suite.get_task_init_states(tid))
        row = {
            "suite": suite_name,
            "task_id": tid,
            "name": task.name,
            "language": task.language,
            "problem_folder": task.problem_folder,
            "bddl_file": task.bddl_file,
            "n_init_states": int(len(init_states)),
        }
        img_rel = f"img/{suite_name}_{tid:02d}.png"
        if (out / img_rel).exists():
            row["image"] = img_rel
            rows.append(row)
            print(f"{suite_name}[{tid}] {task.language} -> {img_rel} (cached)", flush=True)
            continue
        def render():
            bddl = BDDL_ROOT / task.problem_folder / task.bddl_file
            env = OffScreenRenderEnv(bddl_file_name=bddl, camera_heights=RES, camera_widths=RES)
            env.seed(0)
            env.reset()
            obs = env.set_init_state(init_states[0])
            for _ in range(WAIT):
                obs, _, _, _ = env.step(DUMMY)
            agent = np.ascontiguousarray(obs["agentview_image"][::-1, ::-1])
            wrist = np.ascontiguousarray(obs["robot0_eye_in_hand_image"][::-1, ::-1])
            Image.fromarray(np.concatenate([agent, wrist], axis=1)).save(out / img_rel)
            env.close()

        try:
            retry(render)
            row["image"] = img_rel
        except Exception as exc:  # keep going; record failure
            row["image"] = None
            row["error"] = repr(exc)
        rows.append(row)
        print(f"{suite_name}[{tid}] {task.language} -> {row.get('image')}", flush=True)

(out / "tasks.json").write_text(json.dumps(rows, indent=2))
print("done", len(rows))
