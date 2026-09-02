def difficulty_score(pattern_score: float, return_d20: float) -> float:
    clarity=max(0.0,min(100.0,pattern_score)); outcome=min(100.0,abs(return_d20)*5)
    return round(100 - (clarity*.7 + outcome*.3),2)

def level(score:float)->str:
    return 'BEGINNER' if score<=40 else ('INTERMEDIATE' if score<=70 else 'EXPERT')
