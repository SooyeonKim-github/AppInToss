# 루프탑무드 (RooftopMood)

> 노을이 예쁜 서울 루프탑 카페를 찾아드려요.

앱인토스용 루프탑 카페 추천 MVP입니다.
검색창 없이 `뷰 선택 → 가능한 지역 선택 → 추천 TOP3` 흐름으로 동작하며,
`오늘 노을 보기 제일 좋은 곳` 버튼으로 선택 과정을 건너뛸 수 있습니다.

## 현재 구현 범위

- 루프탑무드 홈 UI
- 오늘 서울 일몰 시간 계산 (Astral, 외부 API 불필요)
- 노을 기대도 UI/점수 구조 (현재 날씨 입력은 mock)
- 뷰 4종: 한강뷰 / 시티뷰 / 궁궐뷰 / 숲뷰
- 뷰별 가능한 지역을 카페 데이터에서 동적으로 계산
- 지역 선택 후 추천 TOP3
- 오늘 노을 보기 제일 좋은 곳 BEST 1
- 샘플 카페 JSON 8개
- FastAPI Swagger 문서
- Windows 실행 배치 파일

> `data/seoul_rooftop_cafes.json`의 카페는 구조 검증용 샘플이며 실제 매장 데이터가 아닙니다.

## 구조

```text
RooftopMood/
├─ frontend/        React + TypeScript + Vite + Apps in Toss Web Framework 3.x
├─ backend/         FastAPI
├─ data/            루프탑 카페 원천 데이터
├─ start_all.bat
├─ start_frontend.bat
└─ start_backend.bat
```

## 가장 쉬운 실행 방법 (Windows)

프로젝트 루트에서:

```bat
start_all.bat
```

처음 실행할 때 Python/Node 패키지를 설치합니다.

- 프론트: http://localhost:5173
- 백엔드: http://localhost:8000
- Swagger: http://localhost:8000/docs

## 수동 실행

### Backend

```powershell
cd backend
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### Frontend

```powershell
cd frontend
Copy-Item .env.example .env
npm install
npm run dev
```

## 주요 API

```text
GET /api/v1/home
GET /api/v1/views/{view}/regions
GET /api/v1/recommendations?view=HAN_RIVER&region=YEOUIDO
GET /api/v1/recommendations/sunset-best
GET /api/v1/cafes/{cafe_id}
```

## 추천 구조의 핵심

지역 리스트는 프론트엔드에 하드코딩하지 않습니다.
카페 JSON의 `views`와 `region` 값을 읽어 서버가 해당 뷰에서 선택 가능한 지역을 자동 생성합니다.

예를 들어 성수에 한강뷰 카페를 새로 등록하면 한강뷰 선택 시 성수가 자동으로 지역 후보에 포함됩니다.

## 다음 개발 단계

1. 실제 서울 루프탑 카페 30~50곳 데이터셋 구축
2. 실제 날씨 API 연결 (`WeatherService` 교체)
3. 일몰 방위각(solar azimuth) 계산 후 카페 방향과 비교
4. 카페 상세 화면 + 실제 사진
5. 지도/길찾기 연동
6. 운영시간 및 휴무일 반영
7. PostgreSQL로 데이터 이전
8. 앱인토스 실기기 테스트 및 배포 설정


## 앱인토스 SDK 기준

현재 공식 `toss/apps-in-toss-examples`의 WebView 예제 구조에 맞춰 `@apps-in-toss/web-framework` 3.0.4, `@apps-in-toss/devtools` 3.0.4, `apps-in-toss.config.ts` 형식을 사용합니다.

## DataCollector

`DataCollector/`에는 실제 서울 루프탑 카페 DB 구축을 위한 자동 수집기가 포함되어 있습니다.

```powershell
cd DataCollector
Copy-Item .env.example .env
# .env에 Kakao/Naver API 키 입력
pip install -r requirements.txt

# 1) Kakao + Naver Local 후보 수집 및 중복 제거
python main.py discover

# 2) Naver Blog Evidence 수집 (처음 10개만 테스트)
python main.py evidence --limit 10

# 전체 Evidence 수집
python main.py evidence
```

Windows에서는 루트의 `run_data_collector.bat`도 사용할 수 있습니다.

```bat
run_data_collector.bat discover
run_data_collector.bat evidence --limit 10
```

## DataCollector 설명 생성

Evidence 분류 후 외부 LLM/API 호출 없이 DB 저장용 짧은 뷰 설명을 만들 수 있습니다.

```powershell
cd DataCollector
python main.py describe
```

생성 파일: `output/cafe_descriptions.csv`, `output/cafe_db_ready.csv`

예시: `한강이 정면으로 넓게 펼쳐지고, 해질 무렵에는 오른쪽으로 노을이 내려오는 루프탑이에요.`


## 고정 뷰 설명 / 오늘 노을 정보 분리 (V2)

`DataCollector`의 `describe` 단계는 이제 날짜에 따라 바뀌지 않는 정보만 DB용 CSV에 저장합니다.

- 저장: `view_description`, `view_direction_deg`, `view_direction_confidence`, 뷰 점수/태그
- 저장하지 않음: `sunset_time`, `sunset_azimuth_deg`, `sunset_position`, `best_time`

실행:

```powershell
cd DataCollector
python main.py describe
```

앱 요청 시 백엔드는 카페 좌표와 오늘 날짜를 기준으로 `todaySunsetInfo`를 계산합니다.

```json
{
  "viewDescription": "한강이 정면으로 넓게 펼쳐지는 탁 트인 루프탑이에요.",
  "todaySunsetInfo": {
    "sunsetTime": "18:53",
    "position": "RIGHT",
    "positionLabel": "오른쪽",
    "alignmentScore": 82,
    "bestTime": "18:29 ~ 19:01",
    "message": "오늘 노을은 오른쪽 방향에서 보여요 🌇"
  }
}
```

따라서 계절이 바뀌어도 DB를 다시 생성할 필요 없이 노을 방향과 BEST TIME만 매일 자동으로 바뀝니다.
