import math
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
from vectorbt_ysj.mytt import MyTT, MyTT_plus
from vectorbt_ysj.strategies.common_methods import common_execute
from vectorbt_ysj.utils.date_utils import *
from vectorbt_ysj.utils.db_operation_utils import *
from vectorbt_ysj.utils.kline_utils import *
from vectorbt_ysj.utils.param_utils import *
from vectorbt_ysj.utils.statistic_utils import *

# 设置渲染器为浏览器
pio.renderers.default = "browser"

pd.set_option('Display.max_rows', None)  #展示全部行
pd.set_option('Display.max_columns', None)  # 展示全部列


def calculate_signals(close_price: pd.Series, high_price: pd.Series, low_price: pd.Series, open_price: pd.Series,
                      vols: pd.Series, interval: Interval, length: int, stpr: int, n: int):
    """计算交易信号"""
    if close_price is not None and not close_price.empty:
        dt_list = pd.Series(close_price.index)

        cnn: int = cal_kline_len_single_day(close_price, interval)
        # print(f'>>cnn={cnn}')
        zd: pd.Series = cal_zd(close_price, n, cnn)
        # print(f'>>zd[-10:]={zd[-10:]}')
        # print(f'>>转震荡信号点={dt_list[np.where((zd == 1) & (MyTT.REF(zd, 1) == 0))[0]]}')
        # print(f'>>结束震荡信号点={dt_list[np.where((zd == 0) & (MyTT.REF(zd, 1) == 1))[0]]}')
        cd = close_price - MyTT.REF(close_price, 1)
        buy_v = MyTT.SUM(MyTT.IF(cd > 0, vols, 0), length)
        sell_v = MyTT.SUM(MyTT.IF(cd < 0, vols, 0), length)
        sell_v[sell_v == 0] = 1
        bsr = buy_v / sell_v
        last_bar_hour = LAST_BAR_START_TIME_MAP[interval][0]
        last_bar_minute = LAST_BAR_START_TIME_MAP[interval][1]
        bsl = np.array([bsr[i - 1] if i > 0 and close_price.index[i - 1].hour == last_bar_hour and
                                      close_price.index[i - 1].minute == last_bar_minute else np.nan
                        for i in range(close_price.size)])
        for i in range(1, len(bsl)):
            if np.isnan(bsl[i]) and not np.isnan(bsl[i - 1]):
                bsl[i] = bsl[i - 1]
        mbl = np.maximum(bsl, 1)
        msl = np.minimum(bsl, 1)

        crossup_bsr_mbl = MyTT.CROSS(bsr, mbl)
        op_l = MyTT.BARSLAST(crossup_bsr_mbl)
        crossdown_bsr_msl = MyTT.CROSS(msl, bsr)
        op_s = MyTT.BARSLAST(crossdown_bsr_msl)

        # 开仓信号
        bkcon = [True if i == 0 and j == 0 else False for i, j in zip(op_l, zd)]  # 多头开仓
        skcon = [True if i == 0 and j == 0 else False for i, j in zip(op_s, zd)]  # 空头开仓

        # 平仓信号——止盈止损
        stbar = 40

        # 特别处理：未触发出场条件前，过滤掉重复开仓信号
        dk_l = MyTT.IF(bkcon, 1, MyTT.IF(skcon, 2, 0))  # 多空交叉信号
        pre_final_close_index = np.nan
        finish = False
        while not finish:
            dk_l = handle_close_operation(dk_l, vols, low_price, high_price, zd, stpr, stbar)
            close_indexes = np.where((dk_l == -1) | (dk_l == -2))[0]
            final_close_index = close_indexes[-1] if len(close_indexes) > 0 else np.nan  # 最后一个平仓信号的下标
            # dt_pre_final = np.nan if np.isnan(pre_final_close_index) else dt_list[pre_final_close_index]
            # print(f'>>pre_final_close_index={pre_final_close_index}({dt_pre_final}), \
            #         final_close_index={final_close_index}({dt_list[final_close_index]})')
            finish = (final_close_index == pre_final_close_index) or (
                    np.isnan(final_close_index) and np.isnan(pre_final_close_index))
            pre_final_close_index = final_close_index
        # print(f'>>dk_l[-50:]={dk_l[-50:]}')
        # print(f'>>多开信号={dt_list[np.where(dk_l == 1)[0]]}')
        # print(f'>>多平信号={dt_list[np.where(dk_l == -1)[0]]}')
        # print(f'>>空开信号={dt_list[np.where(dk_l == 2)[0]]}')
        # print(f'>>空平信号={dt_list[np.where(dk_l == -2)[0]]}')

        # 输出
        long_open_signals = [True if s == 1 else False for s in dk_l]
        long_close_signals = [True if s == -1 else False for s in dk_l]
        short_open_signals = [True if s == 2 else False for s in dk_l]
        short_close_signals = [True if s == -2 else False for s in dk_l]
        return long_open_signals, long_close_signals, short_open_signals, short_close_signals


