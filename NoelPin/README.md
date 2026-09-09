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
- 위치: 버튼 클릭 시 브라우저 Geolocation을 요청해 `현재 위치 기준` 상태를 표시
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

## 다음 개발 순서

1. 공공데이터 기반 `SunsetSpotFinder` 후보 생성
2. 관리자 Spot 검증 화면
3. VERIFIED Spot API/DB 분리
4. 실제 일몰 시각 API 연결
5. 현재 위치 기반 거리/도보 경로
6. 지하철 지상구간/한강 통과 구간 데이터 구축
