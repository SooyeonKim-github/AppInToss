# 김대리의 저메추 - 운영 배포 가이드

현재 구조는 로컬에서는 SQLite를 사용하고, 운영에서는 Railway FastAPI + PostgreSQL을 사용합니다.

현재 운영 백엔드 주소:

```text
https://jeomechu-api-production.up.railway.app
```

## 1. 로컬 개발

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

```text
Service: jeomechu-api
Root Directory: /Jeomechu/backend
Dockerfile: Dockerfile
Healthcheck: /health
Restart Policy: ON_FAILURE
```

## 3. PostgreSQL

같은 Railway 프로젝트의 `Postgres` 서비스를 사용하며 persistent volume이 연결되어 있습니다.

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

`DATABASE_URL`이 `postgresql://` 또는 `postgres://` 형식이어도 SQLAlchemy + psycopg v3 형식으로 자동 변환합니다.

## 4. 운영 API

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

## 5. 리워드 광고

`frontend/src/services/adService.ts`에서 Apps-in-Toss 통합 광고 API를 연결했습니다.

흐름:

```text
앱 진입
  -> loadFullScreenAd 미리 로드
  -> loaded
  -> 사용자가 다시뽑기 클릭
  -> showFullScreenAd
  -> userEarnedReward 수신
  -> reroll API 호출
  -> 두구두구
  -> 새 메뉴 공개
  -> 다음 광고 preload
```

`dismissed` 또는 광고 클릭만으로는 재뽑기를 지급하지 않고 `userEarnedReward`가 발생한 경우에만 허용합니다.

로컬 Vite 개발에서는 광고 SDK를 건너뛰어 기존처럼 무료로 재뽑기 UX를 테스트할 수 있습니다.

QR/실기기 테스트용 공식 광고 ID:

```env
VITE_REWARDED_AD_UNIT_ID=ait-ad-test-rewarded-id
```

실제 출시 전에는 Apps-in-Toss 콘솔에서 발급한 라이브 `adGroupId`로 반드시 교체합니다.

## 6. Apps-in-Toss SDK 설정

현재 SDK:

```text
@apps-in-toss/web-framework 3.0.4
@apps-in-toss/devtools 3.0.4
```

SDK 3.0.4는 `apps-in-toss.config.ts`를 사용합니다.

```text
appName: jeomechu
primaryColor: #FF6B4A
webBundleDir: dist
```

Node.js 24 이상을 사용합니다.

앱인토스 콘솔에서 생성한 앱의 `appName`도 반드시 `jeomechu`와 같아야 합니다. 다르면 코드의 `appName`을 콘솔 값으로 변경합니다.

브랜드 표시 이름과 로고는 앱인토스 콘솔 등록값을 기준으로 최종 확인합니다.

## 7. .ait 빌드

로컬:

```powershell
cd Jeomechu\frontend
npm install
npm run typecheck
npm run build
```

성공 시:

```text
jeomechu.ait
```

이 생성됩니다.

GitHub Actions의 `Jeomechu Frontend CI`도 다음을 자동 검증합니다.

```text
npm install
 -> TypeScript typecheck
 -> vite production build
 -> ait build
 -> jeomechu.ait 생성
```

`main`에 push하면 QR 테스트용 환경값을 넣은 `jeomechu-ait-qr-test` artifact도 14일간 생성됩니다.

QR 테스트 artifact는 아래 값을 사용합니다.

```env
VITE_API_BASE_URL=https://jeomechu-api-production.up.railway.app
VITE_REWARDED_AD_UNIT_ID=ait-ad-test-rewarded-id
```

## 8. 앱인토스 콘솔 업로드 / QR 테스트

1. GitHub Actions에서 `jeomechu-ait-qr-test` artifact를 받거나 로컬에서 `npm run build`로 `jeomechu.ait`를 생성합니다.
2. 앱인토스 콘솔의 출시하기 메뉴에 `.ait` 파일을 업로드합니다.
3. 생성된 QR을 실제 토스 앱으로 실행합니다.
4. 첫 메뉴 추천, 좋아요, 랭킹, 다시뽑기 광고를 확인합니다.
5. 광고를 중간에 닫았을 때 새 메뉴가 지급되지 않는지 확인합니다.
6. 광고를 끝까지 봤을 때만 새 메뉴가 지급되는지 확인합니다.

## 9. 실제 출시 직전

- Apps-in-Toss 콘솔에서 리워드 광고 그룹 생성
- 라이브 `adGroupId` 발급
- `VITE_REWARDED_AD_UNIT_ID`를 라이브 ID로 교체해 최종 `.ait` 빌드
- 콘솔의 appName이 `jeomechu`인지 확인
- 브랜드명 `김대리의 저메추`와 앱 아이콘 최종 등록
- 실제 Apps-in-Toss Origin 확인 후 CORS 제한 검토
- QR 실기기 테스트 완료
- 검토 요청

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
