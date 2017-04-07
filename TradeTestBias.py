# -*- coding: utf-8 -*-
import pandas as pd
from core.common import *
from core.Symbol import SymbolRB
from core.Account import Account
from core.Engine import BacKTestEngine2
from core.Function import fn_timer
from core.Strategy import StrategyBase
from collections import deque
import datetime
import numpy as np
from core.Order import MarketOrder
import copy
import matplotlib.pyplot as plt

# 使用订单列表作为持仓进行测试


class ParameterBias:
    """
    Bias策略参数类
    """
    def __init__(self,
                 tau,
                 bias_buy_open,
                 bias_buy_close,
                 bias_sell_open,
                 bias_sell_close,
                 stop_days,
                 take_profit=10):
        self.tau = tau
        self.bias_buy_open = bias_buy_open
        self.bias_buy_close = bias_buy_close
        self.bias_sell_open = bias_sell_open
        self.bias_sell_close = bias_sell_close
        self.stop_days = stop_days
        self.take_profit = take_profit


class StrategyBias(StrategyBase):
    """
    bias策略类
    """
    def __init__(self, strategy_id, parameter, symbol):
        super().__init__(strategy_id, parameter, symbol)

        self.price = deque(maxlen=parameter.tau)
        self.stop_days = datetime.timedelta(days=self.parameter.stop_days)
        self.engine = None
        self.time = None
        self.open_flag = None

    def update_data(self, data):
        self.price.append(data.open)
        self.time = data.date_time

    def open_condition(self):
        """
        开仓条件：
            bias_current < bias_buy<0:做多入场
            bias_current > bias_short>0: 做空入场
        :return:
        """
        # 策略未达到初始化要求不允许开仓
        if len(self.price) < self.parameter.tau:
            return False
        # 当前策略持仓不允许开新仓
        if not self.engine.position_list.is_empty(self.strategy_id):
            self.open_flag = None
            return False
        ma = np.mean(self.price)
        bias_current = (self.price[-1] - ma) / ma
        # print(bias_current)

        # 反转做多
        if bias_current < self.parameter.bias_buy_open:
            self.open_flag = 'buy'
            return True
        # 反转做空
        elif bias_current > self.parameter.bias_sell_open:
            self.open_flag = 'sell'
            return True
        else:
            self.open_flag = None
            return False

    def close_condition(self, pos):
        """
        平仓条件1：
            long: bias_current > bias_buy_close
            short: bias_current < bias_sell_close
        平仓条件2：
            持仓时间超过给定时间
        平仓条件3：
            获利金额达到给定值
        平仓条件4：
            趋势反转
        :return:
        """
        # 达到指定获利
        if pos.profit > self.parameter.take_profit:
            return True
        # 达到指定持仓时间
        if pos.cal_hold_time() > self.stop_days:
            return True
        return False

    def send_order(self, order, _type):
        # 开仓订单，将其加入回测引擎开仓订单流中，等待处理
        if _type == ORDER_OPEN:
            self.engine.open_order_flow.append(order)
        # 平仓订单，将其加入回测引擎平仓订单流中，等待处理
        elif _type == ORDER_CLOSE:
            self.engine.close_order_flow.append(order)
        else:
            raise Exception('send order error: order property undefined!')

    # @fn_timer
    def run(self, data, engine):
        self.engine = engine
        self.update_data(data)
        if self.open_condition():
            if self.open_flag == 'buy':
                open_order = MarketOrder(strategy_id=self.strategy_id, symbol=self.symbol, order_type=ORDER_TYPE_BUY,
                                         send_time=self.time,  lots=1)
                print('send open_buy_order at time:', self.time)
            else:
                open_order = MarketOrder(strategy_id=self.strategy_id, symbol=self.symbol, order_type=ORDER_TYPE_SELL,
                                         send_time=self.time,  lots=1)
                print('send open_sell_order at time:', self.time)
            self.send_order(open_order, ORDER_OPEN)

        pos_ls = self.engine.position_list.get_position(strategy_id=self.strategy_id)
        if len(pos_ls) == 0:
            return
        for pos in pos_ls:
            if self.close_condition(pos):
                order_type = ORDER_TYPE_BUY if pos.position_type == POSITION_TYPE_SHORT else ORDER_TYPE_SELL
                close_order = MarketOrder(strategy_id=self.strategy_id, symbol=self.symbol, order_type=order_type,
                                          send_time=self.time,  lots=pos.lots)
                print('send close order at time:', self.time, 'equity:', self.engine.account.equity)
                self.send_order(close_order, ORDER_CLOSE)


