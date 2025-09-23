from enum import Enum


class Interval(Enum):
    """
    Interval of bar data.
    """
    MINUTE1 = "1m"
    MINUTE5 = "5m"
    MINUTE15 = "15m"
    MINUTE30 = "30m"
    MINUTE60 = "60m"
    MINUTE120 = "120m"
    DAILY = "d"
    WEEKLY = "w"
    TICK = "tick"


class IntervalUnit(Enum):
    """
    Interval unit of bar data.
    """
    MINUTE = "m"
    DAILY = "d"
    TICK = "tick"
