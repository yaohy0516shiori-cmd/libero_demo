"""Use Armory's native fleet runner and PolicyAgent; add observation-only timing/video hooks."""
import os
os.environ.setdefault("MUJOCO_GL","egl")
import sys
from pathlib import Path
# 路径注入
ARMORY=Path(os.environ.get("ARMORY_ROOT","/root/work/armory"))
sys.path[:0]=[str(ARMORY),str(ARMORY/"src"),str(ARMORY/"src/backends"),
              str(ARMORY/"armory-client/src"),str(ARMORY/"third_party/libero")]
import argparse,json,time,multiprocessing,dataclasses
import numpy as np
import imageio.v2 as imageio
from PIL import Image
import scripts.run as runner # armory/scripts/run
from evaluation.envs.libero import LiberoSimEnvironment,LiberoObservation
import evaluation.envs.libero as libero_environment
from armory_client.client import BidirectionalWebsocket
from evaluation.runtime import Runtime as OriginalRuntime
from evaluation.types import ExperimentConfig
from armory.serving.protocol import SchedulerConfig

# 增加观测时间戳和回合数
@dataclasses.dataclass
class TimedObservation(LiberoObservation):
    demo_observation_mono_s: float
    demo_episode: int

# 记录回复时间戳
class MeasuredWebsocket(BidirectionalWebsocket):
    def receive(self):
        reply=super().receive()
        row=dict(request_id=reply.request_id,robot_id=self._robot_id,
                 received_mono_s=time.perf_counter(),received_wall_s=time.time())
        with (TRACE_ROOT/self._robot_id/"responses.jsonl").open("a") as f:
            f.write(json.dumps(row)+"\n")
        return reply

original_renderer_check=libero_environment._assert_egl_rendering

def verify_requested_renderer():
    if os.environ.get("MUJOCO_GL")=="osmesa":
        from OpenGL import GL
        renderer=GL.glGetString(GL.GL_RENDERER)
        if not renderer:raise RuntimeError("OSMesa renderer not initialized")
        print("Explicit CPU rendering:",renderer.decode(),flush=True)
    else:original_renderer_check()

libero_environment._assert_egl_rendering=verify_requested_renderer

class MeasuredEnvironment(LiberoSimEnvironment):

    def __init__(self,*args,trace_dir,**kwargs):
        self.trace_dir=Path(trace_dir);self.trace_dir.mkdir(parents=True,exist_ok=True)
        self.video=None;self.episode=-1
        super().__init__(*args,**kwargs)
        self.records=(self.trace_dir/"stages.jsonl").open("w")

    def reset(self):
        # 每次环境重置，它会记录“重置+稳定”耗时。然后立刻创建一个视频写入器，准备录制这一回合的 MP4。同时渲染并保存第一帧为初始帧 PNG。
        if self.video:self.video.close();self.video=None
        started=time.time();m0=time.perf_counter();super().reset();finished=time.time();m1=time.perf_counter()
        self.episode+=1;self.sim_start=float(self._env.sim.data.time)
        self.records.write(json.dumps(dict(kind="reset",episode=self.episode,
            started=started,finished=finished,reset_and_settle_ms=(m1-m0)*1000,started_mono_s=m0,finished_mono_s=m1,
            task=self.task_language))+"\n");self.records.flush()
        self.video=imageio.get_writer(self.trace_dir/f"episode_{self.episode}.mp4",
            fps=20,codec="libx264",quality=8,macro_block_size=16)
        initial=self._env.sim.render(width=512,height=512,camera_name="agentview")[::-1].copy()
        Image.fromarray(initial).save(self.trace_dir/f"episode_{self.episode}_initial.png")

    def get_observation(self):
        # 调用 get_observation() 时，实际返回的是我们包装过的 TimedObservation，并打上了当前单调时钟的时间戳。
        obs=super().get_observation()
        return TimedObservation(**vars(obs),demo_observation_mono_s=time.perf_counter(),demo_episode=self.episode)

    def record_step(self,obs,action,t0,t1,t2,t3,m0,m1,m2,m3):
        '''
        analyze_armory里 stages.jsonl 数据来源
        接收 8 个时间戳（墙钟+单调时钟）
        计算各个阶段的耗时（观测准备、选择动作并发送、环境步进+相机、视频渲染、视频编码）
        记录当前动作的详细信息（动作块索引、剩余动作数、成功状态等），写入日志
        '''
        image=self._env.sim.render(width=512,height=512,camera_name="agentview")[::-1].copy()
        rendered=time.time();m4=time.perf_counter();self.video.append_data(image);saved=time.time();m5=time.perf_counter()
        row=dict(kind="step",episode=self.episode,step=obs.step,
            started=t0,observation_finished=t1,action_selected=t2,env_finished=t3,finished=saved,
            started_mono_s=m0,observation_finished_mono_s=m1,action_selected_mono_s=m2,env_finished_mono_s=m3,finished_mono_s=m5,
            wall_clock_interval_error_ms=((saved-t0)-(m5-m0))*1000,
            observation_prepare_ms=(m1-m0)*1000,select_action_and_send_ms=(m2-m1)*1000,
            env_step_with_camera_ms=(m3-m2)*1000,video_render_ms=(m4-m3)*1000,
            video_encode_ms=(m5-m4)*1000,sim_time_s=float(self._env.sim.data.time)-self.sim_start,
            action_chunk_index=action.action_chunk_index,action_index=action.index_in_chunk,
            actions_left=action.actions_left,action=np.asarray(action.action).tolist(),
            success=self.current_success)
        self.records.write(json.dumps(row)+"\n");self.records.flush()
    def close(self):
        if self.video:self.video.close()
        self.records.close();super().close()

