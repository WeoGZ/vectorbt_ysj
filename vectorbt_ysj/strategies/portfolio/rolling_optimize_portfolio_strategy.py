"""滚动优化组合策略"""

from datetime import timedelta
from functools import partial
from typing import Callable, Tuple, List
from urllib import parse

import pandas as pd
from pandas import DataFrame
from sqlalchemy import create_engine

import vectorbt_ysj.strategies.w_s12 as strategy_s12
import vectorbt_ysj.strategies.w_s12_v4 as strategy_s12_v4
import vectorbt_ysj.strategies.w_sf20 as strategy_sf20
import vectorbt_ysj.strategies.w_sf20_v4 as strategy_sf20_v4
from vectorbt_ysj.common.future_list import *
from vectorbt_ysj.common.future_margin_ratio import *
from vectorbt_ysj.common.future_size import FUTURE_SIZE_ALL
from vectorbt_ysj.strategies.common_methods import common_execute
from vectorbt_ysj.utils.date_utils import *
from vectorbt_ysj.utils.kline_utils import fetch_klines
from vectorbt_ysj.utils.param_utils import *
from vectorbt_ysj.utils.statistic_utils import calculate_statistics
from vectorbt_ysj.utils.db_operation_utils import *


class FutureInfoSelected:
    """被选中品种的信息"""

    def __init__(self, symbol: str, close_price: float, margin: float, amount: int, strategy: str, params: str,
                 init_cash: float, period: str):
        self.symbol = symbol
        self.close_price = close_price  # 收盘价，用于计算保证金
        self.margin = margin  # 保证金
        self.amount = amount  # 手数
        self.strategy = strategy  # 策略名
        self.params = params  # 策略参数
        self.init_cash = init_cash  # 策略运行的初始资金（这里是品种价值，不是保证金）
        self.period = period  # K线周期


class PortfolioInfo:
    """组合策略信息"""

    def __init__(self, train_date: datetime, run_date_start: datetime, run_date_end: datetime, cash_start: float,
                 cash_end: float, futures_selected: list[FutureInfoSelected], occupied_margin_start: float):
        self.train_date = train_date
        self.run_date_start = run_date_start
        self.run_date_end = run_date_end
        self.cash_start = cash_start
        self.cash_end = cash_end
        self.futures_selected = futures_selected
        self.occupied_margin_start = occupied_margin_start  # 期初最大占用保证金金额（全部开仓的情况下才能达到）


def execute1(strategy_name: str, futures: list, start_date: datetime, end_date: datetime):
    """每个季度优化一次，对每个品种均选取夏普比率最高的一个策略（同一品种多个周期的也是选出一个）"""
    if futures is None or len(futures) == 0:
        print(f'***前检查参数futures')
        return
    if start_date is None or end_date is None or start_date > end_date:
        print(f'***请检查日期参数')
        return

    start_date = start_date.replace(hour=15, minute=0, second=0, microsecond=0)
    end_date = end_date.replace(hour=15, minute=0, second=0, microsecond=0)
    train_end_month = start_date.month - 3 if start_date.month - 3 > 0 else start_date.month + 9
    verify_end_month = end_date.month - 3 if end_date.month - 3 > 0 else end_date.month + 9
    train_end_year = start_date.year if start_date.month - 3 > 0 else start_date.year - 1
    verify_end_year = end_date.year if end_date.month - 3 > 0 else end_date.year - 1
    train_end_date = get_quarter_end_date(start_date.replace(
        year=train_end_year, month=train_end_month, day=1))  # 训练区间的结束日期，用于获取下一区间（验证区间）的参数
    verify_end_date = get_quarter_end_date(end_date.replace(
        year=verify_end_year, month=verify_end_month, day=1))  # 验证区间的结束日期

    all_daily_pnl = pd.DataFrame()
    _start_date = None
    total_init_cash = 0
    all_comb_infos = {}  # 记录每个季度选出的组合信息

    while train_end_date <= verify_end_date:
        print_str = f'>>train_end_date={train_end_date}'
        db_records = query_db_records1(strategy_name, futures, train_end_date)
        if db_records is not None and len(db_records) > 0:
            _start_date = start_date.replace(hour=9) if _start_date is None else (
                    train_end_date.replace(hour=9) + timedelta(days=1))
            _end_date = end_date if train_end_date == verify_end_date else get_quarter_end_date(_start_date)
            _daily_pnl, _total_init_cash, _best_comb_infos = combinatorial_test(strategy_name, db_records, _start_date,
                                                                                _end_date)

            all_daily_pnl = pd.concat([all_daily_pnl, _daily_pnl])
            total_init_cash = max(total_init_cash, _total_init_cash)
            key_date_range = f'{convert2_date_str(_start_date)}-{convert2_date_str(_end_date)}'
            all_comb_infos[key_date_range] = _best_comb_infos
            print_str = (f'{print_str}, start={_start_date}, end={_end_date}, record_len={len(db_records)}, '
                         f'all_daily_pnl_len={len(all_daily_pnl)}, _total_init_cash={_total_init_cash}, '
                         f'total_init_cash={total_init_cash}')

        train_end_date = get_quarter_end_date(train_end_date + timedelta(days=1))
        print('\n', print_str)

    sharpe_ratio = calculate_statistics(all_daily_pnl, total_init_cash, 242, 0)['sharpe_ratio']
    print(f'\n>>[滚动优化组合策略]sharpe_ratio={sharpe_ratio:.2f}')
    print_comb_infos(all_comb_infos)


