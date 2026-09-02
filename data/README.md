# data
- `ohlcv/`: 문제 생성용 종목별 OHLCV CSV
- `question_bank.csv`: 백엔드가 읽는 문제은행
- `oreulkka.db`: 사용자 예측 SQLite DB (실행 시 자동 생성, gitignore 대상)

`question_bank.csv`에는 개발 확인용 DEMO 문제가 들어 있습니다. 실제 출시 전 `scripts/generate_questions.py`로 교체하세요.
