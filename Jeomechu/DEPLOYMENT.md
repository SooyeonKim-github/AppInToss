# 김대리의 저메추 - 운영 배포 가이드

현재 구조는 로컬에서는 SQLite를 그대로 사용하고, 운영에서는 Railway PostgreSQL을 `DATABASE_URL`만으로 자동 사용하도록 구성되어 있습니다.

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

## 2. Railway 백엔드 서비스 생성

GitHub 저장소 `SooyeonKim-github/AppInToss`를 Railway 서비스에 연결합니다.

이 저장소는 모노레포이므로 Railway Backend 서비스의 Root Directory를 아래와 같이 지정합니다.

```text
/Jeomechu/backend
```

Railway Config as Code 경로는 저장소 루트 기준 절대 경로로 지정합니다.

```text
/Jeomechu/backend/railway.toml
```

`Jeomechu/backend/Dockerfile`이 자동으로 사용되며 Railway의 `PORT` 환경변수로 FastAPI가 실행됩니다.

## 3. PostgreSQL 추가

같은 Railway 프로젝트에서 PostgreSQL 서비스를 추가합니다.

PostgreSQL 서비스 이름이 `Postgres`인 경우 Backend 서비스의 Variables에 다음 값을 설정합니다.

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

예:

```env
CORS_ORIGINS=https://example-origin-1,https://example-origin-2
```

## 4. Public Domain 생성

Railway Backend 서비스의 Public Networking에서 HTTPS 도메인을 생성합니다.

예:

```text
https://jeomechu-api-production.up.railway.app
```

아래 주소가 정상이어야 합니다.

```text
https://jeomechu-api-production.up.railway.app/health
```

예상 응답:

```json
{
  "ok": true,
  "environment": "production",
  "database": "postgresql"
}
```

첫 기동 시 테이블이 생성되고 `backend/data/menus.json`의 메뉴 데이터가 PostgreSQL에 자동 seed 됩니다.

## 5. 프론트 운영 API 연결

Railway 도메인이 발급되면:

```powershell
cd Jeomechu\frontend
Copy-Item .env.production.example .env.production
```

`.env.production`을 다음처럼 수정합니다.

```env
VITE_API_BASE_URL=https://jeomechu-api-production.up.railway.app
VITE_REWARDED_AD_UNIT_ID=
```

`VITE_API_BASE_URL` 끝의 `/` 유무는 프론트에서 자동 정리합니다.

그 다음 앱인토스 번들을 빌드합니다.

```powershell
npm install
npm run typecheck
npm run build
```

## 6. 배포 전 체크리스트

- `/health`가 `ok: true`를 반환하는지 확인
- health 응답의 `database`가 `postgresql`인지 확인
- 앱 첫 메뉴가 정상 노출되는지 확인
- 좋아요가 새로고침 후에도 유지되는지 확인
- 다른 기기에서도 같은 오늘 인기 순위가 보이는지 확인
- 다시뽑기 결과가 같은 날 이전 메뉴와 중복되지 않는지 확인
- `.env` / `.env.production` 파일이 Git에 올라가지 않았는지 확인

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
