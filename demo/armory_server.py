"""Compose Armory's original server, scheduler and GPU worker with a Pi0.5 factory."""
import os
import argparse
import multiprocessing as mp
import sys
from pathlib import Path
ARMORY=Path(os.environ.get("ARMORY_ROOT","/root/work/armory"))
sys.path[:0]=[str(ARMORY/"src"),str(ARMORY/"armory-client/src")]
from armory.serving.config import ServerConfig
from armory.serving.protocol import SchedulerConfig,ServerMetadata
from armory.serving.server import PolicyServer
from armory_backend import Pi05Factory

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--out",type=Path,required=True)
    ap.add_argument("--port",type=int,default=8080)
    args=ap.parse_args()
    config=ServerConfig(max_batch_size=1,output_dir=args.out,
        scheduler=SchedulerConfig(scheduling_algorithm="greedy-deadline"))
    metadata=ServerMetadata(config_name="lerobot_pi05_libero_finetuned",
        checkpoint_dir=str(Path(__file__).resolve().parents[1]/"models/pi05_finetuned"),
        action_horizon=50,action_dim=7,num_steps=10,max_batch_size=1,env="libero",
        scheduling_algorithm="greedy-deadline")
    PolicyServer(metadata,Pi05Factory(args.out/"server"),config).serve_forever(host="127.0.0.1",port=args.port)
if __name__=="__main__":
    mp.set_start_method("fork",force=True)
    main()
