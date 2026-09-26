from __future__ import annotations

from pathlib import Path

import numpy as np

from libero.libero import benchmark
from libero.libero.benchmark import Benchmark
from libero.libero.envs.env_wrapper import ControlEnv
from robosuite.utils.binding_utils import MjModel

from common import AuditConfig, Record, Report, SUITES, ZERO
from common import create, restore, emit, csv_out, text_out


def movable(model: MjModel, body: int) -> bool:
    """当前 body 或其祖先存在关节，则它不是固定世界物体。"""
    while body:
        if model.body_jntnum[body] > 0:
            return True
        body = int(model.body_parentid[body])
    return False


def contacts(env: ControlEnv) -> list[Record]:
    """按碰撞几何体对汇总接触；负 dist 表示穿透。"""
    model = env.sim.model
    data = env.sim.data
    groups: dict[tuple[int, int], Record] = {}

    for contact in data.contact[:data.ncon]:
        g1 = int(contact.geom1)
        g2 = int(contact.geom2)
        if g1 < 0 or g2 < 0:
            continue

        b1 = int(model.geom_bodyid[g1])
        b2 = int(model.geom_bodyid[g2])
        key = (g1, g2)

        if key not in groups:
            groups[key] = {
                "geom1": model.geom_id2name(g1),
                "body1": model.body_id2name(b1),
                "movable1": movable(model, b1),
                "geom2": model.geom_id2name(g2),
                "body2": model.body_id2name(b2),
                "movable2": movable(model, b2),
                "count": 0,
                "min_dist_m": float(contact.dist),
            }

        groups[key]["count"] += 1
        groups[key]["min_dist_m"] = min(
            groups[key]["min_dist_m"],
            float(contact.dist),
        )

    return sorted(groups.values(), key=contact_distance)


def contact_distance(row: Record) -> float:
    return float(row["min_dist_m"])


def speed_indices(
    model: MjModel,
) -> tuple[list[int], list[int]]:
    """区分 qvel 中的线速度分量与角速度分量。"""
    linear: list[int] = []
    angular: list[int] = []

    for joint in range(model.njnt):
        kind = int(model.jnt_type[joint])
        address = int(model.jnt_dofadr[joint])

        if kind == 0:  # free：3 个平移 + 3 个旋转
            linear.extend(range(address, address + 3))
            angular.extend(range(address + 3, address + 6))
        elif kind == 1:  # ball：3 个旋转
            angular.extend(range(address, address + 3))
        elif kind == 2:  # slide：1 个平移
            linear.append(address)
        else:  # hinge：1 个旋转
            angular.append(address)

    return linear, angular


