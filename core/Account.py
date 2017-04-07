# -*- coding: utf-8 -*-
from core.common import *


class Account:
    def __init__(self, initial_capital=100000):
        self.initial_capital = initial_capital  # 初始资金
        self.equity = initial_capital   # 账户净值 = 已用保证金+可用保证金 = 账户余额+浮动盈亏
        self.balance = initial_capital      # 账户余额
        self.margin_used = 0    # 已用保证金
        self.margin_free = initial_capital  # 可用保证金
        self.capital_ratio = 0  # 资金使用率
        self.commission = 0     # 手续费合计

    def update(self, profit_increased, margin_increased, event_type=EVENT_TYPE_TICK_CHANGE):
        """
        不同的事件触发不同的账户变动
        :param profit_increased:
        :param margin_increased:
        :param event_type:
        :return:
        """
        if event_type == EVENT_TYPE_TICK_CHANGE:
            self.equity = self.balance + profit_increased  # 账户净值根据当前的tick变化进行计算(包含平仓手续费)
        if event_type == EVENT_TYPE_OPEN:
            self.balance = self.balance + profit_increased
            self.equity = self.balance
        if event_type == EVENT_TYPE_CLOSE:
            self.balance = self.balance + profit_increased
            self.equity = self.balance
        self.margin_used += margin_increased
        self.margin_free = self.equity - self.margin_used
        self.capital_ratio = self.margin_used/self.equity
