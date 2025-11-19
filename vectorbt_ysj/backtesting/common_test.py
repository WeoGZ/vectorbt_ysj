import pandas as pd
import datetime

# 使用字符串创建 Timedelta
# td_from_str = pd.Timedelta('2 days 3 hours 30 minutes')
td_from_str = pd.Timedelta('20.87m')
# td_from_str = pd.Timedelta('4h')
td_from_str_days = pd.Timedelta('365 days')

# 使用整数值和单位参数创建 Timedelta
td_from_int = pd.Timedelta(42, unit='h')  # 42小时

# 直接使用天、小时等参数创建 Timedelta
td_from_components = pd.Timedelta(days=2, hours=5, minutes=30)

# 使用 datetime.timedelta 对象创建 Timedelta
td_from_datetime = pd.Timedelta(datetime.timedelta(days=1, seconds=3600))

# 输出内容
print("Timedelta from string:", td_from_str)
# print("Timedelta from integer and unit:", td_from_int)
# print("Timedelta from components:", td_from_components)
# print("Timedelta from datetime.timedelta:", td_from_datetime)
print(f'>>out={td_from_str_days / td_from_str}')
