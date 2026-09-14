# ziwei-paipan-code

紫微斗数排盘模块，供 `ziwei` Skill 调用，也可独立使用。输出统一为 JSON。

## 能力

- 真太阳时校正：按出生地经度计算真太阳时，含均时差修正，据此确定排盘时辰。
- 内置全球城市库（中文、英文、拼音检索），自动解析经纬度与时区。中国 1986–1991 年夏令时已处理。
- 本命盘：出生四柱、十二宫位置、正曜辅曜杂曜、庙旺、生年四化、身宫、命主身主、五行局、大限起讫与岁数。
- 运限盘：指定日期的大限、流年、流月、流日、流时，各层带四化与宫位名重排。
- 语义层 `ai_context`：出生四柱、按宫名索引的十二宫、核心宫轴、命宫三方四正、四化落宫、空宫清单。

## 安装

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

`geopy` 与 `timezonefinder` 是可选依赖。装上后，内置城市库查不到的地名会走在线地理编码；不装则只用内置库。

## 使用

本命盘：

```bash
python -m ziwei_paipan --date 1990-05-20 --time 12:30 --gender 男 --location 上海
```

运限盘（在本命盘基础上叠加目标时间的大限流年流月流日流时）：

```bash
python -m ziwei_paipan --date 1990-05-20 --time 12:30 --gender 男 \
  --location 上海 --horoscope-date 2026-09-14 --horoscope-time 14:30
```

| 参数 | 说明 |
| --- | --- |
| `--date` | 公历出生日期 `YYYY-MM-DD` |
| `--time` | 出生时间 `HH:MM`，24 小时制 |
| `--gender` | `男` / `女` / `male` / `female` |
| `--location` | 出生地城市名 |
| `--no-true-solar` | 关闭真太阳时校正，直接按钟表时间定时辰 |
| `--horoscope-date` | 运限盘目标日期，给出时输出运限层 |
| `--horoscope-time` | 运限盘目标时间，默认 `00:00` |
| `--no-ai-context` | 只输出原始排盘数据 |
| `--indent` | JSON 缩进，`0` 压缩为单行 |

作为库调用：

```python
from ziwei_paipan import compute, compute_horoscope

chart = compute({
    "solar_date": "1990-05-20",
    "time": "12:30",
    "gender": "男",
    "location": "上海",
})
```

## 输出结构

| 键 | 内容 |
| --- | --- |
| `input` | 规范化后的输入 |
| `location` | 匹配到的城市名、经纬度、时区 |
| `derived` | 平太阳时、UTC、真太阳时、均时差、排盘时辰 |
| `四柱` | 出生年柱、月柱、日柱、时柱（按真太阳时排盘时辰） |
| `data` | 排盘原始数据；运限模式下为运限层 |
| `ai_context` | 整理后的语义层，仅本命盘模式输出。`basic_info.四柱` 与顶层 `四柱` 相同 |
| `target` | 运限盘的目标日期与时辰，仅运限模式输出 |

## 环境变量

`ZIWEI_DATA_DIR` 可指定城市库与星历文件所在目录，默认使用包内 `ziwei_paipan/data`。

## 边界

排盘只负责生成盘面结构，不做任何吉凶判断。断盘规则由 `ziwei` Skill 承担。
