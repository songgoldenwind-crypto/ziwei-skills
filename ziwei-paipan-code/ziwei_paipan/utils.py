# -*- coding: utf-8 -*-
"""真太阳时与地点查询封装。"""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

from .tst import get_instance
from .tst.astronomy import Astronomy
from .tst.data_loader import DataLoader

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"


def init_astronomy(ephe_path: str | None = None) -> None:
    """初始化 Swiss Ephemeris 路径。默认使用公共数据目录。"""
    if ephe_path:
        Astronomy(ephe_path)
        return
    get_instance()


def get_true_solar_time(utc_dt: datetime, lon: float) -> dict:
    """兼容旧接口：基于 UTC 时间和经度直接计算真太阳时。"""
    return get_instance()._astronomy.get_true_solar_time(utc_dt, lon)


class LocationService:
    """兼容旧接口：使用公共城市库查询地点。"""

    _LOCATION_HINT_SUFFIXES = ("省", "市", "区", "县", "州", "盟", "旗", "乡", "镇", "村")
    _REGION_PREFIXES = (
        "北京市", "天津市", "上海市", "重庆市",
        "内蒙古自治区", "广西壮族自治区", "西藏自治区", "宁夏回族自治区", "新疆维吾尔自治区",
        "香港特别行政区", "澳门特别行政区",
        "黑龙江省", "吉林省", "辽宁省", "河北省", "河南省", "山东省", "山西省", "陕西省",
        "江苏省", "浙江省", "安徽省", "福建省", "江西省", "湖北省", "湖南省", "广东省",
        "海南省", "四川省", "贵州省", "云南省", "青海省", "甘肃省", "台湾省",
        "北京", "天津", "上海", "重庆",
        "内蒙古", "内蒙", "广西", "西藏", "宁夏", "新疆", "香港", "澳门",
        "黑龙江", "吉林", "辽宁", "河北", "河南", "山东", "山西", "陕西",
        "江苏", "浙江", "安徽", "福建", "江西", "湖北", "湖南", "广东",
        "海南", "四川", "贵州", "云南", "青海", "甘肃", "台湾",
    )
    _CITY_PREFIXES = (
        "北京", "上海", "天津", "重庆", "广州", "深圳", "杭州", "南京", "苏州", "成都",
        "武汉", "西安", "长沙", "郑州", "青岛", "厦门", "福州", "昆明", "南宁", "南昌",
        "合肥", "济南", "石家庄", "沈阳", "长春", "哈尔滨", "海口", "三亚", "太原", "兰州",
        "乌鲁木齐", "呼和浩特", "银川", "西宁", "拉萨", "贵阳", "宁波", "无锡", "佛山", "东莞",
        "香港", "澳门", "台北", "台中", "台南", "高雄", "纽约", "伦敦",
    )
    _FOREIGN_PREFIXES = (
        "美国", "英国", "法国", "荷兰", "意大利", "德国", "日本", "俄罗斯", "加拿大",
        "澳大利亚", "新西兰", "瑞士", "比利时", "奥地利", "西班牙", "葡萄牙",
    )
    _SPECIAL_NORMALIZATIONS = {
        "中国香港": "香港",
        "中国澳门": "澳门",
        "中国台湾": "台湾",
        "香港特别行政区": "香港",
        "澳门特别行政区": "澳门",
        "台湾台南": "臺南",
        "台湾台东县": "臺東",
        "台湾台东": "臺東",
        "台南": "臺南",
        "台东": "臺東",
        "四川彭县": "彭州",
        "杭州淳安": "淳安",
        "广州佛山": "佛山",
    }
    _FALLBACK_BLOCKLIST = (
        "命造", "八字", "父亲", "母亲", "其母", "其父", "老师", "教师", "老板", "大老板",
        "家庭", "普通家庭", "农村家庭", "毕业", "退休", "透露", "文章", "专一", "网上",
        "先生", "女星", "演员", "将军", "穷人", "小康", "平凡", "富贵", "出生普通",
        "读完", "二把手", "感情", "命格",
    )
    _PROVINCE_DEFAULT_CITIES = {
        "河北": "石家庄",
        "河北省": "石家庄",
        "山西": "太原",
        "山西省": "太原",
        "辽宁": "沈阳",
        "辽宁省": "沈阳",
        "吉林": "长春",
        "吉林省": "长春",
        "黑龙江": "哈尔滨",
        "黑龙江省": "哈尔滨",
        "江苏": "南京",
        "江苏省": "南京",
        "浙江": "杭州",
        "浙江省": "杭州",
        "安徽": "合肥",
        "安徽省": "合肥",
        "福建": "福州",
        "福建省": "福州",
        "江西": "南昌",
        "江西省": "南昌",
        "山东": "济南",
        "山东省": "济南",
        "河南": "郑州",
        "河南省": "郑州",
        "湖北": "武汉",
        "湖北省": "武汉",
        "湖南": "长沙",
        "湖南省": "长沙",
        "广东": "广州",
        "广东省": "广州",
        "海南": "海口",
        "海南省": "海口",
        "四川": "成都",
        "四川省": "成都",
        "贵州": "贵阳",
        "贵州省": "贵阳",
        "云南": "昆明",
        "云南省": "昆明",
        "陕西": "西安",
        "陕西省": "西安",
        "甘肃": "兰州",
        "甘肃省": "兰州",
        "青海": "西宁",
        "青海省": "西宁",
        "台湾": "台北",
        "台湾省": "台北",
        "内蒙古": "呼和浩特",
        "内蒙古自治区": "呼和浩特",
        "内蒙": "呼和浩特",
        "广西": "南宁",
        "广西壮族自治区": "南宁",
        "西藏": "拉萨",
        "西藏自治区": "拉萨",
        "宁夏": "银川",
        "宁夏回族自治区": "银川",
        "新疆": "乌鲁木齐",
        "新疆维吾尔自治区": "乌鲁木齐",
        "香港": "香港",
        "香港特别行政区": "香港",
        "澳门": "澳门",
        "澳门特别行政区": "澳门",
    }

    def __init__(self) -> None:
        self._loader = DataLoader(str(DATA_DIR))
        self._tf = None

    @classmethod
    def _normalize_query(cls, query: str) -> str:
        normalized = str(query or "").strip()
        normalized = re.sub(r"^(?:出生地|出生|地点|地點|位置|城市|籍贯|祖籍|家乡)\s*[:：]?\s*", "", normalized)
        normalized = re.sub(r"^[,，、；;:\s]+", "", normalized)
        normalized = re.sub(r"^分[,，、；;:\s]+", "", normalized)
        normalized = re.sub(r"\s+", "", normalized)
        normalized = normalized.strip("，。；;、")
        normalized = cls._SPECIAL_NORMALIZATIONS.get(normalized, normalized)
        normalized = re.sub(r"(?:东部|西部|南部|北部|东南部|东北部|西南部|西北部|城区|市区|农村)$", "", normalized)
        return normalized.strip("，。；;、")

    @classmethod
    def _candidate_queries(cls, query: str) -> list[str]:
        normalized = cls._normalize_query(query)
        if not normalized:
            return []
        candidates = [normalized]
        for prefix in sorted(cls._REGION_PREFIXES, key=len, reverse=True):
            if normalized.startswith(prefix) and len(normalized) > len(prefix):
                tail = normalized[len(prefix):].strip()
                tail = tail.lstrip("省市区县州盟旗")
                if tail:
                    candidates.append(tail)
                    if not tail.endswith(cls._LOCATION_HINT_SUFFIXES) and len(tail) <= 4:
                        candidates.append(f"{tail}市")
                break
        for prefix in sorted(cls._CITY_PREFIXES, key=len, reverse=True):
            if normalized.startswith(prefix) and len(normalized) > len(prefix):
                tail = normalized[len(prefix):].strip()
                if tail:
                    candidates.append(tail)
                    if tail.endswith("县"):
                        candidates.append(f"{tail[:-1]}")
                    if not tail.endswith(cls._LOCATION_HINT_SUFFIXES) and len(tail) <= 4:
                        candidates.append(f"{tail}市")
                break
        return list(dict.fromkeys(item for item in candidates if item))

    @classmethod
    def _allow_geocode_fallback(cls, query: str) -> bool:
        normalized = cls._normalize_query(query)
        if not normalized or len(normalized) > 24 or any(char.isdigit() for char in normalized):
            return False
        if any(token in normalized for token in cls._FALLBACK_BLOCKLIST):
            return False
        if normalized in cls._FOREIGN_PREFIXES or any(normalized.startswith(prefix) for prefix in cls._FOREIGN_PREFIXES):
            return True
        if normalized.endswith(cls._LOCATION_HINT_SUFFIXES):
            return True
        if any(normalized == prefix or normalized.startswith(prefix) for prefix in cls._REGION_PREFIXES):
            return True
        return bool(re.fullmatch(r"[A-Za-z][A-Za-z .,'-]{1,40}", normalized))

    def search_location(self, query: str) -> dict | None:
        normalized_query = self._normalize_query(query)
        province_fallback = self._PROVINCE_DEFAULT_CITIES.get(normalized_query)
        if province_fallback:
            matches = self._loader.search_location(province_fallback)
            if matches:
                row = matches[0]
                return {
                    "name": row.get("city_name_cn") or row.get("city_name_en"),
                    "lat": row["lat"],
                    "lon": row["lon"],
                    "timezone": row["timezone_id"],
                }
        for candidate in self._candidate_queries(query):
            matches = self._loader.search_location(candidate)
            if not matches:
                continue
            row = matches[0]
            return {
                "name": row.get("city_name_cn") or row.get("city_name_en"),
                "lat": row["lat"],
                "lon": row["lon"],
                "timezone": row["timezone_id"],
            }
        return None

    def get_location_info(self, location_name: str) -> dict | None:
        normalized_query = self._normalize_query(location_name)
        result = self.search_location(normalized_query)
        if result:
            return result
        if not self._allow_geocode_fallback(normalized_query):
            return None

        try:
            from geopy.geocoders import Nominatim
            from timezonefinder import TimezoneFinder
        except ImportError:
            # 在线地理编码为可选能力，缺少依赖时只用内置城市库。
            return None

        geolocator = Nominatim(user_agent="ziwei_true_solar")
        try:
            geo_location = geolocator.geocode(normalized_query)
            if not geo_location:
                return None
            timezone_str = TimezoneFinder().timezone_at(
                lng=geo_location.longitude,
                lat=geo_location.latitude,
            )
            return {
                "name": normalized_query,
                "lat": geo_location.latitude,
                "lon": geo_location.longitude,
                "timezone": timezone_str,
            }
        except Exception:
            return None


def get_chinese_hour(hour: int) -> int:
    """将 24 小时制小时转换为地支时序号。"""
    return (hour + 1) // 2 % 12
