# -*- coding: utf-8 -*-
from core.Position import OrderList, Position, PositionList
from core.common import *
from core.Account import Account
import copy
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


class BacKTestEngine1:
    """
    使用订单列表作为仓位的回测引擎--后续不再使用
    """
    def __init__(self, account):
        self.account = account  # 资金账户
        self.position_list = OrderList()    # 仓位信息
        self.current_data = None    # 回测引擎每次拿到的数据
        self.order_flow = []  # 策略产生的开仓订单流

    # @fn_timer
    def update_engine(self):
        """
        更新引擎状态
            仓位信息更新
            资金账户更新
        :return:
        """
        for order in self.position_list.ol:
            if order.symbol.symbol_name == self.current_data.symbol_name:
                order.update(close_time=self.current_data.date_time, close_price=self.current_data.open)
                self.account.update(profit_increased=order.profit, margin_increased=order.margin[1]-order.margin[0],
                                    event_type=EVENT_TYPE_TICK_CHANGE)

    # @fn_timer
    def handle_orders(self):
        """
        订单流处理
        :return:
        """
        # 处理开仓订单---只处理期货市价订单
        for order in self.order_flow:
            time = self.current_data.date_time
            price = self.current_data.open
            # 开仓--买多 处理
            if order.order_type == ORDER_TYPE_BUY:
                order.open_price = price + order.symbol.slip_point
            # 开仓 -- 卖空 处理
            elif order.order_type == ORDER_TYPE_SELL:
                order.open_price = price - order.symbol.slip_point
            else:
                raise Exception('order type is not defined in common')

            order.open_time = time
            self.position_list.add(order)
            self.account.update(profit_increased=-order.commission, margin_increased=order.margin[0],
                                event_type=EVENT_TYPE_OPEN)
        # 订单流清空
        self.order_flow = []

        # 处理平仓订单
        for order in self.position_list.ol:
            if order.need_closed:
                self.account.update(profit_increased=order.profit,
                                    margin_increased=-order.margin[0],
                                    event_type=EVENT_TYPE_CLOSE)
                self.position_list.remove(order)


class BacKTestEngine2:
    """
    使用仓位列表作为仓位的回测引擎--后续不再使用
    """
    def __init__(self, account=Account()):
        self.account = account  # 资金账户
        self.position_list = PositionList()    # 仓位信息
        self.current_data = None    # 回测引擎每次拿到的数据
        self.open_order_flow = []  # 策略产生的开仓订单流
        self.close_order_flow = []  # 策略产生的平仓订单流

    # @fn_timer
    def update_engine(self):
        """
        更新引擎状态
            仓位信息更新
            资金账户更新
        :return:
        """
        for pos in self.position_list.pl:
            if pos.symbol.symbol_name == self.current_data.symbol_name:
                pos.update(close_time=self.current_data.date_time, close_price=self.current_data.open)
                self.account.update(profit_increased=pos.profit, margin_increased=pos.margin[1]-pos.margin[0],
                                    event_type=EVENT_TYPE_TICK_CHANGE)

    # @fn_timer
    def handle_orders(self):
        """
        订单流处理
        :return: 
        """
        # 开仓订单流处理---只处理期货市价订单
        for order in self.open_order_flow:
            time = self.current_data.date_time
            price = self.current_data.open
            # 开仓--买多 处理
            if order.order_type == ORDER_TYPE_BUY:
                open_price = price + order.symbol.slip_point
                position_type = POSITION_TYPE_LONG
            # 开仓 -- 卖空 处理
            elif order.order_type == ORDER_TYPE_SELL:
                open_price = price - order.symbol.slip_point
                position_type = POSITION_TYPE_SHORT
            else:
                raise Exception('order type is not defined in common')

            new_pos = Position(strategy_id=order.strategy_id, symbol=order.symbol, position_type=position_type,
                               open_time=time, open_price=open_price, lots=order.lots)
            self.position_list.add(new_pos)
            self.account.update(profit_increased=-new_pos.commission, margin_increased=new_pos.margin[0],
                                event_type=EVENT_TYPE_OPEN)
        # 开仓订单流清空
        self.open_order_flow = []

        # 平仓订单流处理
        for order in self.close_order_flow:
            for pos in self.position_list.pl:
                if pos.symbol == order.symbol and pos.strategy_id == order.strategy_id:
                    if order.lots == pos.lots:
                        b1 = order.order_type == ORDER_TYPE_BUY and pos.position_type == POSITION_TYPE_SHORT
                        b2 = order.order_type == ORDER_TYPE_SELL and pos.position_type == POSITION_TYPE_LONG
                        order_match_position = b1 or b2
                        if order_match_position:
                            self.account.update(profit_increased=pos.profit, margin_increased=-pos.margin[0],
                                                event_type=EVENT_TYPE_CLOSE)
                            self.position_list.remove(pos)
                        else:
                            raise Exception('order and position direction does not match! ')    # 订单和仓位的方向不匹配
                    else:
                        raise Exception('order lots and position lots does not match!')     # 订单和仓位的手数不一致

        self.close_order_flow = []


