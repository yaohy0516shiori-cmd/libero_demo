"""Summarize native Armory evidence and export an annotated fleet video."""
import argparse,json,math
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import imageio.v2 as imageio
from PIL import Image,ImageDraw,ImageFont

# jason reader -->list[dict]
def read_jsonl(path):
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]

def analyze(root):
    summaries=[];checks=[];joined_all=[]
    for run in sorted(root.glob("n[14]")):
        n=int(run.name[1:]);client=run/"client";server=run/"serve/server"
        model=pd.DataFrame(read_jsonl(server/"model_stages.jsonl"))
        
        # Excluding the warm up data, the initialization loading time for the first run is extremely long, resulting in abnormal leatency.
        model=model[model.robot_id!="__warmup__"].copy()
        if "inference_entry_mono_s" not in model or model.observation_mono_s.isna().any():
            raise ValueError("Use monotonic-instrumented runs; historical EGL logs require separate analysis")
        
        # rename and store
        model["selected_observation_age_ms"]=(model.inference_entry_mono_s-model.observation_mono_s)*1000
        model["inference_entry_timestamp"]=model.inference_entry_mono_s
        model["inference_exit_timestamp"]=model.inference_exit_mono_s
        model.to_csv(run/"model_stages.csv",index=False)
        
        # crossing verification by using client result record and 
        results=pd.read_csv(client/"results.csv")
        traces={};responses={}
        for robot in range(n):
            d=client/"demo_trace"/f"robot_{robot}"
            trace=pd.DataFrame([r for r in read_jsonl(d/"stages.jsonl") if r["kind"]=="step"])
            for field in ("started","finished","env_finished"):
                trace[field]=trace[field+"_mono_s"]
            assert (trace.finished>=trace.started).all()
            traces[robot]=trace
            trace.to_csv(d/"stages.csv",index=False)
            chunks=[]
            for ep in sorted((client/str(robot)).glob("*")):
                f=ep/"action_chunks.parquet"
                if f.exists():
                    frame=pd.read_parquet(f);frame["episode_folder"]=ep.name;chunks.append(frame)
                if (ep/"steps.parquet").exists():
                    steps=pd.read_parquet(ep/"steps.parquet")
                    episode=int(ep.name.split("_")[0])
                    rec=trace[trace.episode==episode].set_index("step").loc[steps.env_step]
                    np.testing.assert_array_equal(rec.action_chunk_index.fillna(-1).values,steps.action_chunk_index.fillna(-1).values)
                    checks.append(f"{run.name}/robot_{robot}/{episode}: native and instrumented action source match")
            # 合并action chunk
            if chunks:
                chunks=pd.concat(chunks,ignore_index=True)
                chunks=chunks.drop_duplicates("request_id")
                responses[robot]=chunks
            else:
                chunks=pd.DataFrame(columns=["request_id","request_timestamp","response_timestamp"])
                responses[robot]=chunks
            
            # 
            mr=model[model.robot_id==f"robot_{robot}"].copy()
            assert (mr.inference_exit_timestamp>=mr.inference_entry_timestamp).all()
            assert (mr.selected_observation_age_ms>=-.01).all()
            response_path=d/"responses.jsonl"
            receipts=pd.DataFrame(read_jsonl(response_path)) if response_path.exists() else pd.DataFrame()
            if len(receipts):
                merged=mr.merge(receipts[["request_id","received_mono_s"]],on="request_id",how="inner",validate="one_to_one")
                merged["observation_to_response_ms"]=(merged.received_mono_s-merged.observation_mono_s)*1000
                server_part=merged[["preprocess_ms","inference_ms","postprocess_ms","selected_observation_age_ms"]].sum(axis=1)
                assert (merged.observation_to_response_ms+2>=server_part).all()
                merged["N"]=n;joined_all.append(merged)
                rtt=merged.observation_to_response_ms
                gaps=np.concatenate([np.diff(group.sort_values("received_mono_s").received_mono_s)*1000
                                     for _,group in merged.groupby("observation_episode")]) if len(merged) else np.array([])
            else:
                rtt=pd.Series(dtype=float);gaps=np.array([])
            for episode,rows in trace.groupby("episode"):
                np.testing.assert_allclose(rows.sim_time_s,np.arange(1,len(rows)+1)*.05,atol=1e-6)
            rr=results[results.robot_idx==robot]
            summaries.append(dict(N=n,robot=robot,episodes=len(rr),successful_episodes=int(rr.success.sum()),
                truncated_episodes=int(rr.truncated.sum()),recorded_native_steps=int(rr.observed_steps.sum()),
                starvation_steps=int(rr.starvation_steps.sum()),
                post_first_starvation_steps=int(rr.post_first_starvation_steps.sum()),
                post_first_observed_steps=int(rr.post_first_observed_steps.sum()),
                delivered_chunks=len(chunks),model_calls=len(mr),
                inference_mean_ms=float(mr.inference_ms.mean()),inference_p95_ms=float(mr.inference_ms.quantile(.95)),
                selected_observation_age_mean_ms=float(mr.selected_observation_age_ms.mean()),
                preprocess_mean_ms=float(mr.preprocess_ms.mean()),postprocess_mean_ms=float(mr.postprocess_ms.mean()),
                observation_to_response_mean_ms=float(rtt.mean()),response_gap_mean_ms=float(gaps.mean()) if len(gaps) else None,
                observation_prepare_mean_ms=float(trace.observation_prepare_ms.mean()),
                select_and_send_mean_ms=float(trace.select_action_and_send_ms.mean()),
                env_step_with_camera_mean_ms=float(trace.env_step_with_camera_ms.mean()),
                video_render_mean_ms=float(trace.video_render_ms.mean()),
                video_encode_mean_ms=float(trace.video_encode_ms.mean()),
                measured_steps_per_wall_s=len(trace)/(trace.finished.max()-trace.started.min()),
                peak_model_allocated_mib=float(mr.peak_allocated_mib.max())))
        draw_timing(run,model,traces)
        wall_video(run,traces,model)
        if n==1 and results.success.any():
            episode=int(results[results.success].iloc[0].episode_idx)
            wall_video(run,{0:traces[0][traces[0].episode==episode].reset_index(drop=True)},model,
                       output_name="successful_episode_wall_clock",speed=1)
    df=pd.DataFrame(summaries);df.to_csv(root/"comparison.csv",index=False)
    if joined_all:pd.concat(joined_all).to_csv(root/"delivered_requests.csv",index=False)
    (root/"validation.json").write_text(json.dumps({"passed":True,"checks":checks+[
        "server phases fit within selected observation ready to response duration (monotonic clock)","simulation advances 0.05 s per environment step",
        "only actual trained model calls counted; warmup excluded"]},indent=2))
    print(df.to_string(index=False))

