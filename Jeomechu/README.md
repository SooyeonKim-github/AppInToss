# 저메추

직장인이 퇴근 전에 5초 안에 오늘 저녁 메뉴를 뽑는 Apps-in-Toss 미니앱 V1.

## V1 기능

- `오늘 당신의 저메추는… 두구두구 🥁` 1.5초 공개 애니메이션
- 사용자 익명 `clientId + 날짜` 기반 오늘의 메뉴 고정
- COMMON 60% / UNCOMMON 30% / RARE 10% 희귀도 선택
- 광고 후 재뽑기용 reroll API
- 오늘 메뉴 하트 토글
- 당일 하트 TOP10 랭킹 API, 메인 TOP3 노출
- 메뉴 296종 seed 데이터 포함
- 개발 SQLite / 운영 PostgreSQL 전환 가능

## 실행

Windows에서는 `start_all.bat` 실행.

직접 실행하려면:

```bash
cd backend
python -m venv .venv
.venv\\Scripts\\activate
pip install -r requirements.txt
copy .env.example .env
python -m uvicorn app.main:app --reload --port 8000
```

```bash
cd frontend
npm install
copy .env.example .env
npm run dev
```

- Frontend: http://localhost:5173
- Backend: http://localhost:8000
- Swagger: http://localhost:8000/docs

## API

- `GET /api/v1/menu/today?clientId=...`
- `POST /api/v1/menu/reroll`
- `POST /api/v1/menu/{menuId}/like`
- `GET /api/v1/ranking/today`
- `GET /health`

## 메뉴 데이터

`backend/data/menus.json`가 메뉴 마스터의 원본이다. 희귀도와 카테고리별 메뉴명 배열로 압축해 관리하며, 앱 시작 시 `menus` 테이블이 비어 있으면 자동 seed 한다.

구조:

- 1단계 키: `COMMON / UNCOMMON / RARE`
- 2단계 키: `KOREAN / JAPANESE / CHINESE / ...`
- 값: 메뉴명 배열

DB seed 시 `weight`, `emoji`, `tagline`은 희귀도/카테고리 규칙으로 자동 생성한다.

V1에서는 메뉴명 자체가 핵심 콘텐츠이므로 외부 사이트 크롤링에 의존하지 않는다. 음식점/가격/사진 등 외부 변화 데이터가 필요해지는 V2 이후 별도 수집 파이프라인을 붙인다.

## 운영 DB

로컬 기본값:

```env
DATABASE_URL=sqlite:///./jeomechu.db
```

운영에서는 PostgreSQL URL로 교체한다.

```env
DATABASE_URL=postgresql+psycopg://USER:PASSWORD@HOST:5432/DBNAME
```

## 광고

`frontend/src/services/adService.ts`로 광고 의존성을 격리했다. 광고 유닛 미설정 상태에서는 개발 편의를 위해 재뽑기가 바로 진행된다. 앱인토스 광고 유닛을 발급받은 뒤 해당 파일에서 Rewarded Ad SDK의 load/show/reward 흐름을 연결한다.
