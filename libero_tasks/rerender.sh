#!/bin/bash
# 重渲任务清单截图到本目录 libero_tasks/（空跑步数见 render_libero_tasks.py 的 WAIT）。
# 反复创建环境偶发 SIGFPE，脚本自带"图已存在则跳过"，崩了直接重跑即可。
# 需要 Armory 的虚拟环境；Armory 位置由 ARMORY_ROOT 指定，默认 /root/work/armory。
HERE="$(cd "$(dirname "$0")" && pwd)"
ARMORY_ROOT="${ARMORY_ROOT:-/root/work/armory}"
OUT="$HERE"
cd "$HERE" || exit 1

i=0
while [ "$i" -lt 10 ]; do
  i=$((i + 1))
  MUJOCO_GL=egl "$ARMORY_ROOT/.venv/bin/python" render_libero_tasks.py "$OUT" >> /tmp/render.log 2>&1
  n=$(ls "$OUT/img" 2>/dev/null | wc -l)
  echo "pass $i: $n images"
  if [ "$n" -ge 130 ]; then
    break
  fi
done

ls "$OUT/img" | wc -l