def handle_close_operation(dk_l: np.ndarray, vols: pd.Series, low_price: pd.Series, high_price: pd.Series,
                           zd: pd.Series, stpr: int, stbar: int):
    """更新出场信号（多单的平仓信号是-1、空单是-2），以及将平仓信号前的重复开仓信号置为0。注意：此函数每次只处理一个多/空信号。"""
    cumsum_dk_l = MyTT.SUM(dk_l, 0)
    cn_l = MyTT.IF(cumsum_dk_l > 0, MyTT.BARSLAST(MyTT.CROSS(cumsum_dk_l, 0)), np.nan)  # 最近一次交叉信号的位置
    signal = MyTT_plus.REF(dk_l, cn_l)  # 多空信号。1表示多头，2表示空头
    jp_temp = MyTT.IF(signal == 1, MyTT_plus.HV(low_price.values, cn_l),
                      MyTT.IF(signal == 2, MyTT_plus.LV(high_price.values, cn_l), np.nan))
    jp_l = MyTT.IF(MyTT.REF(cumsum_dk_l, 1) > 0, jp_temp, np.nan)
    vp_l = MyTT.IF(signal == 1, jp_l * (1 - stpr / 1000),
                   MyTT.IF(signal == 2, jp_l * (1 + stpr / 1000), np.nan))
    sum_vol_l = MyTT.IF(cn_l > 0, MyTT_plus.SUM(vols.values, cn_l), np.nan)
    sum_amt_l = MyTT.IF(cn_l > 0, MyTT_plus.SUM(vols.values * vp_l, cn_l), np.nan)
    vwap_l = MyTT.IF(cn_l > 0, MyTT.IF(cn_l >= stbar, vp_l, sum_amt_l / sum_vol_l), np.nan)
    close_con = MyTT.IF(signal == 1, low_price.values <= vwap_l,
                        MyTT.IF(signal == 2, high_price.values >= vwap_l, np.nan))
    cnt_close = MyTT_plus.SUM(close_con, cn_l)  # 开仓后触发出场条件的次数
    con1 = (zd == 1) & (MyTT.REF(zd, 1) == 0) & (cnt_close == 0)  # 转震荡（首次触发出场条件前）
    con2 = (close_con == 1) & (cnt_close == 1) & (MyTT_plus.SUM(con1, cn_l) == 0)  # 首次触发出场条件（之前没有转震荡信号）
    con = con1 | con2
    dk_l_2 = MyTT.IF(cn_l > 0, MyTT.IF(con, MyTT.IF(signal == 1, -1, -2), MyTT.IF(cnt_close == 0, 0, dk_l)),
                     dk_l)  # 更新出场信号，以及将平仓信号前的重复开仓信号置为0
    return dk_l_2


