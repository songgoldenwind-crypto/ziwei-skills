# -*- coding: utf-8 -*-
"""把排盘原始数据整理成便于断盘直接引用的语义层。"""

from __future__ import annotations

from typing import Any

MUTAGEN_NAMES = {
    "祿": "化禄",
    "禄": "化禄",
    "權": "化权",
    "权": "化权",
    "科": "化科",
    "忌": "化忌",
}

CORE_PALACES = ["命宫", "官禄", "财帛", "迁移", "福德", "夫妻", "田宅"]
PILLAR_KEYS = ("年柱", "月柱", "日柱", "时柱")


def _unique(items: list[Any]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        if isinstance(item, (list, tuple, set)):
            for nested in _unique(list(item)):
                if nested not in seen:
                    seen.add(nested)
                    result.append(nested)
            continue
        value = str(item or "").strip()
        if value and value not in seen:
            seen.add(value)
            result.append(value)
    return result


def _normalize_star(star: dict[str, Any]) -> dict[str, Any]:
    mutagen = MUTAGEN_NAMES.get(star.get("mutagen"), star.get("mutagen"))
    return {
        "名称": star.get("name"),
        "亮度": star.get("brightness") or None,
        "四化": mutagen or None,
    }


def _normalize_palace(palace: dict[str, Any]) -> dict[str, Any]:
    major = [_normalize_star(star) for star in palace.get("majorStars") or []]
    minor = [_normalize_star(star) for star in palace.get("minorStars") or []]
    adjective = [_normalize_star(star) for star in palace.get("adjectiveStars") or []]
    mutagen_stars = _unique(
        [f"{star['名称']}{star['四化']}" for star in major + minor + adjective if star.get("四化")]
    )
    return {
        "宫位": palace.get("name"),
        "地支": palace.get("earthlyBranch"),
        "天干": palace.get("heavenlyStem"),
        "是否身宫": palace.get("isBodyPalace"),
        "正曜": major,
        "辅曜": minor,
        "杂曜": adjective,
        "长生十二": palace.get("changsheng12"),
        "博士十二": palace.get("boshi12"),
        "将前十二": palace.get("jiangqian12"),
        "岁前十二": palace.get("suiqian12"),
        "大限": palace.get("decadal"),
        "岁数": palace.get("ages"),
        "四化星": mutagen_stars,
        "空宫": len(major) == 0,
    }


def _major_star_combo(palace: dict[str, Any]) -> str | None:
    names = [star.get("名称") for star in palace.get("正曜") or [] if star.get("名称")]
    return "".join(names) if names else None


def parse_four_pillars(chinese_date: str | None) -> dict[str, Any] | None:
    """把 iztro 的 `chineseDate`（年 月 日 时）拆成出生四柱。"""
    parts = str(chinese_date or "").split()
    if len(parts) != 4 or any(len(part) != 2 for part in parts):
        return None
    pillars: dict[str, Any] = {"原文": " ".join(parts)}
    for key, text in zip(PILLAR_KEYS, parts):
        pillars[key] = {"干支": text, "天干": text[0], "地支": text[1]}
    return pillars


def _sanfang_sizheng(palaces: list[dict[str, Any]], target_name: str) -> list[dict[str, Any]]:
    indexed = {palace.get("name"): palace for palace in palaces}
    target = indexed.get(target_name)
    if not target:
        return []
    ordered = sorted(palaces, key=lambda item: item.get("index", 0))
    idx = target.get("index", 0)
    # iztro 的 palace.index 从寅宫起顺行。三合隔四宫，对宫隔六宫。
    # (0, 3, 6, 9) 会误取四墓，不能用来当三方四正。
    focus_indices = {(idx + offset) % 12 for offset in (0, 4, 6, 8)}
    result = []
    for palace in ordered:
        if palace.get("index") in focus_indices:
            result.append(
                {
                    "宫位": palace.get("name"),
                    "正曜组合": "".join(star.get("name") for star in palace.get("majorStars") or []),
                    "地支": palace.get("earthlyBranch"),
                }
            )
    return result


def build_ziwei_ai_context(chart: dict[str, Any]) -> dict[str, Any]:
    raw_palaces = chart.get("palaces") or []
    normalized_palaces = [_normalize_palace(palace) for palace in raw_palaces]
    palaces_by_name = {palace["宫位"]: palace for palace in normalized_palaces}

    core_axes = {name: palaces_by_name[name] for name in CORE_PALACES if name in palaces_by_name}

    mutagen_summary = []
    for palace in normalized_palaces:
        for item in palace.get("四化星") or []:
            mutagen_summary.append(f"{item}在{palace['宫位']}")

    core_combos = _unique(
        [f"{name}{_major_star_combo(core_axes[name])}" for name in core_axes if _major_star_combo(core_axes[name])]
    )
    four_pillars = parse_four_pillars(chart.get("chineseDate"))

    return {
        "basic_info": {
            "性别": chart.get("gender"),
            "公历": chart.get("solarDate"),
            "农历": chart.get("lunarDate"),
            "干支": chart.get("chineseDate"),
            "四柱": four_pillars,
            "时辰": chart.get("time"),
            "命主": chart.get("soul"),
            "身主": chart.get("body"),
            "五行局": chart.get("fiveElementsClass"),
            "命宫地支": chart.get("earthlyBranchOfSoulPalace"),
            "身宫地支": chart.get("earthlyBranchOfBodyPalace"),
        },
        "palaces_by_name": palaces_by_name,
        "core_axes": core_axes,
        "computed_relations": {
            "命宫三方四正": _sanfang_sizheng(raw_palaces, "命宫"),
            "核心星曜组合": core_combos,
            "四化落宫": mutagen_summary,
            "空宫": [palace["宫位"] for palace in normalized_palaces if palace.get("空宫")],
        },
    }
