from datetime import datetime
from urllib import parse

import pandas as pd
from sqlalchemy import create_engine

from vectorbt_ysj.utils.date_utils import convert2_datetime_str

g_db_engine = None


def save_table_optimization(results: list, strategy_class: str, vt_symbol, interval: str, init_cash: float,
                            start_date: datetime, end_date: datetime, target: str, remark: str,
                            generate_datetime: datetime):
    """写入数据库。写到表optimization_data"""
    db_engine = get_db_engine()

    table_columns = ['strategy', 'vt_symbol', 'period', 'start_date', 'end_date', 'target', 'target_value', 'params',
                     'remark', 'generate_datetime', 'zf_year1', 'zf_year2', 'zf_year3', 'count', 'win_count',
                     'init_cash']
    data_dict = {key: [] for key in table_columns}
    data_dict[table_columns[0]] = [strategy_class] * len(results)
    data_dict[table_columns[1]] = [vt_symbol] * len(results)
    data_dict[table_columns[2]] = [interval] * len(results)
    data_dict[table_columns[3]] = [start_date] * len(results)
    data_dict[table_columns[4]] = [end_date] * len(results)
    data_dict[table_columns[5]] = [target] * len(results)
    data_dict[table_columns[8]] = [remark] * len(results)
    data_dict[table_columns[9]] = [generate_datetime] * len(results)
    data_dict[table_columns[15]] = [round(init_cash, 2)] * len(results)
    for result in results:
        params: dict = result[0]
        target_value = result[1]
        data_dict[table_columns[6]].append(round(target_value, 4))
        data_dict[table_columns[7]].append(str(params))
        data_dict[table_columns[10]].append(round(result[2], 4))
        data_dict[table_columns[11]].append(round(result[3], 4))
        data_dict[table_columns[12]].append(round(result[4], 4))
        data_dict[table_columns[13]].append(result[6])
        data_dict[table_columns[14]].append(result[7])
    df = pd.DataFrame.from_dict(data_dict)
    df.to_sql('optimization_data', db_engine, if_exists='append', index=False)


def query_optimization_exist(strategy_class: str, vt_symbol: str, interval: str, start_date: datetime,
                             end_date: datetime, remark: str) -> bool:
    """查询是否存在记录"""
    db_engine = get_db_engine()
    query_sql = ("SELECT COUNT(1) AS cnt FROM `optimization_data` WHERE strategy='%s' AND vt_symbol='%s' AND "
                 "period='%s' AND start_date='%s' AND end_date='%s' AND remark='%s';")
    db_records = pd.read_sql_query(
        query_sql % (strategy_class, vt_symbol, interval, convert2_datetime_str(start_date),
                     convert2_datetime_str(end_date), remark), db_engine)
    if db_records is not None and len(db_records) > 0 and db_records.iloc[0]['cnt'] > 0:
        return True


def get_db_engine():
    global g_db_engine
    if g_db_engine is None:
        # g_db_engine = create_engine('mysql+pymysql://ucnotkline:%s@192.168.2.205:3306/vnpy' % parse.quote_plus('ucnotkline@205'))
        g_db_engine = create_engine('mysql+pymysql://root:%s@localhost:3306/vnpy' % parse.quote_plus('admin'))

    return g_db_engine