def cal_kline_len_single_day(prices: pd.Series, interval: Interval):
    """计算单个交易日有多少根K线。以螺纹钢60分钟为例，返回6"""
    if prices is not None and not prices.empty:
        start_time_array: tuple = LAST_BAR_START_TIME_MAP[interval]

        # 不同品种的起始交易时间不同，夜盘品种是21:00:00、日盘品种是9:00:00或9:30:00
        start_hour = 9
        start_minute = 0
        # 判断是否有夜盘K线
        night_bars_count = prices[prices.index.hour >= 21].size
        day_minutes: list[int] = [index.minute for index, value in prices.items() if index.hour == 9]
        if night_bars_count > 0:
            start_hour = 21
        elif len(day_minutes) > 0:
            start_minute = min(day_minutes)

        cal_day = 3  # 取最近3个交易日
        already_cal_day = 0
        kline_len_per_day: list[int] = []
        start_index = -1
        end_index = -1
        for i in range(len(prices) - 1, -1, -1):
            if (prices.index[i].hour == start_time_array[0] and prices.index[i].minute == start_time_array[1] and
                    prices.index[i].second == 0):
                end_index = i
            elif (prices.index[i].hour == start_hour and prices.index[i].minute == start_minute and
                  prices.index[i].second == 0 and end_index != -1):
                start_index = i
            if start_index != -1 and end_index != -1:
                already_cal_day += 1
                kline_len_per_day.append(end_index - start_index + 1)  # 计算单个交易日所含K线数量
                start_index = -1
                end_index = -1
                if already_cal_day >= cal_day:
                    break

        return math.ceil(max(kline_len_per_day))


def cal_zd(prices: pd.Series, n: int, cnn: int):
    """计算是否震荡"""
    zf: pd.Series = MyTT.LN(prices / MyTT.REF(prices, 1)) * 100
    vlt = MyTT.STD(zf, cnn * n) * MyTT.SQRT(252 * cnn)
    ma_vlt = MyTT.MA(vlt, math.floor(n / 3) * cnn)
    ln1 = max(3, math.floor(cnn / 2))

    # 波动率波峰/波谷拐点
    bf_right = MyTT.REF(ma_vlt, ln1) > MyTT.HHV(ma_vlt, ln1)  # 波峰结构的右边
    bg_right = MyTT.REF(ma_vlt, ln1) < MyTT.LLV(ma_vlt, ln1)  # 波谷结构的右边
    bf_left = pd.Series(MyTT.REF(ma_vlt >= MyTT_plus.HV(ma_vlt, ln1), ln1))
    bf_left2 = pd.Series(MyTT.REF(ma_vlt >= MyTT_plus.HV(ma_vlt, 20 * cnn), ln1))
    bg_left = pd.Series(MyTT.REF(ma_vlt <= MyTT_plus.LV(ma_vlt, ln1), ln1))
    bg_left2 = pd.Series(MyTT.REF(ma_vlt <= MyTT_plus.LV(ma_vlt, 20 * cnn), ln1))
    turn_tag = MyTT.IF(bf_right & bf_left & bf_left2, 1, MyTT.IF(bg_right & bg_left & bg_left2, -1, np.nan))

    hvlt_temp = MyTT.BARSLAST(turn_tag == 1)
    hvlt = MyTT_plus.REF(ma_vlt, hvlt_temp + ln1)
    lvlt_temp = MyTT.BARSLAST(turn_tag == -1)
    lvlt = MyTT_plus.REF(ma_vlt, lvlt_temp + ln1)
    ln2 = 20
    fd1 = MyTT.IF(turn_tag == 1, (hvlt / lvlt - 1) * 100, np.nan)
    fd2 = MyTT.IF(turn_tag == -1, (lvlt / hvlt - 1) * 100, np.nan)
    zd = MyTT.IF(fd1 >= ln2, 1, MyTT.IF(fd2 <= -ln2, 0, np.nan))
    # zd特殊处理1：当等于nan时取前一个有效值
    for i in range(1, len(zd)):
        if np.isnan(zd[i]) and not np.isnan(zd[i - 1]):
            zd[i] = zd[i - 1]
    # zd特殊处理2：起始段的nan置为0，否则会出现由于加载数据不足导致起始段zd值为nan的情况
    zd = np.nan_to_num(zd)

    return zd


