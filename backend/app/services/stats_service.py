from __future__ import annotations
from collections import defaultdict
from ..repositories.prediction_repository import list_predictions

def _avg(values): return sum(values)/len(values) if values else 0.0

def get_stats(user_id: str) -> dict:
    rows=list_predictions(user_id); total=len(rows); correct=sum(r['is_correct'] for r in rows)
    up=[r for r in rows if r['virtual_buy']]
    grouped=defaultdict(list)
    for r in rows: grouped[(r['pattern_type'],r['pattern_name'])].append(r)
    pattern=[]
    for (ptype,pname), items in grouped.items():
        buys=[r for r in items if r['virtual_buy']]
        pattern.append({'patternType':ptype,'patternName':pname,'attempts':len(items),'accuracy':100*_avg([r['is_correct'] for r in items]),'avgD20ReturnOnUp':_avg([r['return_d20'] for r in buys])})
    pattern.sort(key=lambda x:(-x['accuracy'],-x['attempts']))
    return {
      'totalAttempts': total, 'correctCount': correct, 'accuracy':100*correct/total if total else 0.0,
      'upPredictions': len(up), 'upAccuracy':100*_avg([r['is_correct'] for r in up]),
      'avgReturnD1':_avg([r['return_d1'] for r in up]), 'avgReturnD5':_avg([r['return_d5'] for r in up]),
      'avgReturnD10':_avg([r['return_d10'] for r in up]), 'avgReturnD20':_avg([r['return_d20'] for r in up]),
      'patternStats': pattern,
    }
