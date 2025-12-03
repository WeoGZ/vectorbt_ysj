from datetime import date

import numpy as np
import pandas as pd
from pandas import DataFrame, Series
from pandas.core.window import ExponentialMovingWindow

from vectorbt_ysj.common.constant import Interval, LAST_BAR_START_TIME_MAP


def calculate_statistics(
        df: DataFrame,
        init_cash: float,
        annual_days: int,
        risk_free: float,
        output: bool = True
) -> dict:
    """计算策略统计指标"""
    print("\n开始计算策略统计指标")

    # Check DataFrame input exterior
    if df is None:
        print("\n***回测结果为空，无法计算绩效统计指标")
        return {}

    # Init all statistics default value
    start_date: str = ""
    end_date: str = ""
    total_days: int = 0
    profit_days: int = 0
    loss_days: int = 0
    end_balance: float = 0
    max_drawdown: float = 0
    max_ddpercent: float = 0
    max_drawdown_duration: int = 0
    total_net_pnl: float = 0
    daily_net_pnl: float = 0
    total_commission: float = 0
    daily_commission: float = 0
    total_slippage: float = 0
    daily_slippage: float = 0
    total_turnover: float = 0
    daily_turnover: float = 0
    total_trade_count: int = 0
    daily_trade_count: float = 0
    total_return: float = 0
    annual_return: float = 0
    daily_return: float = 0
    return_std: float = 0
    sharpe_ratio: float = 0
    ewm_sharpe: float = 0
    return_drawdown_ratio: float = 0

    # Check if balance is always positive
    positive_balance: bool = False

    if df is not None:
        # Calculate balance related time series data
        df["balance"] = df["net_pnl"].cumsum() + init_cash

        # When balance falls below 0, set daily return to 0
        pre_balance: Series = df["balance"].shift(1)
        pre_balance.iloc[0] = init_cash
        x = df["balance"] / pre_balance
        x[x <= 0] = np.nan
        df["return"] = np.log(x).fillna(0)

        df["highlevel"] = df["balance"].rolling(min_periods=1, window=len(df), center=False).max()
        df["drawdown"] = df["balance"] - df["highlevel"]
        df["ddpercent"] = df["drawdown"] / df["highlevel"] * 100

        # All balance value needs to be positive
        positive_balance = (df["balance"] > 0).all()
        if not positive_balance:
            print("\n***回测中出现爆仓（资金小于等于0），无法计算策略统计指标")

    # Calculate statistics value
    if positive_balance:
        # Calculate statistics value
        start_date = df.index[0]
        end_date = df.index[-1]

        total_days = len(df)
        profit_days = len(df[df["net_pnl"] > 0])
        loss_days = len(df[df["net_pnl"] < 0])

        end_balance = df["balance"].iloc[-1]
        max_drawdown = df["drawdown"].min()
        max_ddpercent = df["ddpercent"].min()
        max_drawdown_end = df["drawdown"].idxmin()

        if isinstance(max_drawdown_end, date):
            max_drawdown_start = df["balance"][:max_drawdown_end].idxmax()  # type: ignore
            max_drawdown_duration = (max_drawdown_end - max_drawdown_start).days
        else:
            max_drawdown_duration = 0

        total_net_pnl = df["net_pnl"].sum()
        daily_net_pnl = total_net_pnl / total_days

        # total_commission = df["commission"].sum()
        # daily_commission = total_commission / total_days
        #
        # total_slippage = df["slippage"].sum()
        # daily_slippage = total_slippage / total_days
        #
        # total_turnover = df["turnover"].sum()
        # daily_turnover = total_turnover / total_days
        #
        # total_trade_count = df["trade_count"].sum()
        # daily_trade_count = total_trade_count / total_days

        total_return = (end_balance / init_cash - 1) * 100
        annual_return = total_return / total_days * annual_days
        daily_return = df["return"].mean() * 100
        return_std = df["return"].std() * 100

        if return_std:
            daily_risk_free: float = risk_free / np.sqrt(annual_days)
            sharpe_ratio = (daily_return - daily_risk_free) / return_std * np.sqrt(annual_days)

            ewm_window: ExponentialMovingWindow = df["return"].ewm(halflife=120)
            ewm_mean: Series = ewm_window.mean() * 100
            ewm_std: Series = ewm_window.std() * 100
            ewm_sharpe = ((ewm_mean - daily_risk_free) / ewm_std).iloc[-1] * np.sqrt(annual_days)
        else:
            sharpe_ratio = 0
            ewm_sharpe = 0

        if max_ddpercent:
            return_drawdown_ratio = -total_return / max_ddpercent
        else:
            return_drawdown_ratio = 0

    # Output
    if output:
        print("-" * 30)
        print(f"首个交易日：\t{start_date}")
        print(f"最后交易日：\t{end_date}")

        print(f"总交易日：\t{total_days}")
        print(f"盈利交易日：\t{profit_days}")
        print(f"亏损交易日：\t{loss_days}")

        print(f"起始资金：\t{init_cash:,.2f}")
        print(f"结束资金：\t{end_balance:,.2f}")

        print(f"总收益率：\t{total_return:,.2f}%")
        print(f"年化收益：\t{annual_return:,.2f}%")
        print(f"最大回撤: \t{max_drawdown:,.2f}")
        print(f"百分比最大回撤: {max_ddpercent:,.2f}%")
        print(f"最大回撤天数: \t{max_drawdown_duration}")

        print(f"总盈亏：\t{total_net_pnl:,.2f}")
        print(f"总手续费：\t{total_commission:,.2f}")
        print(f"总滑点：\t{total_slippage:,.2f}")
        print(f"总成交金额：\t{total_turnover:,.2f}")
        print(f"总成交笔数：\t{total_trade_count}")

        print(f"日均盈亏：\t{daily_net_pnl:,.2f}")
        print(f"日均手续费：\t{daily_commission:,.2f}")
        print(f"日均滑点：\t{daily_slippage:,.2f}")
        print(f"日均成交金额：\t{daily_turnover:,.2f}")
        print(f"日均成交笔数：\t{daily_trade_count}")

        print(f"日均收益率：\t{daily_return:,.2f}%")
        print(f"收益标准差：\t{return_std:,.2f}%")
        print(f"Sharpe Ratio：\t{sharpe_ratio:,.2f}")
        print(f"EWM Sharpe：\t{ewm_sharpe:,.2f}")
        print(f"收益回撤比：\t{return_drawdown_ratio:,.2f}")

    statistics: dict = {
        "start_date": start_date,
        "end_date": end_date,
        "total_days": total_days,
        "profit_days": profit_days,
        "loss_days": loss_days,
        "capital": init_cash,
        "end_balance": end_balance,
        "max_drawdown": max_drawdown,
        "max_ddpercent": max_ddpercent,
        "max_drawdown_duration": max_drawdown_duration,
        "total_net_pnl": total_net_pnl,
        "daily_net_pnl": daily_net_pnl,
        "total_commission": total_commission,
        "daily_commission": daily_commission,
        "total_slippage": total_slippage,
        "daily_slippage": daily_slippage,
        "total_turnover": total_turnover,
        "daily_turnover": daily_turnover,
        "total_trade_count": total_trade_count,
        "daily_trade_count": daily_trade_count,
        "total_return": total_return,
        "annual_return": annual_return,
        "daily_return": daily_return,
        "return_std": return_std,
        "sharpe_ratio": sharpe_ratio,
        "ewm_sharpe": ewm_sharpe,
        "return_drawdown_ratio": return_drawdown_ratio,
    }

    # Filter potential error infinite value
    for key, value in statistics.items():
        if value in (np.inf, -np.inf):
            value = 0
        statistics[key] = np.nan_to_num(value)

    print("策略统计指标计算完成")
    return statistics


def generate_daily_pnl(asset_value: pd.Series, interval: Interval, init_cash: float) -> pd.DataFrame:
    """根据总资产序列构建每日盈亏"""
    last_bar_start_time = LAST_BAR_START_TIME_MAP[interval]  # 每个交易日最后一根K线的起始时间
    key_date = 'date'
    key_pnl = 'net_pnl'

    daily_pnl_dict: dict[str: list] = {key_date: [], key_pnl: []}
    pre_value = init_cash  # 前一个交易日收盘时的总资产
    for index, value in asset_value.items():
        if index.hour == last_bar_start_time[0] and index.minute == last_bar_start_time[1]:
            daily_pnl_dict[key_date].append(index.date())
            daily_pnl_dict[key_pnl].append(value - pre_value)
            pre_value = value

    daily_pnl: pd.DataFrame = pd.DataFrame(daily_pnl_dict).set_index('date')

    return daily_pnl
