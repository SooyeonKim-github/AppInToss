from __future__ import annotations

import unittest
import pandas as pd
from analyzers.subway_window_analyzer import _window_side
from geo_utils import angular_distance_deg, bearing_deg, haversine_m
from ranking.candidate_ranker import CandidateRanker


class GeoUtilsTest(unittest.TestCase):
    def test_haversine_positive(self):
        self.assertGreater(haversine_m(37.5, 127.0, 37.51, 127.0), 1000)

    def test_bearing_east(self):
        self.assertLess(angular_distance_deg(bearing_deg(37.5, 127.0, 37.5, 127.01), 90), 2)

    def test_window_side(self):
        self.assertEqual(_window_side(0, 90), "오른쪽 창문")
        self.assertEqual(_window_side(0, 270), "왼쪽 창문")


class RankerTest(unittest.TestCase):
    def setUp(self):
        self.config = {
            "ranking": {
                "weights": {
                    "openness": .3,
                    "commute": .25,
                    "view": .15,
                    "elevation": .1,
                    "station": .1,
                    "uniqueness": .1,
                }
            }
        }

    def test_ranker_prefers_better_metrics(self):
        frame = pd.DataFrame([
            {
                "candidate_id": "A",
                "source_type": "STAIR",
                "openness_score": .9,
                "commute_score": .9,
                "view_score": .9,
                "elevation_score": .9,
                "station_score": .9,
                "uniqueness_score": .9,
                "station_distance_m": 100,
            },
            {
                "candidate_id": "B",
                "source_type": "PLAZA",
                "openness_score": .2,
                "commute_score": .2,
                "view_score": .2,
                "elevation_score": .2,
                "station_score": .2,
                "uniqueness_score": .2,
                "station_distance_m": 100,
            },
        ])
        ranked = CandidateRanker(self.config).rank(frame)
        self.assertEqual(ranked.iloc[0]["candidate_id"], "A")
        self.assertGreater(ranked.iloc[0]["candidate_priority"], ranked.iloc[1]["candidate_priority"])

    def test_first_wave_source_types(self):
        expected = {
            "STAIR": "계단위노을",
            "HILL_ROAD": "언덕길노을",
            "VIEW_DECK": "전망데크노을",
            "LEVEE": "제방위노을",
            "RIVER_STAIRS": "수변계단노을",
            "PLAZA": "광장노을",
            "BIKE_PATH": "자전거길노을",
        }
        frame = pd.DataFrame([
            {
                "candidate_id": source_type,
                "source_type": source_type,
                "station_distance_m": 100,
            }
            for source_type in expected
        ])
        ranked = CandidateRanker(self.config).rank(frame).set_index("source_type")
        for source_type, sunset_type in expected.items():
            self.assertEqual(ranked.loc[source_type, "sunset_type"], sunset_type)

    def test_v1_sunset_type_is_preserved(self):
        frame = pd.DataFrame([
            {
                "candidate_id": "CUSTOM",
                "source_type": "STAIR",
                "sunset_type": "특별계단노을",
                "station_distance_m": 100,
            }
        ])
        ranked = CandidateRanker(self.config).rank(frame)
        self.assertEqual(ranked.iloc[0]["sunset_type"], "특별계단노을")


if __name__ == "__main__":
    unittest.main()
