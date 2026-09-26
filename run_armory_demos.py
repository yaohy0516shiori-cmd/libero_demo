"""Run both demonstrations through Armory; one fresh server per condition."""
import argparse,json,os,signal,subprocess,time,urllib.request
import psutil
from pathlib import Path
ROOT=Path(__file__).resolve().parent
PY=ROOT/".venv/bin/python"
ARMORY=Path(os.environ.get("ARMORY_ROOT","/root/work/armory"))
ENV_PY=ARMORY/".venv/bin/python"

def stop(process: subprocess.Popen):
    if process.poll() is None:
        process.terminate()
        try:process.wait(timeout=15)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid,signal.SIGKILL);process.wait()

def main():
    # 命令行参数
    ap=argparse.ArgumentParser()
    ap.add_argument("--robots",type=int,nargs="+",default=[1,4])
    ap.add_argument("--seconds",type=float,default=120)
    ap.add_argument("--port",type=int,default=8080)
    ap.add_argument("--control-hz",type=int,default=20)
    ap.add_argument("--renderer",choices=["egl","osmesa"],default="osmesa")
    ap.add_argument("--out",type=Path)
    args=ap.parse_args()
    if any(n not in (1,4) for n in args.robots):raise ValueError("Choose N=1 and/or N=4")

    # 输出目录
    out=args.out or ROOT/"results"/time.strftime("armory_%Y%m%d_%H%M%S")
    out.mkdir(parents=True,exist_ok=False)

    # test mainfest
    manifest=vars(args).copy();manifest["out"]=str(out)
    manifest.update(model="lerobot/pi05_libero_finetuned",
        revision="8e174154ef5f6c60a8da12ae99c303d8963138c1",
        framework="Armory original server/scheduler/PolicyAgent/action broker",
        max_batch_size=1,wait_semantics="asynchronous; consume old actions, then null actions",
        started_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime()),
        armory_commit=subprocess.check_output(["git","-C",str(ARMORY),"rev-parse","HEAD"],text=True).strip())
    (out/"run.json").write_text(json.dumps(manifest,indent=2))
    print("OUTPUT",out,flush=True)

    # env config and start armory
    for n in args.robots:
        run=out/f"n{n}";run.mkdir()
        env=os.environ.copy();env["TOKENIZERS_PARALLELISM"]="false"
        env["MUJOCO_GL"]=args.renderer
        if args.renderer=="osmesa":env["LP_NUM_THREADS"]="2"
        server_log=(run/"server.log").open("w")
        server=subprocess.Popen([str(PY),"-u",str(ROOT/"demo/armory_server.py"),"--out",str(run/"serve"),
            "--port",str(args.port)],stdout=server_log,stderr=subprocess.STDOUT,env=env,start_new_session=True)
        client=None;telemetry=None;gpu_log=None

        # 检查僵尸进程。防止子进程崩掉父进程还在跑
        try:
            deadline=time.monotonic()+900
            while True:
                if server.poll() is not None:raise RuntimeError(f"N={n} server exited; see {run/'server.log'}")
                if any(child.status()==psutil.STATUS_ZOMBIE for child in psutil.Process(server.pid).children()):
                    raise RuntimeError(f"N={n} backend child failed during startup; see {run/'server.log'}")
                try:
                    with urllib.request.urlopen(f"http://127.0.0.1:{args.port}/metadata",timeout=2) as r:
                        metadata=json.load(r)
                    if metadata["config_name"]!="lerobot_pi05_libero_finetuned":raise RuntimeError("Wrong server on port")
                    break
                except (OSError,TimeoutError):
                    if time.monotonic()>deadline:raise TimeoutError("Armory startup timed out")
                    time.sleep(1)
            print(f"N={n} Armory model loaded, warmed and profiled",flush=True)

            # GPU 开销记录
            gpu_log=(run/"gpu.csv").open("w")
            telemetry=subprocess.Popen(["nvidia-smi","--query-gpu=timestamp,memory.used,memory.free,utilization.gpu","--format=csv","--loop=1"],stdout=gpu_log,stderr=subprocess.STDOUT,start_new_session=True)
            
            # listen，记录日志
            with (run/"client.log").open("w") as log:
                command=[str(ENV_PY),"-u",str(ROOT/"demo/armory_client_demo.py"),"--robots",str(n),
                    "--out",str(run/"client"),"--seconds",str(args.seconds),"--port",str(args.port),
                    "--control-hz",str(args.control_hz)]
                client=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT,env=env,start_new_session=True)
                deadline=time.monotonic()+args.seconds+300
                while client.poll() is None:
                    if server.poll() is not None:raise RuntimeError("Armory server failed during rollout")
                    if time.monotonic()>deadline:raise TimeoutError("Armory rollout did not finish on time")
                    time.sleep(1)
                if client.returncode!=0:raise RuntimeError(f"N={n} client failed; see {run/'client.log'}")
            print(f"N={n} finished",flush=True)

        # 释放资源
        finally:
            if client is not None:stop(client)
            stop(server);server_log.close()
            if telemetry is not None:stop(telemetry)
            if gpu_log is not None:gpu_log.close()
    (out/"COMPLETE").write_text("Both requested conditions finished; recorded successes/failures are in client results.")
    print("ARMORY_DEMOS_COMPLETE",out,flush=True)
if __name__=="__main__":main()
