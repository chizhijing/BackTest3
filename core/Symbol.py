# -*- coding: utf-8 -*-
class FutureSymbol:
    def __init__(self, symbol_name, commission, tons_per_lots, slip_point):
        self.symbol_name = symbol_name
        self.MinLots = 1  # 最小手数
        self.MaxLots = 100  # 最大手数
        self.leverage = 0.2  # 保证金比例
        self.commission_ratio = 0.00025  # 手续费
        self.tons_per_lots = 20  # 每手对应的吨数，价格序列对应的是一吨的
        self.slip_point = 1


class SymbolRB(FutureSymbol):
    def __init__(self, symbol_name='rb-SHF', commission=0.00025, tons_per_lots=20, slip_point=1):
        super().__init__(symbol_name, commission, tons_per_lots, slip_point)


class SymbolI(FutureSymbol):
    def __init__(self, symbol_name='i-DCE', commission=0.00025, tons_per_lots=100, slip_point=0.5):
        super().__init__(symbol_name, commission, tons_per_lots, slip_point)