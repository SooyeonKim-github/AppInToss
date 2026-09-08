import os
import sys
from pathlib import Path

# API 테스트가 외부 네트워크에 의존하지 않도록 mock 날씨를 사용한다.
os.environ.setdefault("WEATHER_MODE", "mock")

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))
