from ..config.return_config import UP_THRESHOLD_PCT, DOWN_THRESHOLD_PCT
def classify_outcome(return_d20: float) -> str | None:
    if return_d20 >= UP_THRESHOLD_PCT: return 'UP'
    if return_d20 <= DOWN_THRESHOLD_PCT: return 'DOWN'
    return None
