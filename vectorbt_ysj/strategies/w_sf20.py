import os.path
from collections.abc import Iterable
from concurrent.futures import ProcessPoolExecutor
from functools import partial
from itertools import product
from multiprocessing import get_context
from time import perf_counter
from typing import Callable

import plotly.io as pio
from tqdm import tqdm

from vectorbt_ysj.common.future_list import FUTURE_LIST_ALL
from vectorbt_ysj.common.init_cash import INIT_CASH_ALL
from vectorbt_ysj.mytt import MyTT
from vectorbt_ysj.strategies.common_methods import execute
from vectorbt_ysj.utils.date_utils import *
from vectorbt_ysj.utils.db_operation_utils import *
from vectorbt_ysj.utils.kline_utils import *
from vectorbt_ysj.utils.param_utils import *
from vectorbt_ysj.utils.statistic_utils import *

# 设置渲染器为浏览器
pio.renderers.default = "browser"

# pd.set_option('Display.max_rows', None)  #展示全部行
pd.set_option('Display.max_columns', None)  # 展示全部列


def calculate_signals(close_price: pd.Series, high_price: pd.Series, low_price: pd.Series, open_price: pd.Series,
                      vols: pd.Series, interval: Interval, length: int, stpr: int):
    """计算交易信号"""
    if close_price is not None and not close_price.empty:
        dt_list = pd.Series(close_price.index)

        ma240 = MyTT.MA(close_price, length * 2)
        range1 = high_price - low_price
        upavg = MyTT.HHV(MyTT.REF(high_price + close_price - 2 * close_price, 1) + open_price, length)
        lowavg = MyTT.LLV(MyTT.REF(close_price + low_price - 2 * close_price, 1) + open_price, length)
        median_price = (high_price + low_price) / 2

        upband = (median_price > MyTT.REF(high_price, 1)) & (range1 > MyTT.REF(range1, 1))
        downband = (median_price < MyTT.REF(low_price, 1)) & (range1 > MyTT.REF(range1, 1))

        # 开仓信号
        bkcon = (close_price > ma240) & upband & (close_price > upavg)
        skcon = (close_price < ma240) & downband & (close_price < lowavg)

        # 平仓信号——止盈止损
        stbar = 40

        # 特别处理：未触发出场条件前，过滤掉重复开仓信号
        dk_l = MyTT.IF(bkcon, 1, MyTT.IF(skcon, 2, 0))  # 开仓信号
        handle_close_operation_2(dk_l, vols.values, low_price.values, high_price.values, stpr, stbar)

        # print(f'>>dk_l[-50:]={dk_l[-50:]}')
        # print(f'>>多开信号={dt_list[np.where(dk_l == 1)[0]]}')
        # print(f'>>多平信号={dt_list[np.where(dk_l == -1)[0]]}')
        # print(f'>>空开信号={dt_list[np.where(dk_l == 2)[0]]}')
        # print(f'>>空平信号={dt_list[np.where(dk_l == -2)[0]]}')

        # 输出
        long_open_signals = [True if s == 1 or s == 3 else False for s in dk_l]
        long_close_signals = [True if s == -1 or s == 4 else False for s in dk_l]
        short_open_signals = [True if s == 2 or s == 4 else False for s in dk_l]
        short_close_signals = [True if s == -2 or s == 3 else False for s in dk_l]
        return long_open_signals, long_close_signals, short_open_signals, short_close_signals


def handle_close_operation_2(dk_l: np.ndarray, vols: np.ndarray, low_price: np.ndarray, high_price: np.ndarray,
                             stpr: int, stbar: int):
    """用循环的方式处理出场信号，允许反手。直接修改dk_l，其中3表示BPK，4表示SPK。"""
    dk_sig = 0  # 多空信号。1表示多头，2表示空头
    open_index = -1  # 开仓位置
    vp = np.array([0] * len(dk_l))
    for i in range(len(dk_l)):
        if dk_sig != 0:  # 处理持仓状态下的K线
            if dk_l[i] != 0 and dk_l[i] != dk_sig:  # 反向，直接反手
                dk_l[i] = 4 if dk_sig == 1 else 3  # 3表示BPK，4表示SPK
                dk_sig = 2 if dk_sig == 1 else 1
                open_index = i
            else:  # dk_l是0或同向
                cn = i - open_index
                jp = np.max(low_price[open_index: i]) if dk_sig == 1 else np.min(high_price[open_index: i])
                vp[i] = jp * (1 - stpr / 1000) if dk_sig == 1 else jp * (1 + stpr / 1000)
                sum_vol = np.sum(vols[open_index + 1: i + 1])
                sum_amt = np.sum((vols * vp)[open_index + 1: i + 1])
                vwap = vp[i] if cn >= stbar else sum_amt / sum_vol
                close_con = low_price[i] <= vwap if dk_sig == 1 else high_price[i] >= vwap
                dk_l[i] = -dk_sig if close_con else 0  # 未触发出场信号前的重复开仓信号置为0
                dk_sig = 0 if close_con else dk_sig
                open_index = -1 if close_con else open_index
        else:
            dk_sig = dk_l[i]
            open_index = i if dk_sig != 0 else open_index


