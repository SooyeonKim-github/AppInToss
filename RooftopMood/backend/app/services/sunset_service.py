from dataclasses import dataclass
from datetime import date
from math import acos, atan2, cos, degrees, pi, radians, sin, tan

SEOUL_LAT = 37.5665
SEOUL_LON = 126.9780
SEOUL_UTC_OFFSET = 9
ZENITH = 90.833


@dataclass(frozen=True)
class SunsetResult:
    date: date
    sunset_time: str
    sunset_hour: int
    sunset_minute: int
    sunset_azimuth_deg: float


class SunsetService:
    """NOAA 계열 근사식으로 일몰 시각과 일몰 방위각을 계산한다.

    azimuth: 북=0°, 동=90°, 남=180°, 서=270°.
    """

    @staticmethod
    def _fractional_year(target_date: date, hour: float = 12.0) -> float:
        leap = target_date.year % 4 == 0 and (target_date.year % 100 != 0 or target_date.year % 400 == 0)
        days = 366 if leap else 365
        n = target_date.timetuple().tm_yday
        return 2 * pi / days * (n - 1 + (hour - 12) / 24)

    def get_for_location(
        self,
        target_date: date,
        latitude: float,
        longitude: float,
        timezone_offset_hours: float = SEOUL_UTC_OFFSET,
    ) -> SunsetResult:
        gamma = self._fractional_year(target_date)
        eqtime = 229.18 * (
            0.000075
            + 0.001868 * cos(gamma)
            - 0.032077 * sin(gamma)
            - 0.014615 * cos(2 * gamma)
            - 0.040849 * sin(2 * gamma)
        )
        decl = (
            0.006918
            - 0.399912 * cos(gamma)
            + 0.070257 * sin(gamma)
            - 0.006758 * cos(2 * gamma)
            + 0.000907 * sin(2 * gamma)
            - 0.002697 * cos(3 * gamma)
            + 0.00148 * sin(3 * gamma)
        )

        lat = radians(latitude)
        cos_ha = cos(radians(ZENITH)) / (cos(lat) * cos(decl)) - tan(lat) * tan(decl)
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
        azimuth = (
            degrees(atan2(sin(h), cos(h) * sin(lat) - tan(decl) * cos(lat))) + 180
        ) % 360

        return SunsetResult(
            date=target_date,
            sunset_time=f"{hour:02d}:{minute:02d}",
            sunset_hour=hour,
            sunset_minute=minute,
            sunset_azimuth_deg=round(azimuth, 2),
        )

    def get_today(self, target_date: date | None = None) -> SunsetResult:
        target_date = target_date or date.today()
        return self.get_for_location(target_date, SEOUL_LAT, SEOUL_LON)
