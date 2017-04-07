# -*- coding: utf-8 -*-
# 账户变动事件定义
EVENT_TYPE_OPEN = 1  # 开仓事件
EVENT_TYPE_CLOSE = -1  # 平仓事件
EVENT_TYPE_TICK_CHANGE = 0      # tick数据变动事件
# 订单类别定义
ORDER_TYPE_BUY = 1     # 买多
ORDER_TYPE_SELL = -1     # 卖空
# 订单性质
ORDER_OPEN = 11
ORDER_CLOSE = -11

# 仓位类别定义
POSITION_TYPE_LONG = 1
POSITION_TYPE_SHORT = -1

# 回测数据的格式:
BAR_DATA_COLUMN_NAMES_7 = ['date_time', 'open', 'high', 'low', 'close', 'volume', 'symbol_name']
BAR_DATA_COLUMN_NAMES_10 = ['date_time', 'open', 'high', 'low', 'close', 'volume', 'turn_over', 'match_item', 'interest', 'symbol_name']