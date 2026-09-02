from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
from question_generator.main import run
if __name__=='__main__':
    rows=run(ROOT/'data'/'ohlcv',ROOT/'data'/'question_bank.csv')
    print(f'[DONE] generated {len(rows)} questions -> data/question_bank.csv')
