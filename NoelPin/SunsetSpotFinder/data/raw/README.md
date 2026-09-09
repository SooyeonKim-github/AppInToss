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

GeoJSON의 이름 속성은 기본적으로 `properties.name`을 사용합니다. 선/면 데이터는 V1에서 `sample_interval_m` 간격으로 후보 좌표를 생성합니다.

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
