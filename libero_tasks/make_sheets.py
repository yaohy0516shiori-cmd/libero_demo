"""Build per-suite contact sheets and a markdown task list from tasks.json + img/.

Reads and writes this folder (libero_tasks/) unless another folder is given:
  $ARMORY_ROOT/.venv/bin/python make_sheets.py [task_dir] [bddl_root]
"""

import json
import os
import pathlib
import re
import sys
import textwrap
from collections import Counter

from PIL import Image, ImageDraw, ImageFont

root = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else pathlib.Path(__file__).resolve().parent
rows = json.loads((root / "tasks.json").read_text())

# bddl 根目录；用于补出 libero_spatial / libero_object 的场景名，
# 这两个 suite 的任务名里不带 SCENE 前缀。
BDDL_ROOT = pathlib.Path(
    sys.argv[2] if len(sys.argv) > 2
    else os.path.join(os.environ.get("ARMORY_ROOT", "/root/work/armory"),
                      "third_party/libero/libero/libero/bddl_files")
)

SUITE_DESC = {
    "libero_spatial": "same objects, different spatial layouts (tests spatial reasoning)",
    "libero_object": "same layout, different target objects (tests object recognition)",
    "libero_goal": "same scene and objects, different goals (tests goal/instruction following)",
    "libero_10": "long-horizon, multi-step tasks across varied scenes (a.k.a. LIBERO-Long)",
    "libero_90": "90 short-horizon tasks across kitchen / living-room / study scenes (pretraining set)",
}


def bddl_text(row: dict) -> str:
    path = BDDL_ROOT / row["problem_folder"] / row["bddl_file"]
    return path.read_text() if path.exists() else ""


def scene_of(row: dict) -> str:
    """场景标签。libero_90 / goal / 10 的任务名自带 SCENE 前缀；
    spatial 和 object 不带，退回 bddl 里的 problem 名。"""
    m = re.match(r"^([A-Z_]+SCENE\d+)", row["name"])
    if m:
        return m.group(1)

    m = re.search(r"\(problem\s+([A-Za-z0-9_]+)\)", bddl_text(row))
    return m.group(1) if m else "-"


def fixtures_of(row: dict) -> list[str]:
    """场景里的固定家具（桌子、柜子、炉灶等），用于说明场景构成。"""
    block = re.search(r"\(:fixtures(.*?)\)", bddl_text(row), re.S)
    if not block:
        return []
    return [
        line.split("-")[0].strip()
        for line in block.group(1).strip().splitlines()
        if line.strip()
    ]


try:
    font = ImageFont.truetype("DejaVuSans.ttf", 13)
except OSError:
    font = ImageFont.load_default()

TILE_W, TILE_H, CAP_H, COLS = 512, 256, 44, 5
md = ["# LIBERO task list", "",
      "Rendered from Armory's pinned LIBERO (init state 0, after 30 settle steps). "
      "Each image: left = agent-view camera, right = wrist camera.", "",
      "> Why 30 steps: LIBERO's own evaluation waits 5 zero-action steps and Armory waits 10. "
      "Over all 130 tasks (init state 0), the scene first becomes quiet at a median of 13 steps "
      "and at the latest by step 29 (`libero_test/audit/results_all_tasks`); at step 30 every task is quiet. "
      "At step 10, 17 tasks still have objects in mid-air, so those frames silently omit objects "
      "(`libero_test/audit/results_render_check/wait_10_vs_30.png`).", ""]

for suite in ["libero_spatial", "libero_object", "libero_goal", "libero_10", "libero_90"]:
    srows = [r for r in rows if r["suite"] == suite]
    scenes = Counter(scene_of(r) for r in srows)
    fixtures = sorted({f for r in srows for f in fixtures_of(r)})
    md += [f"## {suite} ({len(srows)} tasks)", "", f"{SUITE_DESC[suite]}.", "",
           "Scenes: " + ", ".join(f"{s} ×{c}" for s, c in sorted(scenes.items())), "",
           "Fixtures: " + (", ".join(fixtures) if fixtures else "-"), "",
           f"Contact sheet: `sheet_{suite}.png`", "",
           "| id | scene | instruction | init states | image |", "|---|---|---|---|---|"]
    for r in srows:
        md.append(f"| {r['task_id']} | {scene_of(r)} | {r['language']} | {r['n_init_states']} | `{r['image']}` |")
    md.append("")

    # contact sheet (libero_90 split into pages of 30)
    pages = [srows[i:i + 30] for i in range(0, len(srows), 30)]
    for p, page in enumerate(pages):
        n_rows = (len(page) + COLS - 1) // COLS
        sheet = Image.new("RGB", (COLS * TILE_W, n_rows * (TILE_H + CAP_H)), "white")
        draw = ImageDraw.Draw(sheet)
        for i, r in enumerate(page):
            x, y = (i % COLS) * TILE_W, (i // COLS) * (TILE_H + CAP_H)
            sheet.paste(Image.open(root / r["image"]), (x, y))
            cap = f"[{r['task_id']}] {r['language']}"
            draw.multiline_text((x + 4, y + TILE_H + 2), "\n".join(textwrap.wrap(cap, 70)[:2]), fill="black", font=font)
        suffix = f"_p{p + 1}" if len(pages) > 1 else ""
        sheet.save(root / f"sheet_{suite}{suffix}.png")

(root / "LIBERO_tasks.md").write_text("\n".join(md), encoding="utf-8")
print("ok")