def wrap_execute(symbol: str, init_cash: float, start_date: datetime, end_date: datetime, interval: Interval,
                 klines_open: pd.DataFrame, klines_high: pd.DataFrame, klines_low: pd.DataFrame,
                 klines_close: pd.DataFrame, klines_vol: pd.DataFrame, params: tuple) -> tuple:
    calculate_func: Callable = partial(calculate_signals, length=params[0], stpr=params[1])
    params_dict = {'len': params[0], 'stpr': params[1]}
    return execute(calculate_func, symbol, init_cash, start_date, end_date, interval, klines_open, klines_high,
                   klines_low, klines_close, klines_vol, params_dict, 180)


def wrap_func(symbol: str, init_cash: float, start_date: datetime, end_date: datetime, interval: Interval,
              klines_open: pd.DataFrame, klines_high: pd.DataFrame, klines_low: pd.DataFrame,
              klines_close: pd.DataFrame, klines_vol: pd.DataFrame) -> Callable:
    """二次封装：预先配置好部分参数，剩下关键参数待穷举输入"""
    func: Callable = partial(wrap_execute, symbol, init_cash, start_date, end_date, interval, klines_open,
                             klines_high, klines_low, klines_close, klines_vol)
    return func


def do_exhaustion(symbol: str, init_cash: float, start_date: datetime, end_date: datetime, interval: Interval,
                  all_param_combs: list, save_remark: str, max_workers: int | None = None):
    """穷举单个品种"""
    # preload_days = (300 + 60) * (31 / 21)  # 换算成自然日数量
    preload_days = (90 / 5 + 1) * 30  # 参数n数值每5大概所需1个月数据计算，在换算成自然日。额外补一个月。参数n的最大值为90
    klines_open, klines_high, klines_low, klines_close, klines_vol = fetch_klines([symbol], start_date, end_date,
                                                                                  interval, preload_days)
    if klines_close.empty:
        print(
            f'###{symbol}没有K线数据, start={convert2_datetime_str(start_date)}, end={convert2_datetime_str(end_date)}, '
            f'interval={interval.value}')
        return
    if (klines_close.index[-1] - klines_close.index[0]).days < 180:
        print(f'###{symbol}的K线数据跨度不足180个自然日, start={convert2_datetime_str(start_date)}, '
              f'end={convert2_datetime_str(end_date)}, interval={interval.value}')
        return
    execute_func: Callable = wrap_func(symbol, init_cash, start_date, end_date, interval, klines_open, klines_high,
                                       klines_low, klines_close, klines_vol)
    strategy_name = os.path.basename(__file__)

    # 查看数据库是否已存在记录
    existed = query_optimization_exist(strategy_name, symbol, interval.value, start_date, end_date, save_remark)
    if existed:
        print(f'###数据库已有记录，跳过。>>[{strategy_name}, {symbol}, {interval.value}, {start_date}, {end_date}, '
              f'{save_remark}]')
        return

    start: float = perf_counter()
    results: list[tuple]
    print(f'\n>>>>开始穷举，symbol={symbol}，startDate={convert2_datetime_str(start_date)}，endDate='
          f'{convert2_datetime_str(end_date)}, interval={interval.value}，size={len(all_param_combs)}')
    with ProcessPoolExecutor(max_workers, mp_context=get_context("spawn")) as executor:
        # tqdm(
        #     executor.map(execute_func, all_param_combs),
        #     total=len(all_param_combs)
        # )  # 多进程中直接使用tqdm无效，需要使用tqdm.contrib.concurrent下的process_map()
        it: Iterable = executor.map(execute_func, all_param_combs)
        results = list(it)
        results.sort(reverse=True, key=lambda x: x[1])  # 按评判指标值倒序排序
    end: float = perf_counter()
    cost: int = int(end - start)
    print(f"\n>>>>穷举算法优化完成，耗时{cost}秒")

    if results is not None and len(results) > 0:
        save_table_optimization(results[:20], strategy_name, symbol, interval.value, init_cash,
                                start_date, end_date, 'sharpe_ratio', save_remark, datetime.now())  # 保存前20名


