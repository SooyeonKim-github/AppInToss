from __future__ import annotations

import unittest
import pandas as pd
from analyzers.subway_window_analyzer import _window_side
from geo_utils import angular_distance_deg,bearing_deg,haversine_m
from ranking.candidate_ranker import CandidateRanker

class GeoUtilsTest(unittest.TestCase):
    def test_haversine_positive(self): self.assertGreater(haversine_m(37.5,127.0,37.51,127.0),1000)
    def test_bearing_east(self): self.assertLess(angular_distance_deg(bearing_deg(37.5,127.0,37.5,127.01),90),2)
    def test_window_side(self): self.assertEqual(_window_side(0,90),"오른쪽 창문"); self.assertEqual(_window_side(0,270),"왼쪽 창문")

class RankerTest(unittest.TestCase):
    def test_ranker_prefers_better_metrics(self):
        config={"ranking":{"weights":{"openness":.3,"commute":.25,"view":.15,"elevation":.1,"station":.1,"uniqueness":.1}}}; frame=pd.DataFrame([{"candidate_id":"A","openness_score":.9,"commute_score":.9,"view_score":.9,"elevation_score":.9,"station_score":.9,"uniqueness_score":.9,"station_distance_m":100},{"candidate_id":"B","openness_score":.2,"commute_score":.2,"view_score":.2,"elevation_score":.2,"station_score":.2,"uniqueness_score":.2,"station_distance_m":100}]); ranked=CandidateRanker(config).rank(frame); self.assertEqual(ranked.iloc[0]["candidate_id"],"A"); self.assertGreater(ranked.iloc[0]["candidate_priority"],ranked.iloc[1]["candidate_priority"])

if __name__=="__main__": unittest.main()