def execute2(strategy_names: list, futures: list, start_date: datetime, end_date: datetime, remark: str,
             init_cash: float, max_rate_one: float, special_max_rate_one: float, total_max_rate: float):
    """"""
    if futures is None or len(futures) == 0:
        print(f'***前检查参数futures')
        return
    if start_date is None or end_date is None or start_date > end_date:
        print(f'***请检查日期参数')
        return

    print(f'>>策略数量={len(strategy_names)}, 品种数量={len(futures)}')

    start_date = start_date.replace(hour=15, minute=0, second=0, microsecond=0)
    end_date = end_date.replace(hour=15, minute=0, second=0, microsecond=0)
    train_end_month = start_date.month - 3 if start_date.month - 3 > 0 else start_date.month + 9
    verify_end_month = end_date.month - 3 if end_date.month - 3 > 0 else end_date.month + 9
    train_end_year = start_date.year if start_date.month - 3 > 0 else start_date.year - 1
    verify_end_year = end_date.year if end_date.month - 3 > 0 else end_date.year - 1
    train_end_date = get_quarter_end_date(start_date.replace(
        year=train_end_year, month=train_end_month, day=1))  # 训练区间的结束日期，用于获取下一区间（验证区间）的参数
    verify_end_date = get_quarter_end_date(end_date.replace(
        year=verify_end_year, month=verify_end_month, day=1))  # 验证区间的结束日期

    current_asset = init_cash  # 实时总资产
    portfolio_infos: dict[str, PortfolioInfo] = {}  # 每个周期的组合策略信息
    all_daily_pnl = pd.DataFrame()
    _start_date = None
    all_comb_infos = {}  # 记录每个季度选出的组合信息

    while train_end_date <= verify_end_date:
        print(f'>>train_end_date={train_end_date}')
        _start_date = start_date.replace(hour=9) if _start_date is None else (
                train_end_date.replace(hour=9) + timedelta(days=1))
        _end_date = end_date if train_end_date == verify_end_date else get_quarter_end_date(_start_date)

        max_margin_one = current_asset * max_rate_one  # 单个品种的最大可使用保证金金额
        spe_max_margin_one = current_asset * special_max_rate_one  # 特殊情况下单个品种的最大可使用保证金金额，如回测指标特别好的
        total_max_margin = current_asset * total_max_rate  # 最大可使用保证金金额

        db_records: DataFrame = query_db_records2(strategy_names, futures, train_end_date, remark)
        if db_records is not None and len(db_records) > 0:
            print_str = f'>>SQL初选rows={len(db_records)}'

            occupied_margins: dict = {}
            selected_strategies: list[FutureInfoSelected] = []
            selected_row_indexes: list = []
            selected_strategy_symbol_period = {}  # 已被选取的“标的-策略-周期”key。用于实现“同一策略同一周期只出一组参数”
            found_future_count: int = 0  # 已遍历到的品种数
            current_margin: float = 0.0  # 当前保证金（这里是假设选中策略全都开仓的情况下，是理论占用保证金）
            finish_pick = False  # 是否结束策略选取（即已经选取完毕）

            # 获取K线数据
            preload_days = 30
            all_symbols = db_records['vt_symbol'].unique().tolist()
            all_close_prices = fetch_klines(all_symbols, train_end_date, train_end_date, Interval.DAILY,
                                            preload_days)[3]
            if len(all_close_prices) == 0:  # 兜底一次
                all_close_prices = fetch_klines(all_symbols, train_end_date, train_end_date, Interval.DAILY,
                                                preload_days * 2)[3]

            # 选取策略，形成当期的组合策略
            round_num = 0
            while finish_pick is False:
                result = pick_strategies(db_records, selected_row_indexes, selected_strategy_symbol_period,
                                         occupied_margins, found_future_count, current_margin, all_close_prices,
                                         max_margin_one, spe_max_margin_one, total_max_margin)
                selected_strategies.extend(result[0])
                finish_pick = result[1]
                current_margin = result[2]
                found_future_count = result[3]
                print_str = (f'{print_str}\n\tRound {round_num}: 已入选策略数量={len(selected_strategies)}, 当前保证金='
                             f'{current_margin:.2f}')
                round_num += 1

            # 计算当期的每日盈亏
            _daily_pnl, _total_init_cash, _best_comb_infos = combinatorial_test2(selected_strategies, _start_date,
                                                                                 _end_date)
            all_daily_pnl = pd.concat([all_daily_pnl, _daily_pnl])
            sum_daily_pnl = _daily_pnl['net_pnl'].sum()  # 每日盈亏汇总
            # 更新期末总资金、保证金等
            cash_start = current_asset
            current_asset += sum_daily_pnl
            # 记录当期组合策略选取结果
            key_date_range = f'{convert2_date_str(_start_date)}-{convert2_date_str(_end_date)}'
            all_comb_infos[key_date_range] = _best_comb_infos
            portfolio_infos[convert2_datetime_str(train_end_date)] = PortfolioInfo(
                train_end_date, _start_date, _end_date, cash_start, current_asset, selected_strategies, current_margin)

            print_str = (f'{print_str}\n\n\t当期每日盈亏汇总={sum_daily_pnl:.2f}, 期初资金={cash_start:.2f}, 期末资金='
                         f'{current_asset:.2f}')
            print('\n', print_str)

        train_end_date = get_quarter_end_date(train_end_date + timedelta(days=1))

    sharpe_ratio = calculate_statistics(all_daily_pnl, init_cash, 242, 0)['sharpe_ratio']
    print(f'\n>>[滚动优化组合策略2]sharpe_ratio={sharpe_ratio:.2f}')
    print_comb_infos(all_comb_infos)


