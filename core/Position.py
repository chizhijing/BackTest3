# -*- coding: utf-8 -*-
from collections import deque
from core.common import *


class Position:
    def __init__(self, strategy_id, symbol, position_type, open_time, open_price, lots=1):
        self.strategy_id = strategy_id
        self.symbol = symbol
        self.position_type = position_type
        self.open_time = open_time
        self.open_price = open_price
        self.close_time = open_time
        self.close_price = open_price
        self.lots = lots

        self.margin = deque(maxlen=2)
        self.cal_position_margin()
        self.commission = self.cal_position_commission()
        self.profit = 0

    def cal_position_margin(self):
        """
        计算当前仓位的保证金
        :return:
        """
        tons = self.lots * self.symbol.tons_per_lots
        position_margin = tons * self.close_price * self.symbol.leverage
        self.margin.append(position_margin)

    def cal_position_commission(self):
        """
        计算手续费
        :return:
        """
        return self.lots * self.symbol.tons_per_lots * self.close_price * self.symbol.commission_ratio

    def cal_position_profit(self):
        """
        计算当前仓位的浮动获利:
            点差盈利扣除平仓手续费(这里不考虑开仓手续费)
        :return:
        """
        point_change = self.open_price - self.close_price
        if self.position_type == POSITION_TYPE_SHORT:
            self.profit = self.lots * self.symbol.tons_per_lots * point_change - self.cal_position_commission()
        elif self.position_type == POSITION_TYPE_LONG:
            self.profit = self.lots * self.symbol.tons_per_lots * (-point_change) - self.cal_position_commission()
        else:
            raise Exception('wrong position type!')

    def cal_hold_time(self):
        """
        计算持仓时间
        :return:
        """
        return self.close_time - self.open_time

    def update(self, close_time, close_price):
        """
        根据新来的价格，对仓位进行更新
        :param close_time:
        :param close_price:
        :return:
        """
        self.close_time = close_time
        self.close_price = close_price

        self.cal_position_profit()
        self.cal_position_margin()


class OrderList:
    """
    使用order列表作为仓位列表
    """
    def __init__(self):
        self.ol = []

    def add(self, order):
        self.ol.append(order)

    def remove(self, order):
        self.ol.remove(order)

    def is_empty(self, strategy_id='all'):
        """
        判断仓位是否为空
        :param strategy_id:'all', [1,2,3]
        :return:
        """
        if strategy_id == 'all':
            return True if len(self.ol) == 0 else False
        else:
            return True if len(self.get_orders(strategy_id)) == 0 else False

    def get_orders(self, strategy_id):
        """
        返回给定对应策略id的订单列表
        :param strategy_id:
        :return:
        """
        ol_ls = []
        for order in self.ol:
            if type(strategy_id) == list:   # 计算多个策略的订单持仓
                if order.strategy_id in strategy_id:
                    ol_ls.append(order)
            else:   # 计算单个策略的订单持仓
                if order.strategy_id == strategy_id:
                    ol_ls.append(order)
        return ol_ls


class PositionList:
    """
    仓位列表
    """
    def __init__(self):
        self.pl = []

    def add(self, pos):
        self.pl.append(pos)

    def remove(self, pos):
        self.pl.remove(pos)

    def is_empty(self, strategy_id='all'):
        """
        判断仓位是否为空
        :param strategy_id:'all', [1,2,3]
        :return:
        """
        if strategy_id == 'all':
            return True if len(self.pl) == 0 else False
        else:
            return True if len(self.get_position(strategy_id)) == 0 else False

    def get_position(self, strategy_id):
        """
        返回给定对应策略id的订单列表
        :param strategy_id:
        :return:
        """
        pos_ls = []
        for pos in self.pl:
            if type(strategy_id) == list:   # 计算多个策略的订单持仓
                if pos.strategy_id in strategy_id:
                    pos_ls.append(pos)
            else:   # 计算单个策略的订单持仓
                if pos.strategy_id == strategy_id:
                    pos_ls.append(pos)
        return pos_ls
