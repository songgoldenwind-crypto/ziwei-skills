# -*- coding: utf-8 -*-
"""
真太阳时模块。

用法:
    from ziwei_paipan.tst import TrueSolar, get_instance
    ts = get_instance()
    result = ts.convert(2024, 6, 15, 14, 30, city="北京")
"""

import datetime
import os
from pathlib import Path

_TST_DIR = Path(__file__).resolve().parent


def _resolve_tst_data_dir() -> Path:
    explicit = os.environ.get("ZIWEI_DATA_DIR")
    if explicit:
        return Path(explicit).expanduser().resolve()
    return _TST_DIR.parent / "data"


_DATA_DIR = _resolve_tst_data_dir()

from .astronomy import Astronomy   # noqa: E402
from .data_loader import DataLoader  # noqa: E402

# 中国夏令时 1986-1991
_CHINA_DST = [
    (1986, 5, 4, 9, 14),
    (1987, 4, 12, 9, 13),
    (1988, 4, 10, 9, 11),
    (1989, 4, 16, 9, 17),
    (1990, 4, 15, 9, 16),
    (1991, 4, 14, 9, 15),
]


def _is_china_dst(year, month, day, hour=0):
    for y, sm, sd, em, ed in _CHINA_DST:
        if year == y:
            start = datetime.date(y, sm, sd)
            end = datetime.date(y, em, ed)
            cur = datetime.date(year, month, day)
            if cur == start:
                return hour >= 2
            if cur == end:
                return hour < 2
            return start < cur < end
    return False


class TrueSolar:
    """真太阳时计算器"""

    def __init__(self):
        self._astronomy = Astronomy(str(_DATA_DIR / "ephe"))
        self._data_loader = DataLoader(str(_DATA_DIR))
        self._tf = None

    @property
    def _timezone_finder(self):
        if self._tf is None:
            from timezonefinder import TimezoneFinder
            self._tf = TimezoneFinder()
        return self._tf

    def search_city(self, query: str) -> list[dict]:
        """按城市名搜索位置（中文/英文/拼音），最多 10 条。"""
        return self._data_loader.search_location(query)

    def convert(
        self,
        year: int, month: int, day: int, hour: int, minute: int,
        *,
        city: str | None = None,
        lat: float | None = None,
        lon: float | None = None,
        tz: str | None = None,
    ) -> dict:
        """
        将钟表时间转换为真太阳时。

        参数（city 与 lat+lon 二选一）:
            year, month, day, hour, minute – 当地钟表时间
            city   – 城市名（自动查询经纬度和时区）
            lat, lon – 手动指定经纬度
            tz     – 手动指定 IANA 时区

        返回:
            dict: input, true_solar_time, eot_minutes, location, dst
        """
        location_info = None
        if city:
            results = self.search_city(city)
            if not results:
                raise ValueError(f"未找到城市: {city}")
            location_info = results[0]
            lat = location_info["lat"]
            lon = location_info["lon"]
            tz = tz or location_info.get("timezone_id")

        if lat is None or lon is None:
            raise ValueError("需要提供 city 或 lat + lon")

        if not tz:
            tz = self._timezone_finder.timezone_at(lat=lat, lng=lon) or "Asia/Shanghai"

        is_china_tz = tz in ("Asia/Shanghai", "Asia/Urumqi", "PRC")
        in_dst = is_china_tz and _is_china_dst(year, month, day, hour)

        if in_dst:
            std = datetime.datetime(year, month, day, hour, minute) - datetime.timedelta(hours=1)
            tz_obj = datetime.timezone(datetime.timedelta(hours=8))
            utc_dt = std.replace(tzinfo=tz_obj).astimezone(datetime.timezone.utc)
        else:
            if is_china_tz:
                tz_obj = datetime.timezone(datetime.timedelta(hours=8))
            else:
                try:
                    from zoneinfo import ZoneInfo
                    tz_obj = ZoneInfo(tz)
                except Exception:
                    tz_obj = datetime.timezone(datetime.timedelta(hours=8))
            utc_dt = datetime.datetime(
                year, month, day, hour, minute, tzinfo=tz_obj
            ).astimezone(datetime.timezone.utc)

        tst_res = self._astronomy.get_true_solar_time(utc_dt, lon)
        tst_dt = tst_res["datetime"]

        return {
            "input": {"year": year, "month": month, "day": day, "hour": hour, "minute": minute},
            "true_solar_time": {
                "year": tst_dt.year, "month": tst_dt.month, "day": tst_dt.day,
                "hour": tst_dt.hour, "minute": tst_dt.minute,
            },
            "eot_minutes": round(tst_res["eot_minutes"], 2),
            "location": {
                "city": city, "lat": lat, "lon": lon, "timezone": tz,
                **({"city_name_cn": location_info.get("city_name_cn"),
                    "city_name_en": location_info.get("city_name_en")}
                   if location_info else {}),
            },
            "dst": in_dst,
        }

    def get_solar_terms(self, year: int) -> dict:
        """获取指定年份 24 节气精确时刻（UTC）。"""
        return self._astronomy.get_solar_terms(year)


_instance: TrueSolar | None = None


def get_instance() -> TrueSolar:
    global _instance
    if _instance is None:
        _instance = TrueSolar()
    return _instance
