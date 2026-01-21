import json

import numpy as np
import pandas as pd
import datetime

import vectorbt as vbt

from vectorbt_ysj.common.future_list import *

# # 使用字符串创建 Timedelta
# # td_from_str = pd.Timedelta('2 days 3 hours 30 minutes')
# # td_from_str = pd.Timedelta('20.87m')
# td_from_str = pd.Timedelta('4h')
# td_from_str_days = pd.Timedelta('365 days')
#
# # 使用整数值和单位参数创建 Timedelta
# td_from_int = pd.Timedelta(42, unit='h')  # 42小时
#
# # 直接使用天、小时等参数创建 Timedelta
# td_from_components = pd.Timedelta(days=2, hours=5, minutes=30)
#
# # 使用 datetime.timedelta 对象创建 Timedelta
# td_from_datetime = pd.Timedelta(datetime.timedelta(days=1, seconds=3600))
#
# dt0 = datetime.datetime(2025, 4, 1, 9, 0, 0, 0)
#
# # 输出内容
# print("Timedelta from string:", td_from_str)
# print("Timedelta from integer and unit:", td_from_int)
# print("Timedelta from components:", td_from_components)
# print("Timedelta from datetime.timedelta:", td_from_datetime)
# print(f'>>out={td_from_str_days / td_from_str}')
# print(f'>>new time={dt0 + datetime.timedelta(days=-0.5)}')


# dt4 = datetime.datetime(2020, 4, 1)
# dt5 = datetime.datetime(2020, 9, 30)
# print((dt5 - dt4).days)


# price = pd.Series([1., 2., 3., 4., 3., 2., 1.])
# size = pd.Series([1., -0.5, -0.5, 2., -0.5, -0.5, -0.5])
# trades = vbt.Portfolio.from_orders(price, size).trades
# 
# print(trades.count())
# # 6
# 
# print(trades.pnl.sum())
# # -3.0
# 
# print(trades.winning.count())
# # 2
# 
# print(trades.winning.pnl.sum())
# # 1.5


# import numpy as np
# import pandas as pd
# from numba import njit
# from collections import namedtuple
# 
# example_dt = np.dtype([
#      ('id', np.int64),
#      ('col', np.int64),
#      ('idx', np.int64),
#      ('some_field', np.float64)
#  ])
# records_arr = np.array([
#      (0, 0, 0, 10.),
#      (1, 0, 1, 11.),
#      (2, 0, 2, 12.),
#      (3, 1, 0, 13.),
#      (4, 1, 1, 14.),
#      (5, 1, 2, 15.),
#      (6, 2, 0, 16.),
#      (7, 2, 1, 17.),
#      (8, 2, 2, 18.)
#  ], dtype=example_dt)
# wrapper = vbt.ArrayWrapper(index=['x', 'y', 'z'],
#      columns=['a', 'b', 'c'], ndim=2, freq='1 day')
# records = vbt.Records(wrapper, records_arr)
# print(records.records)
# print('\n', records.records_readable)


# import pandas as pd
# from datetime import datetime, timedelta
# import vectorbt as vbt
#
# price = pd.Series([1., 2., 3., 4., 3., 2., 1.])
# price.index = [datetime(2020, 1, 1) + timedelta(days=i) for i in range(len(price))]
# orders = pd.Series([1., -0.5, -0.5, 2., -0.5, -0.5, -0.5])
# pf = vbt.Portfolio.from_orders(price, orders)
# pf.trades.plot_pnl()


# df = pd.DataFrame({'A': [1, 2, 3], 'B': [4, 5, 6], 'C': [7, 8, 9]}, index=['a', 'b', 'c'])
# new_index = ['a', 'b', 'c', 'd']
# df1 = df.reindex(new_index, axis=0)
# print(df1)
#
# new_column = ['A', 'B', 'C', 'D']
# df2 = df.reindex(columns=new_column, method='ffill')
# print(df2)
#
# df3 = df.reindex(new_index, fill_value=0)
# print(df3)


# df1 = pd.DataFrame({'A': [1, 2, 3], 'B': [4, 5, 6]}, index=['a', 'b', 'c'])
# df2 = pd.DataFrame({'A': [7, 8, 9], 'B': [10, 11, 12]}, index=['b', 'c', 'd'])
# df3 = df1.reindex_like(df2)
# print(df3)
#
# df1 = pd.DataFrame({'A': [1, 2, 3], 'B': [4, 5, 6]}, index=['a', 'b', 'c'])
# df2 = pd.DataFrame({'A': [7, 8, 9], 'B': [10, 11, 12]}, index=['a', 'b', 'c'])
# df4 = df1.reindex_like(df2)
# print(df4)


