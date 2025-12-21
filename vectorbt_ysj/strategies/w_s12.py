import os.path
from collections.abc import Iterable
from concurrent.futures import ProcessPoolExecutor
from functools import partial
from itertools import product
from multiprocessing import get_context
from time import perf_counter
from typing import Callable

import vectorbt as vbt
from tqdm import tqdm

from vectorbt_ysj.common.future_fee import FUTURE_FEE_ALL
from vectorbt_ysj.common.future_list import FUTURE_LIST_ALL
from vectorbt_ysj.common.future_size import FUTURE_SIZE_ALL
from vectorbt_ysj.common.future_slippage import FUTURE_SLIPPAGE_ALL
from vectorbt_ysj.common.init_cash import INIT_CASH_ALL
from vectorbt_ysj.utils.date_utils import *
from vectorbt_ysj.utils.kline_utils import *
from vectorbt_ysj.utils.param_utils import *
from vectorbt_ysj.utils.db_operation_utils import *
from vectorbt_ysj.utils.statistic_utils import *
from vectorbt_ysj.mytt import MyTT, MyTT_plus

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.io as pio

# 设置渲染器为浏览器
pio.renderers.default = "browser"

# pd.set_option('Display.max_rows', None)  #展示全部行
pd.set_option('Display.max_columns', None)  # 展示全部列


