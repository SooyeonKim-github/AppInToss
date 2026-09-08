# RooftopMood DataCollector

서울 루프탑 카페 후보와 뷰 관련 근거를 자동으로 수집·판정하는 파이프라인입니다.

## 현재 구현 범위

1. Kakao Local API 후보 수집
2. Naver Local API 후보 보완
3. Kakao 주소 API를 이용한 Naver 후보 위경도 보강
4. Kakao/Naver 후보 중복 제거
5. Naver Blog API Evidence 수집
6. RooftopClassifier: 루프탑 운영 가능성 + confidence
7. ViewClassifier: 한강/시티/궁궐/숲 0~5점 + confidence
8. OtherViewDiscovery: 기존 4종 외 반복되는 뷰 후보 자동 발견
9. confidence가 낮거나 근거가 충돌하는 카페만 review_required.csv로 분리
10. ViewFeatureExtractor: 메인뷰/개방감/노을 좌우·정면/랜드마크 feature 추출
11. TemplateDescriptionGenerator: 외부 LLM 없이 짧은 1문장 뷰 설명 생성

## API 키 설정

```powershell
cd DataCollector
Copy-Item .env.example .env
```

```env
KAKAO_REST_API_KEY=...
NAVER_CLIENT_ID=...
NAVER_CLIENT_SECRET=...
```

## 설치

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## 1. 후보 수집

```powershell
python main.py discover
```

생성 파일:
- `output/candidates_raw.csv`
- `output/candidates_deduped.csv`

## 2. Naver Blog Evidence 수집

처음에는 10개 카페만 테스트하는 것을 권장합니다.

```powershell
python main.py evidence --limit 10
```

전체:

```powershell
python main.py evidence
```

생성 파일:
- `output/cafe_evidences.csv`
- `output/evidence_summary.csv`

일반적인 `뷰/전망/뷰 좋은 카페` 검색도 함께 수행해 기존 4개 분류 외의 뷰 표현을 발견할 수 있게 했습니다.

## 3. Rooftop/View 분류

```powershell
python main.py classify
```

생성 파일:
- `output/cafe_classification.csv`: 루프탑 상태 및 4개 뷰 점수/confidence
- `output/review_required.csv`: 수동 확인이 필요한 카페만 추출
- `output/discovered_views.csv`: 남산타워뷰, 한양도성뷰 등 신규 뷰 후보

### Rooftop 상태

- `CONFIRMED`: 최근/직접 근거가 여러 출처에서 반복됨
- `PROBABLE`: 긍정 근거는 있으나 CONFIRMED 기준 미달
- `REVIEW`: 근거가 약함
- `REJECT`: 긍정 근거 없음 또는 최근 폐쇄/미운영 근거가 우세

### View 점수

각 뷰는 `0~5`점과 별도의 `confidence`를 갖습니다.
단일 블로그 한 건만으로 5점이 되지 않도록 source count에 따라 최고점을 제한합니다.

현재 고정 뷰:
- `HAN_RIVER`: 한강뷰
- `CITY`: 시티뷰
- `PALACE`: 궁궐뷰
- `FOREST`: 숲뷰

### OtherViewDiscovery

기존 4개 외 뷰는 자동으로 UI에 추가하지 않습니다.
`discovered_views.csv`에서 여러 카페/여러 근거에 반복 등장하는 후보를 확인한 뒤 정식 카테고리로 승격합니다.

초기 탐지 예시:
- 남산타워
- 북한산
- 한양도성/서울성곽
- 한옥
- 석촌호수
- 청계천
- 롯데타워
- 철길

`cafe_count >= 2`이면 `REVIEW_FOR_CATEGORY`, 한 카페에서만 나온 경우 `KEEP_AS_TAG`로 표시합니다.

## 4. DB 저장용 뷰 설명 생성

외부 LLM/API 호출 없이 Evidence와 분류 결과만 사용합니다.

```powershell
python main.py describe
```

생성 파일:
- `output/cafe_descriptions.csv`: 설명 생성 feature + 최종 1문장
- `output/cafe_db_ready.csv`: 앱 DB import에 바로 쓰기 쉬운 통합 CSV

문장 길이는 한 문장으로 짧게 유지합니다. 예:

> 한강이 정면으로 넓게 펼쳐지고, 해질 무렵에는 오른쪽으로 노을이 내려오는 루프탑이에요.

좌/우/정면 방향은 블로그 Evidence에 해당 표현이 실제로 있을 때만 사용합니다. 방향 근거가 없으면 `노을빛이 함께 들어오는`처럼 보수적으로 생성합니다.

## 5. 한 번에 실행

```powershell
python main.py all --limit 10
```

`discover -> evidence -> classify -> describe`가 순서대로 실행됩니다.

## 다음 단계

1. 실제 수집 결과로 keyword/threshold 튜닝
2. 실제 생성 문장 품질 점검 및 template 튜닝
3. 카페 좌표 + 랜드마크 좌표로 view direction 추정
4. 일몰 azimuth와 view direction 결합
5. 실제 날씨 기반 오늘의 노을 추천 점수

## 좌표 + 일몰 방위각 방향 판정

`describe` 단계는 이제 카페 좌표와 기준일의 실제 일몰 방위각을 계산해 노을 위치를 판정합니다.

```powershell
python main.py describe
```

`--date`를 생략하면 실행일을 기준으로 계산합니다.

### 계산 우선순위

카페 좌표만으로는 루프탑이 바라보는 방향을 알 수 없으므로 주 뷰 방향은 다음 순서로 추정합니다.

1. 블로그 Evidence의 명시적 방위 (`서향`, `남서향`, `서쪽 시야` 등)
2. 확인된 랜드마크 좌표 (`경복궁`, `서울숲`, `남산타워` 등)
3. 한강뷰는 카페에서 가장 가까운 한강 중심선 방향
4. 궁궐뷰/숲뷰는 가장 가까운 대표 target 방향
5. 신뢰 가능한 근거가 없으면 `UNKNOWN`

방위각은 `북=0°, 동=90°, 남=180°, 서=270°`를 사용합니다.

### 출력 필드

- `view_direction_deg`
- `view_direction_confidence`
- `view_direction_source`
- `view_direction_target`
- `sunset_reference_date`
- `sunset_time`
- `sunset_azimuth_deg`
- `sunset_delta_deg`
- `sunset_alignment_score`
- `sunset_position` (`LEFT`, `FRONT`, `RIGHT`, `OUT_OF_VIEW`)
- `sunset_position_confidence`

`sunset_reference_date`를 반드시 함께 저장합니다. 일몰 방위각은 계절에 따라 바뀌므로 날짜가 다른데 동일한 LEFT/RIGHT 문장을 영구적으로 사용하는 것은 권장하지 않습니다. 백엔드 추천 점수는 앱 실행일의 일몰 방위각을 다시 계산하므로 외부 API 키나 LLM 호출이 필요하지 않습니다.


### V2: 동적 노을 정보는 DB에 저장하지 않음
`describe`는 고정 뷰 설명과 뷰 방향만 생성합니다. 일몰 시각/방위각/좌우 판정은 앱 백엔드가 오늘 날짜 기준으로 계산합니다.
