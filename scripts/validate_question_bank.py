from pathlib import Path
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]; path=ROOT/'data'/'question_bank.csv'
if not path.exists(): raise SystemExit('question_bank.csv not found')
df=pd.read_csv(path)
required={'question_id','pattern_type','difficulty','answer','return_d20','candles_json','future_candles_json'}
missing=required-set(df.columns)
if missing: raise SystemExit(f'missing columns: {sorted(missing)}')
assert df.question_id.is_unique,'question_id must be unique'
assert set(df.answer.dropna().unique())<= {'UP','DOWN'}
print('[OK] rows=',len(df)); print(df.groupby(['pattern_type','answer']).size())
