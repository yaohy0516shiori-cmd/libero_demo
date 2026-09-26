from __future__ import annotations

import os
import sys

sys.dont_write_bytecode = True
os.environ.setdefault("MUJOCO_GL", "egl")

import json
from dataclasses import asdict
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Callable, Sequence

from common import (
    AuditConfig,
    Report,
    parse_args,
    serial,
    emit,
    git_info,
    inventory,
)
from probe_io import inspect_case
from probe_stability import settle_cases
from probe_time import timing_cases
from probe_dynamic import dynamic_case


def main(argv: Sequence[str] | None = None) -> None:
    cfg = parse_args(argv)
    report: Report = {}

    if cfg.out is not None:
        cfg.out.mkdir(parents=True, exist_ok=True)

    try:
        import libero.libero as lib

        packages: dict[str, str] = {}
        for name in [
            "robosuite", "mujoco", "numpy", "gym", "libero"
        ]:
            try:
                packages[name] = version(name)
            except PackageNotFoundError:
                packages[name] = "UNKNOWN"

        emit(report, "versions", {
            "python": sys.version,
            "executable": sys.executable,
            "packages": packages,
            "libero_git": git_info(
                Path(lib.__file__).resolve().parent
            ),
            "MUJOCO_GL": os.getenv("MUJOCO_GL"),
            "args": asdict(cfg),
        })

        inventory(cfg, report)

        sections: dict[
            str, Callable[[AuditConfig, Report], None]
        ] = {
            "inspect": inspect_case,
            "settle": settle_cases,
            "timing": timing_cases,
            "dynamic": dynamic_case,
        }

        for name, function in sections.items():
            if cfg.section in [name, "all"]:
                function(cfg, report)

        print(
            "\nNo model/server/network tested; "
            "no fleet-capacity claim."
        )

    finally:
        # 默认不保存；指定 --out 后，即使中途异常，
        # 也会保存已收集的报告。重复使用同目录会覆盖同名结果。
        if cfg.out is not None:
            (cfg.out / "report.json").write_text(
                json.dumps(
                    report,
                    ensure_ascii=False,
                    indent=2,
                    default=serial,
                ),
                encoding="utf-8",
            )


if __name__ == "__main__":
    main()