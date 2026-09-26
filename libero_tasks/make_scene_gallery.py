"""按场景（不是按任务）拼一张总览图：每个场景取一张第三人称视角。

任务清单的截图每张是「第三人称 + 腕部」并排，这里只取左半边，
这样同样的页宽下每格能大一倍。
"""

from __future__ import annotations

import json
import re
from collections import OrderedDict
import os
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent          # libero_tasks/
REPO = HERE.parent                               # 仓库根目录
ARMORY = Path(os.environ.get("ARMORY_ROOT", "/root/work/armory"))
TASKS = HERE
BDDL = ARMORY / "third_party/libero/libero/libero/bddl_files"
OUT = HERE

TILE = 256          # 第三人称画面边长
LABEL = 26          # 标签条高度
COLS = 6


def scene_of(row: dict) -> str:
    match = re.match(r"^([A-Z_]+SCENE\d+)", row["name"])
    if match:
        return match.group(1)

    text = (BDDL / row["problem_folder"] / row["bddl_file"]).read_text()
    match = re.search(r"\(problem\s+([A-Za-z0-9_]+)\)", text)
    return match.group(1) if match else "-"


rows = json.loads((TASKS / "tasks.json").read_text())

# 每个场景保留第一个任务；记录该场景涉及多少任务。
first: OrderedDict[str, dict] = OrderedDict()
counts: dict[str, int] = {}
for row in rows:
    name = scene_of(row)
    counts[name] = counts.get(name, 0) + 1
    first.setdefault(name, row)


def sort_key(name: str) -> tuple[int, str, int]:
    match = re.match(r"^([A-Z_]+SCENE)(\d+)$", name)
    if match:
        return (0, match.group(1), int(match.group(2)))
    return (1, name, 0)


scenes = sorted(first, key=sort_key)
rows_n = (len(scenes) + COLS - 1) // COLS
sheet = Image.new("RGB", (COLS * TILE, rows_n * (TILE + LABEL)), "white")
draw = ImageDraw.Draw(sheet)

try:
    font = ImageFont.truetype("DejaVuSans.ttf", 15)
except OSError:
    font = ImageFont.load_default()

for index, name in enumerate(scenes):
    row = first[name]
    frame = Image.open(TASKS / row["image"])
    agent = frame.crop((0, 0, frame.width // 2, frame.height))
    agent = agent.resize((TILE, TILE), Image.LANCZOS)

    x = (index % COLS) * TILE
    y = (index // COLS) * (TILE + LABEL)
    sheet.paste(agent, (x, y))

    label = name.replace("LIBERO_", "").replace("_Manipulation", "")
    draw.text((x + 5, y + TILE + 5),
              f"{label}  ({counts[name]} tasks)", fill="black", font=font)

OUT.mkdir(exist_ok=True)
sheet.save(OUT / "scene_gallery.png")

# 同时导出按场景归类的清单：场景重复使用，按任务平铺会重复 22 次场景名。
grouped = []
for name in scenes:
    tasks = [r for r in rows if scene_of(r) == name]
    grouped.append({
        "scene": name,
        "tasks": len(tasks),
        "suites": sorted({r["suite"] for r in tasks}),
        "image": first[name]["image"],
        "instructions": [
            {"suite": r["suite"], "task_id": r["task_id"],
             "language": r["language"]}
            for r in tasks
        ],
    })

(TASKS / "scenes.json").write_text(
    json.dumps(grouped, indent=2, ensure_ascii=False), encoding="utf-8"
)

print(json.dumps({
    "scenes": len(scenes),
    "grid": [rows_n, COLS],
    "size": sheet.size,
    "tasks": sum(item["tasks"] for item in grouped),
}))
