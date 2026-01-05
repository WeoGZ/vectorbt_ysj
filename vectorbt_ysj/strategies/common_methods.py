from datetime import datetime
from typing import Callable

import vectorbt as vbt

from vectorbt_ysj.common.future_fee import FUTURE_FEE_ALL
from vectorbt_ysj.common.future_size import FUTURE_SIZE_ALL
from vectorbt_ysj.common.future_slippage import FUTURE_SLIPPAGE_ALL
from vectorbt_ysj.utils.date_utils import convert2_datetime_str
from vectorbt_ysj.utils.kline_utils import fetch_klines
from vectorbt_ysj.utils.param_utils import convert_to_vbt_freq
from vectorbt_ysj.utils.statistic_utils import *


def common_execute(calculate_func: Callable, symbol: str, init_cash: float, start_date: datetime, end_date: datetime,
                   interval: Interval, klines_open: pd.DataFrame = None, klines_high: pd.DataFrame = None,
                   klines_low: pd.DataFrame = None, klines_close: pd.DataFrame = None, klines_vol: pd.DataFrame = None,
                   params_dict: dict = None, preload_days: int = 90, print_trade_detail: bool = False) -> tuple | None:
    """历史回测程序。calculate_func是各个策略计算交易信号的封装函数。出了交易信号之后的绩效评测流程是统一的"""
    if klines_close is None:
        # preload_days = (math.ceil(length / KLINE_SIZE_PER_DAY_MAP[interval]) + 60) * (31 / 21)  # 换算成自然日数量
        # preload_days = (n / 5 + 1) * 30  # 参数n数值每5大概所需1个月数据计算，在换算成自然日。额外补一个月。
        klines_open, klines_high, klines_low, klines_close, klines_vol = fetch_klines([symbol], start_date,
                                                                                      end_date, interval, preload_days)
    if klines_close is not None and not klines_close.empty:
        # print(f'>>total_len={len(klines_close)}')
        long_open_signals, long_close_signals, short_open_signals, short_close_signals = calculate_func(
            klines_close[symbol], klines_high[symbol], klines_low[symbol], klines_open[symbol], klines_vol[symbol],
            interval)

        long_entries = pd.Series(long_open_signals, index=klines_close.index)
        long_exits = pd.Series(long_close_signals, index=klines_close.index)
        short_entries = pd.Series(short_open_signals, index=klines_close.index)
        short_exits = pd.Series(short_close_signals, index=klines_close.index)
        # 开始日期前的开仓信号位置比较，以决定是否需要在截取信号序列补开仓信号
        long_entries_before = long_entries[long_entries.index < start_date]
        long_exits_before = long_exits[long_exits.index < start_date]
        short_entries_before = short_entries[short_entries.index < start_date]
        short_exits_before = short_exits[short_exits.index < start_date]
        # 截取开始日期以后的信号、收盘价
        long_entries = long_entries[long_entries.index >= start_date]
        long_exits = long_exits[long_exits.index >= start_date]
        short_entries = short_entries[short_entries.index >= start_date]
        short_exits = short_exits[short_exits.index >= start_date]
        klines_close = klines_close[klines_close.index >= start_date]
        # 截取信号序列首根K线补开仓信号
        long_open_indexes = long_entries_before[long_entries_before == True].index
        long_close_indexes = long_exits_before[long_exits_before == True].index
        short_open_indexes = short_entries_before[short_entries_before == True].index
        short_close_indexes = short_exits_before[short_exits_before == True].index
        if len(long_open_indexes) > 0 and (len(long_close_indexes) == 0 or
                                           long_open_indexes[-1] > long_close_indexes[-1]):
            long_entries.iloc[0] = True
        if len(short_open_indexes) > 0 and (len(short_close_indexes) == 0 or
                                            short_open_indexes[-1] > short_close_indexes[-1]):
            short_entries.iloc[0] = True

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
        # params_dict = {'len': length, 'stpr': stpr, 'n': n}
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
              f'end={convert2_datetime_str(end_date)}, init_cash={init_cash}, 参数={params_dict}]'
              f'\n总盈利={total_portfolio.total_profit():.2f}, 夏普比率={sharpe_ratio:.2f}, count={signal_count}, '
              f'winning_count={winning_count}，胜率={win_rate * 100:.2f}%, 最大回撤值={max_ddv:.2f}')
        # print(f'\n>>总资产={total_portfolio.value()}')
        # print(f'\n>>asset_value={total_portfolio.asset_value()}')
        if print_trade_detail:
            print(f'\n>>trades=\n{total_portfolio.trades.records_readable}')  # 每笔交易的明细
        # print(f'\n>>trades.pnl=\n{total_portfolio.trades.pnl.values}')  # 每笔交易的盈亏
        # print(f'\n>>daily_returns=\n{total_portfolio.daily_returns()}')  # 每日涨幅。但包含了周六日，数值为NaN
        # print(f'\n>>daily_pnl={daily_pnl}, sharpe_ratio={sharpe_ratio:.2f}')  # 每日盈亏，vnpy方式计算的夏普比率

        # 画图
        # total_portfolio.plot(['cum_returns', 'drawdowns', 'asset_value', 'value', 'underwater', 'gross_exposure',
        #                       'net_exposure']).show()  # 画图
        # total_portfolio.plot_trades(symbol)  # 未成功
        # total_portfolio.plot_trade_pnl(symbol)  # 未成功
        # total_portfolio.trades.plot()  # 未成功

        return params_dict, sharpe_ratio, zf_year1, zf_year2, zf_year3, daily_pnl, signal_count, winning_count
