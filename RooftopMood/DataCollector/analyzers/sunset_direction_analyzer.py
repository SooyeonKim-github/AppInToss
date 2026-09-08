from __future__ import annotations

from datetime import date
from math import cos, radians

from analyzers.solar_geometry import SolarGeometryCalculator


class SunsetDirectionAnalyzer:
    FRONT_THRESHOLD_DEG = 22.0
    SIDE_VISIBLE_THRESHOLD_DEG = 110.0

    def analyze(self, candidate: dict, view_direction: dict, target_date: date) -> dict:
        try:
            lat = float(candidate.get("latitude"))
            lon = float(candidate.get("longitude"))
            view_deg = float(view_direction.get("view_direction_deg"))
        except (TypeError, ValueError):
            return self._empty(target_date, "MISSING_GEOMETRY")

        solar = SolarGeometryCalculator.calculate(target_date, lat, lon)
        delta = self._signed_delta(view_deg, solar.sunset_azimuth_deg)
        abs_delta = abs(delta)

        if abs_delta <= self.FRONT_THRESHOLD_DEG:
            position = "FRONT"
        elif delta > 0 and abs_delta <= self.SIDE_VISIBLE_THRESHOLD_DEG:
            position = "RIGHT"
        elif delta < 0 and abs_delta <= self.SIDE_VISIBLE_THRESHOLD_DEG:
            position = "LEFT"
        else:
            position = "OUT_OF_VIEW"

        in_view = int(abs_delta <= self.SIDE_VISIBLE_THRESHOLD_DEG)
        alignment = max(0.0, cos(radians(min(abs_delta, 90.0)))) * 100
        view_conf = float(view_direction.get("view_direction_confidence", 0) or 0)
        position_conf = min(0.98, max(0.0, view_conf * 0.97))

        return {
            "sunset_reference_date": target_date.isoformat(),
            "sunset_time": solar.sunset_time,
            "sunset_azimuth_deg": solar.sunset_azimuth_deg,
            "sunset_delta_deg": round(delta, 2),
            "sunset_alignment_score": round(alignment, 1),
            "sunset_position": position,
            "sunset_position_confidence": round(position_conf, 3),
            "sunset_visible": in_view,
            "sunset_direction_source": "SOLAR_GEOMETRY",
        }

    @staticmethod
    def _signed_delta(view_deg: float, sunset_deg: float) -> float:
        return (sunset_deg - view_deg + 180) % 360 - 180

    @staticmethod
    def _empty(target_date: date, reason: str) -> dict:
        return {
            "sunset_reference_date": target_date.isoformat(),
            "sunset_time": "",
            "sunset_azimuth_deg": "",
            "sunset_delta_deg": "",
            "sunset_alignment_score": "",
            "sunset_position": "UNKNOWN",
            "sunset_position_confidence": 0.0,
            "sunset_visible": 0,
            "sunset_direction_source": reason,
        }
