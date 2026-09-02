from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
import pandas as pd

@dataclass(frozen=True)
class PatternResult:
    matched: bool
    score: float
    explanation: str

class BasePattern(ABC):
    pattern_id=''; pattern_name=''; pattern_tip=''
    min_bars=30
    @abstractmethod
    def detect(self, df: pd.DataFrame) -> PatternResult: ...
