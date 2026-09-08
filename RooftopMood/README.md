# 루프탑무드 (RooftopMood)

> 노을이 예쁜 서울 루프탑 카페를 찾아드려요.

앱인토스용 서울 루프탑 카페 추천 앱입니다.
검색창 없이 `뷰 선택 → 가능한 지역 선택 → 추천 TOP5` 흐름으로 동작하며,
`오늘 노을 보기 제일 좋은 곳` 버튼을 누르면 서울 전체 TOP5를 바로 보여줍니다.

## 현재 구현 범위

- 루프탑무드 홈 UI
- 실제 서울 일몰 시간/일몰 방위각 계산
- Open-Meteo 기반 일몰 시간대 날씨와 노을 기대도
- 뷰 4종: 한강뷰 / 시티뷰 / 궁궐뷰 / 숲뷰
- 뷰별 가능한 지역을 카페 데이터에서 동적으로 계산
- 지역 선택 후 추천 TOP5 세로 카드
- 오늘 노을 보기 좋은 서울 전체 TOP5
- 카페별 오늘 노을 방향 / BEST TIME
- 카카오맵 바로가기
- 카페별 사용자 대표 사진 1장 업로드
- 사진 WebP 압축 / 최대 10MB 제한
- 사진 PENDING → APPROVED / REJECTED 검수
- Supabase PostgreSQL + Storage 연동
- Render 배포 Blueprint
- 샘플 카페 JSON 8개
- FastAPI Swagger 문서
- Windows 실행 배치 파일

> `data/seoul_rooftop_cafes.json`의 카페는 구조 검증용 샘플이며 실제 매장 데이터가 아닙니다.

## 운영 구조

```text
Apps in Toss / React
        │
        │ HTTPS
        ▼
Render
FastAPI Backend
        │
        ├──────────────┐
        ▼              ▼
Supabase DB       Supabase Storage
cafes             cafe-photos
cafe_photos       {cafe_id}/cover.webp
```

프론트엔드는 Supabase에 직접 쓰지 않습니다.
`SUPABASE_SERVICE_ROLE_KEY`는 FastAPI 서버의 환경변수에만 저장하며 GitHub/프론트 코드에는 절대 넣지 않습니다.

## 구조

```text
RooftopMood/
├─ frontend/                React + TypeScript + Vite + Apps in Toss
├─ backend/                 FastAPI
│  ├─ app/
│  └─ migrations/
├─ DataCollector/           카페 수집/분류/설명 생성
├─ data/                    로컬 샘플 데이터
├─ render.yaml              Render 배포 Blueprint
├─ start_all.bat
├─ start_frontend.bat
├─ start_backend.bat
└─ run_data_collector.bat
```

## 로컬 실행

프로젝트 루트에서:

```bat
start_all.bat
```

- 프론트: http://localhost:5173
- 백엔드: http://localhost:8000
- Swagger: http://localhost:8000/docs

기본 `DATA_BACKEND=json`이므로 로컬에서는 기존 샘플 JSON을 사용합니다.

### Backend 수동 실행

```powershell
cd backend
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
uvicorn app.main:app --reload --port 8000
```

### Frontend 수동 실행

```powershell
cd frontend
Copy-Item .env.example .env
npm install
npm run dev
```

## 운영 환경변수

Render에서는 최소 아래 값을 설정합니다.

```env
APP_ENV=production
DATA_BACKEND=supabase
SUPABASE_URL=https://<project-ref>.supabase.co
SUPABASE_SERVICE_ROLE_KEY=<server-secret>
SUPABASE_STORAGE_BUCKET=cafe-photos
PHOTO_UPLOAD_ENABLED=true
ADMIN_API_KEY=<long-random-secret>
FRONTEND_ORIGIN=<apps-in-toss-frontend-origin>
WEATHER_MODE=open_meteo
```

`SUPABASE_SERVICE_ROLE_KEY`와 `ADMIN_API_KEY`는 GitHub에 커밋하지 않습니다.

## Supabase DB

운영 DB에는 아래 핵심 테이블이 있습니다.

### cafes

- 카페명 / 주소 / 좌표
- 지역
- 뷰 점수
- 고정 뷰 설명
- 뷰 방향
- 카카오맵 URL
- 활성 여부

### cafe_photos

```text
id
cafe_id             UNIQUE
image_url
storage_path         UNIQUE
uploaded_by
status               PENDING / APPROVED / REJECTED
content_type
width / height
file_size_bytes
created_at
approved_at
```