def pick_strategies(alt_strategies: DataFrame, selected_row_indexes: list, selected_strategy_symbol_period: dict,
                    occupied_margins: dict, found_future_count: int, current_margin: float, all_close_prices: DataFrame,
                    max_margin_one: float, spe_max_margin_one: float, total_max_margin: float) -> tuple:
    """遍历一轮并筛选出符合条件的策略。每轮每个品种最多只出一个策略"""

    spe_future_rank = 2  # 特殊情况条件1：排名前n个品种（按品种，不是按参数组）
    spe_sharp_ratio = 2.0  # 特殊情况条件2：夏普比率>=n

    finish_pick = False  # 是否结束策略选取（即已经选取完毕）
    selected_symbols: list[str] = []
    selected_strategies: list[FutureInfoSelected] = []
    selected_keys_start_size = len(selected_strategy_symbol_period)

    if len(selected_row_indexes) == len(alt_strategies):  # 所有策略加起来保证金还没达到最大值的情况
        return [], True, current_margin, found_future_count

    for i in range(len(alt_strategies)):
        row = alt_strategies.iloc[i]
        symbol = row['vt_symbol']
        strategy = row['strategy']
        period = row['period']
        key = f'{symbol}#{strategy}#{period}'
        # all_keys[key] = 1
        if key in selected_strategy_symbol_period:  # “品种-策略-周期”是唯一标识，只出一组参数
            continue
        if i in selected_row_indexes:
            continue
        if symbol in selected_symbols:  # 每轮每个品种最多出一个策略
            continue
        if symbol not in occupied_margins:
            occupied_margins[symbol] = 0
            found_future_count += 1
        occ_margin = occupied_margins[symbol]
        if occ_margin < max_margin_one:
            close_price = all_close_prices[symbol].iloc[-1]
            margin = close_price * FUTURE_SIZE_ALL[symbol] * FUTURE_MARGIN_RATIO_ALL[symbol] / 100  # 实时保证金金额

            if current_margin + margin > total_max_margin:  # 超过最大可用保证金额度，跳过，遍历下一条
                finish_pick = True
                continue

            if occ_margin + margin <= max_margin_one:
                match = True
            else:
                spe_condition = found_future_count <= spe_future_rank and row['target_value'] >= spe_sharp_ratio
                match = spe_condition and occ_margin + margin <= spe_max_margin_one
                if spe_condition:
                    out_str = f'\t\t\t特殊条件成立: {symbol}#{strategy}#{period}#{row['params']}'
                    out_str = f'{out_str} ==>> 满足保证金条件' if match else f'{out_str} ==>> 不满足保证金条件'
                    print(out_str)
            if match:
                occupied_margins[symbol] = occ_margin + margin
                current_margin += margin
                selected_strategies.append(
                    FutureInfoSelected(symbol, close_price, margin, 1, row['strategy'], row['params'],
                                       row['init_cash'], row['period']))
                selected_row_indexes.append(i)
                selected_symbols.append(symbol)
                selected_strategy_symbol_period[key] = 1

    if selected_keys_start_size == len(selected_strategy_symbol_period):  # 没有新增，说明已遍历完所有能满足条件的组合
        finish_pick = True
        print(f'--selected_key没有新增，表示已遍历完全部')

    return selected_strategies, finish_pick, current_margin, found_future_count


