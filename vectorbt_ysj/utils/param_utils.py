import json
import sys

from vectorbt_ysj.common.constant import Interval


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


if __name__ == '__main__':
    comb = generate_param_comb(10, 20, 3)
    print(comb)
