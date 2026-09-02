def _rows(df):
    return [{'date':r.date.strftime('%Y-%m-%d'),'open':float(r.open),'high':float(r.high),'low':float(r.low),'close':float(r.close),'volume':float(r.volume)} for r in df.itertuples()]
def history_window(df,index:int,lookback:int=45): return _rows(df.iloc[max(0,index-lookback+1):index+1])
def future_window(df,index:int,bars:int=20): return _rows(df.iloc[index:min(len(df),index+bars+1)])
