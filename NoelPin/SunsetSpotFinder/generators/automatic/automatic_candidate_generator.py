from __future__ import annotations

from typing import Any
import pandas as pd

from .road_axis_generator import RoadAxisGenerator
from .alley_axis_generator import AlleyAxisGenerator
from .rail_edge_generator import RailEdgeGenerator
from .apartment_gap_generator import ApartmentGapGenerator


class AutomaticCandidateGenerator:
    def __init__(self, config: dict[str, Any]):
        self.config = config
        self.road = RoadAxisGenerator(config)
        self.alley = AlleyAxisGenerator(config)
        self.rail = RailEdgeGenerator(config)
        self.apartment = ApartmentGapGenerator(config)

    def generate(
        self,
        roads: dict[str, Any] | None,
        buildings: dict[str, Any] | None,
        railways: dict[str, Any] | None,
        pedestrian_network: dict[str, Any] | None,
        sunset_azimuth: float,
    ) -> pd.DataFrame:
        frames = [
            self.road.generate(roads, buildings, pedestrian_network, sunset_azimuth),
            self.alley.generate(roads, buildings, pedestrian_network, sunset_azimuth),
            self.rail.generate(railways, pedestrian_network, sunset_azimuth),
            self.apartment.generate(buildings, pedestrian_network, sunset_azimuth),
        ]
        frames = [frame for frame in frames if not frame.empty]
        if not frames:
            return pd.DataFrame()
        combined = pd.concat(frames, ignore_index=True, sort=False)
        return combined.drop_duplicates(subset=["source_type", "latitude", "longitude"]).reset_index(drop=True)
