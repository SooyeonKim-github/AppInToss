# 김대리의 저메추 - 운영 배포 가이드

현재 구조는 로컬에서는 SQLite를 그대로 사용하고, 운영에서는 Railway PostgreSQL을 `DATABASE_URL`만으로 자동 사용하도록 구성되어 있습니다.

현재 운영 백엔드 주소:

```text
https://jeomechu-api-production.up.railway.app
```

## 1. 로컬 개발

백엔드 `.env`는 기존 방식 그대로 사용할 수 있습니다.

```env
APP_ENV=development
DATABASE_URL=sqlite:///./jeomechu.db
CORS_ORIGINS=http://localhost:5173
```

실행:

```powershell
cd Jeomechu
.\start_all.bat
```

백엔드 확인:

```text
http://localhost:8000/health
```

## 2. Railway 백엔드 서비스

GitHub 저장소 `SooyeonKim-github/AppInToss`의 `main` 브랜치를 Railway 서비스 `jeomechu-api`에 연결했습니다.

모노레포 Root Directory:

```text
/Jeomechu/backend
```

빌드는 `Jeomechu/backend/Dockerfile`을 사용합니다. Railway가 주입하는 `PORT` 환경변수로 FastAPI가 실행되며 `/health`를 deployment health check로 사용합니다.

현재 Railway 서비스 설정:

```text
Service: jeomechu-api
Root Directory: /Jeomechu/backend
Dockerfile: Dockerfile
Healthcheck: /health
Restart Policy: ON_FAILURE
```

## 3. PostgreSQL

같은 Railway 프로젝트의 `Postgres` 서비스를 사용합니다. PostgreSQL 서비스에는 persistent volume이 연결되어 있습니다.

Backend Variables:

```env
APP_ENV=production
DATABASE_URL=${{Postgres.DATABASE_URL}}
CORS_ORIGINS=*
WEB_CONCURRENCY=1
DB_POOL_SIZE=5
DB_MAX_OVERFLOW=10
DB_POOL_RECYCLE_SECONDS=300
```

`DATABASE_URL`이 `postgresql://` 또는 `postgres://` 형식이어도 애플리케이션에서 자동으로 SQLAlchemy + psycopg v3 형식으로 변환합니다.

초기 출시에서는 Apps-in-Toss WebView의 실제 Origin이 확정되기 전이므로 `CORS_ORIGINS=*`를 사용합니다. 이 API는 쿠키 기반 인증을 사용하지 않으며 CORS credentials도 비활성화되어 있습니다. 출시 후 실제 Origin이 확인되면 쉼표로 구분해 제한할 수 있습니다.

## 4. 운영 API

Railway Public Networking:

```text
https://jeomechu-api-production.up.railway.app
```

Health endpoint:

```text
https://jeomechu-api-production.up.railway.app/health
```

정상 응답 형태:

```json
{
  "ok": true,
  "environment": "production",
  "database": "postgresql"
}
```

Railway deployment health check에서 `/health` `200 OK`를 확인했습니다.

첫 기동 시 테이블이 생성되고 `backend/data/menus.json`의 메뉴 데이터가 PostgreSQL에 자동 seed 됩니다.

## 5. 프론트 운영 API 연결

프론트의 production 기본 API 주소는 이미 아래 주소로 연결되어 있습니다.

```text
https://jeomechu-api-production.up.railway.app
```

따라서 `.env.production`이 없어도 `npm run build`의 production bundle은 Railway API를 사용합니다. 필요하면 `VITE_API_BASE_URL` 환경변수로 덮어쓸 수 있습니다.

`.env.production.example`:

```env
VITE_API_BASE_URL=https://jeomechu-api-production.up.railway.app
VITE_REWARDED_AD_UNIT_ID=
```

앱인토스 번들 빌드:

```powershell
cd Jeomechu\frontend
npm install
npm run typecheck
npm run build
```

## 6. 출시 전 체크리스트

- Railway `jeomechu-api` deployment 상태가 SUCCESS인지 확인
- `/health`가 `200 OK`인지 확인
- health 응답의 `database`가 `postgresql`인지 확인
- 앱 첫 메뉴가 정상 노출되는지 확인
- 좋아요가 새로고침 후에도 유지되는지 확인
- 다른 기기에서도 같은 오늘 인기 순위가 보이는지 확인
- 다시뽑기 결과가 같은 날 이전 메뉴와 중복되지 않는지 확인
- 실제 Apps-in-Toss Origin 확인 후 CORS 제한 검토
- 리워드 광고 ID 설정

## 운영 구조

```text
Apps-in-Toss WebView
        |
        | HTTPS
        v
Railway FastAPI
        |
        v
Railway PostgreSQL
```

SQLite는 계속 로컬 개발용으로만 유지합니다.
