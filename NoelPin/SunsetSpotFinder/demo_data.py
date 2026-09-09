from __future__ import annotations

import pandas as pd


def demo_points() -> pd.DataFrame:
    rows = [
        {"source_type": "PEDESTRIAN_BRIDGE", "sunset_type": "육교위노을", "source_name": "한강초교 앞 보행육교 후보", "latitude": 37.5209, "longitude": 126.9952},
        {"source_type": "BRIDGE", "sunset_type": "다리위노을", "source_name": "잠수교 보행구간 후보", "latitude": 37.5186, "longitude": 126.9959},
        {"source_type": "PARK", "sunset_type": "산책노을", "source_name": "노들섬 서측 후보", "latitude": 37.5172, "longitude": 126.9584},
        {"source_type": "RIVER", "sunset_type": "한강노을", "source_name": "망원 한강변 후보", "latitude": 37.5555, "longitude": 126.8992},
        {"source_type": "TRAIL", "sunset_type": "산책노을", "source_name": "응봉산 산책로 후보", "latitude": 37.5485, "longitude": 127.0304},
        {"source_type": "URBAN_STREET", "sunset_type": "건물사이노을", "source_name": "여의도 건물사이 후보", "latitude": 37.5225, "longitude": 126.9241},

        # V1 first-wave source expansion. These are demo-only coordinates used to
        # exercise the pipeline until normalized Seoul datasets are connected.
        {"source_type": "STAIR", "sunset_type": "계단위노을", "source_name": "언덕 보행계단 후보 (demo)", "latitude": 37.5448, "longitude": 126.9660},
        {"source_type": "HILL_ROAD", "sunset_type": "언덕길노을", "source_name": "서향 언덕길 후보 (demo)", "latitude": 37.5431, "longitude": 126.9602},
        {"source_type": "VIEW_DECK", "sunset_type": "전망데크노을", "source_name": "공원 전망데크 후보 (demo)", "latitude": 37.5514, "longitude": 127.0178},
        {"source_type": "LEVEE", "sunset_type": "제방위노을", "source_name": "하천 제방 후보 (demo)", "latitude": 37.5630, "longitude": 126.8870},
        {"source_type": "RIVER_STAIRS", "sunset_type": "수변계단노을", "source_name": "한강 수변계단 후보 (demo)", "latitude": 37.5288, "longitude": 126.9340},
        {"source_type": "PLAZA", "sunset_type": "광장노을", "source_name": "역앞 광장 후보 (demo)", "latitude": 37.5660, "longitude": 126.9770},
        {"source_type": "BIKE_PATH", "sunset_type": "자전거길노을", "source_name": "한강 자전거길 후보 (demo)", "latitude": 37.5462, "longitude": 126.9120},
    ]
    return pd.DataFrame(rows)


def demo_stations() -> pd.DataFrame:
    return pd.DataFrame([
        {"station": "서빙고", "line": "경의중앙선", "latitude": 37.5196, "longitude": 126.9886},
        {"station": "고속터미널", "line": "3호선", "latitude": 37.5048, "longitude": 127.0049},
        {"station": "노들", "line": "9호선", "latitude": 37.5129, "longitude": 126.9530},
        {"station": "망원", "line": "6호선", "latitude": 37.5561, "longitude": 126.9101},
        {"station": "응봉", "line": "경의중앙선", "latitude": 37.5499, "longitude": 127.0346},
        {"station": "여의나루", "line": "5호선", "latitude": 37.5271, "longitude": 126.9329},
    ])


def demo_office_hubs() -> pd.DataFrame:
    return pd.DataFrame([
        {"name": "여의도 업무지구", "latitude": 37.5218, "longitude": 126.9245},
        {"name": "용산 업무지구", "latitude": 37.5297, "longitude": 126.9648},
        {"name": "강남 업무지구", "latitude": 37.4979, "longitude": 127.0276},
        {"name": "광화문 업무지구", "latitude": 37.5710, "longitude": 126.9769},
    ])


def demo_subway_segments() -> pd.DataFrame:
    return pd.DataFrame([
        {"line": "2호선", "from_station": "당산", "to_station": "합정", "from_lat": 37.5348, "from_lon": 126.9027, "to_lat": 37.5495, "to_lon": 126.9137, "direction": "합정 방면", "is_surface": True, "is_bridge": True},
        {"line": "4호선", "from_station": "동작", "to_station": "이촌", "from_lat": 37.5029, "from_lon": 126.9803, "to_lat": 37.5224, "to_lon": 126.9735, "direction": "이촌 방면", "is_surface": True, "is_bridge": True},
    ])
