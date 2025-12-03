import json
import sys

from vectorbt_ysj.common.constant import Interval, VbtFreq


def generate_param_comb(start_value: float, end_value: float, step: float) -> list[float]:
    """生成参数范围"""
    if start_value > end_value or step <= 0:
        print(f'【{sys._getframe().f_code.co_name}】***请检查参数')
        return None

    combs: list = []
    _value = start_value
    while _value <= end_value:
        combs.append(_value)
        _value += step

    return combs


def find_interval(interval_str: str) -> Interval:
    """根据Interval的值找到相应的枚举对象"""
    for name, member in Interval.__members__.items():
        if member.value == interval_str:
            return member


def convert2dict(param_str: str) -> dict | None:
    """转换格式"""
    if param_str:
        param_str = param_str.replace("'", '"')
        param_dict = json.loads(param_str)
        return param_dict


def convert_to_vbt_freq(interval: Interval) -> VbtFreq:
    """转换为vbt的freq"""
    vbt_freq: VbtFreq = VbtFreq.DAILY
    if interval == Interval.MINUTE5:
        vbt_freq = VbtFreq.MINUTE5
    elif interval == Interval.MINUTE15:
        vbt_freq = VbtFreq.MINUTE15
    elif interval == Interval.MINUTE30:
        vbt_freq = VbtFreq.MINUTE30
    elif interval == Interval.MINUTE60:
        vbt_freq = VbtFreq.MINUTE60
    elif interval == Interval.MINUTE120:
        vbt_freq = VbtFreq.MINUTE120
    elif interval == Interval.DAILY:
        vbt_freq = VbtFreq.DAILY

    return vbt_freq


if __name__ == '__main__':
    comb = generate_param_comb(10, 20, 3)
    print(comb)
