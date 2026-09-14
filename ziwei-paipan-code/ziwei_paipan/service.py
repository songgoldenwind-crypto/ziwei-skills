from __future__ import annotations

import re
from datetime import datetime
from typing import Any

import pytz
from py_iztro import Astro

from . import utils
from .ai_context import build_horoscope_ai_context, build_ziwei_ai_context, parse_four_pillars


ZHI_LIST = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
GENDER_MAP = {
    "男": "男",
    "male": "男",
    "m": "男",
    "女": "女",
    "female": "女",
    "f": "女",
}


def _normalize_solar_date_text(value: str) -> str:
    normalized = str(value or "").strip()
    normalized = (
        normalized.replace("／", "/")
        .replace("－", "-")
        .replace("—", "-")
        .replace("–", "-")
        .replace(".", "-")
        .replace("年", "-")
        .replace("月", "-")
        .replace("日", "")
        .replace(" ", "")
    )
    match = re.fullmatch(r"(?P<year>\d{4})[-/](?P<month>\d{1,2})[-/](?P<day>\d{1,2})", normalized)
    if not match:
        return str(value or "").strip()
    return f"{int(match.group('year')):04d}-{int(match.group('month')):02d}-{int(match.group('day')):02d}"


def _normalize_time_text(value: str) -> str:
    normalized = str(value or "").strip()
    normalized = (
        normalized.replace("：", ":")
        .replace("，", ":")
        .replace("、", ":")
        .replace("．", ":")
        .replace("。", ":")
        .replace("点", ":")
        .replace("時", ":")
        .replace("时", ":")
        .replace("分", "")
        .replace(" ", "")
    )
    if normalized.endswith(":"):
        normalized = f"{normalized}00"
    match = re.fullmatch(r"(?P<hour>\d{1,2}):(?P<minute>\d{1,2})", normalized)
    if not match:
        return str(value or "").strip()
    hour = int(match.group("hour"))
    minute = int(match.group("minute"))
    if not (0 <= hour <= 23 and 0 <= minute <= 59):
        return str(value or "").strip()
    return f"{hour:02d}:{minute:02d}"


def _normalize_location_text(value: str) -> str:
    normalized = str(value or "").strip()
    normalized = re.sub(r"^(?:出生地|出生|地点|地點|位置|城市|籍贯|祖籍|家乡)\s*[:：]?\s*", "", normalized)
    return normalized.strip()


def _require_str(payload: dict[str, Any], *keys: str) -> str:
    for key in keys:
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    raise ValueError(f"缺少参数: {' / '.join(keys)}")


def _require_bool(payload: dict[str, Any], key: str, default: bool = True) -> bool:
    value = payload.get(key, default)
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"1", "true", "yes", "y", "on", "开启", "开", "是"}:
            return True
        if normalized in {"0", "false", "no", "n", "off", "关闭", "关", "否"}:
            return False
    raise ValueError(f"{key} 只支持布尔值")


def _normalize_payload(payload: dict[str, Any]) -> dict[str, Any]:
    solar_date = _normalize_solar_date_text(_require_str(payload, "solar_date", "date"))
    time_str = _normalize_time_text(_require_str(payload, "time"))
    gender_raw = _require_str(payload, "gender").lower()
    location = _normalize_location_text(_require_str(payload, "location"))
    use_true_solar = _require_bool(payload, "use_true_solar", True)

    gender = GENDER_MAP.get(gender_raw)
    if gender is None:
        raise ValueError("gender 只支持 男/女 或 male/female")

    return {
        "solar_date": solar_date,
        "time": time_str,
        "gender": gender,
        "location": location,
        "use_true_solar": use_true_solar,
    }


def _minutes_to_nearest_shichen_boundary(value: datetime) -> float:
    minute_of_day = value.hour * 60 + value.minute + value.second / 60
    boundaries = range(60, 24 * 60, 120)
    distances = [abs(minute_of_day - boundary) for boundary in boundaries]
    wrapped_distances = [24 * 60 - distance for distance in distances]
    return round(min(distances + wrapped_distances), 3)


