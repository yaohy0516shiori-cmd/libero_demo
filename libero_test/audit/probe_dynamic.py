from __future__ import annotations

import numpy as np

from libero.libero.envs.env_wrapper import ControlEnv
from robosuite.utils.binding_utils import MjSim

from common import AuditConfig, Array, Record, Report, ZERO
from common import create, restore, fresh_obs, frames, emit, csv_out
from probe_stability import contacts, settling


def find_free_object(
    env: ControlEnv,
) -> tuple[str, str, int] | None:
    """返回第一个自由物体的名字、关节名、body ID。"""
    sim: MjSim = env.sim

    for obj in env.env.objects:
        for joint in obj.joints:
            joint_id = sim.model.joint_name2id(joint)
            if sim.model.jnt_type[joint_id] == 0:
                return (
                    obj.name,
                    joint,
                    sim.model.body_name2id(obj.root_body),
                )
    return None


def dynamic_case(
    cfg: AuditConfig,
    report: Report,
) -> None:
    env, suite, _, _ = create(cfg)

    try:
        sim: MjSim = env.sim
        target = find_free_object(env)

        if target is None:
            emit(
                report,
                "dynamic_NOT_TESTED",
                "No free-joint object.",
            )
            return

        name, joint, body_id = target
        mass = float(sim.model.body_mass[body_id])

        # 世界坐标系中的演示外力，单位 N。
        force = np.array([
            3 * mass,
            0,
            2 * mass * abs(sim.model.opt.gravity[2]),
        ])

        trials: dict[str, list[Record]] = {}
        starts: list[Array] = []

        # 两组独立恢复，比较相同初态下有无外力的轨迹。
        for label in ["baseline", "force"]:
            restore(env, suite, cfg.task, cfg.init)
            summary, _ = settling(env, cfg)

            if not summary["stable_at_end"]:
                emit(report, "dynamic_NOT_TESTED", {
                    "reason": "settling criterion failed",
                    **summary,
                })
                return

            starts.append(sim.data.qpos.copy())
            frames(
                cfg.out, fresh_obs(env), label + "_before"
            )

            rows: list[Record] = []
            try:
                for step in range(40):
                    active = (
                        label == "force" and 10 <= step < 15
                    )
                    sim.data.xfrc_applied[body_id, :3] = (
                        force if active else 0
                    )

                    obs, _, _, _ = env.step(ZERO)
                    position = (
                        sim.data.body_xpos[body_id].copy()
                    )

                    rows.append({
                        "step": step,
                        "sim_s": float(sim.data.time),
                        "force_on": active,
                        "x": position[0],
                        "y": position[1],
                        "z": position[2],
                    })
                    if label=="baseline":
                        if step in [14,39]:
                            frames(cfg.out, {"agentview_image": obs["agentview_image"]}, f"{label}_{step}")
                    elif label=="force":
                        if 0<step<20:
                            frames(cfg.out, {"agentview_image": obs["agentview_image"]}, f"{label}_{step}")
            finally:
                # 外力不会自动只作用一次，必须主动清除。
                sim.data.xfrc_applied[body_id, :] = 0

            trials[label] = rows
            csv_out(
                cfg.out, label + "_trajectory", rows
            )

        np.testing.assert_allclose(
            starts[0], starts[1], atol=1e-9, rtol=0
        )

        forced = np.array([
            [r[k] for k in ["x", "y", "z"]]
            for r in trials["force"]
        ])
        baseline = np.array([
            [r[k] for k in ["x", "y", "z"]]
            for r in trials["baseline"]
        ])
        difference = forced - baseline

        emit(report, "force_test", {
            "object": name,
            "mass_kg": mass,
            "force_N": force,
            "applied_control_steps": 5,
            "max_difference_m": np.linalg.norm(
                difference, axis=1
            ).max(),
            "final_difference_m": np.linalg.norm(
                difference[-1]
            ),
        })

        # 独立实验：直接把物体向上移动 5 cm。
        restore(env, suite, cfg.task, cfg.init)
        summary, _ = settling(env, cfg)

        if not summary["stable_at_end"]:
            emit(report, "teleport_NOT_TESTED", summary)
            return

        old = sim.data.get_joint_qpos(joint).copy()
        new = old.copy()
        new[2] += 1
        before = float(sim.data.time)
        # free joint 的 qpos 是 xyz + wxyz 四元数。
        # 注意它不同于观测字典中的 xyzw 顺序。
        sim.data.set_joint_qpos(joint, new)
        sim.data.set_joint_qvel(joint, np.zeros(6))

        obs = fresh_obs(env)

        assert sim.data.time == before
        np.testing.assert_allclose(
            sim.data.get_joint_qpos(joint), new
        )

        frames(cfg.out, obs, "teleport_immediate")
        emit(report, "teleport_test", {
            "object": name,
            "old_free_joint_qpos": old,
            "new_free_joint_qpos": new,
            "sim_time_unchanged": True,
            "contacts_after_edit": contacts(env),
        })
        rows=[]
        start_time=float(sim.data.time)

        # 恢复推进物理后，物体会继续受重力和接触影响。
        for step in range(20):
            if step > 0:
                obs, _, _, _ = env.step(ZERO)
            position=sim.data.body_xpos[body_id].copy()
            rows.append({
                "step": step,
                "elapsed_sim_s": float(sim.data.time) - start_time,
                "x": float(position[0]),
                "y": float(position[1]),
                "z": float(position[2]),
            })
            frames(cfg.out, {"agentview_image": obs["agentview_image"]}, f"move+{step}")
        csv_out(
            cfg.out,"move_item_5cm_up", rows
        )
    finally:
        env.close()