# symbols = ['RBL9', 'SAL9']
# intervals = ['60m']
# for i in range(len(symbols)):
#     for j in range(len(intervals)):
#         print(symbols[i], intervals[j])


# s = pd.Series([2, 1, 3, 4, 5, 4])
# s = pd.Series([False, False, True, False, True, False])
# rs = s.rolling(3, 1).mean()
# print(rs)
# print(s[s == 4].index[0])
# print(s[s == True].index[0])
# s.iloc[0] = True
# print(s)


# param_str = "{'len': 200, 'stpr': 40, 'n': 30}"
# param_str = param_str.replace("'", '"')
# param_dict = json.loads(param_str)
# print(param_dict)


# # df1 = pd.DataFrame().add(pd.DataFrame({'A': [1, 2, 3]}, index=['a', 'b', 'c']), fill_value=0)
# # df1 = pd.DataFrame({'A': [1, 2, 3]}, index=['a', 'b', 'c'])
# df1 = pd.DataFrame({'A': [1, 2]}, index=['b', 'c'])
# # print(df1)
# # df2 = pd.DataFrame({'A': [8, 9]}, index=['b', 'c'])
# df2 = pd.DataFrame({'A': [7, 8, 9]}, index=['a', 'b', 'c'])
# # df3 = df1 + df2
# df3 = df1.add(df2, fill_value=0)
# # df4 = df1._append(df2, ignore_index=False).reset_index().drop_duplicates(subset='index', keep='last').set_index('index')
# df5 = pd.concat([df1, df2])
# print('\n', df3)
# # print('\n', df4)
# print('\n', df5)


# print(FUTURE_LIST, '\n', f'size={len(FUTURE_LIST)}')


# dict1 = {'a': 10, 'b': 8}
# dict2 = {'d': 6, 'c': 4}
# dict3 = {'e': 16, 'f': 14}
# dict1.update(dict2)
# dict1.update(dict3)
# print(f'{dict1}')
# print(f'{str(dict1)}')


# a = 10
# b = 0
# print(f'>>before test')
# c = a / b
# print(c)
# print(f'***分母为0')

# ss1 = np.array([1, 2, 3, 4, 5, 6, 7, 8, 9])
# ss2 = np.array([1, 2, 0, 4, 5, 6, 7, 8, 9])
# print(f'>>before test')
# ss3 = ss1 / ss2
# print(f'ss3={ss3}')
# ss4 = np.array([1, 2, 3, 4, 5, 6, 7, 8, 9]) * 2
# print(f'ss4={ss4}')
# print(f'{ss4 < ss3}')
# ss5 = np.array([0] * len(ss1))
# print(ss5)
# print(f'min={np.min(ss1[1:5])}')
# print(f'sum={np.sum(ss1[1:5])}')
# print(f'multiply_sum={np.sum(ss1[1:5] * ss2[1:5])}')
# print((ss1*ss2)[1:5])
# print(f'multiply_sum={np.sum((ss1*ss2)[1:5])}')


# def ndarray_test(a1: np.ndarray):
#     a1[0] = a1[0] * 2
#
#
# ndarray_test(ss1)
# print(ss1)


# 常见用途
# 需要同时访问索引和值的场景（如修改元素、记录位置）。
# 生成带索引的数据结构（如字典或元组列表）。
# 调试时跟踪元素位置。
# 通过 enumerate()，可以避免手动维护索引变量，使代码更简洁高效。
# fruits = ["apple", "banana", "cherry"]
# # for index, value in enumerate(fruits, start=11):
# #     print(f"索引 {index} 对应的水果是 {value}")
# indexed_fruits = list(enumerate(fruits, start=10))
# print(f'fruits.dtype={type(fruits)}')
# print(fruits)
# print(f'indexed_fruits.dtype={type(indexed_fruits)}')
# print(indexed_fruits)


# fl = [sym for sym in FUTURE_LIST_ALL if sym not in (FUTURE_LIST_PRECIOUS_METALS + FUTURE_LIST_NONFERROUS_METALS)]
# print(fl)


pd1 = pd.DataFrame({'A': [1, 2, 3], 'B': [4, 5, 6], 'C': [7, 8, 9]})
pd1['A'] = pd1['B'].cumsum()
print(pd1)
# sum1 = pd1.sum().iloc[1]
# print(f'sum1={sum1}, type={type(sum1)}')


# l1 = [1]
# l2 = [2, 3, 4]
# l1.append(l2)
# # l1.extend(l2)
# print(l1, f'\ntype={type(l1)}')