def draw_timing(run,model,traces):
    start=min(df.started.min() for df in traces.values())
    fig,(ax,bx)=plt.subplots(2,1,figsize=(13,7),layout="constrained",gridspec_kw={"height_ratios":[1,1.6]})
    ids=sorted(traces);bottom=np.zeros(len(ids))
    for field,label,color in [("selected_observation_age_ms","Selected observation age","#db9655"),
            ("preprocess_ms","Preprocess","#91b4cd"),("inference_ms","Inference","#3d6c9c"),
            ("postprocess_ms","Postprocess","#79ad9a")]:
        values=np.array([model[model.robot_id==f"robot_{i}"][field].mean()/1000 for i in ids])
        ax.bar(ids,values,bottom=bottom,label=label,color=color);bottom+=values
    ax.set_xticks(ids,[f"Robot {i+1}" for i in ids]);ax.set_ylabel("Mean seconds / served observation")
    ax.set_title(f"Armory {run.name.upper()} | native Pi0.5 | max GPU batch = 1")
    ax.legend(ncols=4,fontsize=8)
    for i,trace in traces.items():
        for _,r in model[model.robot_id==f"robot_{i}"].iterrows():
            bx.broken_barh([(r.inference_entry_timestamp-start,r.inference_exit_timestamp-r.inference_entry_timestamp)],
                          (i+.1,.22),facecolors="#3d6c9c")
        for _,r in trace.iterrows():
            color="#db9655" if pd.isna(r.action_chunk_index) else "#79ad9a"
            bx.broken_barh([(r.started-start,r.finished-r.started)],(i-.28,.3),facecolors=color)
    bx.set_yticks(ids,[f"Robot {i+1}" for i in ids]);bx.set_xlabel("Elapsed real seconds (monotonic clock)")
    bx.set_title("Upper blue: model service | Lower green: model action, orange: null action")
    bx.set_ylim(-.5,max(ids)+.6)
    fig.savefig(run/"timing.png",dpi=180);plt.close(fig)

