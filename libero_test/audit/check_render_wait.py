"""量化"空跑 10 步"与"空跑 30 步"渲染出的画面差别。

任务清单的首帧截图目前在空跑 10 步后拍摄，而全量 settle 显示
81% 的任务此时场景仍在运动。本脚本给出判断依据：这段时间里
物体实际移动了多少，够不够肉眼看出来。

用法（在 Armory 的 venv 里）：
  MUJOCO_GL=egl python check_render_wait.py <out_dir>
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

import numpy as np

from common import SUITES, ZERO, AuditConfig, Record, create, restore

EARLY = 10   # LIBERO 默认的 NUM_STEPS_WAIT
LATE = 30    # 覆盖全部 130 个任务首次达标值（最大 29）的建议值

FIELDS = [
    "suite", "task", "task_name", "objects",
    "max_move_m", "max_move_mm", "worst_object",
    "mean_move_mm", "error",
]


def positions(env) -> dict[str, np.ndarray]:
    """取每个可动物体 root body 的世界坐标。"""
    sim = env.sim
    return {
        obj.name: sim.data.body_xpos[
            sim.model.body_name2id(obj.root_body)
        ].copy()
        for obj in env.env.objects
    }


def append(path: Path, row: Record) -> None:
    """逐条落盘。反复创建环境偶发 SIGFPE（signal 8），
    进程可能中途死掉，所以不能等到最后一次性写。"""
    fresh = not path.exists()
    with path.open("a", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=FIELDS, restval="")
        if fresh:
            writer.writeheader()
        writer.writerow({k: row.get(k, "") for k in FIELDS})


def done_pairs(path: Path) -> set[tuple[str, int]]:
    """已经测过的 (suite, task)，用于崩溃后续跑。"""
    if not path.exists():
        return set()
    with path.open(encoding="utf-8") as file:
        return {
            (row["suite"], int(row["task"]))
            for row in csv.DictReader(file)
        }


def main(out: Path) -> None:
    out.mkdir(parents=True, exist_ok=True)
    cfg = AuditConfig(out=out)
    table = out / "render_wait_check.csv"
    finished = done_pairs(table)

    for suite_name in SUITES:
        from libero.libero import benchmark

        count = benchmark.get_benchmark_dict()[suite_name]().n_tasks

        for task_id in range(count):
            if (suite_name, task_id) in finished:
                continue

            try:
                env, suite, task, _ = create(
                    cfg, suite_name, task_id, pixels=False
                )
            except Exception as error:
                append(table, {
                    "suite": suite_name,
                    "task": task_id,
                    "error": f"{type(error).__name__}: {error}",
                })
                continue

            try:
                restore(env, suite, task_id, 0)

                for _ in range(EARLY):
                    env.step(ZERO)
                early = positions(env)

                for _ in range(LATE - EARLY):
                    env.step(ZERO)
                late = positions(env)

                moved = {
                    name: float(
                        np.linalg.norm(late[name] - early[name])
                    )
                    for name in early
                }
                worst = max(moved, key=moved.get) if moved else ""

                row = {
                    "suite": suite_name,
                    "task": task_id,
                    "task_name": task.name,
                    "objects": len(moved),
                    # 10→30 步之间位移最大的物体及其位移
                    "max_move_m": moved[worst] if moved else 0.0,
                    "max_move_mm": (
                        moved[worst] * 1000 if moved else 0.0
                    ),
                    "worst_object": worst,
                    "mean_move_mm": (
                        float(np.mean(list(moved.values()))) * 1000
                        if moved else 0.0
                    ),
                    "error": "",
                }
                append(table, row)
                print(
                    f"{suite_name}[{task_id}] "
                    f"max {row['max_move_mm']:.2f} mm "
                    f"({worst})",
                    flush=True,
                )
            finally:
                env.close()

    with table.open(encoding="utf-8") as file:
        rows = list(csv.DictReader(file))

    good = [
        {**r, "max_move_mm": float(r["max_move_mm"])}
        for r in rows if not r.get("error")
    ]
    values = sorted(r["max_move_mm"] for r in good)
    print("\n### summary")
    print(f"tasks: {len(good)}")
    print(f"median max move: {np.percentile(values, 50):.2f} mm")
    print(f"p95 max move:    {np.percentile(values, 95):.2f} mm")
    print(f"worst:           {values[-1]:.2f} mm")
    for limit in [1, 5, 10, 20]:
        share = sum(1 for v in values if v > limit) / len(values)
        print(f"move > {limit:>2} mm: {share:.0%} of tasks")


if __name__ == "__main__":
    main(Path(sys.argv[1] if len(sys.argv) > 1 else "results_render_check"))
