from .box_breakout import BoxBreakoutPattern
from .pullback_rebound import PullbackReboundPattern
from .volume_breakout import VolumeBreakoutPattern
from .previous_high_breakout import PreviousHighBreakoutPattern
from .ma_support import MaSupportPattern
from .double_bottom import DoubleBottomPattern
from .bottom_base import BottomBasePattern
from .trend_continuation import TrendContinuationPattern

def build_registry():
    items=[BoxBreakoutPattern(),PullbackReboundPattern(),VolumeBreakoutPattern(),PreviousHighBreakoutPattern(),MaSupportPattern(),DoubleBottomPattern(),BottomBasePattern(),TrendContinuationPattern()]
    return {p.pattern_id:p for p in items}