def batch_tasks(period: PeriodType = PeriodType.Quarter):
    """批量任务"""
    # 一般参数
    # symbols = ['AOL9']
    # symbols = ['RBL9', 'SAL9', 'AOL9']
    symbols = FUTURE_LIST_ALL
    # init_cashes = [90000, 90000, 120000]  # vbt不支持保证金制度计算，因此需要按照1手的实际价值来算（大致是文华保证金制度下所需资金的6倍）
    init_cashes = INIT_CASH_ALL
    intervals = [Interval.MINUTE60, Interval.MINUTE30]
    backtest_year = 3
    start_date = datetime(2017, 12, 23, 9, 0, 0)
    end_date = datetime(2022, 9, 30, 15, 0, 0)

    # 需要穷举的参数范围
    length_list = generate_param_comb(20, 300, 20)
    stpr_list = generate_param_comb(20, 50, 10)
    n_list = generate_param_comb(20, 90, 10)
    all_param_combs = list(product(length_list, stpr_list, n_list))

    _end_date_temp = start_date
    if period == PeriodType.Quarter:
        _end_date_temp = get_quarter_end_date(start_date)

    save_remark = f'backtest_year:{backtest_year}'

    for i in tqdm(range(len(symbols)), desc='穷举进度'):
        for j in range(len(intervals)):
            _end_date = _end_date_temp
            while _end_date <= end_date:
                _startDate = _end_date.replace(year=_end_date.year - backtest_year, hour=9, minute=0, second=0,
                                               microsecond=0) + timedelta(days=1)
                do_exhaustion(symbols[i], init_cashes[symbols[i]], _startDate, _end_date, intervals[j], all_param_combs,
                              save_remark)

                _end_date = get_quarter_end_date(_end_date + timedelta(days=1))


def combinatorial_test_two_types():
    """两个品种的组合测试"""
    start_date = datetime(2024, 1, 1, 9, 0, 0)
    end_date = datetime(2025, 4, 23, 15, 0, 0)

    symbol = 'RBL9'
    init_cash = INIT_CASH_ALL[symbol]
    length = 250
    stpr = 20
    interval = Interval.MINUTE60
    calculate_func: Callable = partial(calculate_signals, length=length, stpr=stpr)
    params_dict = {'len': length, 'stpr': stpr}
    params_dict, sharpe_ratio, zf_year1, zf_year2, zf_year3, daily_pnl, signal_count, win_count = (
        execute(calculate_func, symbol, init_cash, start_date, end_date, interval, params_dict=params_dict))

    symbol2 = 'SAL9'
    init_cash2 = INIT_CASH_ALL[symbol2]
    length2 = 50
    stpr2 = 15
    interval2 = Interval.MINUTE60
    calculate_func2: Callable = partial(calculate_signals, length=length2, stpr=stpr2)
    params_dict2 = {'len': length2, 'stpr': stpr2}
    params_dict2, sharpe_ratio2, zf_year1_2, zf_year2_2, zf_year3_2, daily_pnl2, signal_count2, win_count2 = (
        execute(calculate_func2, symbol2, init_cash2, start_date, end_date, interval2, params_dict=params_dict2))

    # 组合测试
    total_daily_pnl = daily_pnl.add(daily_pnl2)
    sharpe_ratio = calculate_statistics(total_daily_pnl, init_cash + init_cash2, 242, 0)['sharpe_ratio']

    print(f'\n>>[组合测试]sharpe_ratio={sharpe_ratio}')


def single_test():
    """单品种测试"""
    symbol = 'RBL9'  # RBL9、SAL9、AOL9
    init_cash = INIT_CASH_ALL[symbol]  # 90000、90000、120000
    length = 290  # RBL9:(250,20,70)、SAL9:(50,15,20)、AOL9:(130,40,20)
    stpr = 40
    interval = Interval.MINUTE60
    start_date = datetime(2024, 4, 10, 9, 0, 0)
    end_date = datetime(2025, 5, 31, 15, 0, 0)

    calculate_func: Callable = partial(calculate_signals, length=length, stpr=stpr)
    params_dict = {'len': length, 'stpr': stpr}
    params_dict, sharpe_ratio, zf_year1, zf_year2, zf_year3, daily_pnl, count, win_count = (
        execute(calculate_func, symbol, init_cash, start_date, end_date, interval, params_dict=params_dict,
                print_trade_detail=True))

    # result = [(params_dict, sharpe_ratio, zf_year1, zf_year2, zf_year3)]
    # save_table_optimization(result, os.path.basename(__file__), symbol, interval.value, start_date, end_date,
    #                         'sharpe_ratio', 'test1', datetime.now())


if __name__ == "__main__":
    """"""
    t0 = datetime.now()

    # 单品种测试
    single_test()

    # 组合测试
    # combinatorial_test_two_types()

    # 多进程并行
    # batch_tasks()

    t1 = datetime.now()
    print(f'\n>>>>>>总耗时{t1 - t0}s, now={t1}')
