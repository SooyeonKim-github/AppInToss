# NoelPin — 퇴근길 노을핀

> 오늘도 고생했어요. 집에 가기 전, 노을 보고 갈까요?

서울 직장인의 퇴근 동선에서 **정확히 어디에 서서, 어느 방향을 보면 노을이 보이는지** 알려주는 Apps-in-Toss용 MVP입니다.

## 지금 구현된 UX

- 첫 화면: `퇴근길 노을핀` 카피 + 오늘 일몰 시간 + `지금 내 퇴근길 노을 보기`
- `지금 내 주변엔`: 대표 노을자리 카드와 도보 시간
- 스크롤 힌트: 첫 화면 하단에 지도가 일부 보이도록 구성
- 지도 탐색: 노을핀 / 지하철 창밖노을 핀 선택
- 스팟 상세: `여기 서세요`, 바라보는 방향, 도착 팁, 태그
- 지하철 창밖노을: 노선/구간/창문 방향을 위한 별도 데이터 구조
- 저장: localStorage 기반 MVP 저장 기능
- 위치: Apps-in-Toss 위치 API를 사용해 현재 위치 기준 탐색
- 지도: Kakao Maps JS SDK 키가 있으면 실제 지도, 없으면 UI 확인용 fallback 지도

## 실행

```powershell
cd AppInToss\NoelPin\frontend
Copy-Item .env.example .env
npm install
npm run dev
```

또는 `NoelPin\start_frontend.bat` 실행.

## Kakao Maps

`frontend/.env`에 JavaScript 키를 넣습니다.

```env
VITE_KAKAO_MAP_APP_KEY=YOUR_JAVASCRIPT_KEY
```

키가 비어 있으면 샘플 지도 UI가 자동으로 표시됩니다.

## Apps-in-Toss

기존 `RooftopMood`와 동일하게 `@apps-in-toss/web-framework` 3.0.4 구조를 사용합니다.

```powershell
npm run build
npm run deploy
```

`apps-in-toss.config.ts`의 `appName`은 현재 `noel-pin`입니다. 실제 콘솔에 등록된 앱 이름이 다르면 배포 전에 맞춰 주세요.

## 데이터 원칙

현재 `src/spots.ts`의 좌표/설명은 **UI 개발용 후보(seed)** 입니다. `verification: "candidate"`로 표시했으며 실제 서비스 공개 전 현장 검증이 필요합니다.

검증할 항목:

1. 정확한 서 있는 좌표
2. 서쪽 시야 개방 여부
3. 실제 일몰 방향과 구도
4. 보행 안전성/출입 가능 여부
5. 추천 도착 시간
6. 지하철 노선별 진행 방향과 창문 방향

## SunsetSpotFinder V1~V5

`NoelPin/SunsetSpotFinder`에 후보 발굴 파이프라인이 구현되어 있습니다.

- V1: 보도육교/교량/공원/둘레길/한강변 후보 좌표 생성 + 일몰 방위각
- V2: 역/업무지구/수변/고도/건물·나무 가림 분석
- V3: 퇴근 접근성 + 동서방향 도로 기반 건물사이노을 후보
- V4: 지상 지하철 구간 + 진행방향 기반 왼쪽/오른쪽 창문 후보
- V5: TOP 후보, HTML 지도, Excel 리포트, 검증 큐, FIELD_VERIFIED publish gate

```powershell
cd AppInToss\NoelPin\SunsetSpotFinder
.\start_finder.bat
```

원본 공공데이터가 없으면 demo 데이터로 전체 V5 흐름을 확인할 수 있고, 실제 데이터만 사용할 때는 `python run_finder.py --stage v5 --no-demo`를 실행합니다.
