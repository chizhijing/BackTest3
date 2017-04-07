# -*- coding: utf-8 -*-
from core.common import *
from collections import deque


class OrderBase(object):
    def __init__(self, strategy_id, symbol, order_type, send_time, send_price=None, lots=1):
        self.strategy_id = strategy_id
        self.symbol = symbol
        self.order_type = order_type    # 由common中定义
        self.lots = lots
        self.send_time = send_time
        self.send_price = send_price


class MarketOrder(OrderBase):
    def __init__(self, strategy_id, symbol, order_type, send_time, lots=1):
        super(MarketOrder, self).__init__(strategy_id=strategy_id, symbol=symbol,
                                          order_type=order_type, send_time=send_time, lots=lots)


class LimitOrder(OrderBase):
    def __init__(self, symbol, order_type, send_time):
        super(LimitOrder, self).__init__(symbol, order_type, send_time)


class FutureMarketOrder:
    """
    期货订单
    """
    def __init__(self, open_time, open_price, symbol, order_type, lots=1, strategy_id=1):
        # 订单开仓时候赋值
        self.symbol = symbol  # 订单对应的品种
        self.open_time = open_time  # 订单时间
        self.open_price = open_price  # 订单开仓价格
        self.close_price = open_price   # 平仓价格
        self.close_time = open_time    # 平仓时间
        self.strategy_id = strategy_id  # 订单对应的策略id
        self.order_type = order_type  # 订单类型
        self.lots = lots  # 订单手数

        # 持仓过程或平仓时候赋值
        self.tons = lots * self.symbol.tons_per_lots  # 订单对应的吨数
        self.margin = deque(maxlen=2)  # 存放订单所需保证金队列:上一时刻和当前时刻
        self.commission = None  # 存放开平仓手续费
        self.cal_order_commission()
        self.cal_order_margin()      # 保证金开始时以开仓价计算
        self.profit = 0   # 订单获利
        self.need_closed = False     # 用来标记订单是否需要平仓

    def cal_order_margin(self):
        """
        根据开仓/平仓价格计算订单保证金：（与实际情况稍微不同，实际情况可能以成交价进行）
        :return:
        """
        order_margin = self.tons * self.close_price * self.symbol.leverage
        self.margin.append(order_margin)

    def cal_order_commission(self):
        """
        根据开仓/平仓价格计算手续费
        :return:
        """
        commission = self.tons * self.close_price * self.symbol.commission_ratio
        self.commission = commission

    def cal_order_profit(self):
        # 订单获利计算，只扣除平仓价格--方便账户更新时候计算(开仓时账户已经扣除了手续费)
        # 计算点差
        point_change = self.open_price - self.close_price
        if self.order_type == ORDER_TYPE_SELL:
            self.profit = self.tons * point_change - self.commission
        elif self.order_type == ORDER_TYPE_BUY:
            self.profit = self.tons * (-point_change) - self.commission
        else:
            raise Exception('order type are not allowed!')

    def cal_hold_time(self):
        return self.close_time - self.open_time

    def update(self, close_price, close_time):
        """
        根据平仓价格/平仓时间进行，订单信息的更新
            订单平仓价格，平仓时间，平仓获利
        :param close_price:
        :param close_time:
        :return:
        """
        # 设置当前平仓价格
        self.close_price = close_price
        self.close_time = close_time

        # 计算手续费
        self.cal_order_commission()

        # 计算获利
        self.cal_order_profit()

        # 计算保证金
        self.cal_order_margin()