def wrap_execute(symbol: str, init_cash: float, start_date: datetime, end_date: datetime, interval: Interval,
                 klines_open: pd.DataFrame, klines_high: pd.DataFrame, klines_low: pd.DataFrame,
                 klines_close: pd.DataFrame, klines_vol: pd.DataFrame, params: tuple) -> tuple:
    calculate_func: Callable = partial(calculate_signals, length=params[0], stpr=params[1], n=params[2])
    params_dict = {'len': params[0], 'stpr': params[1], 'n': params[2]}
    preload_days = (params[2] / 5 + 1) * 30
    return common_execute(calculate_func, symbol, init_cash, start_date, end_date, interval, klines_open, klines_high,
                          klines_low, klines_close, klines_vol, params_dict, preload_days)


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
    intervals = [Interval.MINUTE15, Interval.MINUTE5]  # Interval.MINUTE60, Interval.MINUTE30
    backtest_year = 3
    start_date = datetime(2020, 12, 23, 9, 0, 0)
    end_date = datetime(2025, 3, 31, 15, 0, 0)

    # 需要穷举的参数范围
    length_list = generate_param_comb(20, 300, 20)
    stpr_list = generate_param_comb(20, 50, 10)
    n_list = generate_param_comb(20, 90, 20)
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
    n = 70
    interval = Interval.MINUTE60
    calculate_func: Callable = partial(calculate_signals, length=length, stpr=stpr, n=n)
    params_dict = {'len': length, 'stpr': stpr, 'n': n}
    params_dict, sharpe_ratio, zf_year1, zf_year2, zf_year3, daily_pnl, signal_count, win_count = (
        common_execute(calculate_func, symbol, init_cash, start_date, end_date, interval, params_dict=params_dict))

    symbol2 = 'SAL9'
    init_cash2 = INIT_CASH_ALL[symbol2]
    length2 = 50
    stpr2 = 15
    n2 = 20
    interval2 = Interval.MINUTE60
    calculate_func2: Callable = partial(calculate_signals, length=length2, stpr=stpr2, n=n2)
    params_dict2 = {'len': length2, 'stpr': stpr2, 'n': n2}
    params_dict2, sharpe_ratio2, zf_year1_2, zf_year2_2, zf_year3_2, daily_pnl2, signal_count2, win_count2 = (
        common_execute(calculate_func2, symbol2, init_cash2, start_date, end_date, interval2, params_dict=params_dict2))

    # 组合测试
    total_daily_pnl = daily_pnl.add(daily_pnl2)
    sharpe_ratio = calculate_statistics(total_daily_pnl, init_cash + init_cash2, 242, 0)['sharpe_ratio']

    print(f'\n>>[组合测试]sharpe_ratio={sharpe_ratio}')


def single_test():
    """单品种测试"""
    symbol = 'JML9'  # RBL9、SAL9、AOL9
    init_cash = INIT_CASH_ALL[symbol]  # 90000、90000、120000
    length = 100  # RBL9:(250,20,70)、SAL9:(50,15,20)、AOL9:(130,40,20)
    stpr = 30
    n = 20
    interval = Interval.MINUTE30
    start_date = datetime(2022, 1, 1, 9, 0, 0)
    end_date = datetime(2024, 12, 31, 15, 0, 0)

    calculate_func: Callable = partial(calculate_signals, length=length, stpr=stpr, n=n)
    params_dict = {'len': length, 'stpr': stpr, 'n': n}
    params_dict, sharpe_ratio, zf_year1, zf_year2, zf_year3, daily_pnl, count, win_count = (
        common_execute(calculate_func, symbol, init_cash, start_date, end_date, interval, params_dict=params_dict,
                       print_trade_detail=True, preload_days=570))

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
