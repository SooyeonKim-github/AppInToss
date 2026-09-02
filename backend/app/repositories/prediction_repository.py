from __future__ import annotations
from ..database.db import connect

def save_prediction(user_id: str, q: dict, selected: str) -> None:
    actual=q['answer']; correct=int(actual == selected); virtual_buy=int(selected == 'UP')
    with connect() as con:
        con.execute("""
        INSERT INTO predictions(user_id,question_id,prediction,is_correct,virtual_buy,return_d1,return_d5,return_d10,return_d20,pattern_type,pattern_name)
        VALUES(?,?,?,?,?,?,?,?,?,?,?)
        ON CONFLICT(user_id,question_id) DO UPDATE SET
          prediction=excluded.prediction,is_correct=excluded.is_correct,virtual_buy=excluded.virtual_buy,
          return_d1=excluded.return_d1,return_d5=excluded.return_d5,return_d10=excluded.return_d10,return_d20=excluded.return_d20,
          pattern_type=excluded.pattern_type,pattern_name=excluded.pattern_name,predicted_at=CURRENT_TIMESTAMP
        """, (user_id,q['question_id'],selected,correct,virtual_buy,q['return_d1'],q['return_d5'],q['return_d10'],q['return_d20'],q['pattern_type'],q['pattern_name']))

def list_predictions(user_id: str) -> list[dict]:
    with connect() as con:
        return [dict(r) for r in con.execute('SELECT * FROM predictions WHERE user_id=? ORDER BY id DESC',(user_id,)).fetchall()]
