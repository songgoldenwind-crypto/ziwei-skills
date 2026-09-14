# -*- coding: utf-8 -*-
"""命令行入口：输出 JSON 格式的紫微斗数命盘。"""

from __future__ import annotations

import argparse
import json
import sys

from .service import compute, compute_horoscope


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ziwei-paipan",
        description="紫微斗数排盘（真太阳时校正），输出 JSON",
    )
    parser.add_argument("--date", required=True, help="公历出生日期 YYYY-MM-DD")
    parser.add_argument("--time", required=True, help="出生时间 HH:MM（24 小时制）")
    parser.add_argument("--gender", required=True, help="性别：男 / 女 / male / female")
    parser.add_argument("--location", required=True, help="出生地城市名，如 北京 / Shanghai")
    parser.add_argument(
        "--no-true-solar",
        action="store_true",
        help="关闭真太阳时校正，直接按输入的钟表时间定时辰",
    )
    parser.add_argument(
        "--horoscope-date",
        help="运限盘目标日期 YYYY-MM-DD。给出时输出大限、流年、流月、流日、流时",
    )
    parser.add_argument(
        "--horoscope-time",
        default="00:00",
        help="运限盘目标时间 HH:MM，默认 00:00",
    )
    parser.add_argument(
        "--no-ai-context",
        action="store_true",
        help="只输出原始排盘数据，不附带整理后的语义层",
    )
    parser.add_argument("--indent", type=int, default=2, help="JSON 缩进，0 表示压缩为单行")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    payload = {
        "solar_date": args.date,
        "time": args.time,
        "gender": args.gender,
        "location": args.location,
        "use_true_solar": not args.no_true_solar,
    }

    try:
        if args.horoscope_date:
            payload["target_date"] = args.horoscope_date
            payload["target_time"] = args.horoscope_time
            result = compute_horoscope(payload)
        else:
            result = compute(payload)
            if args.no_ai_context:
                result.pop("ai_context", None)
    except (ValueError, RuntimeError) as exc:
        print(f"排盘失败：{exc}", file=sys.stderr)
        return 1

    indent = args.indent if args.indent > 0 else None
    print(json.dumps(result, ensure_ascii=False, indent=indent))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
