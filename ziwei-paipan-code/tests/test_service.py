from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from ziwei_paipan import compute, compute_horoscope


class NatalChartTests(unittest.TestCase):
    def test_four_pillars_sanfang_and_time_quality(self) -> None:
        chart = compute(
            {
                "solar_date": "1953-06-15",
                "time": "03:30",
                "gender": "男",
                "location": "北京",
            }
        )

        self.assertEqual(chart["四柱"]["原文"], "癸巳 戊午 丁酉 壬寅")
        self.assertEqual(chart["derived"]["clock_chinese_hour"], "寅")
        self.assertEqual(chart["derived"]["chinese_hour"], "寅")
        self.assertFalse(chart["derived"]["crossed_shichen_boundary"])
        self.assertAlmostEqual(chart["derived"]["true_solar_shift_minutes"], -14.4, delta=1)

        relations = chart["ai_context"]["computed_relations"]["命宫三方四正"]
        self.assertEqual({item["地支"] for item in relations}, {"辰", "申", "子", "戌"})

    def test_crossed_and_near_shichen_boundary_are_distinct(self) -> None:
        chart = compute(
            {
                "solar_date": "1993-02-05",
                "time": "01:20",
                "gender": "男",
                "location": "北京",
            }
        )

        self.assertEqual(chart["derived"]["clock_chinese_hour"], "丑")
        self.assertEqual(chart["derived"]["chinese_hour"], "子")
        self.assertTrue(chart["derived"]["crossed_shichen_boundary"])
        self.assertTrue(chart["derived"]["near_shichen_boundary"])

    def test_target_date_normalization_and_horoscope_context(self) -> None:
        chart = compute_horoscope(
            {
                "solar_date": "1993年2月5日",
                "time": "18点26",
                "gender": "男",
                "location": "山东威海",
                "target_date": "2026/9/14",
                "target_time": "12点00",
            }
        )

        self.assertEqual(chart["target"]["solar_date"], "2026-09-14")
        self.assertEqual(chart["target"]["time"], "12:00")
        self.assertIn("原局", chart["ai_context"])
        timing = chart["ai_context"]["运限"]
        self.assertEqual(timing["虚岁"], 34)
        self.assertEqual(timing["运限层"]["大限"]["本层命宫叠原局"], "夫妻")
        self.assertEqual(len(timing["运限层"]["流年"]["四化"]), 4)


if __name__ == "__main__":
    unittest.main()
