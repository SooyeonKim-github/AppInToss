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
│  ├─ adapters/              # ChartExpertAnalyzer 연동 어댑터
│  └─ config/                # 활성 패턴/문제/수익률 설정
├─ data/                     # 샘플 문제은행 및 OHLCV
└─ scripts/                  # 문제 생성/검증/수익률 업데이트
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

## 3. 문제은행 생성

OHLCV CSV 형식:

```text
date,open,high,low,close,volume,ticker,name,market
2026-01-02,70000,71000,69000,70500,12345678,005930,삼성전자,KOSPI
```

파일은 `data/ohlcv/<ticker>.csv` 형태로 둡니다.

```bash
pip install -r question_generator/requirements.txt
python scripts/generate_questions.py
python scripts/validate_question_bank.py
```

생성 결과: `data/question_bank.csv`

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

## ChartExpertAnalyzer 연동

`question_generator/adapters/chart_expert_adapter.py`는 ChartExpertAnalyzer의 확정 후보 CSV를 읽어 문제 후보 universe로 활용하기 위한 어댑터입니다. Analyzer 점수와 Timing 점수는 문제 메타데이터로 보존하되, 패턴 판정 자체는 이 저장소의 독립 패턴 엔진이 담당합니다.

## Apps in Toss 배포 메모

Apps in Toss는 WebView/React Native SDK를 제공하며, 공식 `create-ait-app`으로 React TypeScript 프로젝트를 시작할 수 있습니다. 실제 앱명/콘솔 설정/샌드박스 연결은 Apps in Toss 콘솔의 등록값에 맞게 설정하세요.