def wall_video(run,traces,model,output_name="demo_wall_clock",speed=2):
    ids=sorted(traces);n=len(ids);cols=1 if n==1 else 2;rows=math.ceil(n/cols)
    width,height=512,608
    font=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",17)
    start=min(df.started.min() for df in traces.values());end=max(df.finished.max() for df in traces.values())
    readers={};opened_episode={};last_frames={}
    fps=10
    writer=imageio.get_writer(run/f"{output_name}.mp4",fps=fps,codec="libx264",quality=8,macro_block_size=16)
    times=np.arange(start,end+speed,speed/fps)
    try:
        for frame_no,t in enumerate(times):
            canvas=Image.new("RGB",(width*cols,height*rows),(17,24,36));draw=ImageDraw.Draw(canvas)
            for cell,i in enumerate(ids):
                df=traces[i];index=np.searchsorted(df.finished.values,t,side="right")-1
                d=run/"client/demo_trace"/f"robot_{i}"
                if index<0:
                    image=np.asarray(Image.open(d/f"episode_{int(df.iloc[0].episode)}_initial.png"));sim=0;left=0;episode=int(df.iloc[0].episode);source="READY"
                else:
                    r=df.iloc[index];episode=int(r.episode);sim=r.sim_time_s;left=int(r.actions_left)
                    if opened_episode.get(i)!=episode:
                        if i in readers:readers[i].close()
                        readers[i]=imageio.get_reader(d/f"episode_{episode}.mp4")
                        opened_episode[i]=episode
                    image=readers[i].get_data(int(r.step))
                    source="NULL ACTION" if pd.isna(r.action_chunk_index) else "MODEL ACTION"
                    if r.success:source="SUCCESS"
                busy=model[(model.robot_id==f"robot_{i}")&(model.inference_entry_timestamp<=t)&(model.inference_exit_timestamp>t)]
                serving="MODEL INFERENCE" if len(busy) else "MODEL SERVING OTHER / IDLE"
                x=(cell%cols)*width;y=(cell//cols)*height
                canvas.paste(Image.fromarray(image),(x,y))
                draw.text((x+10,y+517),f"Armory | Robot {i+1} | episode {episode+1}",font=font,fill="white")
                draw.text((x+10,y+539),f"{source} | actions left {left}",font=font,fill="#ffcc80" if source=="NULL ACTION" else "#7ed4ae")
                draw.text((x+10,y+561),f"Wall {t-start:.1f}s | sim in episode {sim:.2f}s",font=font,fill="white")
                draw.text((x+10,y+583),f"{serving} | {speed}x real-time playback",font=font,fill="#a9bdde")
            writer.append_data(np.asarray(canvas))
            if frame_no==len(times)//2:canvas.save(run/f"{output_name}_preview.png")
        (run/f"{output_name}.json").write_text(json.dumps(dict(time_basis="monotonic_elapsed_real_time",playback_speed=speed,
            output_fps=fps,wall_duration_s=end-start,source="recorded simulation frames and Armory inference timestamps"),indent=2))
    finally:
        writer.close()
        for reader in readers.values():reader.close()

if __name__=="__main__":
    ap=argparse.ArgumentParser();ap.add_argument("run",type=Path);analyze(ap.parse_args().run)