class MyTradeTest:
    def __init__(self, data, strategy, engine):
        self.data = data
        self.strategy = strategy
        self.engine = engine
        self.account_dict = []

    def back_test(self):
        for index, row in self.data.iterrows():
            # 将当前数据存入到回测引擎中
            self.engine.current_data = row
            # 更新回测引擎中的状态--仓位信息和资金账户
            self.engine.update_engine()
            # 处理回测引擎中的订单流信息
            self.engine.handle_orders()
            # 运行每个策略
            for i, s in enumerate(self.strategy):
                    s.run(row, self.engine)
            self.account_dict.append(dict(copy.deepcopy(self.engine.account.__dict__), **{'time': row.date_time}))
        day_num = (self.account_dict[-1].get('time') - self.account_dict[0].get('time')) / np.timedelta64(1, 'D')
        total_rate = (self.engine.account.equity / self.engine.account.initial_capital) - 1
        annualized_rate = (self.engine.account.equity / self.engine.account.initial_capital) ** (365 / day_num) - 1
        print('back test OK!')
        # print('测试周期(days)', day_num, '总收益:', total_rate, '年化收益：', annualized_rate)
        return day_num, total_rate, annualized_rate

    def result_analysis(self, need_plot=False):
        res_account = pd.DataFrame(self.account_dict).set_index('time')
        equity_array = np.array(res_account['equity'])
        res_account['max_draw_down'] = [(equity_array[i:].min()-equity_array[i])/equity_array[i] for i in range(len(equity_array)) ]
        capital = res_account[['balance', 'equity']]
        if need_plot:
            plt.figure(1)
            ax1 = plt.subplot(211)
            ax2 = plt.subplot(212)
            # plt.figure(1)
            plt.sca(ax1)
            plt.plot(capital)
            plt.sca(ax2)
            plt.plot(res_account['max_draw_down'])
            plt.show()

        rate = res_account['equity'][-1]/res_account['equity'][0]-1
        max_draw_down = min(res_account['max_draw_down'])

        day_num = (self.account_dict[-1].get('time') - self.account_dict[0].get('time')) / np.timedelta64(1, 'D')
        annualized_rate = (rate + 1) ** (365 / day_num) - 1

        print('Days', day_num, 'equity at last:', res_account['equity'][-1], 'equity at begin:', res_account['equity'][0],
              'Total Rate:', rate, 'Annualized Rate:', annualized_rate, 'Max-Draw down:', max_draw_down)
        plt.savefig('test.png')
        return annualized_rate, max_draw_down


@fn_timer
def test():
    # 获取测试数据
    test_data = pd.read_csv('../Data/FutureData/rb-SHF_min.csv', nrows=100000, parse_dates=[0])
    test_data['symbol_name'] = 'rb-SHF'
    test_data.columns = BAR_DATA_COLUMN_NAMES_10
    # 回测引擎初始化
    account = Account()
    bt_engine = BacKTestEngine2(account)
    # 构建策略
    symbol = SymbolRB()
    p_bias = ParameterBias(tau=120, bias_buy_open=-0.005, bias_buy_close=0, bias_sell_open=0.005,
                           bias_sell_close=0, stop_days=0.5, take_profit=500)
    s = StrategyBias(strategy_id=1, parameter=p_bias, symbol=symbol)
    # 构建回测
    mtt = MyTradeTest(test_data, [s], bt_engine)
    print('back test begin...')
    mtt.back_test()
    print('back test end...')
    mtt.result_analysis(need_plot=True)

if __name__ == '__main__':
    test()
