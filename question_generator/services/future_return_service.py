def future_returns(df,index:int,horizons=(1,5,10,20)):
    base=float(df.close.iloc[index]); out={}
    for h in horizons:
        j=index+h
        if j>=len(df): return None
        out[h]=round((float(df.close.iloc[j])/base-1)*100,4)
    return out
