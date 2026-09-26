from huggingface_hub import snapshot_download
from pathlib import Path
p=Path(__file__).resolve().parents[1]
print(snapshot_download('lerobot/pi05_libero_finetuned',revision='8e174154ef5f6c60a8da12ae99c303d8963138c1',local_dir=p/'models/pi05_finetuned',max_workers=4),flush=True)
