from pathlib import Path
from .services.market_data_service import load_ohlcv
from .generators.question_generator import generate_for_dataframe,export_csv

def run(input_dir:Path,output:Path):
    rows=[]
    for path in sorted(input_dir.glob('*.csv')):
        try: rows.extend(generate_for_dataframe(load_ohlcv(path)))
        except Exception as e: print(f'[WARN] {path.name}: {e}')
    export_csv(rows,output); return rows
