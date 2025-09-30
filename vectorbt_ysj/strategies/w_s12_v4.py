import math

import vectorbt as vbt
from vectorbt_ysj.common.constant import *
from vectorbt_ysj.utils.kline_utils import *
from vectorbt_ysj.mytt import MyTT, MyTT_plus

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


def execute(symbol: str, start_date: datetime, end_date: datetime, interval: Interval, len: int, stpr: int, n: int):
    """程序入口"""
    _, klines_high, klines_low, klines_close, klines_vol = fetch_klines([symbol], start_date, end_date, interval)
    if klines_close is not None and not klines_close.empty:
        pass


def calculate_signals(close_price: pd.Series, high_price: pd.Series, low_price: pd.Series, vols: pd.Series,
                      interval: Interval, length: int, stpr: int, n: int):
    """计算交易信号"""
    if close_price is not None and not close_price.empty:
        in_trade_list = np.zeros(close_price.size)

        cnn: int = cal_kline_len_single_day(close_price, interval)
        zd: pd.Series = cal_zd(close_price, n, cnn)
        cd = close_price - MyTT.REF(close_price, 1)
        buy_v = MyTT.SUM(MyTT.IF(cd > 0, vols, 0), length)
        sell_v = MyTT.SUM(MyTT.IF(cd < 0, vols, 0), length)
        bsr = buy_v / sell_v
        last_bar_hour = LAST_BAR_START_TIME_MAP[interval][0]
        last_bar_minute = LAST_BAR_START_TIME_MAP[interval][1]
        bsl = pd.Series([bsr[i - 1] if i > 0 and close_price[i - 1].index.hour == last_bar_hour and
                                       close_price[i - 1].index.minute == last_bar_minute else np.nan
                         for i in range(close_price.size)])
        for i in range(1, bsl.size):
            if np.isnan(bsl[i]) and not np.isnan(bsl[i - 1]):
                bsl[i] = bsl[i - 1]
        mbl = np.maximum(bsl, 1)
        msl = np.minimum(bsl, 1)

        crossup_bsr_mbl = MyTT.CROSS(bsr, mbl) and MyTT.REF(in_trade_list, 1) == 0
        op_l = MyTT.BARSLAST(crossup_bsr_mbl)
        crossdown_bsr_msl = MyTT.CROSS(msl, bsr) and MyTT.REF(in_trade_list, 1) == 0
        op_s = MyTT.BARSLAST(crossdown_bsr_msl)
        op_temp1 = ~np.isnan(op_l) and ~np.isnan(op_s)
        op = MyTT.IF(op_temp1, np.minimum(op_l, op_s), MyTT.IF(np.isnan(op_l), op_s, MyTT.IF(np.isnan(op_s), op_l, -1)))
        dk = MyTT.IF(op_l == 0, 1, MyTT.IF(op_s == 0, -1, np.nan))
        # dk特殊处理：当等于nan时取前一个有效值
        for i in range(1, dk.size):
            if np.isnan(dk[i]) and not np.isnan(dk[i - 1]):
                dk[i] = dk[i - 1]

        # 开仓信号
        bkcon = op_l == 0 and zd == 0  # 多头开仓
        skcon = op_s == 0 and zd == 0  # 空头开仓

        # 平仓信号——止盈止损
        stbar = 40
        jp = MyTT.IF(MyTT.REF(dk, 1) == 1, MyTT.REF(MyTT_plus.HHV(low_price.values, op), 1),
                     MyTT.IF(MyTT.REF(dk, 1) == -1, MyTT.REF(MyTT_plus.LLV(high_price.values, op), 1), np.nan))
        vp = jp * MyTT.IF(MyTT.REF(dk, 1) == 1, 1 - stbar / 1000, MyTT.IF(MyTT.REF(dk, 1) == -1, 1 + stbar / 1000, np.nan))
        cn = MyTT.IF(np.isnan(dk), np.nan, op)
        sum_vol = MyTT_plus.SUM(vols.values, cn) if not np.isnan(cn) else np.nan
        sum_amt = MyTT_plus.SUM(vols.values * vp, cn) if not np.isnan(cn) else np.nan
        vwap = MyTT.IF(op > 0, MyTT.IF(op >= stbar, vp, sum_amt / sum_vol), np.nan)
        pcon_l = MyTT.REF(dk, 1) == 1 and low_price <= vwap
        pcon_s = MyTT.REF(dk, 1) == -1 and high_price >= vwap

        # 平仓信号——转震荡
        zd_close_l = MyTT.REF(zd, 1) == 0 and zd == 1 and MyTT.REF(dk, 1) == 1
        zd_close_s = MyTT.REF(zd, 1) == 0 and zd == 1 and MyTT.REF(dk, 1) == -1

        # 特别处理：未平仓时不反向开仓
        # # 多单未平、不开空单
        # bkcon2 = pd.Series(
        #     [True if pcon_l[i] and skcon[i] and low_price[i] > vwap[i] else bkcon[i] for i in range(bkcon)])
        # pcon_l2 = pd.Series(
        #     [False if pcon_l[i] and skcon[i] and low_price[i] > vwap[i] else pcon_l[i] for i in range(bkcon)])
        # skcon2 = pd.Series(
        #     [False if pcon_l[i] and skcon[i] and low_price[i] > vwap[i] else skcon[i] for i in range(bkcon)])
        # # 空单未平、不开多单
        # skcon2 = pd.Series(
        #     [True if pcon_s[i] and bkcon[i] and high_price[i] < vwap[i] else skcon[i] for i in range(bkcon)])
        # pcon_s2 = pd.Series(
        #     [False if pcon_s[i] and bkcon[i] and high_price[i] < vwap[i] else pcon_s[i] for i in range(bkcon)])
        # bkcon2 = pd.Series(
        #     [False if pcon_s[i] and bkcon[i] and high_price[i] < vwap[i] else skcon[i] for i in range(bkcon)])

        bkcon2 = pd.Series(bkcon)
        skcon2 = pd.Series(skcon)
        pcon_l2 = pd.Series(pcon_l)
        pcon_s2 = pd.Series(pcon_s)
        in_trade = False
        for i in range(close_price.size):
            if ~in_trade and (bkcon[i] or skcon[i]):
                in_trade = True

            if in_trade:
                # 多单未平、不开空单
                if pcon_l[i] and skcon[i]:
                    if low_price[i] > vwap[i]:
                        bkcon2[i] = True
                        pcon_l2[i] = False
                        skcon2[i] = False
                    else:  # 若同一根K线同时触发多单止盈止损和开空，则忽略开空
                        skcon2[i] = False

                    dk[i] = 1
                elif pcon_s[i] and bkcon[i]:
                    if high_price[i] < vwap[i]:
                        skcon2[i] = True
                        pcon_s2[i] = False
                        bkcon2[i] = False
                    else:  # 若同一根K线同时触发空单止盈止损和开多，则忽略开多
                        bkcon2[i] = False

                    dk[i] = -1


