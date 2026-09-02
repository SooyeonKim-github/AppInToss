from __future__ import annotations
import json
from pathlib import Path
import pandas as pd
from ..patterns.registry import build_registry
from ..config.beginner_patterns import ENABLED_BEGINNER_PATTERNS
from ..config.question_config import MIN_PATTERN_SCORE,MAX_DIFFICULTY_SCORE,MIN_HISTORY_BARS,MAX_QUESTIONS_PER_TICKER,CHART_LOOKBACK_BARS,FUTURE_DISPLAY_BARS
from ..classifiers.outcome_classifier import classify_outcome
from ..classifiers.quality_classifier import is_quality_question
from ..classifiers.difficulty_classifier import difficulty_score, level
from ..services.future_return_service import future_returns
from ..services.chart_window_service import history_window, future_window

REGISTRY=build_registry()

def generate_for_dataframe(df:pd.DataFrame)->list[dict]:
    out=[]; ticker=str(df.get('ticker',pd.Series(['UNKNOWN'])).iloc[0]); name=str(df.get('name',pd.Series([ticker])).iloc[0]); market=str(df.get('market',pd.Series(['KR'])).iloc[0])
    for i in range(MIN_HISTORY_BARS,len(df)-20):
        hist=df.iloc[:i+1]
        returns=future_returns(df,i)
        if returns is None: continue
        answer=classify_outcome(returns[20])
        if answer is None: continue
        for pid in ENABLED_BEGINNER_PATTERNS:
            p=REGISTRY[pid]
            if len(hist)<p.min_bars: continue
            pr=p.detect(hist)
            if not pr.matched or not is_quality_question(pr.score,returns,MIN_PATTERN_SCORE): continue
            diff=difficulty_score(pr.score,returns[20])
            if diff>MAX_DIFFICULTY_SCORE: continue
            qid=f"{ticker}-{df.date.iloc[i].strftime('%Y%m%d')}-{pid}"
            out.append({
              'question_id':qid,'ticker':ticker,'name':name,'market':market,'base_date':df.date.iloc[i].strftime('%Y-%m-%d'),'base_price':round(float(df.close.iloc[i]),4),
              'pattern_type':pid,'pattern_name':p.pattern_name,'pattern_tip':p.pattern_tip,'pattern_score':round(pr.score,2),'difficulty':level(diff),'difficulty_score':diff,'answer':answer,
              'return_d1':returns[1],'return_d5':returns[5],'return_d10':returns[10],'return_d20':returns[20],
              'explanation':pr.explanation,'candles_json':json.dumps(history_window(df,i,CHART_LOOKBACK_BARS),ensure_ascii=False),
              'future_candles_json':json.dumps(future_window(df,i,FUTURE_DISPLAY_BARS),ensure_ascii=False),'analyzer':'','analyzer_score':'','timing_score':'','is_active':'true'
            })
        if len(out)>=MAX_QUESTIONS_PER_TICKER: break
    return out

def export_csv(rows:list[dict],path:Path):
    path.parent.mkdir(parents=True,exist_ok=True)
    pd.DataFrame(rows).to_csv(path,index=False,encoding='utf-8-sig')
