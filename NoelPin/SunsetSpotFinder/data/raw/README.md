# Raw data drop zone

Finder는 원본 파일이 없어도 demo 데이터로 끝까지 실행됩니다. 실제 실행 시 아래 규격으로 정규화한 파일을 넣습니다.

- `pedestrian_bridges.csv`: `name,latitude,longitude`
- `bridges.geojson`, `parks.geojson`, `trails.geojson`, `riverside.geojson`
- `subway_stations.csv`: `station,line,latitude,longitude`
- `office_hubs.csv`: `name,latitude,longitude`
- `trees.csv`: `name,latitude,longitude,height_m,crown_m`
- `buildings.geojson`: Polygon/MultiPolygon, optional `height_m`
- `roads.geojson`: LineString/MultiLineString
- `water.geojson`: LineString/Polygon/Multi* geometry
- `subway_segments.csv`: `line,from_station,to_station,from_lat,from_lon,to_lat,to_lon,direction,is_surface,is_bridge`
- `seoul_dem.tif`: optional DEM; install `requirements-geo.txt` to enable raster sampling.

GeoJSON 좌표계는 WGS84(EPSG:4326)를 기준으로 합니다.