# 记录每一部分运行时间
class MeasuredRuntime(OriginalRuntime):
    def _step(self):
        t0=time.time();m0=time.perf_counter();obs=self._environment.get_observation();t1=time.time();m1=time.perf_counter()
        action=self._agent.get_action(obs);t2=time.time();m2=time.perf_counter()
        self._environment.apply_action(action);t3=time.time();m3=time.perf_counter()
        self._environment.record_step(obs,action,t0,t1,t2,t3,m0,m1,m2,m3)
        return obs,action

def create_environment(config,robot_idx,libero_spec=None):
    return MeasuredEnvironment(libero_spec,max_episode_steps=config.environment.max_steps_per_episode,
        seed=config.seed+robot_idx,trace_dir=TRACE_ROOT/f"robot_{robot_idx}")

# The spawn/forkserver child imports this entrypoint too; these assignments preserve
# the native run_robot/run_fleet control flow in every process.
TRACE_ROOT=Path(os.environ.get("ARMORY_DEMO_TRACE_ROOT","/tmp/armory_demo_missing_trace_path"))
runner.create_environment=create_environment
runner.Runtime=MeasuredRuntime
runner.BidirectionalWebsocket=MeasuredWebsocket

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--robots",type=int,required=True);ap.add_argument("--out",type=Path,required=True)
    ap.add_argument("--seconds",type=float,default=90);ap.add_argument("--port",type=int,default=8080)
    ap.add_argument("--control-hz",type=int,default=20)
    ap.add_argument("--host",default="127.0.0.1",help="address of the model server")
    args=ap.parse_args()
    if args.robots not in (1,4):raise ValueError("Choose N=1 or N=4 for the requested demos")
    global TRACE_ROOT
    TRACE_ROOT=args.out/"demo_trace";os.environ["ARMORY_DEMO_TRACE_ROOT"]=str(TRACE_ROOT)
    robot=dict(control_hz=args.control_hz,execution_horizon={"min":1,"max":10})
    config=ExperimentConfig.model_validate(dict(
        environment={"kind":"libero","task_suite_name":"libero_spatial","max_steps_per_episode":280},
        robots=[robot for _ in range(args.robots)],time_limit=args.seconds,seed=7))
    runner.main(runner.Args(experiment_config=config,output_dir=args.out,host=args.host,port=args.port,
        scheduler_config=SchedulerConfig(scheduling_algorithm="greedy-deadline")))
if __name__=="__main__":
    multiprocessing.set_start_method("forkserver")
    main()
