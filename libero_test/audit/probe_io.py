from __future__ import annotations

import numpy as np
import robosuite.utils.transform_utils as T

from libero.libero.benchmark import Benchmark, Task
from libero.libero.envs.env_wrapper import ControlEnv
from libero.libero.envs.bddl_base_domain import BDDLBaseDomain
from robosuite.controllers.osc import OperationalSpaceController
from robosuite.robots.single_arm import SingleArm
from robosuite.utils.binding_utils import MjSim

from common import AuditConfig, Observation, Record, Report, ZERO
from common import create, restore, emit, source, frames
from probe_stability import contacts


def check_observations(
    env: ControlEnv,
    obs: Observation,
    report: Report,
) -> None:
    '''
    check output obs
    args:
        env: env wrapper; env.sim gives the raw MuJoCo data used as
             ground truth to verify obs against
        obs: observation dict returned by the env
        report: used to store result
    '''
    # the robosuite env built from the bddl file (step / reward /
    # success live here); the parsed bddl text is inner.parsed_problem
    inner: BDDLBaseDomain = env.env
    sim: MjSim = env.sim
    robot: SingleArm = inner.robots[0]

    fields: dict[str, Record] = {}
    # record shape/dtype/value into the report; images keep only
    # shape+dtype (value=None) to keep the JSON small
    for key, value in obs.items():
        array = np.asarray(value)
        fields[key] = {
            "shape": array.shape,
            "dtype": str(array.dtype),
            "value": None if key.endswith("_image") else array,
        }

    emit(report, "observations", {
        "field_count": len(obs),
        "fields": fields,
    })

    # 验证 proprio-state / object-state 是哪些字段拼接而成。
    for modality in ["robot0_proprio", "object"]:
        keys = [
            key
            for key, item in inner._observables.items()
            if item.is_enabled()
            and item.is_active()
            and item.modality == modality
        ]

        offset = 0
        layout: list[Record] = []
        parts = []

        for key in keys:
            value = np.asarray(obs[key]).reshape(-1)
            layout.append({
                "field": key,
                "start": offset,
                "stop": offset + value.size,
            })
            offset += value.size
            parts.append(value)

        np.testing.assert_allclose(
            np.concatenate(parts),
            obs[modality + "-state"],
        )
        emit(report, modality + "_layout", layout)

    # 验证末端位置是世界坐标；观测四元数顺序是 xyzw。
    np.testing.assert_allclose(
        obs["robot0_eef_pos"],
        sim.data.site_xpos[robot.eef_site_id],
    )
    quat = T.convert_quat(
        sim.data.get_body_xquat(robot.robot_model.eef_name),
        to="xyzw",
    )
    np.testing.assert_allclose(obs["robot0_eef_quat"], quat)

    rotation = T.quat2mat(obs["robot0_eef_quat"])

    for obj in inner.objects:
        name = obj.name
        body_id = sim.model.body_name2id(obj.root_body)

        np.testing.assert_allclose(
            obs[name + "_pos"],
            sim.data.body_xpos[body_id],
        )
        np.testing.assert_allclose(
            obs[name + "_quat"],
            T.convert_quat(
                sim.data.body_xquat[body_id], to="xyzw"
            ),
        )

        # 相对位置是在末端坐标系中表达，不只是世界坐标相减。
        relative_pos = rotation.T @ (
            obs[name + "_pos"] - obs["robot0_eef_pos"]
        )
        np.testing.assert_allclose(
            obs[name + "_to_robot0_eef_pos"],
            relative_pos,
            atol=1e-6,
        )

    emit(
        report,
        "coordinate_checks",
        "PASS: world position, xyzw, relative position in eef frame",
    )


def check_gripper(
    env: ControlEnv,
    suite: Benchmark,
    cfg: AuditConfig,
    report: Report,
) -> None:
    '''
    check -1/0/1 meanings in gripper.
    suite: the benchmark (task list, language, 50 init states per task)
    cfg: selects suite / task / init state to test
    '''
    robot: SingleArm = env.env.robots[0]
    trials: list[Record] = []

    # 每次独立恢复初态，避免前一次动作影响下一次比较。
    for command in [-1.0, 0.0, 1.0]:
        restore(env, suite, cfg.task, cfg.init)

        start = env.sim.data.qpos[
            robot._ref_gripper_joint_pos_indexes
        ].copy()

        action = ZERO.copy()
        action[-1] = command

        for _ in range(20):
            obs, _, _, _ = env.step(action)

        qpos = obs["robot0_gripper_qpos"].copy()
        target = robot.gripper.current_action.copy()

        for _ in range(5):
            env.step(ZERO)

        # 零夹爪命令保持内部目标；不等于瞬间冻结关节位置。
        np.testing.assert_allclose(
            robot.gripper.current_action, target
        )

        trials.append({
            "command": command,
            "start_qpos": start,
            "end_qpos": qpos,
            "internal_target": target,
            "zero_preserved_target": True,
        })

    emit(
        report,
        "gripper_trials_minus1_open_plus1_close",
        trials,
    )


