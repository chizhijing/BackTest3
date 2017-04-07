# -*- coding: utf-8 -*-


class StrategyBase(object):
    def __init__(self, strategy_id, parameter, symbol):
        """
        策略初始化参数
        """
        self.strategy_id = strategy_id
        self.parameter = parameter
        self.symbol = symbol

    def open_condition(self):
        """
        开仓条件
        :return:
        """
        pass

    def close_condition(self, pos):
        """
        平仓条件
        :return:
        """
        pass

    def run(self, data, pos_ls):
        pass
