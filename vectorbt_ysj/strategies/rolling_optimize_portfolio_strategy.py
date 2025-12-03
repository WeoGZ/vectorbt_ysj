"""滚动优化组合策略"""

from datetime import datetime, timedelta
from urllib import parse

import pandas as pd
from sqlalchemy import create_engine

from vectorbt_ysj.strategies.w_s12_v4 import execute
from vectorbt_ysj.utils.date_utils import *
from vectorbt_ysj.utils.param_utils import *
from vectorbt_ysj.utils.statistic_utils import calculate_statistics


def execute1(strategy_name: str, futures: list, start_date: datetime, end_date: datetime) -> pd.DataFrame | None:
    """每个季度优化一次，对每个品种均选取夏普比率最高的一个策略（同一品种多个周期的也是选出一个）"""
    if futures is None or len(futures) == 0:
        print(f'***前检查参数futures')
        return
    if start_date is None or end_date is None or start_date > end_date:
        print(f'***请检查日期参数')
        return

    db_engine = create_engine('mysql+pymysql://root:%s@localhost:3306/vnpy' % parse.quote_plus('admin'))
    symbols_str = "','".join(futures)
    query_sql = ("SELECT t1.vt_symbol,t1.period,t1.start_date,t1.end_date,t1.target,t1.target_value,t1.params,"
                 "t1.zf_year1,t1.zf_year2,t1.zf_year3,t1.count,t1.init_cash "
                 "FROM optimization_data t1 LEFT JOIN ("
                 "SELECT vt_symbol,MAX(target_value) as sp "
                 "FROM optimization_data "
                 "WHERE strategy='%s' AND vt_symbol in ('%s') AND end_date='%s' AND target_value>0 GROUP BY vt_symbol) AS t2 "
                 "ON t1.target_value=t2.sp "
                 "WHERE t2.sp IS NOT NULL "
                 "ORDER BY t1.vt_symbol,t1.params;")
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
        db_records = pd.read_sql_query(
            query_sql % (strategy_name, symbols_str, convert2_datetime_str(train_end_date)), db_engine)
        if db_records is not None and len(db_records) > 0:
            _start_date = start_date.replace(hour=9) if _start_date is None else (
                    train_end_date.replace(hour=9) + timedelta(days=1))
            _end_date = end_date if train_end_date == verify_end_date else get_quarter_end_date(_start_date)
            _daily_pnl, _total_init_cash, _best_comb_infos = combinatorial_test(db_records, _start_date, _end_date)

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
    print(f'\n>>[滚动优化组合策略]sharpe_ratio={sharpe_ratio}')
    print_comb_infos(all_comb_infos)


def combinatorial_test(db_records: pd.DataFrame, start_date: datetime, end_date: datetime) -> tuple | None:
    """组合测试。返回汇总的每日盈亏"""
    if db_records is not None and len(db_records) > 0:
        total_daily_pnl = None
        total_init_cash = 0
        best_comb_infos = {}

        for i in range(0, len(db_records)):
            symbol = db_records.iloc[i]['vt_symbol']
            if symbol in best_comb_infos:  # SQL有可能查出多个结果（多组参数的夏普比率一样），此时只处理第一个结果
                continue
            init_cash = db_records.iloc[i]['init_cash']
            interval = find_interval(db_records.iloc[i]['period'])
            params_dict = convert2dict(db_records.iloc[i]['params'])
            _, _, _, _, _, daily_pnl, _ = execute(symbol, init_cash, start_date, end_date, interval,
                                                  length=params_dict['len'], stpr=params_dict['stpr'],
                                                  n=params_dict['n'])
            if total_daily_pnl is None:
                total_daily_pnl = daily_pnl
            else:
                total_daily_pnl = total_daily_pnl.add(daily_pnl)  # 不能直接用运算符‘+’，否则不重叠的索引行的数据会被置为NaN
            total_init_cash += init_cash
            best_comb_infos[symbol] = f'{db_records.iloc[i]['period']}#{db_records.iloc[i]['params']}'

        return total_daily_pnl, total_init_cash, best_comb_infos


def print_comb_infos(comb_infos: dict) -> None:
    """打印组合策略信息"""
    if comb_infos is not None and len(comb_infos) > 0:
        out_str = '\n>>>>[各区间组合信息]'
        for key, value in comb_infos.items():
            out_str = out_str + f'\n{key}: {value}'
        out_str = out_str + '\n>>>>\n'
        print(out_str)


if __name__ == '__main__':
    t0 = datetime.now()

    start_date = datetime(2023, 1, 1, 9, 0, 0)
    end_date = datetime(2025, 5, 14, 15, 0, 0)
    # end_date = datetime(2025, 5, 14, 15, 0, 0)
    execute1('w_s12_v4.py', ['RBL9', 'SAL9', 'AOL9'], start_date, end_date)

    t1 = datetime.now()
    print(f'\n>>>>>>总耗时{t1 - t0}s, now={t1}')
