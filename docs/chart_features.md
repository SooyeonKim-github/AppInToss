# 오를까? 차트 읽기 Feature V1

문제 생성기는 특정 패턴 이름을 정답 근거로 사용하지 않는다. 기준일 이전 OHLCV만으로 아래 15개 차트 읽기 요소를 계산하고, 각 요소를 `BULLISH`, `BEARISH`, `NEUTRAL` 중 하나로 해석한다.

1. 단기 추세
2. 중기 추세
3. 고점 구조
4. 저점 구조
5. 이동평균선 배열
6. 이동평균선 기울기
7. 가격과 이동평균선 관계
8. 이동평균선 이격도
9. 최근 고점·저점 내 가격 위치
10. 거래량 수준
11. 상승일·하락일 거래량 비교
12. 변동성 확대·축소
13. 모멘텀
14. 지지·저항 반응
15. 조정·반등의 힘

## 하락 차트 해석 예

- 최근 가격이 계속 낮아지고 있어요.
- 반등하더라도 고점이 이전보다 낮아지고 있어요.
- 최근 저점이 이전보다 더 낮아지고 있어요.
- 단기·중기 이동평균선이 하락 방향으로 정렬돼 있어요.
- 20일선과 60일선이 함께 아래를 향하고 있어요.
- 가격이 20일선과 60일선 아래에서 움직이고 있어요.
- 내리는 날의 거래량이 오르는 날보다 더 강해요.
- 하락하면서 가격 변동폭도 함께 커지고 있어요.
- 최근 버티던 가격대를 아래로 이탈했어요.
- 최근 반등이 나왔지만 이전 하락폭을 충분히 회복하지 못하고 있어요.

## 문제 생성 원칙

- Feature는 정답(D+20)을 보기 전에 기준일 당시 데이터만으로 계산한다.
- D+20은 문제의 `UP/DOWN` 라벨과 애매한 결과 제외에만 사용한다.
- 15개 Feature 중 강도와 다양성이 높은 3~4개를 사용자에게 보여준다.
- 한 방향 Feature만 강제로 고르지 않는다. 상승/하락 특징이 동시에 존재하면 함께 보여준다.
- 같은 종목에서 생성된 후보는 Chart Interest Score가 높은 문제를 우선 선택한다.
- 종목별 문제 수는 UP/DOWN이 가능한 한 균형을 이루도록 선택한다.

## 관련 파일

- `question_generator/features/chart_feature_engine.py`
- `question_generator/interpretation/chart_explainer.py`
- `question_generator/selection/chart_interest_score.py`
- `question_generator/generators/question_generator.py`
- `scripts/test_chart_features.py`
