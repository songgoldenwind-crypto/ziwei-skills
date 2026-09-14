#!/usr/bin/env python3
"""Run the bundled paipan package from an installed skill or the source repo."""

from __future__ import annotations

import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
CANDIDATES = (
    SCRIPT_DIR / "ziwei-paipan",
    SCRIPT_DIR.parent / "ziwei-paipan",
    SCRIPT_DIR.parents[2] / "ziwei-paipan-code",
)


def find_package_root() -> Path | None:
    for candidate in CANDIDATES:
        if (candidate / "ziwei_paipan" / "__main__.py").is_file():
            return candidate
    return None


def run() -> int:
    package_root = find_package_root()
    if package_root is None:
        print("排盘模块不完整：未找到 ziwei_paipan。请重新安装完整 ziwei Skill。", file=sys.stderr)
        return 2

    sys.path.insert(0, str(package_root))
    try:
        from ziwei_paipan.__main__ import main
    except ModuleNotFoundError as exc:
        requirements = package_root / "requirements.txt"
        print(
            f"排盘依赖缺失：{exc.name}。请执行：\n"
            f"{sys.executable} -m pip install -r {requirements}",
            file=sys.stderr,
        )
        return 2
    return main()


if __name__ == "__main__":
    raise SystemExit(run())