def execute(symbol: str, init_cash: float, start_date: datetime, end_date: datetime, interval: Interval,
            klines_open: pd.DataFrame = None, klines_high: pd.DataFrame = None, klines_low: pd.DataFrame = None,
            klines_close: pd.DataFrame = None, klines_vol: pd.DataFrame = None,
            length: int = 0, stpr: int = 0) -> tuple | None:
    """程序入口"""
    if klines_close is None:
        preload_days = 3 * 30  # 预加载3个月
        klines_open, klines_high, klines_low, klines_close, klines_vol = fetch_klines([symbol], start_date,
                                                                                      end_date, interval, preload_days)
    if klines_close is not None and not klines_close.empty:
        # print(f'>>total_len={len(klines_close)}')
        long_open_signals, long_close_signals, short_open_signals, short_close_signals = calculate_signals(
            klines_close[symbol], klines_high[symbol], klines_low[symbol], klines_vol[symbol],
            interval, length, stpr)

        long_entries = pd.Series(long_open_signals, index=klines_close.index)
        long_exits = pd.Series(long_close_signals, index=klines_close.index)
        short_entries = pd.Series(short_open_signals, index=klines_close.index)
        short_exits = pd.Series(short_close_signals, index=klines_close.index)
        # 截取开始日期以后的信号、收盘价
        long_entries = long_entries[long_entries.index >= start_date]
        long_exits = long_exits[long_exits.index >= start_date]
        short_entries = short_entries[short_entries.index >= start_date]
        short_exits = short_exits[short_exits.index >= start_date]
        klines_close = klines_close[klines_close.index >= start_date]

        vbt.settings['returns']['year_freq'] = '242 days'  # 平均一年242个交易日。vbt默认是365天
        freq = convert_to_vbt_freq(interval).value
        total_portfolio = vbt.Portfolio.from_signals(
            close=klines_close,
            entries=long_entries,
            exits=long_exits,
            short_entries=short_entries,
            short_exits=short_exits,
            init_cash=init_cash,
            # cash_sharing=True,
            group_by=True,
            freq=freq,
            size=FUTURE_SIZE_ALL[symbol] * 1,  # 默认1手
            fees=FUTURE_FEE_ALL[symbol],
            slippage=FUTURE_SLIPPAGE_ALL[symbol]
        )

        # 检测是否爆仓（***暂不使用，因为即使爆仓，计算结果也是大致相同，而且保证金制度下未必爆仓***）
        # trades_size = total_portfolio.trades.records_readable['Size']
        # if trades_size[trades_size < FUTURE_SIZE_MAP[symbol] * 1].size > 0:
        #     print(f'\ntrades.size={trades_size}')
        #     print(f'\n*****可能爆仓，请调整初始金额*****')
        #     return None

        # 计算滚动年收益率
        asset_values = total_portfolio.value()  # 总资产
        date_1year_ago = end_date.replace(year=end_date.year - 1, hour=15, minute=0, second=0,
                                          microsecond=0)  # 1年前
        date_2year_ago = end_date.replace(year=end_date.year - 2, hour=15, minute=0, second=0,
                                          microsecond=0)
        date_3year_ago = end_date.replace(year=end_date.year - 3, hour=15, minute=0, second=0,
                                          microsecond=0)
        if date_1year_ago < klines_close.index[0]:
            date_1year_ago = klines_close.index[0]
        elif date_2year_ago < klines_close.index[0]:
            date_2year_ago = klines_close.index[0]
        elif date_3year_ago < klines_close.index[0]:
            date_3year_ago = klines_close.index[0]
        year1_con = asset_values.index[0] <= date_1year_ago  # 至少有一年数据
        year2_con = asset_values.index[0] <= date_2year_ago
        year3_con = asset_values.index[0] <= date_3year_ago
        val_year1 = asset_values[asset_values.index <= date_1year_ago].iloc[-1] if year1_con else np.nan
        val_year2 = asset_values[asset_values.index <= date_2year_ago].iloc[-1] if year2_con else np.nan
        val_year3 = asset_values[asset_values.index <= date_3year_ago].iloc[-1] if year3_con else np.nan
        zf_year1 = (asset_values.iloc[-1] - val_year1) / init_cash if year1_con else np.nan  # 单利计算，且要求至少有一年数据
        zf_year2 = (val_year1 - val_year2) / init_cash if year2_con else np.nan
        zf_year3 = (val_year2 - val_year3) / init_cash if year3_con else np.nan
        # print(f'\n>>val_year1: {val_year1:.2f}, val_year2: {val_year2:.2f}, val_year3: {val_year3:.2f}, '
        #       f'zf_year1: {zf_year1:.4f}, zf_year2: {zf_year2:.4f}, zf_year3: {zf_year3:.4f}')

        # 穷举的参数
        params_dict = {'len': length, 'stpr': stpr}
        # 每日盈亏
        daily_pnl = generate_daily_pnl(asset_values, interval, init_cash)
        sharpe_ratio = calculate_statistics(daily_pnl, init_cash, 242, 0, False)['sharpe_ratio']
        # 信号数量
        signal_count = len(total_portfolio.trades.records_readable)  # 信号对数（一买一卖为一对）
        winning_count = len(total_portfolio.trades.winning)
        win_rate = 0 if signal_count == 0 else winning_count / signal_count
        # 最大回撤
        max_ddv = calculate_max_drawdown(total_portfolio, return_type=0, output=False)

        # 打印
        # print(f'\n>>[len={length}, stpr={stpr}, n={n}]\n{total_portfolio.stats()}')
        print(f'\n>>[symbol={symbol}, interval={interval.value}, start={convert2_datetime_str(start_date)}, '
              f'end={convert2_datetime_str(end_date)}, init_cash={init_cash}, len={length}, stpr={stpr}]'
              f'\n总盈利={total_portfolio.total_profit():.2f}, 夏普比率={sharpe_ratio:.2f}, count={signal_count}, '
              f'winning_count={winning_count}，胜率={win_rate * 100:.2f}%, 最大回撤值={max_ddv:.2f}')
        # print(f'\n>>总资产={total_portfolio.value()}')
        # print(f'\n>>asset_value={total_portfolio.asset_value()}')
        # print(f'\n>>trades=\n{total_portfolio.trades.records_readable}')  # 每笔交易的明细
        # print(f'\n>>trades.pnl=\n{total_portfolio.trades.pnl.values}')  # 每笔交易的盈亏
        # print(f'\n>>daily_returns=\n{total_portfolio.daily_returns()}')  # 每日涨幅。但包含了周六日，数值为NaN
        # print(f'\n>>daily_pnl={daily_pnl}, sharpe_ratio={sharpe_ratio:.2f}')  # 每日盈亏，vnpy方式计算的夏普比率
        # print(f'\n>>drawdowns=\n{total_portfolio.drawdowns.records_readable}')  # 每一个回撤的明细

        # 画图
        # total_portfolio.plot(['cum_returns', 'drawdowns', 'asset_value', 'value', 'underwater', 'gross_exposure',
        #                       'net_exposure']).show()  # 画图
        # total_portfolio.plot_trades(symbol)  # 未成功
        # total_portfolio.plot_trade_pnl(symbol)  # 未成功
        # total_portfolio.trades.plot()  # 未成功

        return params_dict, sharpe_ratio, zf_year1, zf_year2, zf_year3, daily_pnl, signal_count, winning_count