def combinatorial_test(strategy_name: str, db_records: pd.DataFrame, start_date: datetime,
                       end_date: datetime) -> tuple | None:
    """组合测试。返回汇总的每日盈亏"""
    if db_records is not None and len(db_records) > 0:
        total_daily_pnl = pd.DataFrame()
        total_init_cash = 0
        best_comb_infos = {}

        for i in range(0, len(db_records)):
            symbol = db_records.iloc[i]['vt_symbol']
            if symbol in best_comb_infos:  # SQL有可能查出多个结果（多组参数的夏普比率一样），此时只处理第一个结果
                continue
            init_cash = db_records.iloc[i]['init_cash']
            interval = find_interval(db_records.iloc[i]['period'])
            params_dict = convert2dict(db_records.iloc[i]['params'])
            daily_pnl = pd.DataFrame()
            calculate_func: Callable = print  # 初始化变量
            par_dict: dict = {}
            if strategy_name == 'w_s12_v4.py':
                calculate_func = partial(strategy_s12_v4.calculate_signals, length=params_dict['len'],
                                         stpr=params_dict['stpr'], n=params_dict['n'])
                par_dict = {'len': params_dict['len'], 'stpr': params_dict['stpr'], 'n': params_dict['n']}
            elif strategy_name == 'w_s12.py':
                calculate_func = partial(strategy_s12.calculate_signals, length=params_dict['len'],
                                         stpr=params_dict['stpr'])
                par_dict = {'len': params_dict['len'], 'stpr': params_dict['stpr']}
            result = common_execute(calculate_func, symbol, init_cash, start_date, end_date, interval,
                                    params_dict=par_dict)
            # _, _, _, _, _, daily_pnl, _, _
            if result is None:
                continue
            else:
                daily_pnl = result[5]

            total_daily_pnl = total_daily_pnl.add(daily_pnl, fill_value=0)  # 不能直接用运算符‘+’，否则不重叠的索引行的数据会被置为NaN
            total_init_cash += init_cash
            best_comb_infos[symbol] = f'{db_records.iloc[i]['period']}#{db_records.iloc[i]['params']}'

        return total_daily_pnl, total_init_cash, best_comb_infos


