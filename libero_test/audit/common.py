from __future__ import annotations

import os
import sys

os.environ.setdefault("MUJOCO_GL", "egl")
sys.dont_write_bytecode = True

import argparse
import csv
import inspect
import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Sequence, TypeAlias

import numpy as np
from numpy.typing import NDArray
from PIL import Image

from libero.libero import benchmark, get_libero_path
from libero.libero.benchmark import Benchmark, Task
from libero.libero.envs.env_wrapper import ControlEnv
from robosuite.utils.errors import RandomizationError


# 类型别名：鼠标悬停时可以看到更清楚的输入输出类型。
Array: TypeAlias = NDArray[Any]
Observation: TypeAlias = dict[str, Array]
Record: TypeAlias = dict[str, Any]
Report: TypeAlias = dict[str, Any]

SUITES = [
    "libero_spatial",
    "libero_object",
    "libero_goal",
    "libero_90",
    "libero_10",
]
CAMERAS = ["agentview", "robot0_eye_in_hand"]

# OSC_POSE：末端平移 3 + 旋转 3 + 夹爪 1。
# 零动作不是暂停物理仿真。
ZERO = np.zeros(7, dtype=np.float64)


@dataclass(frozen=True)
class AuditConfig:
    section: str = "inspect"
    suite: str = "libero_10"
    task: int = 0
    init: int = 0
    steps: int = 100
    max_wait: int = 200
    window: int = 20
    init_count: int = 1
    all_tasks: bool = False
    out: Path | None = None
    only_task: bool = False


def parse_args(argv: Sequence[str] | None = None) -> AuditConfig:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--section",
        default="inspect",
        choices=["inspect", "settle", "timing", "dynamic", "all"],
    )
    parser.add_argument("--suite", default="libero_10", choices=SUITES)
    parser.add_argument("--task", type=int, default=0)
    parser.add_argument("--init", type=int, default=0)
    parser.add_argument("--steps", type=int, default=100)
    parser.add_argument("--max-wait", type=int, default=200)
    parser.add_argument("--window", type=int, default=20)
    parser.add_argument("--init-count", type=int, default=1)
    parser.add_argument("--all-tasks", action="store_true")
    parser.add_argument("--out", type=Path)
    parser.add_argument("--only-task", action="store_true")

    cfg = AuditConfig(**vars(parser.parse_args(argv)))

    if not (1 <= cfg.steps <= 500 and 20 <= cfg.max_wait <= 500):
        parser.error("steps: 1..500; max-wait: 20..500")
    if not (1 <= cfg.window <= cfg.max_wait and cfg.init_count >= 1):
        parser.error("window: 1..max-wait; init-count >= 1")
    if cfg.task < 0 or cfg.init < 0:
        parser.error("task and init must be nonnegative")

    return cfg


def serial(value: Any) -> Any:
    """把 NumPy 数组、标量和路径转换成 JSON 可保存的值。"""
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, Path):
        return str(value)
    raise TypeError(f"Cannot serialize {type(value).__name__}")


def emit(report: Report, key: str, value: Any) -> None:
    """同时打印一项结果，并放进报告字典。"""
    report[key] = value
    print("\n###", key)
    print(
        json.dumps(value, ensure_ascii=False, indent=2, default=serial),
        flush=True,
    )


def csv_out(
    out: Path | None,
    name: str,
    rows: Sequence[Record],
) -> None:
    """只有指定 --out 时才保存 CSV。"""
    if out is None or not rows:
        return

    # 各行字段可能不一致（例如失败的用例只有错误信息），
    # 所以表头取所有行字段的并集，缺失的留空。
    fieldnames = list(
        dict.fromkeys(key for row in rows for key in row)
    )

    with (out / f"{name}.csv").open(
        "w", newline="", encoding="utf-8"
    ) as file:
        writer = csv.DictWriter(
            file, fieldnames=fieldnames, restval=""
        )
        writer.writeheader()
        writer.writerows(rows)


def text_out(
    out: Path | None,
    name: str,
    text: str,
) -> None:
    """只有指定 --out 时才保存 Markdown 汇总。"""
    if out is None:
        return

    (out / f"{name}.md").write_text(text, encoding="utf-8")


def frames(
    out: Path | None,
    obs: Observation,
    label: str,
) -> None:
    """保存两个相机的图像；不打印图像像素数组。"""
    if out is None:
        return

    for camera in CAMERAS:
        key = camera + "_image"
        if key in obs:
            # 这里只用于人眼查看。
            # Armory 给模型使用的图像预处理在另一个模块中检查。
            Image.fromarray(obs[key][::-1]).save(
                out / f"{label}_{camera}.png"
            )


