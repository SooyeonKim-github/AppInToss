from __future__ import annotations
import random
from ..repositories.question_repository import load_questions, get_question
from ..repositories.prediction_repository import save_prediction

def today(limit: int=5) -> list[dict]:
    rows=load_questions()
    random.shuffle(rows)
    return [public_question(q) for q in rows[:max(1,min(limit,20))]]

def public_question(q: dict) -> dict:
    return {
      'questionId': q['question_id'], 'patternType': q['pattern_type'], 'patternName': q['pattern_name'],
      'patternTip': q['pattern_tip'], 'difficulty': q.get('difficulty','BEGINNER'), 'candles': q['candles_json']
    }

def answer(question_id: str, selected: str, user_id: str) -> dict:
    q=get_question(question_id)
    if not q: raise KeyError(question_id)
    save_prediction(user_id,q,selected)
    return {
      'correct': q['answer']==selected, 'actualAnswer': q['answer'], 'selectedAnswer': selected,
      'returns': {'d1':q['return_d1'],'d5':q['return_d5'],'d10':q['return_d10'],'d20':q['return_d20']},
      'explanation': q['explanation'], 'futureCandles': q['future_candles_json']
    }
