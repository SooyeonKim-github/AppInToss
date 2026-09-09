# SunsetSpotFinder V1~V5

`NoelPin`의 데이터 생산기입니다. 서울 전역에서 **퇴근길에 접근하기 쉬운 정확한 노을 후보 좌표를 자동 생성하고, 사람이 검증할 TOP 후보만 남기는 것**이 목적입니다.

앱 사용자에게 노을 점수는 노출하지 않습니다. `candidate_priority`, `frame_score`는 후보 조사 순서를 정하기 위한 내부 값입니다.

## V1 — Candidate Generator

기존/1차/2차 후보 소스는 그대로 유지합니다.

- 육교위노을, 다리위노을, 산책노을, 한강노을
- 계단위노을, 언덕길노을, 전망데크노을, 제방위노을, 수변계단노을, 광장노을, 자전거길노을
- 공원끝노을, 나들목노을, 보행로노을, 성곽길노을, 능선노을, 운동장노을

### 3차 자동발굴 후보

3차는 이미 이름이 붙은 시설을 수집하는 방식이 아니라 **도로/건물/철도/보행망 geometry에서 새로운 좌표를 생성**합니다.

- `ROAD_AXIS` → `대로끝노을`
  - 긴 도로축
  - 일몰방향 정렬
  - 전방 건물 가림 Early Filter
  - 가까운 보행망으로 좌표 snap
- `ALLEY_AXIS` → `골목끝노을`
  - 좁은 서향 도로
  - 좌/우 건물 프레임 존재
  - 정면 가림이 적은 corridor만 통과
- `RAIL_EDGE` → `철길너머노을`
  - 공공 보행망을 sampling
  - 서쪽 방향에 철도가 놓인 지점만 후보화
  - 철도와 너무 가깝거나 먼 후보 제거
- `APARTMENT_GAP` → `아파트사이노을`
  - 아파트/공동주택 건물쌍 탐지
  - 동 사이 corridor가 일몰방향과 일치하는 경우 후보화
  - 보행망이 있으면 공공보행 좌표로 snap

자동발굴 후보에는 다음 내부 필드가 추가됩니다.

- `auto_sunset_alignment_deg`
- `view_bearing_deg`
- `frame_score`
- `access_status`
- `requires_access_verification`
- `discovery_reason`

보행망 데이터가 있으면 `PEDESTRIAN_NETWORK`로 확인된 후보만 우선 사용합니다. 보행망 데이터 자체가 없을 때는 `ACCESS_UNCHECKED`로 남으며 **현장 검증 전 공개하지 않습니다.**

## V2 — Geo Analysis

- 지하철역/업무지구 최단거리
- 한강/수변 거리 및 일몰방향 정렬
- DEM 고도 샘플링
- 건물/나무의 일몰 sector 가림 추정
- `frame_score` 정규화

3차 자동발굴에서는 `openness_score`만 높다고 좋은 후보로 보지 않습니다. 좌우 구조물이 자연스럽게 노을을 감싸는 골목/아파트 후보는 `frame_score`를 별도로 평가합니다.

## V3 — Commute + Building Gap

- 역 접근성 기반 `is_commute_candidate`
- 기존 `URBAN_STREET` 건물사이 후보 생성
- 도로방향/건물프레임 힌트
- V1에서 생성된 장소형 `sunset_type`은 유지

## V4 — Subway Window Sunset

- 지상 지하철/교량 구간 필터
- 열차 진행방향과 일몰 azimuth 비교
- `왼쪽 창문 / 오른쪽 창문 / 앞쪽 / 뒤쪽`
- `지하철창밖노을`

## V5 — Ranking + Verification

- 내부 후보 TOP N
- `frame_score` 포함 Ranking
- 월별 추천 계절 힌트
- Folium HTML 지도
- Excel 검토 리포트
- 검증 Queue
- `CANDIDATE → REMOTE_VERIFIED → FIELD_VERIFIED`
- FIELD_VERIFIED만 `verified_spots.json`으로 publish

3차 자동발굴 후보는 HTML 지도 팝업에서 **왜 발견됐는지**, 일몰축 오차, frame score, 접근성 상태를 함께 확인할 수 있습니다.

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

## 3차 자동발굴 raw layer

```text
data/raw/roads.geojson
data/raw/buildings.geojson
data/raw/railways.geojson
data/raw/pedestrian_network.geojson
```

없으면 demo geometry로 4종 자동발굴 흐름을 테스트할 수 있습니다.

## 결과

`data/processed/`
- `v1_candidates.csv`
- `v2_geo_analysis.csv`
- `v3_commute_urban.csv`
- `v4_subway_window.csv`
- `v5_ranked.csv`

`data/output/`
- `candidate_map.html`
- `finder_report.xlsx`
- `top_candidates.csv`
- `verification_queue.csv`
- `noelpin_candidates.json`
- `verified_spots.json`

## 원칙

- 자동 후보는 실제 명소가 아님
- 도로 중앙, 사유지, 철도 시설 내부 등을 최종 추천 좌표로 사용하지 않음
- 보행망으로 snap되지 않은 후보는 `ACCESS_UNCHECKED`
- 현장 안전/출입 가능 여부 확인 전 FIELD_VERIFIED 금지
- 내부 ranking/frame score는 앱의 사용자용 `노을점수`로 노출하지 않음
