# SunsetSpotFinder V1~V5

`NoelPin`의 데이터 생산기입니다. 목적은 **서울 전역에서 퇴근길에 접근하기 쉬운 정확한 노을 후보 좌표를 자동 생성하고, 사람이 검증할 TOP 후보만 남기는 것**입니다.

앱 사용자에게 노을 점수는 노출하지 않습니다. `candidate_priority`는 현장조사 순서를 정하기 위한 내부 값입니다.

## V1 — Candidate Generator

기존 후보 소스:
- 보도육교 CSV → `육교위노을`
- 교량 GeoJSON → `다리위노을`
- 공원 GeoJSON → `산책노을`
- 둘레길 GeoJSON → `산책노을`
- 한강변 GeoJSON → `한강노을`

1차 확장 후보 소스:
- 계단 → `STAIR / 계단위노을`
- 언덕길 → `HILL_ROAD / 언덕길노을`
- 전망데크 → `VIEW_DECK / 전망데크노을`
- 제방 → `LEVEE / 제방위노을`
- 수변계단 → `RIVER_STAIRS / 수변계단노을`
- 광장 → `PLAZA / 광장노을`
- 자전거길 → `BIKE_PATH / 자전거길노을`

2차 확장 후보 소스:
- 공원 서쪽 끝 → `PARK_EDGE / 공원끝노을`
  - 기존 `parks.geojson`을 재사용하고 Polygon의 서쪽 25% 경계만 파생 후보로 생성
- 한강/하천 나들목 → `RIVER_ACCESS / 나들목노을`
- 일반 보행로 → `PEDESTRIAN_PATH / 보행로노을`
- 성곽길 → `FORTRESS_TRAIL / 성곽길노을`
- 능선길 → `RIDGE_TRAIL / 능선노을`
- 공공 운동장 → `SPORTS_GROUND / 운동장노을`

V1에서 `source_type`과 사용자 노출용 `sunset_type`을 함께 생성합니다. 이후 V2~V5를 통과해도 최초 장소형 `sunset_type`은 유지되며, `퇴근길노을`, `건물사이노을`, `한강노을` 같은 상황/구도 정보는 추가 태그로만 붙습니다.

공통 처리:
- LineString/Polygon 경계를 일정 간격으로 세분화
- `sampling_mode: west_edge`를 사용하면 서쪽 경계 후보만 남김
- NOAA 방식 일몰시각/일몰 방위각 계산(외부 천문 API 불필요)
- 실데이터가 없을 때 demo 후보 자동 사용

## V2 — Geo Analysis
- 지하철역/업무지구 최단거리
- 한강/수변 거리 및 일몰방향 정렬
- DEM 고도 샘플링(선택)
- 육교/교량/계단/전망데크/제방/성곽길 등 구조물 높이 보정
- 건물/나무의 일몰 sector 가림 추정
- 장소형 source별 내부 view/uniqueness prior 적용

## V3 — Commute + Building Gap
- 역 접근성 기반 `is_commute_candidate`
- 동서 방향 도로에서 `URBAN_STREET` 신규 후보 생성
- 주변 도로 방향으로 `BUILDING_GAP` 힌트
- `BUILDING_GAP`은 내부 힌트이며 V1의 장소형 노을 종류를 덮어쓰지 않음

## V4 — Subway Window Sunset
- 지상 지하철/교량 구간 필터
- 열차 진행방향 bearing 계산
- 일몰 azimuth와 비교해 `왼쪽 창문 / 오른쪽 창문 / 앞쪽 / 뒤쪽` 산출
- 지하철 후보의 `sunset_type`은 `지하철창밖노을`

## V5 — Ranking + Verification Skeleton
- 내부 후보 우선순위 TOP N
- 월별 일몰 방향 기반 추천 계절 힌트
- Folium 검토 지도 + Excel 검토 리포트
- 검증 큐 CSV
- `CANDIDATE → REMOTE_VERIFIED → FIELD_VERIFIED` 상태 모델
- FIELD_VERIFIED만 `verified_spots.json`으로 내보내는 publish gate
- NoelPin이 읽을 `noelpin_candidates.json`

## 실행
```powershell
cd AppInToss\NoelPin\SunsetSpotFinder
.\start_finder.bat
```

직접 실행:
```powershell
py -3.10 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python run_finder.py --stage v5
```

실제 데이터만 허용:
```powershell
python run_finder.py --stage v5 --no-demo
```

단계별 실행: `--stage v1` ~ `--stage v5`.

## 결과
`data/processed/`: `v1_candidates.csv`, `v2_geo_analysis.csv`, `v3_commute_urban.csv`, `v4_subway_window.csv`, `v5_ranked.csv`

`data/output/`: `candidates.csv`, `top_candidates.csv`, `subway_window_candidates.csv`, `candidate_map.html`, `finder_report.xlsx`, `verification_queue.csv`, `noelpin_candidates.json`, `verified_spots.json`, `manifest.json`

## 공공데이터 연결
`data/raw/README.md` 규격으로 정규화합니다. `collectors/seoul_open_api.py`에는 서울 열린데이터광장용 1,000건 단위 generic pager가 들어 있습니다. 데이터셋별 서비스명/컬럼은 수집 스크립트에서 매핑하도록 분리했습니다.

환경변수: `$env:SEOUL_OPEN_DATA_API_KEY="YOUR_KEY"`

## DEM
기본 실행은 DEM 없이 가능합니다. `data/raw/seoul_dem.tif`와 Rasterio가 있으면 자동 사용합니다.
```powershell
pip install -r requirements-geo.txt
```
DEM이 없으면 구조물 높이 보정을 상대고도 proxy로 쓰고 `dem_available=False`를 남깁니다.

## 검증 워크플로
V5 실행 후 `verification_queue.csv`를 지도/로드뷰/현장에서 채웁니다.
```powershell
python verify_candidate.py --id SXXXXXXXXXX --status FIELD_VERIFIED --reviewer sy --standing-description "육교 서쪽 끝 두 번째 가로등 앞" --view-direction 268 --access-ok Y --safety-ok Y --sunset-visible Y --notes "9월 현장 확인"
```
FIELD_VERIFIED에는 위치 설명/접근/안전/노을 확인이 비어 있으면 저장을 거부합니다. 이후 V5를 다시 실행하면 기존 검증 큐를 보존하며 `verified_spots.json`을 재생성합니다.

## 원칙
- 자동 후보는 실제 명소가 아님
- 좌표/안전/출입 가능 여부는 현장 검증 전 VERIFIED 처리하지 않음
- 공원끝 후보는 공원 서쪽 경계의 구조적 후보일 뿐 실제 조망은 V2~V5 및 현장검증으로 판단
- 능선/성곽길은 위험 구간 및 출입 제한 구간을 실제 서비스에서 제외
- 건물 가림 계산은 V2 1차 휴리스틱이며 추후 skyline ray casting으로 교체 가능
- 지하철 창밖노을은 진행방향/지상여부/창문 방향 현장 검증 필요
- 내부 ranking은 사용자 `노을점수`로 노출하지 않음
