import datetime
from collections import deque
import numpy as np
from core.Account import Account
from core.Engine import BackTestEngine
from core.Order import MarketOrder
from core.Strategy import StrategyBase
from core.Symbol import SymbolRB
from core.common import *
from data_manager.DataEngine import get_future_data


class ParameterBoll:
    """
    策略参数类
    """
    def __init__(self, tau=120, delta=2, take_profit=5000, stop_days=14):
        self.tau = tau
        self.delta = delta
        self.take_profit = take_profit
        self.stop_days = stop_days


class StrategyBoll(StrategyBase):
    """
    策略类
    """
    def __init__(self, strategy_id, parameter, symbol):
        super().__init__(strategy_id, parameter, symbol)
        self.price = deque(maxlen=parameter.tau)
        self.stop_days = datetime.timedelta(days=self.parameter.stop_days)
        self.time = None
        self.open_flag = None
        self.position_ls = None

    def update(self, data, pos_ls):
        self.price.append(data.open)
        self.time = data.date_time
        self.position_ls = pos_ls

    def open_condition(self):
        """
        开仓条件：
            价格突破布林带mean(tau)±delta*sigma(tau),做趋势
        :return:
        """
        # 策略未达到初始化要求不允许开仓
        if len(self.price) < self.parameter.tau:
            return False

        # 当前策略持仓不允许开新仓
        if not len(self.position_ls) == 0:
            self.open_flag = None
            return False

        mean = np.mean(self.price)
        std = np.std(self.price)
        # 向上趋势突破
        if self.price[-1] > mean + std*self.parameter.delta:
            self.open_flag = 'buy'
            return True
        # 向下趋势突破
        elif self.price[-1] < mean - std*self.parameter.delta:
            self.open_flag = 'sell'
            return True
        else:
            self.open_flag = None
            return False

    def close_condition(self, pos):
        """
        平仓条件：
            仓位获利达到指定值
            持仓时间超过一定时间
        :return:
        """
        # 达到指定获利
        if pos.profit > self.parameter.take_profit:
            return True
        # 达到指定持仓时间
        if pos.cal_hold_time() > self.stop_days:
            return True
        return False

    # @fn_timer
    def run(self, data_new, pos_ls):
        open_order_flow = []
        close_order_flow = []
        # 更新策略状态 -- 数据和仓位等
        self.update(data_new, pos_ls)

        # 开仓判断--产生开仓订单
        if self.open_condition():
            if self.open_flag == 'buy':
                open_order = MarketOrder(strategy_id=self.strategy_id, symbol=self.symbol, order_type=ORDER_TYPE_BUY,
                                         send_time=self.time,  lots=1)
                print('send open_buy_order at time:', self.time)
            else:
                open_order = MarketOrder(strategy_id=self.strategy_id, symbol=self.symbol, order_type=ORDER_TYPE_SELL,
                                         send_time=self.time,  lots=1)
                print('send open_sell_order at time:', self.time)
            open_order_flow.append(open_order)

        # 当前策略空仓无需平仓
        if len(self.position_ls) == 0:
            return open_order_flow, close_order_flow

        # 平仓判断
        for pos in self.position_ls:
            if self.close_condition(pos):
                order_type = ORDER_TYPE_BUY if pos.position_type == POSITION_TYPE_SHORT else ORDER_TYPE_SELL
                close_order = MarketOrder(strategy_id=self.strategy_id, symbol=self.symbol, order_type=order_type,
                                          send_time=self.time,  lots=pos.lots)
                print('send close order at time:', self.time)
                close_order_flow.append(close_order)

        return open_order_flow, close_order_flow


if __name__ == '__main__':
    data = get_future_data(path='../Data/FutureData/', nrows=100000)
    s = StrategyBoll(strategy_id=1, parameter=ParameterBoll(), symbol=SymbolRB())
    account = Account(initial_capital=100000)
    bt = BackTestEngine(data=data, strategy=[s], account=account)
    bt.run()
    bt.result_analysis()