def calculate_signals(close_price: pd.Series, high_price: pd.Series, low_price: pd.Series, vols: pd.Series,
                      interval: Interval, length: int, stpr: int):
    """计算交易信号"""
    if close_price is not None and not close_price.empty:
        dt_list = pd.Series(close_price.index)

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
        bkcon = [True if i == 0 else False for i in op_l]  # 多头开仓
        skcon = [True if i == 0 else False for i in op_s]  # 空头开仓

        # 平仓信号——止盈止损
        stbar = 40

        # 特别处理：未触发出场条件前，过滤掉重复开仓信号
        dk_l = MyTT.IF(bkcon, 1, MyTT.IF(skcon, 2, 0))  # 多空交叉信号
        pre_final_close_index = np.nan
        finish = False
        while not finish:
            dk_l = handle_close_operation(dk_l, vols, low_price, high_price, stpr, stbar)
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
                           stpr: int, stbar: int):
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
    con = (close_con == 1) & (cnt_close == 1)  # 首次触发出场条件
    dk_l_2 = MyTT.IF(cn_l > 0, MyTT.IF(con, MyTT.IF(signal == 1, -1, -2), MyTT.IF(cnt_close == 0, 0, dk_l)),
                     dk_l)  # 更新出场信号，以及将平仓信号前的重复开仓信号置为0
    return dk_l_2


def wrap_execute(symbol: str, init_cash: float, start_date: datetime, end_date: datetime, interval: Interval,
                 klines_open: pd.DataFrame, klines_high: pd.DataFrame, klines_low: pd.DataFrame,
                 klines_close: pd.DataFrame, klines_vol: pd.DataFrame, params: tuple) -> tuple:
    return execute(symbol, init_cash, start_date, end_date, interval, klines_open, klines_high, klines_low,
                   klines_close, klines_vol, params[0], params[1])


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
        print(f'###{symbol}没有K线数据, start={convert2_datetime_str(start_date)}, end={convert2_datetime_str(end_date)}, '
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
    start_date = datetime(2018, 12, 23, 9, 0, 0)
    end_date = datetime(2024, 12, 31, 15, 0, 0)

    # 需要穷举的参数范围
    length_list = generate_param_comb(20, 300, 20)
    stpr_list = generate_param_comb(20, 50, 10)
    all_param_combs = list(product(length_list, stpr_list))

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
    init_cash = 60000
    interval = Interval.MINUTE60
    params_dict, sharpe_ratio, zf_year1, zf_year2, zf_year3, daily_pnl, signal_count, win_count = (
        execute(symbol, init_cash, start_date, end_date, interval, length=250, stpr=20))

    symbol2 = 'SAL9'
    init_cash2 = 60000
    interval2 = Interval.MINUTE60
    params_dict2, sharpe_ratio2, zf_year1_2, zf_year2_2, zf_year3_2, daily_pnl2, signal_count2, win_count2 = (
        execute(symbol2, init_cash2, start_date, end_date, interval2, length=50, stpr=15))

    # 组合测试
    total_daily_pnl = daily_pnl.add(daily_pnl2)
    sharpe_ratio = calculate_statistics(total_daily_pnl, init_cash + init_cash2, 242, 0)['sharpe_ratio']

    print(f'\n>>[组合测试]sharpe_ratio={sharpe_ratio}')


def single_test():
    """单品种测试"""
    symbol = 'PGL9'  # RBL9、SAL9、AOL9
    init_cash = INIT_CASH_ALL[symbol]  # 90000、90000、120000
    length = 140  # RBL9:(250,20)、SAL9:(50,15,20)、AOL9:(130,40,20)
    stpr = 40
    interval = Interval.MINUTE60
    start_date = datetime(2017, 4, 1, 9, 0, 0)
    end_date = datetime(2020, 3, 31, 15, 0, 0)
    params_dict, sharpe_ratio, zf_year1, zf_year2, zf_year3, daily_pnl, count, win_count = (
        execute(symbol, init_cash, start_date, end_date, interval, length=length, stpr=stpr))

    # result = [(params_dict, sharpe_ratio, zf_year1, zf_year2, zf_year3)]
    # save_table_optimization(result, os.path.basename(__file__), symbol, interval.value, start_date, end_date,
    #                         'sharpe_ratio', 'test1', datetime.now())


if __name__ == "__main__":
    """"""
    t0 = datetime.now()

    # 单品种测试
    # single_test()

    # 组合测试
    # combinatorial_test_two_types()

    # 多进程并行
    batch_tasks()

    t1 = datetime.now()
    print(f'\n>>>>>>总耗时{t1 - t0}s, now={t1}')