class BackTestEngine:
    """
    回测引擎升级--使用版本
    """
    def __init__(self, data, strategy, account=Account()):
        self.data = data    # 回测数据
        self.strategy = strategy    # 回测策略
        self.account = account      # 账户信息
        self.position_list = PositionList()     # 仓位信息

        self.current_data = None
        self.open_order_flow = []   # 策略产生的开仓订单流
        self.close_order_flow = []      # 策略产生的平仓订单流

        self.account_dict = []

    def update_engine(self):
        """
        更新引擎状态
            仓位信息更新
            资金账户更新
        :return:
        """
        for pos in self.position_list.pl:
            if pos.symbol.symbol_name == self.current_data.symbol_name:
                pos.update(close_time=self.current_data.date_time, close_price=self.current_data.open)
                self.account.update(profit_increased=pos.profit, margin_increased=pos.margin[1] - pos.margin[0],
                                    event_type=EVENT_TYPE_TICK_CHANGE)

    def handle_orders(self):
        """
        订单流处理
        :return:
        """
        # 开仓订单流处理---只处理期货市价订单
        for order in self.open_order_flow:
            time = self.current_data.date_time
            price = self.current_data.open
            # 开仓--买多 处理
            if order.order_type == ORDER_TYPE_BUY:
                open_price = price + order.symbol.slip_point
                position_type = POSITION_TYPE_LONG
            # 开仓 -- 卖空 处理
            elif order.order_type == ORDER_TYPE_SELL:
                open_price = price - order.symbol.slip_point
                position_type = POSITION_TYPE_SHORT
            else:
                raise Exception('order type is not defined in common')

            new_pos = Position(strategy_id=order.strategy_id, symbol=order.symbol, position_type=position_type,
                               open_time=time, open_price=open_price, lots=order.lots)
            self.position_list.add(new_pos)
            self.account.update(profit_increased=-new_pos.commission, margin_increased=new_pos.margin[0],
                                event_type=EVENT_TYPE_OPEN)
        # 开仓订单流清空
        self.open_order_flow = []

        # 平仓订单流处理
        for order in self.close_order_flow:
            for pos in self.position_list.pl:
                if pos.symbol == order.symbol and pos.strategy_id == order.strategy_id:
                    if order.lots == pos.lots:
                        b1 = order.order_type == ORDER_TYPE_BUY and pos.position_type == POSITION_TYPE_SHORT
                        b2 = order.order_type == ORDER_TYPE_SELL and pos.position_type == POSITION_TYPE_LONG
                        order_match_position = b1 or b2
                        if order_match_position:
                            self.account.update(profit_increased=pos.profit, margin_increased=-pos.margin[0],
                                                event_type=EVENT_TYPE_CLOSE)
                            self.position_list.remove(pos)
                        else:
                            raise Exception('order and position direction does not match! ')  # 订单和仓位的方向不匹配
                    else:
                        raise Exception('order lots and position lots does not match!')  # 订单和仓位的手数不一致

        self.close_order_flow = []

    def run(self):
        print('back test begin...')
        for index, row in self.data.iterrows():
            # 将当前数据存入到回测引擎中
            self.current_data = row
            # 更新回测引擎中的状态--仓位信息和资金账户
            self.update_engine()
            # 处理回测引擎中的订单流信息
            self.handle_orders()
            # 运行每个策略
            for i, s in enumerate(self.strategy):
                pos_to_strategy = self.position_list.get_position(s.strategy_id)
                # 传递新数据和策略相关的仓位至指定策略，返回开仓订单和平仓订单
                open_orders, close_orders = s.run(row, pos_to_strategy)
                self.open_order_flow.extend(open_orders)
                self.close_order_flow.extend(close_orders)
            # 记录账户资金变动
            self.account_dict.append(dict(copy.deepcopy(self.account.__dict__), **{'time': row.date_time}))

        day_num = (self.account_dict[-1].get('time') - self.account_dict[0].get('time')) / np.timedelta64(1, 'D')
        total_rate = (self.account.equity / self.account.initial_capital) - 1
        annualized_rate = (self.account.equity / self.account.initial_capital) ** (365 / day_num) - 1
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
            plt.savefig('test.png')
            plt.show()

        day_num = (self.account_dict[-1].get('time') - self.account_dict[0].get('time')) / np.timedelta64(1, 'D')
        rate = res_account['equity'][-1]/res_account['equity'][0]-1     # 总收益
        annualized_rate = (rate + 1) ** (365 / day_num) - 1     # 年化收益
        max_draw_down = min(res_account['max_draw_down'])   # 最大回测

        print('Days', day_num, 'equity at last:', res_account['equity'][-1], 'equity at begin:', res_account['equity'][0],
              'Total Rate:', rate, 'Annualized Rate:', annualized_rate, 'Max-Draw down:', max_draw_down)
        return annualized_rate, max_draw_down


