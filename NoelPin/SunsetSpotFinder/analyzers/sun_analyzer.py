from __future__ import annotations

import math
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import pandas as pd

from geo_utils import angular_distance_deg


class SunDirectionAnalyzer:
    def __init__(self, timezone_name: str = "Asia/Seoul"):
        self.tz = ZoneInfo(timezone_name)

    @staticmethod
    def _solar_terms(target_date: date) -> tuple[float, float]:
        day = target_date.timetuple().tm_yday
        gamma = 2 * math.pi / 365 * (day - 1)
        eq_time = 229.18 * (0.000075 + 0.001868 * math.cos(gamma) - 0.032077 * math.sin(gamma) - 0.014615 * math.cos(2 * gamma) - 0.040849 * math.sin(2 * gamma))
        decl = 0.006918 - 0.399912 * math.cos(gamma) + 0.070257 * math.sin(gamma) - 0.006758 * math.cos(2 * gamma) + 0.000907 * math.sin(2 * gamma) - 0.002697 * math.cos(3 * gamma) + 0.00148 * math.sin(3 * gamma)
        return eq_time, decl

    def sunset_info(self, latitude: float, longitude: float, target_date: date) -> tuple[str, float]:
        eq_time, decl = self._solar_terms(target_date)
        lat_rad = math.radians(latitude); zenith = math.radians(90.833)
        cos_ha = math.cos(zenith) / (math.cos(lat_rad) * math.cos(decl)) - math.tan(lat_rad) * math.tan(decl)
        cos_ha = max(-1.0, min(1.0, cos_ha)); hour_angle = math.acos(cos_ha); hour_angle_deg = math.degrees(hour_angle)
        solar_noon_utc_min = 720 - 4 * longitude - eq_time; sunset_utc_min = solar_noon_utc_min + 4 * hour_angle_deg
        utc_midnight = datetime(target_date.year, target_date.month, target_date.day, tzinfo=timezone.utc)
        sunset_dt = (utc_midnight + timedelta(minutes=sunset_utc_min)).astimezone(self.tz)
        azimuth = (math.degrees(math.atan2(math.sin(hour_angle), math.cos(hour_angle) * math.sin(lat_rad) - math.tan(decl) * math.cos(lat_rad))) + 180) % 360
        return sunset_dt.isoformat(timespec="seconds"), float(azimuth)

    def annotate(self, candidates: pd.DataFrame, target_date: date) -> pd.DataFrame:
        frame = candidates.copy(); timestamps=[]; azimuths=[]
        for row in frame.itertuples(index=False):
            timestamp, value = self.sunset_info(float(row.latitude), float(row.longitude), target_date)
            timestamps.append(timestamp); azimuths.append(round(value, 2))
        frame["sunset_at"] = timestamps; frame["sunset_azimuth_deg"] = azimuths
        return frame

    def monthly_profile(self, latitude: float, longitude: float, year: int) -> dict[int, float]:
        return {month: round(self.sunset_info(latitude, longitude, date(year, month, 15))[1], 1) for month in range(1, 13)}

    @staticmethod
    def recommended_months(profile: dict[int, float], view_direction_deg: float, tolerance_deg: float = 22) -> list[int]:
        return [month for month, value in profile.items() if angular_distance_deg(value, view_direction_deg) <= tolerance_deg]
