# Raw data drop zone

Finder는 원본 파일이 없어도 demo 데이터로 끝까지 실행됩니다. 실제 실행에서는 WGS84(EPSG:4326)로 정규화한 파일을 넣습니다.

## 기존/1차/2차 V1 후보

- `pedestrian_bridges.csv`: `name,latitude,longitude`
- `bridges.geojson`
- `parks.geojson`
- `trails.geojson`
- `riverside.geojson`
- `stairs.geojson`
- `hill_roads.geojson`
- `view_decks.csv`: `name,latitude,longitude`
- `levees.geojson`
- `river_stairs.csv`: `name,latitude,longitude`
- `plazas.geojson`
- `bike_paths.geojson`
- `river_access.csv`: `name,latitude,longitude`
- `pedestrian_paths.geojson`
- `fortress_trails.geojson`
- `ridge_trails.geojson`
- `sports_grounds.geojson`

`PARK_EDGE / 공원끝노을`은 `parks.geojson`의 서쪽 경계를 재사용합니다.

## 3차 자동발굴 layer

### `roads.geojson`
LineString/MultiLineString.

선택 속성:
- `name`
- `width_m` 또는 `width`, `road_width`

용도:
- 대로끝노을
- 골목끝노을
- 기존 V3 건물사이노을

### `buildings.geojson`
Polygon/MultiPolygon.

선택 속성:
- `name`
- `height_m`
- `is_apartment`
- 건물 용도/명칭에 `아파트`, `공동주택`, `apartment` 등이 포함되어도 아파트 후보로 인식

용도:
- 골목 좌우 frame
- 전방 obstruction
- 아파트사이노을

### `railways.geojson`
LineString/MultiLineString.

선택 속성:
- `name`
- 노선명

용도:
- 철길너머노을

### `pedestrian_network.geojson`
LineString/MultiLineString 형태의 **공공 보행가능 네트워크**.

용도:
- 자동 생성 좌표를 실제 보행망으로 snap
- 철길너머노을의 관찰 후보 생성
- 아파트 사유지 내부 후보 억제

보행망 파일이 없으면 대로/골목/아파트 후보는 `ACCESS_UNCHECKED`로 남을 수 있으며, FIELD_VERIFIED 전 앱에 공개하지 않습니다. 철길너머노을은 안전상 보행망이 없으면 자동 생성하지 않습니다.

## Context layer

- `subway_stations.csv`: `station,line,latitude,longitude`
- `office_hubs.csv`: `name,latitude,longitude`
- `trees.csv`: `name,latitude,longitude,height_m,crown_m`
- `water.geojson`
- `subway_segments.csv`: `line,from_station,to_station,from_lat,from_lon,to_lat,to_lon,direction,is_surface,is_bridge`
- `seoul_dem.tif`: optional DEM

GeoJSON 좌표계는 WGS84(EPSG:4326)를 기준으로 합니다.