class BackTestOptEngine(BackTestEngine):
    """
    优化迭代的回测引擎
    """
    def __init__(self, data, strategy, account=Account(),
                 init_opt_tau=(1000,), opt_frequency=(1000,)):
        super().__init__(data, strategy, account)
        self.init_opt_tau = init_opt_tau
        self.opt_frequency = opt_frequency
        self.opt_count = [0] * len(self.opt_frequency)

    def init_strategy(self):
        """
        将初始优化周期/优化间隔/优化计数等注入到策略中
        :return:
        """
        for i, s in enumerate(self.strategy):
            s.init_opt_tau = self.init_opt_tau[i]   # 初始优化周期
            s.opt_frequency = self.opt_frequency[i]  # 两次优化的时间间隔
            s.opt_count = self.opt_count[i]  # 优化计数器
            s.init_flag = False  # 参数是否初始化标志
            s.opt_begin = 0  # 优化数据的起点

    def run(self):
        print('opt back test begin...')
        self.init_strategy()
        # 遍历回测数据集
        for index, row in self.data.iterrows():
            self.current_data = row
            self.update_engine()
            self.handle_orders()
            # 遍历策略集
            for i, s in enumerate(self.strategy):
                if row.symbol_name == s.symbol.symbol_name:
                    # 当前策略参数有效 -- 使用原参数进行回测
                    if self.check_strategy_valid(s):
                        # 传递新数据和策略相关的仓位至指定策略，返回开仓订单和平仓订单
                        pos_to_strategy = self.position_list.get_position(s.strategy_id)
                        open_orders, close_orders = s.run(row, pos_to_strategy)
                        self.open_order_flow.extend(open_orders)
                        self.close_order_flow.extend(close_orders)

                    # 当前策略参数无效 -- 需要进行参数优化
                    else:
                        # 具备优化条件
                        if self.check_condition_for_opt(s):
                            # 对策略进行重新优化参数
                            data_for_opt = self.data.iloc[s.opt_begin:index, :]
                            s.opt_begin = index     # 重置下次优化数据的起点为当前点
                            pass

            # 记录账户资金变动
            self.account_dict.append(dict(copy.deepcopy(self.account.__dict__), **{'time': row.date_time}))
            day_num = (self.account_dict[-1].get('time') - self.account_dict[0].get('time')) / np.timedelta64(1, 'D')
            total_rate = (self.account.equity / self.account.initial_capital) - 1
            annualized_rate = (self.account.equity / self.account.initial_capital) ** (365 / day_num) - 1
            print('back test OK!')
            # print('测试周期(days)', day_num, '总收益:', total_rate, '年化收益：', annualized_rate)
            return day_num, total_rate, annualized_rate

    def check_strategy_valid(self, strategy):
        """
        检验策略的有效性:
            方式1：达到固定周期且空仓时，策略无效，需要重新优化参数
        :param strategy:
        :return:
        """
        # 策略尚未冷启动，未进行第一次参数优化
        if not strategy.init_flag:
            return False

        # 达到再次优化的时间且空仓时，参数无效
        if strategy.opt_count >= strategy.opt_frequency \
                and self.position_list.is_empty(strategy.strategy_id):
            strategy.opt_count = 0  # 重置优化计数器
            return False
        # 未达到重新优化的条件，参数仍有效
        else:
            strategy.opt_count += 1     # 优化计数器自增
            return True

    def check_condition_for_opt(self, strategy):
        """
        判断策略是否具备初始化条件
            策略已经冷启动过，或者策略未冷启动但是达到冷启动条件
        :param strategy:
        :return:
        """
        # 策略已经冷启动
        if strategy.init_flag:
            return True
        # 策略未冷启动，但满足冷启动要求
        if strategy.init_opt_tau <= strategy.opt_count:
            strategy.init_flag = True
            return True
        else:
            strategy.opt_count += 1
            return False
