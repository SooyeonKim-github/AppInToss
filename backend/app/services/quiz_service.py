from __future__ import annotations

import random

from ..repositories.prediction_repository import save_prediction
from ..repositories.question_repository import get_question, load_questions


def today(limit: int = 5) -> list[dict]:
    rows = load_questions()
    random.shuffle(rows)
    return [public_question(q) for q in rows[: max(1, min(limit, 20))]]


def public_question(q: dict) -> dict:
    return {
        "questionId": q["question_id"],
        "patternType": q.get("pattern_type", "FEATURE_READING"),
        "patternName": q.get("pattern_name", "차트의 흐름 읽기"),
        "patternTip": q.get(
            "pattern_tip",
            "추세, 이동평균선, 거래량과 변동성을 함께 살펴보세요.",
        ),
        "difficulty": q.get("difficulty", "BEGINNER"),
        "features": q.get("primary_features_json", []),
        "candles": q["candles_json"],
    }


def answer(question_id: str, selected: str, user_id: str) -> dict:
    q = get_question(question_id)
    if not q:
        raise KeyError(question_id)
    save_prediction(user_id, q, selected)
    return {
        "correct": q["answer"] == selected,
        "actualAnswer": q["answer"],
        "selectedAnswer": selected,
        "returns": {
            "d1": q["return_d1"],
            "d5": q["return_d5"],
            "d10": q["return_d10"],
            "d20": q["return_d20"],
        },
        "explanation": q["explanation"],
        "futureCandles": q["future_candles_json"],
    }
