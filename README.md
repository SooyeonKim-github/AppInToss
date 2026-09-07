# AppInToss - 오를까? 입문편

주식 차트 초보자가 **대표 패턴을 짧게 배우고 → 실제 과거 차트를 보고 상승/하락을 예측하고 → 이후 D+20까지의 결과를 확인**하는 게임형 Apps in Toss 미니앱 MVP입니다.

> 이 프로젝트는 투자 추천/매수 신호 제공이 아니라 과거 차트를 활용한 게임형 학습을 목적으로 설계했습니다.

## 핵심 기능

- 오늘의 차트 5문제
- 문제 전 패턴 미니 튜토리얼
- `오른다 / 내린다` 이진 예측
- 정답 공개 + D+1 / D+5 / D+10 / D+20 수익률
- 사용자가 `오른다`를 선택한 차트만 가상매수 기록
- 전체 정답률 / 상승 예측 적중률 / D+20 평균 가상수익률
- 패턴별 정답률 및 D+20 평균 수익률
- 패턴 탐지 로직을 `question_generator/patterns/`로 독립
- 패턴 ON/OFF를 `question_generator/config/beginner_patterns.py`에서 관리

## 기본 활성 패턴

1. `BOX_BREAKOUT` - 박스권 돌파
2. `PULLBACK_REBOUND` - 눌림목 후 재상승
3. `VOLUME_BREAKOUT` - 거래량 동반 돌파
4. `DOUBLE_BOTTOM` - 쌍바닥
5. `TREND_CONTINUATION` - 상승 추세 유지

엔진에는 `PREVIOUS_HIGH_BREAKOUT`, `MA_SUPPORT`, `BOTTOM_BASE`도 포함되어 있으며 설정에서 쉽게 활성화할 수 있습니다.

## 구조

```text
AppInToss/
├─ frontend/                 # Apps in Toss WebView용 React + TypeScript UI
├─ backend/                  # FastAPI + SQLite API
├─ question_generator/       # 문제은행 생성기
│  ├─ patterns/              # 패턴 탐지 로직 (독립)
│  ├─ classifiers/           # 난이도/품질/정답 분류
│  ├─ services/              # OHLCV, 미래수익률, 차트 윈도우
│  ├─ adapters/              # ChartExpertAnalyzer/MarketData 연동
│  └─ config/                # 활성 패턴/문제/수익률 설정
├─ data/
│  ├─ ohlcv/                 # 종목별 OHLCV CSV (생성 데이터, gitignore)
│  ├─ universe/              # 거래대금 Universe/동기화 보고서 (gitignore)
│  └─ question_bank.csv      # 앱이 읽는 문제은행
└─ scripts/                  # 데이터 동기화/문제 생성/검증
```

## 1. 백엔드 실행

```bash
cd backend
python -m venv .venv
# Windows
.venv\\Scripts\\activate
# macOS/Linux
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Swagger: `http://localhost:8000/docs`

## 2. 프론트 실행

공식 Apps in Toss `create-ait-app`의 React + TypeScript/TDS 계열 구조를 참고한 Vite 프로젝트입니다.

```bash
cd frontend
npm install
npm run dev
```

`.env` 예시:

```env
VITE_API_BASE_URL=http://localhost:8000
```

## 3. ChartExpertAnalyzer MarketData 동기화

AppInToss는 `ChartExpertAnalyzer/MarketData` 코드를 복사하지 않고 어댑터로 재사용합니다.

기본 흐름:

```text
ChartExpertAnalyzer/MarketData
→ 기준일 KOSPI/KOSDAQ 최근 20거래일 평균 거래대금 TOP 300
→ 종목별 OHLCV 동기화
→ AppInToss/data/ohlcv/*.csv
→ 문제 생성기
→ data/question_bank.csv
```

두 저장소를 아래처럼 형제 폴더로 두면 기본 경로를 자동 인식합니다.

```text
C:\Users\<USER>\
├─ AppInToss\
└─ ChartExpertAnalyzer\
```

Windows에서는 프로젝트 루트에서 다음 BAT 파일을 실행하면 됩니다.

```bat
sync_market_data.bat
```

기본 설정은 다음과 같습니다.

- Markets: KOSPI + KOSDAQ
- Universe: 기준일 최근 20거래일 평균 거래대금 TOP 300
- OHLCV 기간: 2023-01-01 ~ 2026-08-31
- ETF 제외
- MarketData provider/cache/fallback 로직 재사용

직접 실행하려면:

```powershell
python -m pip install -r question_generator\requirements.txt

python scripts\sync_market_data.py `
  --chart-expert-root C:\Users\ksy10\ChartExpertAnalyzer `
  --markets KOSPI KOSDAQ `
  --top-n 300 `
  --lookback 20 `
  --start 20230101 `
  --end 20260831
```

출력:

```text
data/universe/korea_liquidity_universe.csv
data/universe/market_data_sync_report.csv
data/ohlcv/005930.csv
data/ohlcv/000660.csv
...
```

이미 요청 범위를 모두 포함하는 종목 CSV가 있으면 기본적으로 다시 받지 않습니다. 강제로 새로 받으려면 `--overwrite`를 추가합니다.

## 4. 문제은행 생성

OHLCV 동기화 후:

```powershell
python scripts\generate_questions.py
python scripts\validate_question_bank.py
```

생성 결과: `data/question_bank.csv`

OHLCV CSV 형식:

```text
date,open,high,low,close,volume,trading_value,ticker,name,market
2026-01-02,70000,71000,69000,70500,12345678,870000000000,005930,삼성전자,KOSPI
```

## 패턴 수정 방법

예: 박스권 돌파 조건 변경

```text
question_generator/patterns/box_breakout.py
```

입문편에서 사용할 패턴 변경

```text
question_generator/config/beginner_patterns.py
```

패턴 파일을 삭제하지 않고 `ENABLED_BEGINNER_PATTERNS` 목록에서 켜고 끄는 것을 권장합니다.

## 정답 기준

기본값은 D+20 종가 수익률 기준입니다.

- `>= +5%` → `UP`
- `<= -5%` → `DOWN`
- `-5% ~ +5%` → 문제은행 제외

설정: `question_generator/config/return_config.py`

패턴 감지는 문제 후보를 만들기 위한 조건일 뿐 정답을 결정하지 않습니다. 동일한 패턴에서도 D+20 실제 결과에 따라 `UP`과 `DOWN` 문제가 모두 생성될 수 있습니다.

## ChartExpertAnalyzer 연동 원칙

- `question_generator/adapters/chart_expert_market_data_adapter.py`: `ChartExpertAnalyzer/MarketData`의 Universe/OHLCV 기능만 재사용
- `question_generator/adapters/chart_expert_adapter.py`: Analyzer 결과 CSV를 추가 후보 메타데이터로 사용할 때만 사용
- Analyzer의 `CONFIRMED/WATCH/REJECT` 또는 점수가 퀴즈 정답을 직접 결정하지 않음
- 실제 정답은 미래 D+20 수익률로 결정

## Apps in Toss 배포 메모

Apps in Toss는 WebView/React Native SDK를 제공하며, 공식 `create-ait-app`으로 React TypeScript 프로젝트를 시작할 수 있습니다. 실제 앱명/콘솔 설정/샌드박스 연결은 Apps in Toss 콘솔의 등록값에 맞게 설정하세요.
