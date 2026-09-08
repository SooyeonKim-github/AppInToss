from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from math import acos, atan2, cos, degrees, pi, radians, sin, tan


@dataclass(frozen=True)
class SunsetGeometry:
    date: date
    sunset_time: str
    sunset_hour: int
    sunset_minute: int
    sunset_azimuth_deg: float


class SolarGeometryCalculator:
    ZENITH_DEG = 90.833

    @staticmethod
    def _fractional_year(target_date: date, hour: float = 12.0) -> float:
        days = 366 if target_date.year % 4 == 0 and (target_date.year % 100 != 0 or target_date.year % 400 == 0) else 365
        n = target_date.timetuple().tm_yday
        return 2 * pi / days * (n - 1 + (hour - 12) / 24)

    @classmethod
    def calculate(cls, target_date: date, latitude: float, longitude: float, timezone_offset_hours: float = 9.0) -> SunsetGeometry:
        gamma = cls._fractional_year(target_date)
        eqtime = 229.18 * (0.000075 + 0.001868 * cos(gamma) - 0.032077 * sin(gamma) - 0.014615 * cos(2 * gamma) - 0.040849 * sin(2 * gamma))
        decl = 0.006918 - 0.399912 * cos(gamma) + 0.070257 * sin(gamma) - 0.006758 * cos(2 * gamma) + 0.000907 * sin(2 * gamma) - 0.002697 * cos(3 * gamma) + 0.00148 * sin(3 * gamma)
        lat = radians(latitude)
        cos_ha = cos(radians(cls.ZENITH_DEG)) / (cos(lat) * cos(decl)) - tan(lat) * tan(decl)
        cos_ha = max(-1.0, min(1.0, cos_ha))
        hour_angle_deg = degrees(acos(cos_ha))
        solar_noon_min = 720 - 4 * longitude - eqtime + timezone_offset_hours * 60
        sunset_min = (solar_noon_min + 4 * hour_angle_deg) % (24 * 60)
        hour = int(sunset_min // 60)
        minute = int(round(sunset_min - hour * 60))
        if minute == 60:
            hour = (hour + 1) % 24
            minute = 0
        h = radians(hour_angle_deg)
        azimuth = (degrees(atan2(sin(h), cos(h) * sin(lat) - tan(decl) * cos(lat))) + 180) % 360
        return SunsetGeometry(target_date, f"{hour:02d}:{minute:02d}", hour, minute, round(azimuth, 2))
