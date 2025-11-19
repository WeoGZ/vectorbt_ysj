import vectorbt as vbt
from vectorbt_ysj.common.constant import *
from vectorbt_ysj.utils.kline_utils import *

import pandas as pd
import numpy as np
from datetime import datetime
from sqlalchemy import create_engine
from urllib import parse
import plotly.io as pio

# 设置渲染器为浏览器
pio.renderers.default = "browser"

# pd.set_option('Display.max_rows',None)#展示全部行
pd.set_option('Display.max_columns', None)  # 展示全部列


def ma_test(symbols: list[str], start_date: datetime, end_date: datetime, interval: Interval):
    _, _, _, klines_close, _ = fetch_klines(symbols, start_date, end_date, interval)
    if klines_close is not None and not klines_close.empty:
        # ma = vbt.MA.run(klines_close, window=[20, 60], short_name='ma22')
        # print(ma.ma)
        # f_ma, s_ma, fs_ma = vbt.MA.run_combs(klines_close, window=[20, 60, 80, 100], r=3, short_names=['fast_ma22', 'slow_ma22', 'fs33'])
        # print(f_ma.ma)
        # print('\n', s_ma.ma)
        # print('\n', fs_ma.ma)

        fast_ma = vbt.MA.run(klines_close, window=20, short_name='fast_ma')
        slow_ma = vbt.MA.run(klines_close, window=60, short_name='slow_ma')
        # print(f'fast_ma: \n{fast_ma.ma}')
        # print(f'slow_ma: \n{slow_ma.ma}')
        long_open_signals = fast_ma.ma_crossed_above(slow_ma)
        long_close_signals = fast_ma.ma_crossed_below(slow_ma)
        short_open_signals = fast_ma.ma_crossed_below(slow_ma)
        short_close_signals = fast_ma.ma_crossed_above(slow_ma)
        # print(f'long_open_signals=\n{long_open_signals.columns}')
        # print(f'long_close_signals=\n{long_close_signals}')
        # print(f'short_open_signals=\n{short_open_signals}')
        # print(f'short_close_signals=\n{short_close_signals}')
        total_portfolio = vbt.Portfolio.from_signals(
            close=klines_close,
            entries=long_open_signals,
            exits=long_close_signals,
            short_entries=short_open_signals,
            short_exits=short_close_signals,
            init_cash=60000,
            # cash_sharing=True,
            group_by=True,
            freq='D',
            size=[10, 20],
            fees=[0.0002, 0.0003],
            slippage=[0.0003, 0.0006]
        )
        print(total_portfolio.stats())
        # print('\n', total_portfolio[20, 60, 'RBL9'].stats())
        # print('\n', total_portfolio[20, 60, 'SAL9'].stats())
        # print('\n', total_portfolio['SAL9'].stats())
        # total_portfolio[20, 60, 'RBL9'].plot().show()
        # total_portfolio[20, 60, 'SAL9'].plot().show()
        total_portfolio.plot(
            ['cum_returns', 'drawdowns', 'asset_value', 'underwater', 'gross_exposure', 'net_exposure']).show()


if __name__ == "__main__":
    """"""
    t0 = datetime.now()

    startDate = datetime(2024, 1, 1, 9, 0, 0)
    endDate = datetime(2025, 5, 14, 15, 0, 0)
    ma_test(['RBL9'], startDate, endDate, Interval.DAILY)
    # ma_test(['RBL9', 'SAL9'], startDate, endDate, Interval.DAILY)

    # startDate = datetime(2023, 6, 1, 9, 0, 0)
    # endDate = datetime(2023, 6, 30, 15, 0, 0)
    # fetch_klines(['RBL9', 'SAL9', 'AOL9'], startDate, endDate, Interval.DAILY)

    t1 = datetime.now()
    print(f'\n>>>>>>总耗时{t1 - t0}s')
