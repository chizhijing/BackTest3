import pandas as pd
from core.common import *
import os


# 获取测试数据
def get_future_data(file_name='rb-SHF_min.csv', symbol_name='rb-SHF', path='../../Data/FutureData/', nrows=10000):
    _data = pd.read_csv(path+file_name, nrows=nrows, parse_dates=[0])
    _data['symbol_name'] = symbol_name
    _data.columns = BAR_DATA_COLUMN_NAMES_10
    return _data

if __name__ == '__main__':
    # data = pd.read_csv('..\\..\\Data\\FutureData\\' + 'rb-SHF_min.csv', nrows=10000, parse_dates=[0])
    get_future_data()
