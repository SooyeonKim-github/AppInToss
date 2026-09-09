from __future__ import annotations

import json
from typing import Any

import pandas as pd

from config_loader import resolve_path
from demo_data import demo_office_hubs, demo_points, demo_stations, demo_subway_segments


class LocalCollector:
    def __init__(self, config: dict[str, Any]):
        self.config = config

    def load_csv(self, path: str, required: list[str] | None = None) -> pd.DataFrame:
        resolved = resolve_path(self.config, path)
        if not resolved.exists():
            return pd.DataFrame(columns=required or [])
        frame = pd.read_csv(resolved)
        missing = [column for column in (required or []) if column not in frame.columns]
        if missing:
            raise ValueError(f"{resolved} missing columns: {missing}")
        return frame

    def load_geojson(self, path: str) -> dict[str, Any] | None:
        resolved = resolve_path(self.config, path)
        if not resolved.exists():
            return None
        with resolved.open("r", encoding="utf-8") as fp:
            return json.load(fp)

    def candidate_source_payloads(self) -> list[dict[str, Any]]:
        payloads: list[dict[str, Any]] = []
        for name, source in (self.config.get("candidate_sources") or {}).items():
            if not source.get("enabled", True):
                continue
            path = source.get("path", "")
            kind = source.get("kind")
            resolved = resolve_path(self.config, path)
            if not resolved.exists():
                continue
            if kind == "point_csv":
                payloads.append({"name": name, "config": source, "data": pd.read_csv(resolved)})
            elif kind == "geojson":
                payloads.append({"name": name, "config": source, "data": self.load_geojson(path)})
        return payloads

    def stations(self) -> pd.DataFrame:
        frame = self.load_csv(self.config["context_layers"]["stations_csv"], ["station", "line", "latitude", "longitude"])
        return frame if not frame.empty else demo_stations()

    def office_hubs(self) -> pd.DataFrame:
        frame = self.load_csv(self.config["context_layers"]["office_hubs_csv"], ["name", "latitude", "longitude"])
        return frame if not frame.empty else demo_office_hubs()

    def trees(self) -> pd.DataFrame:
        return self.load_csv(self.config["context_layers"]["trees_csv"], ["latitude", "longitude"])

    def subway_segments(self) -> pd.DataFrame:
        required = ["line", "from_station", "to_station", "from_lat", "from_lon", "to_lat", "to_lon", "direction", "is_surface", "is_bridge"]
        frame = self.load_csv(self.config["context_layers"]["subway_segments_csv"], required)
        return frame if not frame.empty else demo_subway_segments()

    def demo_candidates(self) -> pd.DataFrame:
        return demo_points()