def stats(values: Sequence[float]) -> dict[str, float]:
    array = np.asarray(values, dtype=float)
    if array.size == 0:
        raise ValueError("Cannot summarize empty measurements")

    return {
        "mean": float(array.mean()),
        "p50": float(np.percentile(array, 50)),
        "p95": float(np.percentile(array, 95)),
        "max": float(array.max()),
    }


def source(function: Callable[..., Any]) -> Record:
    """取得当前安装版本的函数位置及源码。"""
    return {
        "file": inspect.getsourcefile(function),
        "line": inspect.getsourcelines(function)[1],
        "code": inspect.getsource(function),
    }


def git_info(path: Path) -> Record:
    def run(*arguments: str) -> str:
        return subprocess.check_output(
            ["git", "-C", str(path), *arguments],
            text=True,
            timeout=10,
        ).strip()

    try:
        return {
            "commit": run("rev-parse", "HEAD"),
            "changes": run(
                "status", "--porcelain", "--untracked-files=no"
            ),
        }
    except (OSError, subprocess.SubprocessError) as error:
        return {"unavailable": str(error)}


def create(
    cfg: AuditConfig,
    suite_name: str | None = None,
    task_id: int | None = None,
    pixels: bool = True,
    resolution: int = 128,
) -> tuple[ControlEnv, Benchmark, Task, Path]:
    """创建环境，返回：环境、任务集、任务描述、BDDL 路径。"""
    suite_name = cfg.suite if suite_name is None else suite_name
    task_id = cfg.task if task_id is None else task_id

    suite: Benchmark = benchmark.get_benchmark_dict()[suite_name]()
    if not 0 <= task_id < suite.n_tasks:
        raise ValueError(
            f"task_id={task_id}; available={suite.n_tasks}"
        )

    task: Task = suite.get_task(task_id)
    path = (
        Path(get_libero_path("bddl_files"))
        / task.problem_folder
        / task.bddl_file
    )

    env = ControlEnv(
        bddl_file_name=str(path),
        hard_reset=False,
        use_camera_obs=pixels,
        has_renderer=False,
        has_offscreen_renderer=pixels,
        camera_names=CAMERAS,
        camera_heights=resolution,
        camera_widths=resolution,
    )
    return env, suite, task, path


def restore(
    env: ControlEnv,
    suite: Benchmark,
    task_id: int,
    init_id: int,
) -> tuple[Observation, Array]:
    """恢复 benchmark 初始状态；不会自动让场景稳定。"""
    states = np.asarray(suite.get_task_init_states(task_id))
    if not 0 <= init_id < len(states):
        raise ValueError(
            f"init_id={init_id}; available={len(states)}"
        )

    env.seed(0)

    # 当前版本包装层 reset 存在无限重试逻辑。
    # 这里调用内部 reset，只对随机放置失败进行有限重试。
    for attempt in range(10):
        try:
            env.env.reset()
            break
        except RandomizationError:
            if attempt == 9:
                raise

    obs: Observation = env.set_init_state(states[init_id])
    return obs, states


def fresh_obs(env: ControlEnv) -> Observation:
    """修改物理状态后刷新观测，不推进仿真时间。"""
    env.sim.forward()
    env.env._post_process()
    return env.env._get_observations(force_update=True)


def inventory(cfg: AuditConfig, report: Report) -> None:
    """枚举任务；完整列表放入 report，可选保存 CSV。"""
    counts: dict[str, int] = {}
    tasks: list[Record] = []
    scenes: set[str] = set()

    for name in SUITES:
        suite: Benchmark = benchmark.get_benchmark_dict()[name]()
        counts[name] = suite.n_tasks

        for task_id in range(suite.n_tasks):
            task: Task = suite.get_task(task_id)
            tasks.append({
                "suite": name,
                "task_id": task_id,
                "name": task.name,
                "prompt": task.language,
                "bddl": task.bddl_file,
            })

            match = re.match(
                r"((?:KITCHEN|LIVING_ROOM|STUDY)_SCENE\d+)",
                task.name,
            )
            if match:
                scenes.add(match.group(1))

    report["task_list"] = tasks
    emit(report, "task_inventory", {
        "counts": counts,
        "total": len(tasks),
        "scene_labels_in_task_names": sorted(scenes),
    })
    csv_out(cfg.out, "tasks", tasks)