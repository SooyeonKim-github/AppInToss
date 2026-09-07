# Indicators-based Feature Question Generator

`오를까? 입문편`의 문제 생성기는 패턴 이름을 정답 힌트처럼 사용하지 않고, 기준일 당시 차트를 15개의 읽기 요소로 설명합니다.

## 원칙

1. 기준일 이후 데이터는 Feature 계산에 절대 사용하지 않습니다.
2. Feature 계산과 문제 적합성 판정이 끝난 뒤에만 D+20 수익률을 읽습니다.
3. D+20 >= +5%는 UP, <= -5%는 DOWN이며 그 사이는 제외합니다.
4. 상승 차트와 하락 차트 모두 동일한 15개 Feature 체계를 사용합니다.
5. `Indicators` 저장소 전체를 런타임 의존성으로 import하지 않고, 필요한 계산식과 해석 기준을 AppInToss 내부에 독립 구현합니다.

## Indicators 저장소에서 참고한 핵심

### MovingAverageAnalysis
- MA5 / MA20 / MA60 / MA120
- MA slope
- Disparity / Close-to-MA
- Bullish / Bearish alignment
- MA support/rejection 개념

### DMIAnalyzer
- Wilder smoothing
- +DI / -DI
- ADX
- ATR%
- 상승/하락 방향과 추세 강도를 분리해서 해석

### BollingerBandAnalyzer
- Bollinger(20, 2)
- BB Width %
- 60일 밴드폭 percentile
- 3일 밴드폭 확장률
- %B
- 중심선 지지/저항 관점

### OscillatorAnalysis
- Wilder RSI(14)
- RSI 50 중심축
- 30/70 과매도/과매수 구간
- 추세 방향과 함께 모멘텀을 해석

### CandleAnalysis / 공통 가격 해석
- 봉 내 종가 위치
- 위/아래 꼬리 비율
- 가격 움직임과 거래량을 함께 해석

## 15개 사용자 Feature

| # | Feature | 주요 내부 근거 |
|---|---|---|
| 1 | 단기 추세 | Return 5/20D, +DI/-DI |
| 2 | 중기 추세 | Return 60D, MA60 slope, ADX |
| 3 | 고점 구조 | 최근/이전 20일 high 비교 |
| 4 | 저점 구조 | 최근/이전 20일 low 비교 |
| 5 | 이동평균선 배열 | MA5/20/60/120 정배열/역배열 |
| 6 | 이동평균선 기울기 | MA20/60 slope |
| 7 | 가격과 이동평균선 관계 | Close vs MA20/60 |
| 8 | 이동평균선 이격도 | Close-to-MA20, MA20 slope |
| 9 | 최근 고점·저점 위치 | 60D range position, BB %B |
| 10 | 거래량 수준 | Volume / Volume MA20, 5D price direction |
| 11 | 상승·하락일 거래량 | Up-day vs Down-day average volume |
| 12 | 변동성 | ATR%, BB Width percentile/change |
| 13 | 모멘텀 | Wilder RSI, RSI slope, +DI/-DI, ADX |
| 14 | 지지·저항 반응 | MA20 touch, recent range break |
| 15 | 조정·반등의 힘 | prior move, pullback/recovery, MA20 |

각 Feature는 `BULLISH`, `BEARISH`, `NEUTRAL` 중 하나와 0~1 `strength`를 반환합니다.

## 문제 생성 순서

```text
OHLCV (기준일까지)
  -> indicator snapshot
  -> 15 FeatureSignal
  -> active feature filter
  -> Chart Interest Score
  -> Difficulty Score
  -> primary 3~4 features
  -> (여기까지 미래 데이터 없음)
  -> D+20 future return
  -> UP / DOWN label
  -> nearby duplicate removal
  -> per-ticker UP/DOWN balanced sampling
  -> question_bank.csv
```

## 설명 선택

한 문제에서 이평선 Feature만 여러 개 노출되지 않도록 네 가지 교육 관점에서 다양하게 선택합니다.

- Trend / Price Structure
- Moving Average
- Volume / Momentum
- Price Position / Volatility / Support / Pullback

가능하면 주 방향 Feature 2~3개와 반대/주의 Feature 0~1개를 함께 보여줍니다.

## 실행

```powershell
python scripts\test_chart_features.py
python scripts\generate_questions.py
python scripts\validate_question_bank.py
```

새 문제은행의 `analyzer` 값은 `INDICATORS_FEATURE_V2`입니다.
