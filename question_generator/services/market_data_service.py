from pathlib import Path
import pandas as pd
REQUIRED={'date','open','high','low','close','volume'}
def load_ohlcv(path:Path)->pd.DataFrame:
    df=pd.read_csv(path,dtype={'ticker':str}); missing=REQUIRED-set(df.columns)
    if missing: raise ValueError(f'{path.name}: missing columns {sorted(missing)}')
    df['date']=pd.to_datetime(df['date']); df=df.sort_values('date').reset_index(drop=True)
    return df