def combinatorial_test2(strategies: list[FutureInfoSelected], start_date: datetime, end_date: datetime) -> tuple | None:
    """组合测试2。返回汇总的每日盈亏"""
    if strategies is not None and len(strategies) > 0:
        total_daily_pnl = pd.DataFrame()
        total_init_cash = 0
        best_comb_infos: dict[str, list] = {}

        for i in range(0, len(strategies)):
            fi = strategies[i]
            symbol = fi.symbol
            # if symbol in best_comb_infos:  # SQL有可能查出多个结果（多组参数的夏普比率一样），此时只处理第一个结果
            #     continue
            init_cash = fi.init_cash
            interval = find_interval(fi.period)
            params_dict = convert2dict(fi.params)
            strategy_name = fi.strategy
            # daily_pnl = pd.DataFrame()
            calculate_func: Callable = print  # 初始化变量
            par_dict: dict = {}
            preload_days = 180
            if strategy_name == 'w_s12_v4.py':
                calculate_func = partial(strategy_s12_v4.calculate_signals, length=params_dict['len'],
                                         stpr=params_dict['stpr'], n=params_dict['n'])
                par_dict = {'len': params_dict['len'], 'stpr': params_dict['stpr'], 'n': params_dict['n']}
                preload_days = (params_dict['n'] / 5 + 1) * 30
            elif strategy_name == 'w_s12.py':
                calculate_func = partial(strategy_s12.calculate_signals, length=params_dict['len'],
                                         stpr=params_dict['stpr'])
                par_dict = {'len': params_dict['len'], 'stpr': params_dict['stpr']}
            elif strategy_name == 'w_sf20_v4.py':
                calculate_func = partial(strategy_sf20_v4.calculate_signals, length=params_dict['len'],
                                         stpr=params_dict['stpr'], n=params_dict['n'])
                par_dict = {'len': params_dict['len'], 'stpr': params_dict['stpr'], 'n': params_dict['n']}
                preload_days = (params_dict['n'] / 5 + 1) * 30
            elif strategy_name == 'w_sf20.py':
                calculate_func = partial(strategy_sf20.calculate_signals, length=params_dict['len'],
                                         stpr=params_dict['stpr'])
                par_dict = {'len': params_dict['len'], 'stpr': params_dict['stpr']}
            result = common_execute(calculate_func, symbol, init_cash, start_date, end_date, interval,
                                    params_dict=par_dict, preload_days=preload_days)
            if result is None:
                continue
            else:
                daily_pnl = result[5]
                print(f'--symbol={symbol}, strategy={strategy_name}, params={fi.params}, sum_pnl='
                      f'{daily_pnl.sum().iloc[0]:.2f}')  # , pnl=\n{daily_pnl}

            total_daily_pnl = total_daily_pnl.add(daily_pnl, fill_value=0)  # 不能直接用运算符‘+’，否则不重叠的索引行的数据会被置为NaN
            total_init_cash += init_cash
            if symbol not in best_comb_infos:
                best_comb_infos[symbol] = []
            best_comb_infos[symbol].append(f'{strategy_name}#{fi.period}#{fi.params}')

        return total_daily_pnl, total_init_cash, best_comb_infos


def query_db_records1(strategy_name: str, futures: list, train_end_date: datetime) -> pd.DataFrame | None:
    """查询指定策略、指定训练时间节点下，每个标的表现最好的一组参数"""
    db_engine = get_db_engine()
    symbols_str = "','".join(futures)
    query_sql = ("SELECT t1.vt_symbol,t1.period,t1.start_date,t1.end_date,t1.target,t1.target_value,t1.params,"
                 "t1.zf_year1,t1.zf_year2,t1.zf_year3,t1.count,t1.init_cash "
                 "FROM optimization_data t1 LEFT JOIN ("
                 "SELECT vt_symbol,MAX(target_value) as sp "
                 "FROM optimization_data "
                 "WHERE strategy='%s' AND vt_symbol in ('%s') AND end_date='%s' AND target_value>0 GROUP BY vt_symbol) AS t2 "
                 "ON t1.target_value=t2.sp "
                 "WHERE t2.sp IS NOT NULL AND t1.strategy='%s' AND t1.vt_symbol in ('%s') AND t1.end_date='%s' "
                 "ORDER BY t1.vt_symbol,t1.params;")
    end_date_str = convert2_datetime_str(train_end_date)
    db_records = pd.read_sql_query(query_sql % (strategy_name, symbols_str, end_date_str, strategy_name, symbols_str,
                                                end_date_str), db_engine)

    return db_records


