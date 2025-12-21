import calendar
from datetime import datetime


def get_quarter_end_date(d: datetime) -> datetime:
    """获取季度末的日期，时间固定为15:00:00"""
    month = d.month
    quarter_end_month = 3
    if 3 < month <= 6:
        quarter_end_month = 6
    elif 6 < month <= 9:
        quarter_end_month = 9
    elif 9 < month <= 12:
        quarter_end_month = 12

    _, num_of_month = calendar.monthrange(d.year, quarter_end_month)

    return datetime(d.year, quarter_end_month, num_of_month, 15, 0, 0, 0)


def convert2_datetime_str(d: datetime) -> str:
    return d.strftime("%Y-%m-%d %H:%M:%S")


def convert2_date_str(d: datetime) -> str:
    return d.strftime("%Y-%m-%d")