def settling(
    env: ControlEnv,
    cfg: AuditConfig,
    label: str = "",
) -> tuple[Record, list[Record]]:
    """持续发送零动作，记录速度、穿透和连续安静步数。"""
    linear, angular = speed_indices(env.sim.model)

    rows: list[Record] = []
    streak = 0
    first_confirmed: int | None = None
    first_quiet: int | None = None
    corrupted_at: int | None = None

    for step in range(1, cfg.max_wait + 1):
        if not (np.isfinite(env.sim.data.qpos).all() and np.isfinite(env.sim.data.qvel).all()):
            # 非有限状态说明这一轮已经不可信，记下位置并停止。
            corrupted_at = step
            print(f"bad state: {label} step={step}", flush=True)
            break

        _, reward, success, _ = env.step(ZERO)
        velocity = np.asarray(env.sim.data.qvel)

        lv = (
            float(np.max(np.abs(velocity[linear])))
            if linear else 0.0
        )
        av = (
            float(np.max(np.abs(velocity[angular])))
            if angular else 0.0
        )
        penetration = max(
            [
                max(0.0, -row["min_dist_m"])
                for row in contacts(env)
                if row["movable1"] or row["movable2"]
            ],
            default=0.0,
        )

        # 实验判据，不是 LIBERO 官方定义。
        quiet = (
            lv < 1e-3
            and av < 1e-2
            and penetration < 1e-4
        )
        streak = streak + 1 if quiet else 0

        if quiet and first_quiet is None:
            first_quiet = step
        if streak == cfg.window and first_confirmed is None:
            first_confirmed = step

        rows.append({
            "step": step,
            "sim_s": float(env.sim.data.time),
            "linear_max_m_s": lv,
            "angular_max_rad_s": av,
            "penetration_m": penetration,
            "quiet": quiet,
            "success": bool(success),
            "reward": float(reward),
        })

    step_s = float(env.env.control_timestep)
    # 默认空跑步数（LIBERO 的 NUM_STEPS_WAIT）够不够：
    # 判断第 10 步当时是否已经安静。
    default_wait = 10
    quiet_at_default = (
        bool(rows[default_wait - 1]["quiet"])
        if len(rows) >= default_wait else None
    )

    return {
        # 判据首次连续满足 window 步的那一步（主结论）
        "first_confirmed_step": first_confirmed,
        "first_confirmed_sim_s": (
            round(first_confirmed * step_s, 4)
            if first_confirmed is not None else None
        ),
        # 首次瞬间满足判据的步（可能之后又被打破）
        "first_quiet_step": first_quiet,
        "final_quiet_run": streak,
        "stable_at_end": streak >= cfg.window,
        "tested_steps": len(rows),
        "max_wait": cfg.max_wait,
        "window": cfg.window,
        # 默认 10 步空跑够不够
        "quiet_at_step10": quiet_at_default,
        # 过程量：便于判断是"还在动"还是"穿透没解开"
        "penetration_start_m": (
            rows[0]["penetration_m"] if rows else None
        ),
        "penetration_max_m": max(
            (r["penetration_m"] for r in rows), default=None
        ),
        "penetration_end_m": (
            rows[-1]["penetration_m"] if rows else None
        ),
        "linear_max_m_s": max(
            (r["linear_max_m_s"] for r in rows), default=None
        ),
        "angular_max_rad_s": max(
            (r["angular_max_rad_s"] for r in rows), default=None
        ),
        "success_at_end": (
            rows[-1]["success"] if rows else None
        ),
        # 非 None 表示该轮在此步出现非有限状态，结果不可用
        "corrupted_at_step": corrupted_at,
    }, rows


def settle_cases(
    cfg: AuditConfig,
    report: Report,
) -> None:
    result: list[Record] = []

    # 默认测试所选任务集的前 3 个任务。
    # --all-tasks 才遍历全部五个任务集。
    suite_names = [cfg.suite] if cfg.only_task or not cfg.all_tasks else SUITES

    for name in suite_names:
        suite = benchmark.get_benchmark_dict()[name]()

        if cfg.only_task:
            task_ids = [cfg.task]                        # 只跑指定的这一个
        elif cfg.all_tasks:
            task_ids = range(suite.n_tasks)
        else:
            task_ids = range(min(3, suite.n_tasks))

        for task_id in task_ids:
            # 单个任务失败不应中断整轮；失败原因记进结果表。
            try:
                env, suite, task, _ = create(
                    cfg, name, task_id, pixels=False
                )
            except Exception as error:
                result.append({
                    "suite": name,
                    "task": task_id,
                    "task_name": "",
                    "init": None,
                    "error": f"{type(error).__name__}: {error}",
                })
                print("create failed:", name, task_id, error, flush=True)
                continue

            try:
                count = len(suite.get_task_init_states(task_id))

                for init_id in range(min(cfg.init_count, count)):
                    label = f"{name}/{task_id}/{init_id}"
                    try:
                        restore(env, suite, task_id, init_id)
                        summary, rows = settling(env, cfg, label)
                    except Exception as error:
                        result.append({
                            "suite": name,
                            "task": task_id,
                            "task_name": task.name,
                            "init": init_id,
                            "error": f"{type(error).__name__}: {error}",
                        })
                        print("settle failed:", label, error, flush=True)
                        continue

                    row = {
                        "suite": name,
                        "task": task_id,
                        "task_name": task.name,
                        "init": init_id,
                        **summary,
                        "error": "",
                    }
                    result.append(row)
                    print(
                        f"settling {label}: "
                        f"confirmed={summary['first_confirmed_step']} "
                        f"stable={summary['stable_at_end']} "
                        f"quiet@10={summary['quiet_at_step10']}",
                        flush=True,
                    )

                    # 逐步曲线放进 steps/ 子目录，与汇总分开。
                    csv_out(
                        steps_dir(cfg.out),
                        f"settle_{name}_{task_id}_{init_id}",
                        rows,
                    )
            finally:
                env.close()

    stats_all = settling_stats(result)

    emit(report, "settling_distribution", {
        "criteria": (
            "linear<1e-3 m/s; angular<1e-2 rad/s; "
            "dynamic penetration<1e-4 m"
        ),
        "consecutive_steps": cfg.window,
        "action": ZERO,
        "scope": (
            "all tasks" if cfg.all_tasks and not cfg.only_task
            else "sampled cases only"
        ),
        "stats": stats_all,
        "cases": result,
    })
    csv_out(cfg.out, "settling_summary", result)
    text_out(cfg.out, "settling_summary", markdown(result, stats_all))