`cafe_id UNIQUE` 제약으로 DB 자체에서 카페당 사진을 1장만 허용합니다.

Supabase 스키마는 다음 파일에도 보관합니다.

```text
backend/migrations/001_create_rooftop_mood_schema.sql
```

## 사진 저장 구조

사용자가 사진을 고르면:

```text
React
  ↓ multipart/form-data
POST /api/v1/cafes/{cafe_id}/photo
  ↓
FastAPI
  ├─ 확장자/MIME 검사
  ├─ 최대 10MB 검사
  ├─ EXIF 방향 보정
  └─ 1600px 이하 WebP 변환
  ↓
Supabase Storage
cafe-photos/{cafe_id}/cover.webp
  ↓
Supabase cafe_photos
status=PENDING
```

업로드 직후 사용자의 카드에는 선택한 사진이 보이지만, 다른 사용자에게 영구 노출되는 대표 사진은 `APPROVED` 이후에만 추천 API의 `imageUrl`로 반환됩니다.

동시에 두 사람이 같은 카페에 올리면 Storage 고정 경로와 DB `UNIQUE(cafe_id)` 양쪽에서 두 번째 업로드를 거부합니다.

## 사진 검수

별도 관리자 화면을 만들기 전에는 Swagger로 검수할 수 있습니다.
모든 관리자 요청에는 Render의 `ADMIN_API_KEY` 값을 `X-Admin-Key` 헤더로 넣어야 합니다.

```text
GET  /api/v1/admin/photos?status=PENDING
POST /api/v1/admin/photos/{photo_id}/approve
POST /api/v1/admin/photos/{photo_id}/reject
```

## 주요 API

```text
GET  /api/v1/home
GET  /api/v1/views/{view}/regions
GET  /api/v1/recommendations?view=HAN_RIVER&region=YEOUIDO
GET  /api/v1/recommendations/sunset-best
GET  /api/v1/cafes/{cafe_id}
POST /api/v1/cafes/{cafe_id}/photo
```

## Render 배포

저장소에 `RooftopMood/render.yaml`이 포함되어 있습니다.
Render에서 GitHub 저장소 `SooyeonKim-github/AppInToss`를 연결하고 Blueprint를 사용하면 FastAPI 서비스 설정이 자동으로 잡힙니다.

필수 비밀 환경변수:

```text
SUPABASE_URL
SUPABASE_SERVICE_ROLE_KEY
ADMIN_API_KEY
FRONTEND_ORIGIN
```

배포 후 생성되는 주소 예시:

```text
https://<render-service>/health
https://<render-service>/api/v1/home
https://<render-service>/docs
```

프론트 운영 환경의 `VITE_API_BASE_URL`은 다음처럼 Render API 주소로 설정합니다.

```env
VITE_API_BASE_URL=https://<render-service>/api/v1
```

## DataCollector

`DataCollector/`에는 실제 서울 루프탑 카페 DB 구축을 위한 자동 수집기가 포함되어 있습니다.

```powershell
cd DataCollector
Copy-Item .env.example .env
# .env에 Kakao/Naver API 키 입력
pip install -r requirements.txt

python main.py discover
python main.py evidence --limit 10
python main.py evidence
python main.py describe
```

Windows에서는:

```bat
run_data_collector.bat discover
run_data_collector.bat evidence --limit 10
```

생성 파일:

```text
output/cafe_descriptions.csv
output/cafe_db_ready.csv
```

## 고정 뷰 설명 / 오늘 노을 정보 분리

DB에는 날짜에 따라 변하지 않는 정보만 저장합니다.

```text
view_description
view_direction_deg
view_direction_confidence
view score / tags
```

매일 바뀌는 아래 값은 API 요청 시 계산합니다.

```text
sunset_time
sunset_azimuth_deg
sunset_position
best_time
```

예시:

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

따라서 계절이 바뀌어도 DB를 다시 생성할 필요 없이 오늘의 노을 방향과 BEST TIME만 자동으로 바뀝니다.

## 다음 단계

1. DataCollector 실제 결과를 Supabase `cafes`로 적재
2. Render 서비스 생성 및 비밀 환경변수 등록
3. 운영 Render URL을 frontend `VITE_API_BASE_URL`에 연결
4. 앱인토스 사용자 식별키를 사진 업로드 `X-User-Key`에 연결
5. 사진 신고/삭제 및 관리자 UI 추가
6. 앱인토스 실기기 테스트 후 배포