def prepare_true_solar(payload: dict[str, Any]) -> dict[str, Any]:
    normalized = _normalize_payload(payload)
    utils.init_astronomy()
    location_service = utils.LocationService()

    try:
        local_dt_naive = datetime.strptime(
            f"{normalized['solar_date']} {normalized['time']}",
            "%Y-%m-%d %H:%M",
        )
    except ValueError as exc:
        raise ValueError("日期或时间格式错误！请使用 YYYY-MM-DD 和 HH:MM 格式。") from exc

    loc_info = location_service.get_location_info(normalized["location"])
    if not loc_info:
        raise ValueError(f"未找到地点 '{normalized['location']}' 的信息。无法计算真太阳时。")

    try:
        tz = pytz.timezone(loc_info["timezone"])
        local_dt = tz.localize(local_dt_naive)
        utc_dt = local_dt.astimezone(pytz.utc)
    except Exception as exc:
        raise RuntimeError(f"时区转换失败: {exc}") from exc

    try:
        tst_result = utils.get_true_solar_time(utc_dt, loc_info["lon"]) if normalized["use_true_solar"] else None
        chart_dt = tst_result["datetime"] if tst_result else local_dt
    except Exception as exc:
        raise RuntimeError(f"真太阳时计算失败: {exc}") from exc

    clock_chinese_hour_idx = utils.get_chinese_hour(local_dt.hour)
    chinese_hour_idx = utils.get_chinese_hour(chart_dt.hour)
    solar_date_tst = chart_dt.strftime("%Y-%m-%d")
    # Astronomy returns a wall-clock true-solar datetime whose tzinfo may use a
    # historical local-mean offset. Compare naive wall times so the reported
    # correction matches what the user sees in the timestamps.
    solar_shift_minutes = round(
        (
            chart_dt.replace(tzinfo=None) - local_dt.replace(tzinfo=None)
        ).total_seconds()
        / 60,
        3,
    )
    boundary_distance = _minutes_to_nearest_shichen_boundary(chart_dt)
    crossed_shichen = clock_chinese_hour_idx != chinese_hour_idx

    return {
        "input": normalized,
        "location": {
            "name": loc_info["name"],
            "lat": loc_info["lat"],
            "lon": loc_info["lon"],
            "timezone": loc_info["timezone"],
        },
        "derived": {
            "local_datetime": local_dt.strftime("%Y-%m-%d %H:%M:%S"),
            "utc_datetime": utc_dt.strftime("%Y-%m-%d %H:%M:%S"),
            "true_solar_enabled": normalized["use_true_solar"],
            "true_solar_datetime": chart_dt.strftime("%Y-%m-%d %H:%M:%S") if normalized["use_true_solar"] else None,
            "chart_datetime": chart_dt.strftime("%Y-%m-%d %H:%M:%S"),
            "equation_of_time_minutes": round(float(tst_result.get("eot_minutes", 0.0)), 6) if tst_result else None,
            "true_solar_shift_minutes": solar_shift_minutes,
            "clock_chinese_hour": ZHI_LIST[clock_chinese_hour_idx],
            "chinese_hour_index": chinese_hour_idx,
            "chinese_hour": ZHI_LIST[chinese_hour_idx],
            "crossed_shichen_boundary": crossed_shichen,
            "minutes_to_nearest_shichen_boundary": boundary_distance,
            "near_shichen_boundary": boundary_distance <= 10,
            "solar_date_for_chart": solar_date_tst,
        },
        "chart_input": {
            "solar_date": solar_date_tst,
            "chinese_hour_index": chinese_hour_idx,
            "gender": normalized["gender"],
        },
    }


def _build_astrolabe(payload: dict[str, Any]) -> tuple[dict[str, Any], Any]:
    prepared = prepare_true_solar(payload)
    astro = Astro()
    try:
        astrolabe = astro.by_solar(
            prepared["chart_input"]["solar_date"],
            prepared["chart_input"]["chinese_hour_index"],
            prepared["chart_input"]["gender"],
        )
    except Exception as exc:
        raise RuntimeError(f"排盘计算失败: {exc}") from exc
    return prepared, astrolabe


def _resolve_horoscope_target(payload: dict[str, Any]) -> dict[str, Any]:
    target_date = _normalize_solar_date_text(_require_str(payload, "target_date", "targetDate"))
    raw_target_time = payload.get("target_time", payload.get("targetTime", "00:00"))
    if raw_target_time is None:
        target_time = "00:00"
    elif isinstance(raw_target_time, str):
        target_time = _normalize_time_text(raw_target_time.strip() or "00:00")
    else:
        raise ValueError("target_time 只支持 HH:MM 字符串")

    try:
        target_dt = datetime.strptime(f"{target_date} {target_time}", "%Y-%m-%d %H:%M")
    except ValueError as exc:
        raise ValueError("target_date / target_time 格式错误！请使用 YYYY-MM-DD 和 HH:MM 格式。") from exc

    chinese_hour_idx = utils.get_chinese_hour(target_dt.hour)
    return {
        "solar_date": target_date,
        "time": target_time,
        "hour": target_dt.hour,
        "minute": target_dt.minute,
        "chinese_hour_index": chinese_hour_idx,
        "chinese_hour": ZHI_LIST[chinese_hour_idx],
    }


def compute(payload: dict[str, Any]) -> dict[str, Any]:
    prepared, astrolabe = _build_astrolabe(payload)
    chart_data = astrolabe.model_dump(by_alias=True)

    ai_context = build_ziwei_ai_context(chart_data)

    return {
        "domain": "ziwei",
        "input": prepared["input"],
        "location": prepared["location"],
        "derived": prepared["derived"],
        "四柱": parse_four_pillars(chart_data.get("chineseDate")),
        "data": chart_data,
        "ai_context": ai_context,
    }


def compute_horoscope(payload: dict[str, Any]) -> dict[str, Any]:
    prepared, astrolabe = _build_astrolabe(payload)
    target = _resolve_horoscope_target(payload)

    natal_data = astrolabe.model_dump(by_alias=True)
    try:
        horoscope_data = astrolabe.horoscope(
            target["solar_date"],
            target["chinese_hour_index"],
        ).model_dump(by_alias=True)
    except Exception as exc:
        raise RuntimeError(f"时序盘计算失败: {exc}") from exc

    return {
        "domain": "ziwei",
        "input": prepared["input"],
        "location": prepared["location"],
        "derived": prepared["derived"],
        "四柱": parse_four_pillars(natal_data.get("chineseDate")),
        "target": target,
        "data": horoscope_data,
        "ai_context": {
            "原局": build_ziwei_ai_context(natal_data),
            "运限": build_horoscope_ai_context(natal_data, horoscope_data),
        },
    }
