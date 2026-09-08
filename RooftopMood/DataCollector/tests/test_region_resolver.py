from pipeline.region_resolver import RegionResolver
from settings import BASE_DIR


def resolver() -> RegionResolver:
    return RegionResolver(BASE_DIR / "config" / "regions.yaml")


def test_seongsu_address_resolves_to_seongsu():
    result = resolver().resolve({
        "road_address": "서울 성동구 서울숲2길 24-1",
        "address": "서울 성동구 성수동1가 685-483",
        "latitude": "37.54686182777454",
        "longitude": "127.04126958888213",
    })
    assert result["region_code"] == "SEONGSU"
    assert str(result["region_resolution_source"]).startswith("ADDRESS:")


def test_apgujeong_result_is_not_mislabeled_as_seongsu():
    result = resolver().resolve({
        "address": "서울 강남구 압구정동 376-1",
        "latitude": "37.531416532105254",
        "longitude": "127.04226573399961",
    })
    assert result["region_code"] == "GANGNAM"
    assert result["region_code"] != "SEONGSU"


def test_yeouido_is_resolved_by_real_address():
    result = resolver().resolve({
        "address": "서울 영등포구 여의도동 23",
        "latitude": "37.5220",
        "longitude": "126.9245",
    })
    assert result["region_code"] == "YEOUIDO"