def check_armory(
    obs: Observation,
    task: Task,
    report: Report,
) -> None:
    try:
        from evaluation.envs.libero import LiberoSimEnvironment
        from armory_client import msgpack_numpy
    except ImportError as error:
        emit(report, "armory_NOT_TESTED", str(error))
        return

    # 只检查当前 Armory 的预处理函数：
    # 不执行构造函数，不创建第二个环境，不启动服务器。
    adapter: LiberoSimEnvironment = object.__new__(
        LiberoSimEnvironment
    )
    adapter._last_obs = obs
    adapter._step_counter = 0
    adapter._task_description = task.language

    packet = adapter.get_observation() # real field that used in armory
    assert packet.state.shape == (8,)

    emit(report, "armory_preprocessing", {
        "state": packet.state,
        "image_shape": packet.image.shape,
        "wrist_shape": packet.wrist_image.shape,
        "dtype": str(packet.image.dtype),
        "prompt": packet.prompt,
        "source": source(LiberoSimEnvironment.get_observation),
        "stop_logic": source(LiberoSimEnvironment.apply_action),
    })

    payload = {
        "image": packet.image,
        "wrist_image": packet.wrist_image,
        "state": packet.state,
        "prompt": packet.prompt,
    }
    # package data and decode,
    packed = msgpack_numpy.packb(payload)
    decoded = msgpack_numpy.unpackb(packed)
    # 检查：数据变成字节，再还原后，是否与打包前一致。
    np.testing.assert_array_equal(
        decoded["image"], packet.image
    )

    emit(report, "armory_serialization", {
        "payload_bytes": len(packed),
        "lossless_roundtrip": True,
        "pack_array_source": source(msgpack_numpy.pack_array),
    })


def inspect_case(
    cfg: AuditConfig,
    report: Report,
) -> None:
    # create/restore env 
    env, suite, task, path = create(cfg)

    try:
        obs, states = restore(env, suite, cfg.task, cfg.init)

        inner: BDDLBaseDomain = env.env
        sim: MjSim = env.sim
        robot: SingleArm = inner.robots[0]

        controller = robot.controller
        assert isinstance(controller, OperationalSpaceController)
        assert inner.action_dim == 7
        assert controller.control_dim == 6
        assert controller.use_delta

        emit(report, "task", {
            "name": task.name,
            "prompt": task.language,
            "bddl": str(path),
            "parsed": inner.parsed_problem,
        })

        emit(report, "action", {
            "controller": type(controller).__name__,
            "name": controller.name,
            "dimension": inner.action_dim,
            "limits": inner.action_spec,
            "delta": controller.use_delta,
            "input_min": controller.input_min,
            "input_max": controller.input_max,
            "output_min": controller.output_min,
            "output_max": controller.output_max,
            # shows how [-1,1] maps to a per-step delta;
            # pure arithmetic, the sim is not advanced
            "scaled_example": controller.scale_action(
                np.array([.2, 0, 0, 0, 0, 0])
            ),
        })

        emit(report, "initial_state", {
            "count": len(states),
            "shape": states[cfg.init].shape,
            "time": sim.data.time,
            "nq": sim.model.nq,
            "nv": sim.model.nv,
            "expected_flat_length": 1 + sim.model.nq + sim.model.nv,
            "qvel": sim.data.qvel.copy(),
            "all_qvel_zero": bool(
                np.allclose(sim.data.qvel, 0)
            ),
        })
        assert (
            states[cfg.init].size
            == 1 + sim.model.nq + sim.model.nv
        )

        emit(report, "initial_contacts", contacts(env))
        # verifies what each obs field means: layout, frame, quat order
        check_observations(env, obs, report)
        frames(cfg.out, obs, "initial")

        emit(report, "semantics_source", {
            "reward": source(inner.reward),
            "success": source(inner._check_success),
            "libero_step": source(inner.step),
            "gripper": source(robot.gripper.format_action),
        })

        evaluate = getattr(inner, "_eval_predicate")
        emit(report, "goal_predicates", [
            {
                "predicate": item,
                "satisfied": bool(evaluate(item)),
            }
            for item in inner.parsed_problem["goal_state"]
        ])

        before = float(sim.data.time)
        # first real step of this probe: restore() only does
        # set_state + forward, it does not advance sim time
        _, reward, done, info = env.step(ZERO)
        assert bool(done) == bool(inner._check_success())

        emit(report, "time_model", {
            "control_hz": inner.control_freq, # 20 Hz; its reciprocal is the step length
            "nominal_step_s": inner.control_timestep, # = 1 / control_hz
            "measured_step_s": sim.data.time - before, # sim time advanced by one env.step(); checked against the nominal value
            "physics_dt_s": sim.model.opt.timestep,  # a physical step execute time
            "scheduled_substeps": int(
                inner.control_timestep / inner.model_timestep
            ), # how many physics step in one control step
            "horizon": inner.horizon, # maximum execute steps num in one episode
            "horizon_sim_s": inner.horizon / inner.control_freq, # time
            "chunk50_sim_s": 50 / inner.control_freq, # 50 is Armory's chunk length; LIBERO itself has no chunk concept
            "reward": reward,
            "returned_done": done,
            "underlying_done": inner.done,
            "info": info,
        })

        # 区分 LIBERO 返回的成功标记与底层 horizon 标记。
        old_horizon = inner.horizon
        try:
            restore(env, suite, cfg.task, cfg.init) # restore env
            # shrink the horizon to force a horizon termination:
            # env.step returns the SUCCESS flag, while inner.done is the
            # underlying termination flag -> here done=True, success=False
            inner.horizon = 3

            rows: list[Record] = []
            for step in range(3):
                _, reward, success, _ = env.step(ZERO)
                rows.append({
                    "step": step + 1,
                    "reward": float(reward),
                    "returned_success": bool(success),
                    "underlying_done": bool(inner.done),
                })

            assert inner.done
            emit(report, "horizon_test", rows)
        finally:
            inner.horizon = old_horizon # restore

        check_gripper(env, suite, cfg, report) 

        obs, _ = restore(env, suite, cfg.task, cfg.init)
        check_armory(obs, task, report)

    finally:
        env.close()