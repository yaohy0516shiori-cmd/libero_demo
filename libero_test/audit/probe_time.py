from __future__ import annotations

import json
import time
from collections import defaultdict
from pathlib import Path
from typing import Any, Callable

import numpy as np

from libero.libero.envs.env_wrapper import ControlEnv
from robosuite.utils.binding_utils import MjSim

from common import AuditConfig, Record, Report, ZERO
from common import create, restore, emit, stats, csv_out


def timed_steps(
    env: ControlEnv,
    count: int,
    paced: bool = False,
) -> list[Record]:
    """测量每步耗时；paced=True 时尝试按控制周期等待。"""
    sim: MjSim = env.sim

    originals: dict[str, Callable[..., Any]] = {
        "step": sim.step,
        "render": sim.render,
    }
    costs: defaultdict[str, float] = defaultdict(float)
    calls: defaultdict[str, int] = defaultdict(int)
    captures: dict[str, Record] = {}

    def wrapper(name: str) -> Callable[..., Any]:
        def call(*args: Any, **kwargs: Any) -> Any:
            start = time.perf_counter()
            wall = time.time()
            state_time = float(sim.data.time)

            result = originals[name](*args, **kwargs)

            end = time.perf_counter()
            costs[name] += (end - start) * 1000
            calls[name] += 1

            if name == "render":
                camera = str(
                    kwargs.get("camera_name", "unknown")
                )
                captures[camera] = {
                    "render_start_wall_s": wall,
                    "render_start_mono_s": start,
                    "render_end_mono_s": end,
                    "state_sim_s": state_time,
                }

            return result

        return call

    # 临时包装当前 sim 实例的方法，最后恢复。
    for name in originals:
        setattr(sim, name, wrapper(name))

    rows: list[Record] = []
    base_sim = float(sim.data.time)
    base_wall = time.perf_counter()
    dt = env.env.control_timestep

    try:
        for index in range(count):
            costs.clear()
            calls.clear()
            captures.clear()

            start = time.perf_counter()
            env.step(ZERO)
            end = time.perf_counter()

            deadline = base_wall + (index + 1) * dt
            late = max(0.0, end - deadline)

            if paced:
                time.sleep(
                    max(0.0, deadline - time.perf_counter())
                )

            rows.append({
                "step": index + 1,
                "sim_elapsed_s": float(
                    sim.data.time - base_sim
                ),
                "wall_elapsed_s": (
                    time.perf_counter() - base_wall
                ),
                "full_step_ms": (end - start) * 1000,
                "mj_step_ms": costs["step"],
                "render_ms": costs["render"],
                "physics_calls": calls["step"],
                "render_calls": calls["render"],
                "late_ms": late * 1000 if paced else 0.0,
                "captures": json.dumps(captures),
            })
    finally:
        for name, function in originals.items():
            setattr(sim, name, function)

    return rows


def plot_alignment(
    out: Path,
    unpaced: list[Record],
    paced: list[Record],
) -> None:
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("matplotlib unavailable; use the CSV trace.")
        return

    for label, rows in [
        ("unpaced", unpaced),
        ("paced", paced),
    ]:
        plt.plot(
            [r["wall_elapsed_s"] for r in rows],
            [r["sim_elapsed_s"] for r in rows],
            label=label,
        )

    upper = max(
        unpaced[-1]["wall_elapsed_s"],
        paced[-1]["wall_elapsed_s"],
        unpaced[-1]["sim_elapsed_s"],
        paced[-1]["sim_elapsed_s"],
    )
    plt.plot(
        [0, upper], [0, upper], "--", label="real-time y=x"
    )
    plt.xlabel("wall seconds")
    plt.ylabel("simulation seconds")
    plt.legend()
    plt.tight_layout()
    plt.savefig(out / "time_alignment.png")
    plt.close()


def timing_cases(
    cfg: AuditConfig,
    report: Report,
) -> None:
    # 比较无相机、128 双相机、256 双相机。
    for pixels, size in [
        (False, 128),
        (True, 128),
        (True, 256),
    ]:
        tag = (
            f"timing_{'camera' if pixels else 'no_camera'}_{size}"
        )
        env, suite, _, _ = create(
            cfg, pixels=pixels, resolution=size
        )

        try:
            restore(env, suite, cfg.task, cfg.init)

            # 性能预热，不代表已经通过稳定性判据。
            for _ in range(30):
                env.step(ZERO)

            if pixels:
                from OpenGL import GL
                renderer = GL.glGetString(GL.GL_RENDERER)
                emit(
                    report,
                    tag + "_renderer",
                    renderer.decode() if renderer else "UNKNOWN",
                )

            rows = timed_steps(env, cfg.steps)
            budget = 1000 / env.env.control_freq

            emit(report, tag, {
                "full_step_ms": stats(
                    [r["full_step_ms"] for r in rows]
                ),
                "mj_step_only_ms": stats(
                    [r["mj_step_ms"] for r in rows]
                ),
                "dual_camera_render_ms": stats(
                    [r["render_ms"] for r in rows]
                ),
                "budget_ms": budget,
                "p95_margin_ms": budget - np.percentile(
                    [r["full_step_ms"] for r in rows], 95
                ),
                "simulated_over_wall": (
                    rows[-1]["sim_elapsed_s"]
                    / rows[-1]["wall_elapsed_s"]
                ),
                "physics_calls_per_step": sorted({
                    r["physics_calls"] for r in rows
                }),
                "render_calls_per_step": sorted({
                    r["render_calls"] for r in rows
                }),
            })
            csv_out(cfg.out, tag, rows)

            if pixels and size == 256:
                restore(env, suite, cfg.task, cfg.init)
                for _ in range(30):
                    env.step(ZERO)

                paced = timed_steps(
                    env, cfg.steps, paced=True
                )

                emit(report, "paced_256", {
                    "lateness_ms": stats(
                        [r["late_ms"] for r in paced]
                    ),
                    "missed_deadlines": sum(
                        r["late_ms"] > 0 for r in paced
                    ),
                    "first": paced[0],
                    "last": paced[-1],
                })
                csv_out(cfg.out, "paced_256", paced)

                if cfg.out is not None:
                    plot_alignment(cfg.out, rows, paced)
        finally:
            env.close()