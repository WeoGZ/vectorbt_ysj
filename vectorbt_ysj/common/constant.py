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


class VbtFreq(Enum):
    """
    vbt.Portfolio.from_signals()的freq参数枚举。因为vbt的年化数量计算是“365*(一天所含freq的数量)”，例如freq=60m，一天含有24个60分钟，
    年化的数量就是365*24=8760，但实际上期货一天只含有6个60分钟（有夜盘）。因此这里做一下转换
    """
    MINUTE1 = "4.17m"   # 345根K线
    MINUTE5 = "20.87m"  # 69
    MINUTE15 = "1.04h"  # 23
    MINUTE30 = "2h"     # 12
    MINUTE60 = "4h"     # 6
    MINUTE120 = "8h"    # 3
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


class PeriodType(Enum):
    Year = 0
    HalfYear = 1
    Quarter = 2
    Month = 3
    Week = 4


LAST_BAR_START_TIME_MAP: dict[Interval, tuple] = {
    Interval.MINUTE5: (14, 55),
    Interval.MINUTE15: (14, 45),
    Interval.MINUTE30: (14, 45),
    Interval.MINUTE60: (14, 15),
    Interval.MINUTE120: (11, 15),
}
"""各周期对应的交易日最后一根K线的起始时间"""
