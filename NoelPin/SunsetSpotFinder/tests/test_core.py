from __future__ import annotations

import unittest

import pandas as pd

from analyzers.subway_window_analyzer import _window_side
from demo_data import demo_automatic_layers
from generators.automatic import AutomaticCandidateGenerator
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
                    "openness": .25, "commute": .25, "view": .15,
                    "elevation": .1, "station": .1, "uniqueness": .05, "frame": .1,
                }
            }
        }

    def test_ranker_prefers_better_metrics(self):
        frame = pd.DataFrame([
            {"candidate_id": "A", "source_type": "STAIR", "openness_score": .9, "commute_score": .9, "view_score": .9, "elevation_score": .9, "station_score": .9, "uniqueness_score": .9, "frame_score": .9, "station_distance_m": 100},
            {"candidate_id": "B", "source_type": "PLAZA", "openness_score": .2, "commute_score": .2, "view_score": .2, "elevation_score": .2, "station_score": .2, "uniqueness_score": .2, "frame_score": .2, "station_distance_m": 100},
        ])
        ranked = CandidateRanker(self.config).rank(frame)
        self.assertEqual(ranked.iloc[0]["candidate_id"], "A")
        self.assertGreater(ranked.iloc[0]["candidate_priority"], ranked.iloc[1]["candidate_priority"])

    def test_automatic_source_types(self):
        expected = {
            "ROAD_AXIS": "대로끝노을",
            "ALLEY_AXIS": "골목끝노을",
            "RAIL_EDGE": "철길너머노을",
            "APARTMENT_GAP": "아파트사이노을",
        }
        frame = pd.DataFrame([
            {"candidate_id": source_type, "source_type": source_type, "station_distance_m": 100}
            for source_type in expected
        ])
        ranked = CandidateRanker(self.config).rank(frame).set_index("source_type")
        for source_type, sunset_type in expected.items():
            self.assertEqual(ranked.loc[source_type, "sunset_type"], sunset_type)


class AutomaticDiscoveryTest(unittest.TestCase):
    def test_demo_layers_generate_all_third_wave_types(self):
        layers = demo_automatic_layers()
        generated = AutomaticCandidateGenerator({"automatic_discovery": {}}).generate(
            layers["roads_geojson"], layers["buildings_geojson"],
            layers["railways_geojson"], layers["pedestrian_network_geojson"], 270.0,
        )
        types = set(generated["source_type"].astype(str))
        self.assertTrue({"ROAD_AXIS", "ALLEY_AXIS", "RAIL_EDGE", "APARTMENT_GAP"}.issubset(types))
        self.assertTrue(generated["frame_score"].between(0, 1).all())
        self.assertTrue(generated["auto_generated"].all())
        self.assertTrue((generated["access_status"] == "PEDESTRIAN_NETWORK").all())


if __name__ == "__main__":
    unittest.main()