def cal_kline_len_single_day(prices: pd.Series, interval: Interval):
    """计算单个交易日有多少根K线。以螺纹钢60分钟为例，返回6"""
    if prices is not None and not prices.empty:
        start_time_array: tuple = LAST_BAR_START_TIME_MAP[interval]

        # 不同品种的起始交易时间不同，夜盘品种是21:00:00、日盘品种是9:00:00或9:30:00
        start_hour = 9
        start_minute = 0
        # 判断是否有夜盘K线
        night_bars_count = prices[prices.index.hour >= 21].size
        day_minutes: list[int] = [bar.index.minute for bar in prices if bar.index.hour == 9]
        if night_bars_count > 0:
            start_hour = 21
        elif len(day_minutes) > 0:
            start_minute = min(day_minutes)

        cal_day = 3  # 取最近3个交易日
        already_cal_day = 0
        kline_len_per_day: list[int] = []
        start_index = -1
        end_index = -1
        for i in reversed(prices.index):
            if i.hour == start_time_array[0] and i.minute == start_time_array[1] and i.second == 0:
                end_index = i
            elif (prices[i].index.hour == start_hour and prices[i].index.minute == start_minute and
                  prices[i].index.second == 0 and end_index != -1):
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
    ln1 = max(3, math.floor(n / 2))

    # 波动率波峰/波谷拐点
    bf_right = MyTT.REF(ma_vlt, ln1) > MyTT.HHV(ma_vlt, ln1)  # 波峰结构的右边
    bg_right = MyTT.REF(ma_vlt, ln1) < MyTT.LLV(ma_vlt, ln1)  # 波谷结构的右边
    bf_left = MyTT.REF(ma_vlt >= MyTT.REF(MyTT.HHV(ma_vlt, ln1), 1), ln1).fillna(False).convert_dtypes()
    bf_left2 = MyTT.REF(ma_vlt >= MyTT.REF(MyTT.HHV(ma_vlt, 20 * cnn), 1), ln1).fillna(False).convert_dtypes()
    bg_left = MyTT.REF(ma_vlt <= MyTT.REF(MyTT.LLV(ma_vlt, ln1), 1), ln1).fillna(False).convert_dtypes()
    bg_left2 = MyTT.REF(ma_vlt <= MyTT.REF(MyTT.LLV(ma_vlt, 20 * cnn), 1), ln1).fillna(False).convert_dtypes()
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


if __name__ == "__main__":
    """"""
    t0 = datetime.now()

    startDate = datetime(2024, 1, 1, 9, 0, 0)
    endDate = datetime(2025, 5, 14, 15, 0, 0)

    t1 = datetime.now()
    print(f'\n>>>>>>总耗时{t1 - t0}s')
