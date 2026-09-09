# Raw data drop zone

Finder는 원본 파일이 없어도 demo 데이터로 끝까지 실행됩니다. 실제 실행 시 아래 규격으로 정규화한 파일을 넣습니다.

## V1 candidate sources

기존 후보:
- `pedestrian_bridges.csv`: `name,latitude,longitude` → `육교위노을`
- `bridges.geojson` → `다리위노을`
- `parks.geojson` → `산책노을`
- `trails.geojson` → `산책노을`
- `riverside.geojson` → `한강노을`

1차 확장 후보:
- `stairs.geojson`: Point/LineString/MultiLineString → `계단위노을`
- `hill_roads.geojson`: LineString/MultiLineString → `언덕길노을`
- `view_decks.csv`: `name,latitude,longitude` → `전망데크노을`
- `levees.geojson`: LineString/MultiLineString → `제방위노을`
- `river_stairs.csv`: `name,latitude,longitude` → `수변계단노을`
- `plazas.geojson`: Point/Polygon/MultiPolygon → `광장노을`
- `bike_paths.geojson`: LineString/MultiLineString → `자전거길노을`

2차 확장 후보:
- `parks.geojson` 재사용 → `공원끝노을`
  - 별도 파일 없이 공원 Polygon의 서쪽 25% 경계만 `PARK_EDGE` 후보로 자동 생성
- `river_access.csv`: `name,latitude,longitude` → `나들목노을`
- `pedestrian_paths.geojson`: LineString/MultiLineString → `보행로노을`
- `fortress_trails.geojson`: LineString/MultiLineString → `성곽길노을`
- `ridge_trails.geojson`: LineString/MultiLineString → `능선노을`
- `sports_grounds.geojson`: Polygon/MultiPolygon → `운동장노을`

GeoJSON의 이름 속성은 기본적으로 `properties.name`을 사용합니다. 선/면 데이터는 V1에서 `sample_interval_m` 간격으로 후보 좌표를 생성합니다. `PARK_EDGE`만 `sampling_mode: west_edge`를 사용해 서쪽 경계 후보만 남깁니다.

`ridge_trails.geojson`은 일반 등산로 전체가 아니라 실제 능선 구간만 넣는 것을 권장합니다. `sports_grounds.geojson`은 공공 접근이 가능한 운동장/체육공원만 대상으로 합니다.

## Context layers

- `subway_stations.csv`: `station,line,latitude,longitude`
- `office_hubs.csv`: `name,latitude,longitude`
- `trees.csv`: `name,latitude,longitude,height_m,crown_m`
- `buildings.geojson`: Polygon/MultiPolygon, optional `height_m`
- `roads.geojson`: LineString/MultiLineString
- `water.geojson`: LineString/Polygon/Multi* geometry
- `subway_segments.csv`: `line,from_station,to_station,from_lat,from_lon,to_lat,to_lon,direction,is_surface,is_bridge`
- `seoul_dem.tif`: optional DEM; install `requirements-geo.txt` to enable raster sampling.

GeoJSON 좌표계는 WGS84(EPSG:4326)를 기준으로 합니다.

모든 후보는 현장 검증 전 `CANDIDATE`입니다. 차도, 출입 제한 구역, 사유지, 위험한 제방/절벽 등 보행 안전성이 확인되지 않은 위치는 실제 NoelPin 스팟으로 공개하지 않습니다.
