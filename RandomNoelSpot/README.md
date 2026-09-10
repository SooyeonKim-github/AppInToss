# RandomNoelSpot

카페·공원·육교·한강·산책로 등 서울의 다양한 노을 자리를 카드뉴스처럼 한 곳씩 추천하는 AppInToss 앱입니다.

## 재사용한 구조

- `NoelPin/frontend`: 위치 권한, 후보 장소 필드, 퇴근길/도보 정보, AppInToss 설정
- `NoelPin/SunsetSpotFinder`: Haversine 거리, 일몰 시각·방위각, 방향 적합도 기반 후보 점수
- `Jeomechu/frontend`: 한 번에 하나를 뽑는 흐름, 다시 뽑기 애니메이션, 저장 액션

## 실행

```bash
npm install
npm run dev
```

Windows에서는 `start_frontend.bat`을 실행해도 됩니다.

## 현재 범위

- 장소 유형 필터 및 랜덤 추천
- 오늘 일몰 시각/방위각 계산
- 일몰 방향·현재 위치를 반영한 기대도
- Apps-in-Toss 위치 권한 및 브라우저 fallback
- 좌표 기반 카카오맵 링크
- 현장 검증 전 후보 표시

실서비스 전 후보 장소의 정확한 좌표, 서향 시야, 접근 안전성, 사진 사용 권한을 검증해야 합니다.
