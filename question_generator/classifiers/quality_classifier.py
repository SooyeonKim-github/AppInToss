def is_quality_question(pattern_score: float, returns: dict[int,float], min_score:float=65.0)->bool:
    if pattern_score < min_score: return False
    if 20 not in returns: return False
    return all(abs(v) < 80 for v in returns.values())
