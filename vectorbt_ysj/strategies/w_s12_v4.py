import calendar
import math
from collections.abc import Iterable
from concurrent.futures import ProcessPoolExecutor
from functools import partial
from itertools import product
from multiprocessing import get_context
from time import perf_counter
from typing import Callable

import vectorbt as vbt
from tqdm import tqdm

from vectorbt_ysj.common.constant import *
from vectorbt_ysj.utils.kline_utils import *
from vectorbt_ysj.utils.param_utils import *
from vectorbt_ysj.mytt import MyTT, MyTT_plus

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from urllib import parse
import plotly.io as pio

# 设置渲染器为浏览器
pio.renderers.default = "browser"

# pd.set_option('Display.max_rows',None)  #展示全部行
pd.set_option('Display.max_columns', None)  # 展示全部列


def execute(symbol: str, start_date: datetime, end_date: datetime, interval: Interval, klines_open: pd.DataFrame = None,
            klines_high: pd.DataFrame = None, klines_low: pd.DataFrame = None, klines_close: pd.DataFrame = None,
            klines_vol: pd.DataFrame = None, length: int = 0, stpr: int = 0, n: int = 0):
    """程序入口"""
    if klines_close is None:
        klines_open, klines_high, klines_low, klines_close, klines_vol = fetch_klines([symbol], start_date,
                                                                                      end_date, interval)
    if klines_close is not None and not klines_close.empty:
        # print(f'>>total_len={len(klines_close)}')
        long_open_signals, long_close_signals, short_open_signals, short_close_signals = calculate_signals(
            klines_close[symbol], klines_high[symbol], klines_low[symbol], klines_vol[symbol],
            interval, length, stpr, n)

        long_entries = pd.Series(long_open_signals, index=klines_close.index)
        long_exits = pd.Series(long_close_signals, index=klines_close.index)
        short_entries = pd.Series(short_open_signals, index=klines_close.index)
        short_exits = pd.Series(short_close_signals, index=klines_close.index)

        vbt.settings['returns']['year_freq'] = '252 days'  # 平均一年252个交易日。vbt默认是365天
        freq = convert_to_vbt_freq(interval).value
        total_portfolio = vbt.Portfolio.from_signals(
            close=klines_close,
            entries=long_entries,
            exits=long_exits,
            short_entries=short_entries,
            short_exits=short_exits,
            init_cash=60000,
            # cash_sharing=True,
            group_by=True,
            freq=freq,
            size=10,
            fees=0.0002,
            slippage=0.0003
        )
        # print(f'\n>>[length={length}, stpr={stpr}, n={n}]\n{total_portfolio.stats()}')
        print(f'\n>>[length={length}, stpr={stpr}, n={n}]'
              f'\n总盈利={total_portfolio.total_profit():.2f}, 夏普比率={total_portfolio.sharpe_ratio():.2f}')
        # total_portfolio.plot(
        #     ['cum_returns', 'drawdowns', 'asset_value', 'underwater', 'gross_exposure', 'net_exposure']).show()


def calculate_signals(close_price: pd.Series, high_price: pd.Series, low_price: pd.Series, vols: pd.Series,
                      interval: Interval, length: int, stpr: int, n: int):
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
            dt_pre_final = np.nan if np.isnan(pre_final_close_index) else dt_list[pre_final_close_index]
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


def wrap_execute(symbol: str, start_date: datetime, end_date: datetime, interval: Interval, klines_open: pd.DataFrame,
                 klines_high: pd.DataFrame, klines_low: pd.DataFrame, klines_close: pd.DataFrame,
                 klines_vol: pd.DataFrame, params: tuple):
    execute(symbol, start_date, end_date, interval, klines_open, klines_high, klines_low, klines_close, klines_vol,
            params[0], params[1], params[2])


def wrap_func(symbol: str, start_date: datetime, end_date: datetime, interval: Interval, klines_open: pd.DataFrame,
              klines_high: pd.DataFrame, klines_low: pd.DataFrame, klines_close: pd.DataFrame,
              klines_vol: pd.DataFrame) -> Callable:
    """二次封装：预先配置好部分参数，剩下关键参数待穷举输入"""
    func: Callable = partial(wrap_execute, symbol, start_date, end_date, interval, klines_open, klines_high,
                             klines_low, klines_close, klines_vol)
    return func


def do_exhaustion(symbol: str, start_date: datetime, end_date: datetime, interval: Interval, all_param_combs: list,
                  max_workers: int | None = None):
    """穷举"""
    klines_open, klines_high, klines_low, klines_close, klines_vol = fetch_klines([symbol], start_date, end_date,
                                                                                  interval)
    execute_func: Callable = wrap_func(symbol, start_date, end_date, interval, klines_open, klines_high, klines_low,
                                       klines_close, klines_vol)

    start: float = perf_counter()
    print(f'\n>>>>开始穷举，startDate={start_date.strftime('%Y-%m-%d %H:%M:%S')}，endDate='
          f'{end_date.strftime('%Y-%m-%d %H:%M:%S')}，size={len(all_param_combs)}')
    with ProcessPoolExecutor(max_workers, mp_context=get_context("spawn")) as executor:
        # tqdm(
        #     executor.map(execute_func, all_param_combs),
        #     total=len(all_param_combs)
        # )  # 多进程中直接使用tqdm无效，需要使用tqdm.contrib.concurrent下的process_map()
        executor.map(execute_func, all_param_combs)
    end: float = perf_counter()
    cost: int = int(end - start)
    print(f"\n>>>>穷举算法优化完成，耗时{cost}秒")


def get_quarter_end_date(d: datetime):
    """获取季度末的日期"""
    month = d.month
    quarter_end_month = 3
    if 3 < month <= 6:
        quarter_end_month = 6
    elif 6 < month <= 9:
        quarter_end_month = 9
    elif 9 < month <= 12:
        quarter_end_month = 12

    _, num_of_month = calendar.monthrange(d.year, quarter_end_month)

    return datetime(d.year, quarter_end_month, num_of_month, 15, 0, 0, 0)


def batch_tasks(period: PeriodType = PeriodType.Quarter):
    """批量任务"""
    # 一般参数
    backtest_year = 3
    startDate = datetime(2025, 4, 23, 9, 0, 0)
    endDate = datetime(2025, 6, 30, 15, 0, 0)
    interval = Interval.MINUTE60

    # 需要穷举的参数范围
    length_list = generate_param_comb(20, 300, 10)
    stpr_list = generate_param_comb(20, 50, 5)
    n_list = generate_param_comb(20, 90, 10)
    all_param_combs = list(product(length_list, stpr_list, n_list))

    _end_date = startDate
    if period == PeriodType.Quarter:
        _end_date = get_quarter_end_date(startDate)

    while _end_date <= endDate:
        _startDate = _end_date.replace(year=_end_date.year - backtest_year, hour=9, minute=0, second=0,
                                       microsecond=0) + timedelta(days=1)
        do_exhaustion('RBL9', _startDate, _end_date, interval, all_param_combs)

        _end_date = get_quarter_end_date(_end_date + timedelta(days=1))


if __name__ == "__main__":
    """"""
    t0 = datetime.now()

    startDate = datetime(2024, 1, 1, 9, 0, 0)
    endDate = datetime(2025, 4, 23, 15, 0, 0)
    execute('RBL9', startDate, endDate, Interval.MINUTE60, length=250, stpr=20, n=70)

    # 多进程并行
    # batch_tasks()

    t1 = datetime.now()
    print(f'\n>>>>>>总耗时{t1 - t0}s')
