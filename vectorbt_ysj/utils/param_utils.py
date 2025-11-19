import sys


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


if __name__ == '__main__':
    comb = generate_param_comb(10, 20, 3)
    print(comb)