def steps_dir(out: Path | None) -> Path | None:
    """逐步曲线的输出目录；不存在时创建。"""
    if out is None:
        return None
    path = out / "steps"
    path.mkdir(parents=True, exist_ok=True)
    return path


def settling_stats(cases: list[Record]) -> Record:
    """按任务集和整体汇总稳定步数分布。"""
    def summarize(rows: list[Record]) -> Record:
        good = [
            r for r in rows
            if not r.get("error")
            and r.get("first_confirmed_step") is not None
        ]
        steps = sorted(r["first_confirmed_step"] for r in good)

        return {
            "cases": len(rows),
            "failed": sum(1 for r in rows if r.get("error")),
            "never_confirmed": sum(
                1 for r in rows
                if not r.get("error")
                and r.get("first_confirmed_step") is None
            ),
            "unstable_at_end": sum(
                1 for r in rows if r.get("stable_at_end") is False
            ),
            "quiet_at_step10": sum(
                1 for r in rows if r.get("quiet_at_step10")
            ),
            "min_step": steps[0] if steps else None,
            "median_step": (
                float(np.percentile(steps, 50)) if steps else None
            ),
            "p95_step": (
                float(np.percentile(steps, 95)) if steps else None
            ),
            "max_step": steps[-1] if steps else None,
            "max_sim_s": (
                max(
                    r["first_confirmed_sim_s"] for r in good
                ) if good else None
            ),
        }

    per_suite = {}
    for name in dict.fromkeys(r["suite"] for r in cases):
        per_suite[name] = summarize(
            [r for r in cases if r["suite"] == name]
        )

    return {"overall": summarize(cases), "per_suite": per_suite}


def markdown(cases: list[Record], stats: Record) -> str:
    """生成英文汇总表（Markdown）。"""
    lines = [
        "# Settling summary",
        "",
        "A step is quiet when linear speed < 1e-3 m/s, angular speed < 1e-2 rad/s "
        "and dynamic penetration < 1e-4 m. A case is confirmed once it has been "
        "quiet for `window` consecutive steps.",
        "",
        "## Overall",
        "",
        "| Item | Value |",
        "|---|---|",
    ]
    for key, value in stats["overall"].items():
        lines.append(f"| {key} | {value} |")

    lines += [
        "",
        "## Per suite",
        "",
        "| Suite | Cases | Failed | Never confirmed | Quiet at step 10 "
        "| Min | Median | P95 | Max (confirmed step) | Max sim. s |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for name, item in stats["per_suite"].items():
        lines.append(
            f"| {name} | {item['cases']} | {item['failed']} | "
            f"{item['never_confirmed']} | {item['quiet_at_step10']} | "
            f"{item['min_step']} | {item['median_step']} | "
            f"{item['p95_step']} | {item['max_step']} | "
            f"{item['max_sim_s']} |"
        )

    lines += [
        "",
        "## Per case",
        "",
        "| Suite | Task | Init | First quiet step | Confirmed step | Sim. s "
        "| Stable at end | Quiet at step 10 | Initial penetration (m) | Task name |",
        "|---|---:|---:|---:|---:|---:|---|---|---:|---|",
    ]
    for row in cases:
        if row.get("error"):
            lines.append(
                f"| {row['suite']} | {row['task']} | {row.get('init')} | "
                f"ERROR | | | | | | {row['error']} |"
            )
            continue
        start = row.get("penetration_start_m")
        penetration = f"{start:.5f}" if start is not None else ""
        lines.append(
            f"| {row['suite']} | {row['task']} | {row['init']} | "
            f"{row.get('first_quiet_step')} | "
            f"{row['first_confirmed_step']} | "
            f"{row['first_confirmed_sim_s']} | "
            f"{row['stable_at_end']} | {row['quiet_at_step10']} | "
            f"{penetration} | {row['task_name']} |"
        )

    return "\n".join(lines) + "\n"