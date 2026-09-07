# Legacy pattern threshold is kept because the old pattern modules remain available for research.
MIN_PATTERN_SCORE = 65.0

# 130 bars are required so MA120 and Bollinger 60-day width percentile are stable.
MIN_HISTORY_BARS = 130
MAX_QUESTIONS_PER_TICKER = 30
CHART_LOOKBACK_BARS = 45
FUTURE_DISPLAY_BARS = 20

MIN_FEATURE_STRENGTH = 0.42
MIN_ACTIVE_FEATURES = 3
PRIMARY_FEATURE_COUNT = 4
MIN_CHART_INTEREST_SCORE = 52.0
MAX_DIFFICULTY_SCORE = 45.0

# Avoid near-duplicate questions from the same ticker with almost identical feature states.
MIN_QUESTION_GAP_BARS = 8
