from datetime import date

from app.services.sunset_service import SunsetService
from app.services.sunset_score_service import SunsetScoreService
from app.services.weather_service import WeatherService, WeatherSnapshot


def test_open_meteo_payload_uses_sunset_window():
    sunset = SunsetService().get_today(date(2026, 9, 8))
    payload = {
        "hourly": {
            "time": [
                "2026-09-08T17:00",
                "2026-09-08T18:00",
                "2026-09-08T19:00",
                "2026-09-08T20:00",
            ],
            "cloud_cover": [10, 30, 50, 90],
            "precipitation_probability": [0, 10, 20, 70],
            "visibility": [25000, 20000, 15000, 4000],
        }
    }

    snapshot = WeatherService._snapshot_from_payload(payload, sunset)
    assert snapshot.cloud_cover == 40
    assert snapshot.precipitation_probability == 20
    assert snapshot.visibility_km == 15.0
    assert snapshot.source == "OPEN_METEO"


def test_sunset_score_penalizes_rain_and_low_visibility():
    good = WeatherSnapshot(35, 5, 22.0)
    bad = WeatherSnapshot(90, 80, 3.0)

    scorer = SunsetScoreService()
    good_score, _ = scorer.calculate(good)
    bad_score, _ = scorer.calculate(bad)

    assert good_score > bad_score
    assert good_score >= 80
    assert bad_score < 40
