"""Resumable HTTPS byte ranges, using the official pinned checkpoint URL."""
import concurrent.futures, hashlib, json, os, time, urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
DEST=ROOT/"models/pi05_finetuned/model.safetensors"
SIZE=7473096344
CHUNK=32*1024*1024
URL="https://huggingface.co/lerobot/pi05_libero_finetuned/resolve/8e174154ef5f6c60a8da12ae99c303d8963138c1/model.safetensors"
SHA="877b3ec1130548b69af7f8aeef3ec9d3fc7738040f0b9beb490857ec970997ae"
part=DEST.with_suffix(".part")
manifest=DEST.with_suffix(".parts.json")
done=set(json.loads(manifest.read_text())) if manifest.exists() else set()
if not part.exists():
    candidates=list((DEST.parent/".cache/huggingface/download").glob("*.incomplete"))
    candidate=max(candidates,key=lambda x:x.stat().st_size) if candidates else None
    if candidate and candidate.stat().st_size:
        completed=candidate.stat().st_size//CHUNK
        with candidate.open("rb") as src,part.open("wb") as dst:
            for _ in range(completed):dst.write(src.read(CHUNK))
        done=set(range(completed))
    else:part.touch()
    manifest.write_text(json.dumps(sorted(done)))
fd=os.open(part,os.O_RDWR)
os.ftruncate(fd,SIZE)
def fetch(i):
    start=i*CHUNK;end=min(SIZE,(i+1)*CHUNK)-1
    for attempt in range(5):
        try:
            req=urllib.request.Request(URL+f"?download=true&part={i}",headers={"Range":f"bytes={start}-{end}"})
            with urllib.request.urlopen(req,timeout=60) as response:
                if response.status!=206 or response.headers.get("Content-Range")!=f"bytes {start}-{end}/{SIZE}":
                    raise ValueError("Invalid HTTP range response")
                data=response.read()
            if len(data)!=end-start+1:raise ValueError("Truncated range")
            os.pwrite(fd,data,start)
            return i
        except Exception:
            if attempt==4:raise
            time.sleep(min(2**attempt,8))
started=time.perf_counter()
print("RESUMED",len(done),"of",(SIZE+CHUNK-1)//CHUNK,flush=True)
try:
    with concurrent.futures.ThreadPoolExecutor(max_workers=16) as pool:
        futures=[pool.submit(fetch,i) for i in range((SIZE+CHUNK-1)//CHUNK) if i not in done]
        for future in concurrent.futures.as_completed(futures):
            done.add(future.result());manifest.write_text(json.dumps(sorted(done)))
            print(f"download {min(len(done)*CHUNK,SIZE)/1e9:.2f}/{SIZE/1e9:.2f} GB, elapsed {time.perf_counter()-started:.0f}s",flush=True)
finally:os.close(fd)
digest=hashlib.file_digest(part.open("rb"),"sha256").hexdigest()
if digest!=SHA:raise RuntimeError(f"Checkpoint hash mismatch {digest}")
part.rename(DEST)
(ROOT/"verification/checkpoint_sha256.txt").write_text(digest+"\n")
print("CHECKPOINT_VERIFIED",digest,flush=True)
