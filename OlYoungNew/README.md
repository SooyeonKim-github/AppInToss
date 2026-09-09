# 올영뉴 (OlYoungNew)

앱인토스 출시를 전제로 만든 **신상 뷰티 발견 + 반응지수 + 조합 분석** 미니앱입니다.

## V0.1 UX 원칙

- 검색창 없이 클릭/드래그만으로 탐색
- 홈은 Apple Watch 앱 그리드처럼 신상 제품을 원형 버블로 노출
- 버블 크기는 `신상 반응지수`에 비례
- 제품을 선택하면 하단 카드에서 반응지수, 상승폭, 출시 경과일을 바로 확인
- `+ 조합해보기`로 최대 4개까지 담고 조합 화면으로 이동
- 상세 데이터/성분 엔진은 이후 백엔드 모듈로 확장

## 현재 구현 범위

### Frontend

- Apps in Toss Web Framework `3.0.4`
- React 19 + TypeScript + Vite
- Apple Watch 스타일 draggable bubble cluster
- 중앙 근접 제품 확대 효과
- 반응지수 기반 버블 크기
- HOT glow / NEW badge / score badge
- 홈 / 신상 / 조합 3탭
- Mock 데이터만으로 프론트 단독 실행 가능

### Backend

- FastAPI skeleton
- `GET /health`
- `GET /api/v1/trends/home`
- `POST /api/v1/mix/analyze`
- 현재는 Mock 응답이며 다음 단계에서 수집/DB/점수 엔진 연결

## 실행

Windows에서는 프로젝트 폴더에서 다음 파일을 실행합니다.

```bat
start_all.bat
```

또는 각각 실행:

```bat
start_backend.bat
start_frontend.bat
```

프론트엔드 기본 포트: `5174`
백엔드 기본 포트: `8010`

## 프론트만 실행

`frontend/.env`가 없거나 `VITE_API_BASE_URL`이 비어 있으면 내장 Mock 데이터로 실행됩니다.

```powershell
cd frontend
npm install
npm run dev
```

## 앱인토스 빌드

```powershell
cd frontend
npm install
npm run build
```

`apps-in-toss.config.ts`의 현재 appName은 `olyoung-new`입니다. 실제 앱인토스 콘솔에서 발급/등록한 appName이 다르면 출시 전에 해당 값과 정확히 맞춰야 합니다.

## 다음 구현 순서

1. 제품 상세 화면 + 반응지수 7개 지표 UI
2. 제품 snapshot DB
3. 리뷰 증가 속도/평점/할인/기획전/신상도 기반 Reaction Score V1
4. 성분 DB + product_ingredients
5. 조합 중복/주의/커버리지 분석 엔진
6. 실제 신상 수집 파이프라인
7. SNS 화제성 지표 연결
8. 앱인토스 QA / 권한 / 배포 설정 hardening

> 현재 제품명/브랜드/수치는 UI 테스트용 Mock 데이터입니다. 실제 서비스 데이터로 오해되지 않도록 운영 배포 전 실제 데이터 파이프라인으로 교체해야 합니다.