def query_db_records2(strategy_names: list, futures: list, train_end_date: datetime,
                      remark: str) -> pd.DataFrame | None:
    """查询指定日期、指定策略集合、指定品种集合下的所有回测数据"""
    db_engine = get_db_engine()
    strategies_str = "','".join(strategy_names)
    symbols_str = "','".join(futures)
    query_sql = ("SELECT vt_symbol,strategy,period,params,start_date,end_date,target,target_value,zf_year1,zf_year2,"
                 "zf_year3,count,win_count,init_cash,generate_datetime FROM optimization_data WHERE strategy in ('%s') "
                 "AND vt_symbol in ('%s') AND end_date='%s' AND target_value>0 AND remark='%s' AND zf_year1>=0.05 AND "
                 "target_value>=0.8 ORDER BY target_value DESC;")
    end_date_str = convert2_datetime_str(train_end_date)
    db_records = pd.read_sql_query(query_sql % (strategies_str, symbols_str, end_date_str, remark), db_engine)

    return db_records


def print_comb_infos(comb_infos: dict) -> None:
    """打印组合策略信息"""
    if comb_infos is not None and len(comb_infos) > 0:
        out_str = '\n>>>>[各区间组合信息]'
        for key, value in comb_infos.items():
            out_str = out_str + f'\n{key}: {value}'
            if isinstance(value, dict):  # 打印每个品种选出的策略数量
                count = 0
                out_str = out_str + f'\n--各品种策略数量统计: ['
                for k, v in value.items():
                    out_str = out_str + f'{k}: {len(v)}, '
                    count += len(v)
                out_str = out_str[:-2] + f']\n--策略数量={count}, 品种数量={len(value)}'
        out_str = out_str + '\n>>>>\n'
        print(out_str)


if __name__ == '__main__':
    t0 = datetime.now()

    start_date = datetime(2025, 1, 1, 9, 0, 0)
    end_date = datetime(2025, 6, 30, 15, 0, 0)

    # execute1('w_s12.py', ['RBL9', 'SAL9', 'AOL9'], start_date, end_date)
    # execute1('w_s12.py', FUTURE_LIST_ALL, start_date, end_date)
    # execute1('w_s12.py', [sym for sym in FUTURE_LIST_ALL if
    #                       sym not in (FUTURE_LIST_PRECIOUS_METALS + FUTURE_LIST_PETROLEUM +
    #                                   FUTURE_LIST_AGRICULTURAL_SIDELINE_PRODUCTS + FUTURE_LIST_SHIPPING)],
    #          start_date, end_date)

    strategies = ['w_s12.py', 'w_s12_v4.py', 'w_sf20.py', 'w_sf20_v4.py']
    futures = [sym for sym in FUTURE_LIST_ALL if sym not in (FUTURE_LIST_PRECIOUS_METALS + FUTURE_LIST_PETROLEUM +
                                                             FUTURE_LIST_AGRICULTURAL_SIDELINE_PRODUCTS +
                                                             FUTURE_LIST_SHIPPING)]
    remark = 'backtest_year:3'
    init_cash = 1_000_000
    max_rate_one = 0.04  # 单个品种最大占用保证金比例
    special_max_rate_one = 0.08  # 特殊情况下，单个品种最大占用保证金比例
    total_max_rate = 0.9  # 最大动用保证金比例，即保证金除以总资金的比例
    execute2(strategies, futures, start_date, end_date, remark, init_cash, max_rate_one, special_max_rate_one,
             total_max_rate)

    t1 = datetime.now()
    print(f'\n>>>>>>总耗时{t1 - t0}s, now={t1}')
