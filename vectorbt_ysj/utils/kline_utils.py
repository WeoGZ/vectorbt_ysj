import pandas as pd
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from urllib import parse

from vectorbt_ysj.common.constant import *


def fetch_klines(symbols: list[str], start_date: datetime, end_date: datetime, interval: Interval,
                 preload_days: float = 0) -> tuple | None:
    """
    获取K线

    Parameters
    ----------
    preload_days: 开始日期前预加载的天数（自然日）"""

    all_klines_open = pd.DataFrame()
    all_klines_high = pd.DataFrame()
    all_klines_low = pd.DataFrame()
    all_klines_close = pd.DataFrame()
    all_klines_vol = pd.DataFrame()
    klineEngine = create_engine('mysql+pymysql://root:%s@localhost:3306/vnpy' % parse.quote_plus('admin'))
    if preload_days > 0:
        start_date = start_date - timedelta(days=preload_days)

    for symbol in symbols:
        query_kline_sql = "SELECT * FROM `dbbardata` WHERE symbol='%s' and `interval`='%s' and \
                datetime>='%s' and datetime<='%s' ORDER BY datetime;" % (symbol, interval.value,
                                                                         start_date.strftime('%Y-%m-%d %H:%M:%S'),
                                                                         end_date.strftime('%Y-%m-%d %H:%M:%S'))
        klines = pd.read_sql_query(query_kline_sql, klineEngine).set_index('datetime')
        if klines is not None and not klines.empty:
            all_klines_open = pd.concat([all_klines_open, klines['open_price']], axis=1)
            all_klines_high = pd.concat([all_klines_high, klines['high_price']], axis=1)
            all_klines_low = pd.concat([all_klines_low, klines['low_price']], axis=1)
            all_klines_close = pd.concat([all_klines_close, klines['close_price']], axis=1)
            all_klines_vol = pd.concat([all_klines_vol, klines['volume']], axis=1)

    if not all_klines_close.empty and all_klines_close.iloc[0].size == len(symbols):
        all_klines_open.columns = symbols
        all_klines_high.columns = symbols
        all_klines_low.columns = symbols
        all_klines_close.columns = symbols
        all_klines_vol.columns = symbols
        all_klines_open.index = pd.to_datetime(all_klines_open.index)
        all_klines_high.index = pd.to_datetime(all_klines_open.index)
        all_klines_low.index = pd.to_datetime(all_klines_open.index)
        all_klines_close.index = pd.to_datetime(all_klines_open.index)
        all_klines_vol.index = pd.to_datetime(all_klines_open.index)

    return all_klines_open, all_klines_high, all_klines_low, all_klines_close, all_klines_vol
