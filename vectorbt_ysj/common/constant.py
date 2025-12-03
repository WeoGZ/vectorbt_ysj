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
    MINUTE1 = "4.17m"  # 345根K线
    MINUTE5 = "20.87m"  # 69
    MINUTE15 = "1.04h"  # 23
    MINUTE30 = "2h"  # 12
    MINUTE60 = "4h"  # 6
    MINUTE120 = "8h"  # 3
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

KLINE_SIZE_PER_DAY_MAP: dict[Interval, int] = {
    Interval.MINUTE1: 345,
    Interval.MINUTE5: 69,
    Interval.MINUTE15: 23,
    Interval.MINUTE30: 12,
    Interval.MINUTE60: 6,
    Interval.MINUTE120: 3,
    Interval.DAILY: 1,
}
"""各周期对应的单个交易日所含数量，按有夜盘来算"""

FUTURE_SIZE_MAP: dict[str, float] = {
    "RBL9": 10,  # 螺纹钢
    "SAL9": 20,  # 纯碱
    "AOL9": 20,  # 氧化铝
    "SIL9": 5,  # 工业硅
    "LCL9": 1,  # 碳酸锂
    "TAL9": 5,  # PTA
    "CL9": 10,  # 玉米
    "JML9": 60,  # 焦煤
}
"""各期货品种的交易单位，XX吨/手"""

FUTURE_FEE_MAP: dict[str, float] = {
    "RBL9": 0.0002,  # 螺纹钢
    "SAL9": 0.0003,  # 纯碱
    "AOL9": 0.0002,  # 氧化铝
    "SIL9": 0.0001,  # 工业硅
    "LCL9": 0.0002,  # 碳酸锂
    "TAL9": 0.0002,  # PTA
    "CL9": 0.0001,  # 玉米
    "JML9": 0.0003,  # 焦煤
}
"""各期货品种的交易手续费，百分比。vbt框架不支持设置XX元/手，所以个别品种要换算成百分比"""

FUTURE_SLIPPAGE_MAP: dict[str, float] = {
    "RBL9": 0.0003,  # 螺纹钢
    "SAL9": 0.0006,  # 纯碱
    "AOL9": 0.0003,  # 氧化铝
    "SIL9": 0.0004,  # 工业硅
    "LCL9": 0.0002,  # 碳酸锂
    "TAL9": 0.0004,  # PTA
    "CL9": 0.0005,  # 玉米
    "JML9": 0.0003,  # 焦煤
}
"""各期货品种的滑点，百分比"""

INIT_CASH_MAP: dict[str, float] = {
    "RBL9": 90000,  # 螺纹钢
    "SAL9": 90000,  # 纯碱
    "AOL9": 120000,  # 氧化铝
    "SIL9": 120000,  # 工业硅
    "LCL9": 240000,  # 碳酸锂
    "TAL9": 90000,  # PTA
    "CL9": 30000,  # 玉米
    "JML9": 300000,  # 焦煤
}
"""各期货品种的起始资金"""
