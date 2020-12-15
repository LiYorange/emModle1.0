# -------------------------------------------------------------------------------
# Name:         grGenerator1
# Description:
# Author:       A07567
# Date:         1010/11/8
# -------------------------------------------------------------------------------
# 自定义模块区
from DAL import import_data
from DAL import base_setting
from BLL import tool
# 自定义模块区结束
import time
from PyQt5.QtCore import QThread, pyqtSignal, QObject
import gc
import copy
import numpy as np
import pyqtgraph as pg
import pandas as pd

pd.set_option('display.max_columns', None)


class Generator1(QObject):
    """
    发电机预警模型
    """
    # 类变量
    signal_ge_color = pyqtSignal(list)
    signal_ge_show_message = pyqtSignal(str)
    signal_ge_progress = pyqtSignal(dict)
    signal_ge_write_log = pyqtSignal(list)
    signal_ge_over = pyqtSignal(list)

    def __init__(self, tickets_file_path=None, import_data_path=None, df=None,
                 project_index=None, plt_list=None, draw=False):
        """
        :param tickets_file_path: 将中文标签转化为英文标签的list
        :param import_data_path: 需要处理的数据路径
        :param project_index: 选区的项目序号
        :param plt_list: 绘图对象

        """
        super(Generator1, self).__init__()

        self.draw = False
        # 初始化一个df
        self.df = pd.DataFrame()
        # 初始化标签列表
        self.tickets = []
        # 初始化缺失标签列表
        self.missing_tickets = []
        # ------------------------------------------->>>实例变量初始化
        if tickets_file_path is not None:
            self.tickets_file_path = tickets_file_path
        if import_data_path is not None:
            self.import_file_path = import_data_path
        if df is not None:
            self.df = df
        else:
            self.df = None
        if project_index is not None:
            self.project_index = project_index
        if plt_list is not None:
            self.plt_list = plt_list
        if draw:
            self.draw = draw

        # 定义一个函数执行列表，依次执行，统计函数执行进度
        self.function_list = [
            self.get_df,
            self.generator_winding_PT100,
            self.generator_winding_temperature,
            self.generator_gearbox_bearing_temperature,
            self.generator_nacelle_bearing_temperature,
            self.generator_bearing_temperature_sensor,
            self.generator_inRecycle_inlet_temperature_sensor,
            self.generator_inRecycle_outlet_temperature_sensor,
            self.generator_outRecycle_inlet_temperature_sensor,
            self.generator_outRecycle_outlet_temperature_sensor,
            self.generator_inRecycle_inlet_temperature,
            self.generator_inRecycle_outlet_temperature,
            self.generator_inRecycle_temperature_difference,
            self.generator_outRecycle_temperature_difference,
            self.over
        ]
        # ------------------------------------------->>>实例变量初始化结束

    # def __del__(self):
    #     self.wait()

    def run(self):
        self.signal_ge_show_message.emit("发电机模块已启动！")
        self.signal_ge_write_log.emit(
            [2, [-1, time.strftime('%Y{y}%m{m}%d{d} %H{h}%M{f}%S{s}').format(y='年', m='月', d='日',
                                                                             h='时', f='分', s='秒') + ":发电机模块进程开始运行"]])

        for (func, i) in zip(self.function_list, range(len(self.function_list))):
            func()
            del func
            # print(int((i + 1) / len(self.function_list) * 100))
            self.signal_ge_progress.emit({"generator": int((i + 1) / len(self.function_list) * 100)})
        self.signal_ge_show_message.emit("发电机模块计算完成！")
        del self.df
        del self.tickets
        gc.collect()

    # 获取df
    def get_df(self):
        """
        通过调用 base_setting.AutoSelectTickets得到英文标签
        通过调用import_data.ImportData得到df
        :return:
        """
        # 中文标签
        tickets_list = [
            "时间",
            "机组运行模式",
            "发电机绕组温度1",
            "发电机绕组温度2",
            "发电机绕组温度3",
            "发电机绕组温度4",
            "发电机绕组温度5",
            "发电机绕组温度6",
            "发电机齿轮箱侧轴承温度",
            "发电机机舱侧轴承温度",
            "变流器功率",
            "发电机空空冷内循环入口温度1",
            "发电机空空冷内循环入口温度2",
            "发电机空空冷内循环出口温度1",
            "发电机空空冷内循环出口温度2",
            "发电机空空冷外循环入口温度1",
            "发电机空空冷外循环入口温度2",
            "发电机空空冷外循环出口温度1",
            "发电机空空冷外循环出口温度2"
        ]
        auto_select_tickets = base_setting.AutoSelectTickets(self.tickets_file_path)
        # 得到英文标签，可能存在缺失情况！
        self.tickets = auto_select_tickets.select_tickets_by_project(self.project_index, tickets_list)
        # 如果df是None 则开启第二种模式，创建df
        if self.df is None:
            # 记录缺失位置
            for i in range(len(self.tickets)):
                if not self.tickets[i]:
                    self.missing_tickets.append(i)
            # 创建一个临时列表用于读取df，倒序移除缺失元素
            # 深拷贝 防止修改原self.tickets
            li = copy.deepcopy(self.tickets)
            for i in range(len(li) - 1, -1, -1):
                if not li[i]:
                    del li[i]

            # 记录缺失位置，用于在df中插入空列

            import__data = import_data.ImportData(self.import_file_path, li)
            self.df = import__data.handle_import_data()
            self.df.insert(0, "time", pd.to_datetime(self.df[li[0]]))
            for i in range(len(self.missing_tickets)):
                self.df.insert(self.missing_tickets[i], self.missing_tickets[i], np.nan)

    # 绘图
    def drawing(self, graphicsView=None, canvas_setting=None, data=None):
        """

        :param graphicsView: 绘图对象
        :param canvas_setting: 绘图设置
        :param data: 绘图数据
        :return:
        """
        if canvas_setting is None:
            canvas_setting = {}
        if data is None:
            data = []
        if graphicsView is not None:
            graph = graphicsView.addPlot(axisItems={'bottom': pg.DateAxisItem(orientation='bottom')},
                                         **canvas_setting)
            graph.addLegend()
            graph.showGrid(x=True, y=True)
            for data in data:
                graph.plot(**data)

    # 处理信号与日志
    def handle_signal_and_log(self, color_signal, log_signal):
        """
        :param color_signal: 为list ,包含两个数据，
                                        li[0]:第一个为需要修改的UI的颜色，值为3种类型，-1 0 1：丢失标签，预警，正常；
                                        li[1]:第二个为需要修改的UI对应的序号
        :param log_signal: 为list，包含两个数据
                                        list[0]:需要在哪个日志框内写日志
                                        li[1]:为list
                                                list[0]:用于判断日志的颜色 1 正常 0 报警 -1表示缺失
                                                list[1]:字符型日志，值示例为：齿轮箱主轴承温度正常
        :return:
        """
        self.signal_ge_color.emit(color_signal)
        log_signal[1][1] = time.strftime('%Y{y}%m{m}%d{d} %H{h}%M{f}%S{s}').format(y='年', m='月', d='日',
                                                                                   h='时', f='分', s='秒') + ":" + \
                           log_signal[1][1]
        self.signal_ge_write_log.emit(log_signal)

    # 1 发电机绕组PT100接线异常
    def generator_winding_PT100(self):
        """
        1≤机组运行模式≤14，6个发电机绕组中任意两个变量值差值的绝对值>10，且持续10min
        :return:
        """
        try:
            # 获取  时间 0 机组模式 1	发电机绕组温度1 2 发电机绕组温度2 3 发电机绕组温度3 4 发电机绕组温度4 5
            # 发电机绕组温度5 6 发电机绕组温度6 7英文标签
            # print(self.tickets)
            tickets = [self.tickets[0], self.tickets[1], self.tickets[2], self.tickets[3], self.tickets[4],
                       self.tickets[5], self.tickets[6], self.tickets[7]]
            # tickets = self.tickets

            df = self.df[['time', tickets[0], tickets[1], tickets[2], tickets[3],
                          tickets[4], tickets[5], tickets[6], tickets[7]]]
            df.set_index(df['time'], inplace=True)
        except Exception as e:
            print(e)
            print("发电机跳过函数1")
            self.handle_signal_and_log([-1, 0], [2, [-1, "发电机绕组温度英文标签丢失"]])
            return

        # 绘图
        if self.draw:
            print("发电机绘图1")
            df1 = df.copy()
            df1['timestamp'] = df[tickets[0]].apply(lambda x: time.mktime(time.strptime(x, '%Y-%m-%d %H:%M:%S')))
            self.drawing(graphicsView=self.plt_list[0],
                         canvas_setting={"title": "发电机绕组PT100接线时间图"},
                         data=[
                             {"pen": "g", "name": "发电机绕组温度1", "x": df1['timestamp'], "y": df1[tickets[2]]},
                             {"pen": "r", "name": "发电机绕组温度2", "x": df1['timestamp'], "y": df1[tickets[3]]},
                             {"pen": "b", "name": "发电机绕组温度3", "x": df1['timestamp'], "y": df1[tickets[4]]},
                             {"pen": "c", "name": "发电机绕组温度4", "x": df1['timestamp'], "y": df1[tickets[5]]},
                             {"pen": "m", "name": "发电机绕组温度5", "x": df1['timestamp'], "y": df1[tickets[6]]},
                             {"pen": "y", "name": "发电机绕组温度6", "x": df1['timestamp'], "y": df1[tickets[7]]}
                         ])
            del df1
            gc.collect()

        # 1≤机组运行模式≤14
        df = df.drop(df[(df[tickets[1]] > 14) | (df[tickets[1]] < 1)].index)
        if df.empty:
            self.handle_signal_and_log([1, 0], [2, [1, "发电机绕组PT100温度正常"]])

        else:
            # 6个发电机绕组中任意两个变量值差值的绝对值>10，且持续10min
            """
            1-2 1-3 1-4 1-5 1-6
            2-3 2-4 2-5 2-6
            3-4 -3-5 -3-6
            4-5 4-6
            5-6
            做差
            """
            # df = df.drop(df[(df[tickets[1]] != 14)].index)
            df['绕组1-绕组2'] = (df[tickets[2]] - df[tickets[3]]).abs()
            df['绕组1-绕组3'] = (df[tickets[2]] - df[tickets[4]]).abs()
            df['绕组1-绕组4'] = (df[tickets[2]] - df[tickets[5]]).abs()
            df['绕组1-绕组5'] = (df[tickets[2]] - df[tickets[6]]).abs()
            df['绕组1-绕组6'] = (df[tickets[2]] - df[tickets[7]]).abs()
            df['绕组2-绕组3'] = (df[tickets[3]] - df[tickets[4]]).abs()
            df['绕组2-绕组4'] = (df[tickets[3]] - df[tickets[5]]).abs()
            df['绕组2-绕组5'] = (df[tickets[3]] - df[tickets[6]]).abs()
            df['绕组2-绕组6'] = (df[tickets[3]] - df[tickets[7]]).abs()
            df['绕组3-绕组4'] = (df[tickets[4]] - df[tickets[5]]).abs()
            df['绕组3-绕组5'] = (df[tickets[4]] - df[tickets[6]]).abs()
            df['绕组3-绕组6'] = (df[tickets[4]] - df[tickets[7]]).abs()
            df['绕组4-绕组5'] = (df[tickets[5]] - df[tickets[6]]).abs()
            df['绕组4-绕组6'] = (df[tickets[5]] - df[tickets[7]]).abs()
            df['绕组5-绕组6'] = (df[tickets[6]] - df[tickets[7]]).abs()
            df = df.drop(df[(df["绕组1-绕组2"] <= 10) &
                            (df["绕组1-绕组3"] <= 10) &
                            (df["绕组1-绕组4"] <= 10) &
                            (df["绕组1-绕组5"] <= 10) &
                            (df["绕组1-绕组6"] <= 10) &
                            (df["绕组2-绕组3"] <= 10) &
                            (df["绕组2-绕组4"] <= 10) &
                            (df["绕组2-绕组5"] <= 10) &
                            (df["绕组2-绕组6"] <= 10) &
                            (df["绕组3-绕组4"] <= 10) &
                            (df["绕组3-绕组5"] <= 10) &
                            (df["绕组3-绕组6"] <= 10) &
                            (df["绕组4-绕组5"] <= 10) &
                            (df["绕组4-绕组6"] <= 10) &
                            (df["绕组5-绕组6"] <= 10)
                            ].index)
            if df.empty:
                self.handle_signal_and_log([1, 0], [2, [1, "发电机绕组PT100温度正常"]])

            else:

                # ------------------判断连续性 持续10min
                result = tool.duration_calculation_to_csv(tickets,
                                                          df,
                                                          600,
                                                          str(self.import_file_path).split(r'/')[-1].split('.')[0] +
                                                          '/发电机绕组PT100温度异常.csv')
                if result[0]:
                    self.handle_signal_and_log([1, 0], [2, [1, "发电机绕组PT100温度正常"]])

                else:
                    self.handle_signal_and_log([0, 0], [2, [0, "发电机绕组PT100温度异常"]])
                    self.handle_signal_and_log([0, 0], [0, [0, "发电机绕组PT100温度异常报警次数{}".format(len(result[1]))]])
                    for i in result[1]:
                        self.signal_ge_write_log.emit([2, [0, i]])
                    self.signal_ge_write_log.emit([2, [-1, "*" * 40]])

        del df
        # # 从原数据中删除 发电机绕组温度温度
        # del self.df[tickets[2]]
        del tickets
        gc.collect()

    # 2 发电机绕组温度高
    def generator_winding_temperature(self):

        """
        ：发电机绕组温度高
        ：机组运行模式 = 14，发电机绕组温度(1-6) > 105℃，持续10min
        """

        try:
            # 获取 1 时间 2 机组运行模式 3-8 发电机绕组温度(1-6) 英文标签
            # print(self.tickets)
            tickets = [self.tickets[0], self.tickets[1], self.tickets[2], self.tickets[3], self.tickets[4],
                       self.tickets[5], self.tickets[6], self.tickets[7]]
            # tickets = self.tickets

            df = self.df[['time', tickets[0], tickets[1], tickets[2], tickets[3], tickets[4], tickets[5],
                          tickets[6], tickets[7]]]
            df.set_index(df['time'], inplace=True)
        except Exception as e:
            print(e)
            print("发电机跳过函数2")
            self.handle_signal_and_log([-1, 1], [2, [-1, "发电机绕组温度英文标签丢失"]])
            return

        # 绘图
        if self.draw:
            print("发电机绘图2")
            df1 = df.copy()
            df1['timestamp'] = df[tickets[0]].apply(lambda x: time.mktime(time.strptime(x, '%Y-%m-%d %H:%M:%S')))
            self.drawing(graphicsView=self.plt_list[1],
                         canvas_setting={"title": "发电机绕组温度时间图"},
                         data=[
                             {"pen": "g", "name": "发电机绕组温度1", "x": df1['timestamp'], "y": df1[tickets[2]]},
                             {"pen": "r", "name": "发电机绕组温度2", "x": df1['timestamp'], "y": df1[tickets[3]]},
                             {"pen": "b", "name": "发电机绕组温度3", "x": df1['timestamp'], "y": df1[tickets[4]]},
                             {"pen": "c", "name": "发电机绕组温度4", "x": df1['timestamp'], "y": df1[tickets[5]]},
                             {"pen": "m", "name": "发电机绕组温度5", "x": df1['timestamp'], "y": df1[tickets[6]]},
                             {"pen": "y", "name": "发电机绕组温度6", "x": df1['timestamp'], "y": df1[tickets[7]]}
                         ])
            del df1
            gc.collect()

        # 删除 1 != 14
        df = df.drop(df[(df[tickets[1]] != 14)].index)
        if df.empty:
            self.handle_signal_and_log([1, 1], [2, [1, "发电机绕组温度正常"]])

        else:
            # 删除 2-7 全部 <= 90
            df = df.drop(df[(
                    (df[tickets[2]] <= 105) & (df[tickets[3]] <= 105) & (df[tickets[4]] <= 105) & (
                    df[tickets[5]] <= 105) & (df[tickets[6]] <= 105) & (df[tickets[7]] <= 105))].index)
            if df.empty:
                self.handle_signal_and_log([1, 1], [2, [1, "发电机绕组温度正常"]])
            else:
                # ------------------判断连续性
                result = tool.duration_calculation_to_csv(tickets,
                                                          df,
                                                          600,
                                                          str(self.import_file_path).split(r'/')[-1].split('.')[0] +
                                                          '/发电机绕组温度高.csv')
                if result[0]:
                    self.handle_signal_and_log([1, 1], [2, [1, "发电机绕组温度正常"]])

                else:
                    self.handle_signal_and_log([0, 1], [2, [0, "发电机绕组温度高"]])
                    self.handle_signal_and_log([0, 1], [0, [0, "发电机绕组温度高报警次数{}".format(len(result[1]))]])
                    for i in result[1]:
                        self.signal_ge_write_log.emit([2, [0, i]])
                    self.signal_ge_write_log.emit([2, [-1, "*" * 40]])

        del df
        # # 从原数据中删除 发电机绕组温度
        # del self.df[tickets[2]]
        del tickets
        gc.collect()

    # 3 发电机齿轮箱侧轴承温度高
    def generator_gearbox_bearing_temperature(self):

        """
        ：发电机齿轮箱侧轴承温度高
        ：12 ≤ 机组运行模式 ≤ 14，发电机齿轮箱侧轴承温度 > 83℃，持续10min
        """

        try:
            # 获取 1 时间 2 机组模式 9	发电机齿轮箱侧轴承温度 英文标签
            # print(self.tickets)
            tickets = [self.tickets[0], self.tickets[1], self.tickets[8]]
            # tickets = self.tickets

            df = self.df[['time', tickets[0], tickets[1], tickets[2]]]
            df.set_index(df['time'], inplace=True)
        except Exception as e:
            print(e)
            print("发电机跳过函数3")
            self.handle_signal_and_log([-1, 2], [2, [-1, "发电机齿轮箱侧轴承温度英文标签丢失"]])
            return

        # 绘图
        if self.draw:
            print("发电机绘图3")
            df1 = df.copy()
            df1['timestamp'] = df[tickets[0]].apply(lambda x: time.mktime(time.strptime(x, '%Y-%m-%d %H:%M:%S')))
            self.drawing(graphicsView=self.plt_list[2],
                         canvas_setting={"title": "发电机齿轮箱侧轴承温度时间图"},
                         data=[
                             {"pen": "g", "name": "发电机齿轮箱侧轴承温度", "x": df1['timestamp'], "y": df1[tickets[2]]}
                         ])
            del df1
            gc.collect()

        # 删除不在12-14之间
        df = df.drop(df[(df[tickets[1]] > 14) | (df[tickets[1]] < 12)].index)
        if df.empty:
            self.handle_signal_and_log([1, 2], [2, [1, "发电机齿轮箱侧轴承温度正常"]])

        else:
            # 删除温度小于等于83
            df = df.drop(df[(df[tickets[2]] <= 83)].index)
            if df.empty:
                self.handle_signal_and_log([1, 2], [2, [1, "发电机齿轮箱侧轴承温度正常"]])

            else:
                # ------------------判断连续性
                result = tool.duration_calculation_to_csv(tickets,
                                                          df,
                                                          600,
                                                          str(self.import_file_path).split(r'/')[-1].split('.')[0] +
                                                          '/发电机齿轮箱侧轴承温度高.csv')
                if result[0]:
                    self.handle_signal_and_log([1, 2], [2, [1, "发电机齿轮箱侧轴承温度正常"]])

                else:
                    self.handle_signal_and_log([0, 2], [2, [0, "发电机齿轮箱侧轴承温度高"]])
                    self.handle_signal_and_log([0, 2], [0, [0, "发电机齿轮箱侧轴承温度高报警次数{}".format(len(result[1]))]])
                    for i in result[1]:
                        self.signal_ge_write_log.emit([2, [0, i]])
                    self.signal_ge_write_log.emit([2, [-1, "*" * 40]])

        del df
        # # 从原数据中删除 发电机齿轮箱侧轴承温度
        # del self.df[tickets[2]]
        del tickets
        gc.collect()

    # 4 发电机机舱侧轴承温度高
    def generator_nacelle_bearing_temperature(self):

        """
        ：发电机机舱侧轴承温度高
        ：12 ≤ 机组运行模式 ≤ 14，发电机机舱侧轴承温度 > 83℃，持续10min
        """

        try:
            # 获取 1 时间 2 机组模式 10 发电机机舱侧轴承温度 英文标签
            # print(self.tickets)
            tickets = [self.tickets[0], self.tickets[1], self.tickets[9]]
            # tickets = self.tickets

            df = self.df[['time', tickets[0], tickets[1], tickets[2]]]
            df.set_index(df['time'], inplace=True)
        except Exception as e:
            print(e)
            print("发电机跳过函数4")
            self.handle_signal_and_log([-1, 3], [2, [-1, "发电机机舱侧轴承温度英文标签丢失"]])
            return

        # 绘图
        if self.draw:
            print("发电机绘图4")
            df1 = df.copy()
            df1['timestamp'] = df[tickets[0]].apply(lambda x: time.mktime(time.strptime(x, '%Y-%m-%d %H:%M:%S')))
            self.drawing(graphicsView=self.plt_list[3],
                         canvas_setting={"title": "发电机机舱侧轴承温度时间图"},
                         data=[
                             {"pen": "g", "name": "发电机机舱侧轴承温度", "x": df1['timestamp'], "y": df1[tickets[2]]}
                         ])
            del df1
            gc.collect()

        # 删除不在12-14之间
        df = df.drop(df[(df[tickets[1]] > 14) | (df[tickets[1]] < 12)].index)
        if df.empty:
            self.handle_signal_and_log([1, 3], [2, [1, "发电机机舱侧轴承温度正常"]])

        else:
            # 删除温度小于等于83
            df = df.drop(df[(df[tickets[2]] <= 83)].index)
            if df.empty:
                self.handle_signal_and_log([1, 3], [2, [1, "发电机机舱侧轴承温度正常"]])

            else:
                # ------------------判断连续性
                result = tool.duration_calculation_to_csv(tickets,
                                                          df,
                                                          600,
                                                          str(self.import_file_path).split(r'/')[-1].split('.')[0] +
                                                          '/发电机机舱侧轴承温度高.csv')
                if result[0]:
                    self.handle_signal_and_log([1, 3], [2, [1, "发电机机舱侧轴承温度正常"]])

                else:
                    self.handle_signal_and_log([0, 3], [2, [0, "发电机机舱侧轴承温度高"]])
                    self.handle_signal_and_log([0, 3], [0, [0, "发电机机舱侧轴承温度高报警次数{}".format(len(result[1]))]])
                    for i in result[1]:
                        self.signal_ge_write_log.emit([2, [0, i]])
                    self.signal_ge_write_log.emit([2, [-1, "*" * 40]])

        del df
        # # 从原数据中删除 发电机机舱侧轴承温度
        # del self.df[tickets[2]]
        del tickets
        gc.collect()

    # 5 发电机轴承温度传感器异常
    def generator_bearing_temperature_sensor(self):

        """
        ：发电机轴承温度传感器异常
        ：变流器功率 ＞ 4500KW，发电机机舱侧轴承温度 - 发电机齿轮箱侧轴承温度 ＜ 5℃，持续10min
        """

        try:
            # 获取 1 时间 11 变流器功率  10 发电机机舱侧轴承温度  9 发电机齿轮箱侧轴承温度 英文标签
            # print(self.tickets)
            tickets = [self.tickets[0], self.tickets[10], self.tickets[9], self.tickets[8]]
            # tickets = self.tickets

            df = self.df[['time', tickets[0], tickets[1], tickets[2], tickets[3]]]
            df.set_index(df['time'], inplace=True)
        except Exception as e:
            print(e)
            print("发电机跳过函数5")
            self.handle_signal_and_log([-1, 4], [2, [-1, "发电机轴承温度传感器英文标签丢失"]])
            return

        # 绘图
        if self.draw:
            print("发电机绘图5")
            df1 = df.copy()
            df1['timestamp'] = df[tickets[0]].apply(lambda x: time.mktime(time.strptime(x, '%Y-%m-%d %H:%M:%S')))
            self.drawing(graphicsView=self.plt_list[4],
                         canvas_setting={"title": "发电机轴承温度传感器时间图"},
                         data=[
                             {"pen": "g", "name": "变流器功率", "x": df1['timestamp'], "y": df1[tickets[1]]},
                             {"pen": "r", "name": "发电机机舱侧轴承温度", "x": df1['timestamp'], "y": df1[tickets[2]]},
                             {"pen": "b", "name": "发电机齿轮箱侧轴承温度", "x": df1['timestamp'], "y": df1[tickets[3]]},
                         ])
            del df1
            gc.collect()

        # 删除 1 <= 4500
        df = df.drop(df[(df[tickets[1]] <= 4500)].index)
        if df.empty:
            self.handle_signal_and_log([1, 4], [2, [1, "发电机轴承温度传感器正常"]])

        else:
            # 删除 2-3 >= 5
            df = df.drop(df[(df[tickets[2]] - df[tickets[3]] >= 5)].index)
            if df.empty:
                self.handle_signal_and_log([1, 4], [2, [1, "发电机轴承温度传感器正常"]])

            else:
                # ------------------判断连续性
                result = tool.duration_calculation_to_csv(tickets,
                                                          df,
                                                          600,
                                                          str(self.import_file_path).split(r'/')[-1].split('.')[0] +
                                                          '/发电机轴承温度传感器异常.csv')
                if result[0]:
                    self.handle_signal_and_log([1, 4], [2, [1, "发电机轴承温度传感器正常"]])

                else:
                    self.handle_signal_and_log([0, 4], [2, [0, "发电机轴承温度传感器异常"]])
                    self.handle_signal_and_log([0, 4], [0, [0, "发电机轴承温度传感器异常报警次数{}".format(len(result[1]))]])
                    for i in result[1]:
                        self.signal_ge_write_log.emit([2, [0, i]])
                    self.signal_ge_write_log.emit([2, [-1, "*" * 40]])

        del df
        # # 从原数据中删除 发电机轴承温度传感器
        # del self.df[tickets[2]]
        del tickets
        gc.collect()

    # 6 发电机内冷入口温度传感器异常
    def generator_inRecycle_inlet_temperature_sensor(self):

        """
        ：发电机内冷入口温度传感器异常
        ：机组运行模式 = 14,发电机内冷入口温度1 和 发电机内冷入口温度2的 温差绝对值 > 5℃, 持续时间1min
        """

        try:
            # 获取 1 时间 2 机组运行模式 12	发电机空空冷内循环入口温度1  13 发电机空空冷内循环入口温度2 英文标签
            # print(self.tickets)
            tickets = [self.tickets[0], self.tickets[1], self.tickets[11], self.tickets[12]]
            # tickets = self.tickets

            df = self.df[['time', tickets[0], tickets[1], tickets[2], tickets[3]]]
            df.set_index(df['time'], inplace=True)
        except Exception as e:
            print(e)
            print("发电机跳过函数6")
            self.handle_signal_and_log([-1, 5], [2, [-1, "发电机内冷入口温度传感器英文标签丢失"]])
            return

        # 绘图
        if self.draw:
            print("发电机绘图6")
            df1 = df.copy()
            df1['timestamp'] = df[tickets[0]].apply(lambda x: time.mktime(time.strptime(x, '%Y-%m-%d %H:%M:%S')))
            self.drawing(graphicsView=self.plt_list[5],
                         canvas_setting={"title": "发电机内冷入口温度传感器时间图"},
                         data=[
                             {"pen": "g", "name": "发电机空空冷内循环入口温度1", "x": df1['timestamp'], "y": df1[tickets[2]]},
                             {"pen": "r", "name": "发电机空空冷内循环入口温度2", "x": df1['timestamp'], "y": df1[tickets[3]]},
                         ])
            del df1
            gc.collect()

        # 删除 1 != 14
        df = df.drop(df[(df[tickets[1]] != 14)].index)
        if df.empty:
            self.handle_signal_and_log([1, 5], [2, [1, "发电机内冷入口温度传感器正常"]])

        else:
            # 删除 (2-3).abs <= 5℃
            df = df.drop(df[((df[tickets[2]] - df[tickets[3]]).abs() <= 5)].index)
            if df.empty:
                self.handle_signal_and_log([1, 5], [2, [1, "发电机内冷入口温度传感器正常"]])

            else:
                # ------------------判断连续性
                result = tool.duration_calculation_to_csv(tickets,
                                                          df,
                                                          60,
                                                          str(self.import_file_path).split(r'/')[-1].split('.')[0] +
                                                          '/发电机内冷入口温度传感器异常.csv')
                if result[0]:
                    self.handle_signal_and_log([1, 5], [2, [1, "发电机内冷入口温度传感器正常"]])

                else:
                    self.handle_signal_and_log([0, 5], [2, [0, "发电机内冷入口温度传感器异常"]])
                    self.handle_signal_and_log([0, 5], [0, [0, "发电机内冷入口温度传感器异常报警次数{}".format(len(result[1]))]])
                    for i in result[1]:
                        self.signal_ge_write_log.emit([2, [0, i]])
                    self.signal_ge_write_log.emit([2, [-1, "*" * 40]])

        del df
        # # 从原数据中删除 发电机内冷入口温度传感器
        # del self.df[tickets[2]]
        del tickets
        gc.collect()

    # 7 发电机内冷出口温度传感器异常
    def generator_inRecycle_outlet_temperature_sensor(self):

        """
        ：发电机内冷出口温度传感器异常
        ：机组运行模式 = 14,发电机内冷出口温度1 和 发电机内冷出口温度2的 温差绝对值 > 5℃,持续时间1min"

        """

        try:
            # 获取 1 时间 2 机组运行模式  14 发电机空空冷内循环出口温度1  15 发电机空空冷内循环出口温度2 英文标签
            # print(self.tickets)
            tickets = [self.tickets[0], self.tickets[1], self.tickets[13], self.tickets[14]]
            # tickets = self.tickets

            df = self.df[['time', tickets[0], tickets[1], tickets[2], tickets[3]]]
            df.set_index(df['time'], inplace=True)
        except Exception as e:
            print(e)
            print("发电机跳过函数7")
            self.handle_signal_and_log([-1, 6], [2, [-1, "发电机内冷出口温度传感器英文标签丢失"]])
            return

        # 绘图
        if self.draw:
            print("发电机绘图7")
            df1 = df.copy()
            df1['timestamp'] = df[tickets[0]].apply(lambda x: time.mktime(time.strptime(x, '%Y-%m-%d %H:%M:%S')))
            self.drawing(graphicsView=self.plt_list[6],
                         canvas_setting={"title": "发电机内冷出口温度传感器时间图"},
                         data=[
                             {"pen": "g", "name": "发电机空空冷内循环出口温度1", "x": df1['timestamp'], "y": df1[tickets[2]]},
                             {"pen": "r", "name": "发电机空空冷内循环出口温度2", "x": df1['timestamp'], "y": df1[tickets[3]]},
                         ])
            del df1
            gc.collect()

        # 删除 1 != 14
        df = df.drop(df[(df[tickets[1]] != 14)].index)
        if df.empty:
            self.handle_signal_and_log([1, 6], [2, [1, "发电机内冷出口温度传感器正常"]])

        else:
            # 删除 (2-3).abs() <= 5
            df = df.drop(df[((df[tickets[2]] - df[tickets[3]]).abs() <= 5)].index)
            if df.empty:
                self.handle_signal_and_log([1, 6], [2, [1, "发电机内冷出口温度传感器正常"]])

            else:
                # ------------------判断连续性
                result = tool.duration_calculation_to_csv(tickets,
                                                          df,
                                                          60,
                                                          str(self.import_file_path).split(r'/')[-1].split('.')[0] +
                                                          '/发电机内冷出口温度传感器异常.csv')
                if result[0]:
                    self.handle_signal_and_log([1, 6], [2, [1, "发电机内冷出口温度传感器正常"]])

                else:
                    self.handle_signal_and_log([0, 6], [2, [0, "发电机内冷出口温度传感器异常"]])
                    self.handle_signal_and_log([0, 6], [0, [0, "发电机内冷出口温度传感器异常报警次数{}".format(len(result[1]))]])
                    for i in result[1]:
                        self.signal_ge_write_log.emit([2, [0, i]])
                    self.signal_ge_write_log.emit([2, [-1, "*" * 40]])

        del df
        # # 从原数据中删除 发电机内冷出口温度传感器
        # del self.df[tickets[2]]
        del tickets
        gc.collect()

    # 8 发电机外冷入口温度传感器异常
    def generator_outRecycle_inlet_temperature_sensor(self):

        """
        ：发电机外冷入口温度传感器异常
        ：机组运行模式 = 14,发电机外冷入口温度1 和 发电机外冷入口温度2的 温差绝对值 > 5℃, 持续时间1min
        """

        try:
            # 获取 1 时间 2 机组运行模式 16	发电机空空冷外循环入口温度1  17 发电机空空冷外循环入口温度2 英文标签
            # print(self.tickets)
            tickets = [self.tickets[0], self.tickets[1], self.tickets[15], self.tickets[16]]
            # tickets = self.tickets

            df = self.df[['time', tickets[0], tickets[1], tickets[2], tickets[3]]]
            df.set_index(df['time'], inplace=True)
        except Exception as e:
            print(e)
            print("发电机跳过函数8")
            self.handle_signal_and_log([-1, 7], [2, [-1, "发电机外冷入口温度传感器英文标签丢失"]])
            return

        # 绘图
        if self.draw:
            print("发电机绘图8")
            df1 = df.copy()
            df1['timestamp'] = df[tickets[0]].apply(lambda x: time.mktime(time.strptime(x, '%Y-%m-%d %H:%M:%S')))
            self.drawing(graphicsView=self.plt_list[7],
                         canvas_setting={"title": "发电机外冷入口温度传感器时间图"},
                         data=[
                             {"pen": "g", "name": "发电机空空冷外循环入口温度1", "x": df1['timestamp'], "y": df1[tickets[2]]},
                             {"pen": "r", "name": "发电机空空冷外循环入口温度2", "x": df1['timestamp'], "y": df1[tickets[3]]},
                         ])
            del df1
            gc.collect()

        # 删除 1 != 14
        df = df.drop(df[(df[tickets[1]] != 14)].index)
        if df.empty:
            self.handle_signal_and_log([1, 7], [2, [1, "发电机外冷入口温度传感器正常"]])

        else:
            # 删除 (2-3).abs <= 5℃
            df = df.drop(df[((df[tickets[2]] - df[tickets[3]]).abs() <= 5)].index)
            if df.empty:
                self.handle_signal_and_log([1, 7], [2, [1, "发电机外冷入口温度传感器正常"]])

            else:
                # ------------------判断连续性
                result = tool.duration_calculation_to_csv(tickets,
                                                          df,
                                                          60,
                                                          str(self.import_file_path).split(r'/')[-1].split('.')[0] +
                                                          '/发电机外冷入口温度传感器异常.csv')
                if result[0]:
                    self.handle_signal_and_log([1, 7], [2, [1, "发电机外冷入口温度传感器正常"]])

                else:
                    self.handle_signal_and_log([0, 7], [2, [0, "发电机外冷入口温度传感器异常"]])
                    self.handle_signal_and_log([0, 7], [0, [0, "发电机外冷入口温度传感器异常报警次数{}".format(len(result[1]))]])
                    for i in result[1]:
                        self.signal_ge_write_log.emit([2, [0, i]])
                    self.signal_ge_write_log.emit([2, [-1, "*" * 40]])

        del df
        # # 从原数据中删除 发电机外冷入口温度传感器
        # del self.df[tickets[2]]
        del tickets
        gc.collect()

    # 9 发电机外冷出口温度传感器异常
    def generator_outRecycle_outlet_temperature_sensor(self):

        """
        ：发电机外冷出口温度传感器异常
        ：机组运行模式 = 14,发电机外冷出口温度1 和 发电机外冷出口温度2的 温差绝对值 > 5℃,持续时间1min"

        """

        try:
            # 获取 1 时间 2 机组运行模式  18 发电机空空冷外循环出口温度1  19 发电机空空冷外循环出口温度2 英文标签
            # 105(self.tickets)
            tickets = [self.tickets[0], self.tickets[1], self.tickets[17], self.tickets[18]]
            # tickets = self.tickets

            df = self.df[['time', tickets[0], tickets[1], tickets[2], tickets[3]]]
            df.set_index(df['time'], inplace=True)
        except Exception as e:
            print(e)
            print("发电机跳过函数9")
            self.handle_signal_and_log([-1, 8], [2, [-1, "发电机外冷出口温度传感器英文标签丢失"]])
            return

        # 绘图
        if self.draw:
            print("发电机绘图9")
            df1 = df.copy()
            df1['timestamp'] = df[tickets[0]].apply(lambda x: time.mktime(time.strptime(x, '%Y-%m-%d %H:%M:%S')))
            self.drawing(graphicsView=self.plt_list[8],
                         canvas_setting={"title": "发电机外冷出口温度传感器时间图"},
                         data=[
                             {"pen": "g", "name": "发电机空空冷外循环出口温度1", "x": df1['timestamp'], "y": df1[tickets[2]]},
                             {"pen": "r", "name": "发电机空空冷外循环出口温度2", "x": df1['timestamp'], "y": df1[tickets[3]]},
                         ])
            del df1
            gc.collect()

        # 删除 1 != 14
        df = df.drop(df[(df[tickets[1]] != 14)].index)
        if df.empty:
            self.handle_signal_and_log([1, 8], [2, [1, "发电机外冷出口温度传感器正常"]])

        else:
            # 删除 (2-3).abs() <= 5
            df = df.drop(df[((df[tickets[2]] - df[tickets[3]]).abs() <= 5)].index)
            if df.empty:
                self.handle_signal_and_log([1, 8], [2, [1, "发电机外冷出口温度传感器正常"]])

            else:
                # ------------------判断连续性
                result = tool.duration_calculation_to_csv(tickets,
                                                          df,
                                                          60,
                                                          str(self.import_file_path).split(r'/')[-1].split('.')[0] +
                                                          '/发电机外冷出口温度传感器异常.csv')
                if result[0]:
                    self.handle_signal_and_log([1, 8], [2, [1, "发电机外冷出口温度传感器正常"]])

                else:
                    self.handle_signal_and_log([0, 8], [2, [0, "发电机外冷出口温度传感器异常"]])
                    self.handle_signal_and_log([0, 8], [0, [0, "发电机外冷出口温度传感器异常报警次数{}".format(len(result[1]))]])
                    for i in result[1]:
                        self.signal_ge_write_log.emit([2, [0, i]])
                    self.signal_ge_write_log.emit([2, [-1, "*" * 40]])

        del df
        # # 从原数据中删除 发电机外冷出口温度传感器
        # del self.df[tickets[2]]
        del tickets
        gc.collect()

    # 10 发电机内冷入口温度高
    def generator_inRecycle_inlet_temperature(self):

        """
        ：发电机内冷入口温度高
        ：机组运行模式 = 14,发电机内冷入口温度1 和 发电机内冷入口温度2 任意一个 > 70℃，持续时间 1min

        """

        try:
            # 获取 1 时间 2 机组运行模式 12	发电机空空冷内循环入口温度1  13 发电机空空冷内循环入口温度2 英文标签
            # 105(self.tickets)
            tickets = [self.tickets[0], self.tickets[1], self.tickets[11], self.tickets[12]]
            # tickets = self.tickets

            df = self.df[['time', tickets[0], tickets[1], tickets[2], tickets[3]]]
            df.set_index(df['time'], inplace=True)
        except Exception as e:
            print(e)
            print("发电机跳过函数10")
            self.handle_signal_and_log([-1, 9], [2, [-1, "发电机内冷入口温度英文标签丢失"]])
            return

        # 绘图
        if self.draw:
            print("发电机绘图10")
            df1 = df.copy()
            df1['timestamp'] = df[tickets[0]].apply(lambda x: time.mktime(time.strptime(x, '%Y-%m-%d %H:%M:%S')))
            self.drawing(graphicsView=self.plt_list[9],
                         canvas_setting={"title": "发电机内冷入口温度时间图"},
                         data=[
                             {"pen": "g", "name": "发电机空空冷内循环入口温度1", "x": df1['timestamp'], "y": df1[tickets[2]]},
                             {"pen": "r", "name": "发电机空空冷内循环入口温度2", "x": df1['timestamp'], "y": df1[tickets[3]]},
                         ])
            del df1
            gc.collect()

        # 删除 1 != 14
        df = df.drop(df[(df[tickets[1]] != 14)].index)
        if df.empty:
            self.handle_signal_and_log([1, 9], [2, [1, "发电机内冷入口温度正常"]])

        else:
            # 删除 2<=70 & 3<=70
            df = df.drop(df[((df[tickets[2]] <= 70) & (df[tickets[3]] <= 70))].index)
            if df.empty:
                self.handle_signal_and_log([1, 9], [2, [1, "发电机内冷入口温度正常"]])

            else:
                # ------------------判断连续性
                result = tool.duration_calculation_to_csv(tickets,
                                                          df,
                                                          60,
                                                          str(self.import_file_path).split(r'/')[-1].split('.')[0] +
                                                          '/发电机内冷入口温度高.csv')
                if result[0]:
                    self.handle_signal_and_log([1, 9], [2, [1, "发电机内冷入口温度正常"]])

                else:
                    self.handle_signal_and_log([0, 9], [2, [0, "发电机内冷入口温度高"]])
                    self.handle_signal_and_log([0, 9], [0, [0, "发电机内冷入口温度高报警次数{}".format(len(result[1]))]])
                    for i in result[1]:
                        self.signal_ge_write_log.emit([2, [0, i]])
                    self.signal_ge_write_log.emit([2, [-1, "*" * 40]])

        del df
        # # 从原数据中删除 发电机内冷入口温度
        # del self.df[tickets[2]]
        del tickets
        gc.collect()

    # 11 发电机内冷出口温度高
    def generator_inRecycle_outlet_temperature(self):

        """
        ：发电机内冷出口温度高
        ：机组运行模式 = 14, 发电机内冷出口温度1 和 发电机内冷出口温度2 任意一个 > 60℃,持续时间1min"
        """

        try:
            # 获取 1 时间 2 机组运行模式  14 发电机空空冷内循环出口温度1  15 发电机空空冷内循环出口温度2 英文标签
            # 105(self.tickets)
            tickets = [self.tickets[0], self.tickets[1], self.tickets[13], self.tickets[14]]
            # tickets = self.tickets

            df = self.df[['time', tickets[0], tickets[1], tickets[2], tickets[3]]]
            df.set_index(df['time'], inplace=True)
        except Exception as e:
            print(e)
            print("发电机跳过函数11")
            self.handle_signal_and_log([-1, 10], [2, [-1, "发电机内冷出口温度英文标签丢失"]])
            return

        # 绘图
        if self.draw:
            print("发电机绘图11")
            df1 = df.copy()
            df1['timestamp'] = df[tickets[0]].apply(lambda x: time.mktime(time.strptime(x, '%Y-%m-%d %H:%M:%S')))
            self.drawing(graphicsView=self.plt_list[10],
                         canvas_setting={"title": "发电机内冷出口温度时间图"},
                         data=[
                             {"pen": "g", "name": "发电机空空冷内循环出口温度1", "x": df1['timestamp'], "y": df1[tickets[2]]},
                             {"pen": "r", "name": "发电机空空冷内循环出口温度2", "x": df1['timestamp'], "y": df1[tickets[3]]},
                         ])
            del df1
            gc.collect()

        # 删除 1 != 14
        df = df.drop(df[(df[tickets[1]] != 14)].index)
        if df.empty:
            self.handle_signal_and_log([1, 10], [2, [1, "发电机内冷出口温度正常"]])

        else:
            # 删除 2 <= 60 & 3 <= 60
            df = df.drop(df[((df[tickets[2]] <= 60) & (df[tickets[3]] <= 60))].index)
            if df.empty:
                self.handle_signal_and_log([1, 10], [2, [1, "发电机内冷出口温度正常"]])

            else:
                # ------------------判断连续性
                result = tool.duration_calculation_to_csv(tickets,
                                                          df,
                                                          60,
                                                          str(self.import_file_path).split(r'/')[-1].split('.')[0] +
                                                          '/发电机内冷出口温度高.csv')
                if result[0]:
                    self.handle_signal_and_log([1, 10], [2, [1, "发电机内冷出口温度正常"]])

                else:
                    self.handle_signal_and_log([0, 10], [2, [0, "发电机内冷出口温度高"]])
                    self.handle_signal_and_log([0, 10], [0, [0, "发电机内冷出口温度高报警次数{}".format(len(result[1]))]])
                    for i in result[1]:
                        self.signal_ge_write_log.emit([2, [0, i]])
                    self.signal_ge_write_log.emit([2, [-1, "*" * 40]])

        del df
        # # 从原数据中删除 发电机内冷出口温度
        # del self.df[tickets[2]]
        del tickets
        gc.collect()

    # 12 发电机内冷温差异常
    def generator_inRecycle_temperature_difference(self):

        """
        ：发电机内冷温差异常
        ：机组运行模式 = 14, 发电机绕组温度（任选一个） > 90℃,
        发电机内冷入口温度1 - 发电机内冷出口温度1 ≤ 10 或 发电机内冷入口温度2 - 发电机内冷出口温度2 ≤ 10 ，持续时间10min
        """

        try:
            # 获取 1 时间 2 机组运行模式 3-8 发电机绕组温度(1-6)
            # 12 发电机空空冷内循环入口温度1 13 发电机空空冷内循环入口温度2 14	发电机空空冷内循环出口温度1 15 发电机空空冷内循环出口温度2英文标签
            # 105(self.tickets)
            tickets = [self.tickets[0], self.tickets[1], self.tickets[2], self.tickets[3], self.tickets[4],
                       self.tickets[5], self.tickets[6], self.tickets[7], self.tickets[11], self.tickets[12],
                       self.tickets[13], self.tickets[14]]
            # tickets = self.tickets

            df = self.df[['time', tickets[0], tickets[1], tickets[2], tickets[3], tickets[4], tickets[5],
                          tickets[6], tickets[7], tickets[8], tickets[9], tickets[10], tickets[11]]]
            df.set_index(df['time'], inplace=True)
        except Exception as e:
            print(e)
            print("发电机跳过函数12")
            self.handle_signal_and_log([-1, 11], [2, [-1, "发电机内冷温差英文标签丢失"]])
            return

        # 绘图
        if self.draw:
            print("发电机绘图12")
            df1 = df.copy()
            df1['timestamp'] = df[tickets[0]].apply(lambda x: time.mktime(time.strptime(x, '%Y-%m-%d %H:%M:%S')))
            self.drawing(graphicsView=self.plt_list[11],
                         canvas_setting={"title": "发电机内冷温差时间图"},
                         data=[
                             {"pen": "g", "name": "发电机空空冷内循环入口温度1", "x": df1['timestamp'], "y": df1[tickets[8]]},
                             {"pen": "r", "name": "发电机空空冷内循环入口温度2", "x": df1['timestamp'], "y": df1[tickets[9]]},
                             {"pen": "b", "name": "发电机空空冷内循环出口温度1", "x": df1['timestamp'], "y": df1[tickets[10]]},
                             {"pen": "c", "name": "发电机空空冷内循环出口温度2", "x": df1['timestamp'], "y": df1[tickets[11]]}
                         ])
            del df1
            gc.collect()

        # 删除 1 != 14
        df = df.drop(df[(df[tickets[1]] != 14)].index)
        if df.empty:
            self.handle_signal_and_log([1, 11], [2, [1, "发电机内冷温差正常"]])

        # 删除 2-7 全部 <= 90
        df = df.drop(df[((df[tickets[2]] <= 90) & (df[tickets[3]] <= 90) & (df[tickets[4]] <= 90) & (
                df[tickets[5]] <= 90) & (df[tickets[6]] <= 90) & (df[tickets[7]] <= 90))].index)
        if df.empty:
            self.handle_signal_and_log([1, 11], [2, [1, "发电机内冷温差正常"]])

        else:
            # 删除 (8-10) > 10 & (9-11) > 10
            df = df.drop(df[((df[tickets[8]] - df[tickets[10]] > 10) & (df[tickets[9]] - df[tickets[11]] > 10))].index)
            if df.empty:
                self.handle_signal_and_log([1, 11], [2, [1, "发电机内冷温差正常"]])

            else:
                # ------------------判断连续性
                result = tool.duration_calculation_to_csv(tickets,
                                                          df,
                                                          600,
                                                          str(self.import_file_path).split(r'/')[-1].split('.')[0] +
                                                          '/发电机内冷温差异常.csv')
                if result[0]:
                    self.handle_signal_and_log([1, 11], [2, [1, "发电机内冷温差正常"]])

                else:
                    self.handle_signal_and_log([0, 11], [2, [0, "发电机内冷温差异常"]])
                    self.handle_signal_and_log([0, 11], [0, [0, "发电机内冷温差异常报警次数{}".format(len(result[1]))]])
                    for i in result[1]:
                        self.signal_ge_write_log.emit([2, [0, i]])
                    self.signal_ge_write_log.emit([2, [-1, "*" * 40]])

        del df
        # # 从原数据中删除 发电机内冷温差
        # del self.df[tickets[2]]
        del tickets
        gc.collect()

    # 13 发电机外冷温差异常
    def generator_outRecycle_temperature_difference(self):

        """
        ：发电机外冷温差异常
        ：机组运行模式 = 14, 发电机内冷入口温度1 和 发电机内冷入口温度2都 > 60℃
        发电机外冷入口温度1 - 发电机外冷出口温度1 ≤ 10 或 发电机外冷入口温度2 - 发电机外冷出口温度2 ≤ 10 ，持续时间10min
        """

        try:
            # 获取 1 时间 2 机组运行模式
            # 16 发电机空空冷外循环入口温度1 17 发电机空空冷外循环入口温度2 18	发电机空空冷外循环出口温度1 19 发电机空空冷外循环出口温度2英文标签
            # 105(self.tickets)
            tickets = [self.tickets[0], self.tickets[1], self.tickets[15], self.tickets[16],
                       self.tickets[17], self.tickets[18]]
            # tickets = self.tickets

            df = self.df[['time', tickets[0], tickets[1], tickets[2], tickets[3], tickets[4], tickets[5]]]
            df.set_index(df['time'], inplace=True)
        except Exception as e:
            print(e)
            print("发电机跳过函数13")
            self.handle_signal_and_log([-1, 12], [2, [-1, "发电机外冷温差英文标签丢失"]])
            return

        # 绘图
        if self.draw:
            print("发电机绘图13")
            df1 = df.copy()
            df1['timestamp'] = df[tickets[0]].apply(lambda x: time.mktime(time.strptime(x, '%Y-%m-%d %H:%M:%S')))
            self.drawing(graphicsView=self.plt_list[12],
                         canvas_setting={"title": "发电机外冷温差时间图"},
                         data=[
                             {"pen": "g", "name": "发电机空空冷外循环入口温度1", "x": df1['timestamp'], "y": df1[tickets[2]]},
                             {"pen": "r", "name": "发电机空空冷外循环入口温度2", "x": df1['timestamp'], "y": df1[tickets[3]]},
                             {"pen": "b", "name": "发电机空空冷外循环出口温度1", "x": df1['timestamp'], "y": df1[tickets[4]]},
                             {"pen": "c", "name": "发电机空空冷外循环出口温度2", "x": df1['timestamp'], "y": df1[tickets[5]]}
                         ])
            del df1
            gc.collect()

        # 删除 1 != 14
        df = df.drop(df[(df[tickets[1]] != 14)].index)
        if df.empty:
            self.handle_signal_and_log([1, 12], [2, [1, "发电机外冷温差正常"]])

        # 删除 2 <= 60 | 3 <= 60
        df = df.drop(df[((df[tickets[2]] <= 60) | (df[tickets[3]] <= 60))].index)
        if df.empty:
            self.handle_signal_and_log([1, 12], [2, [1, "发电机外冷温差正常"]])

        else:
            # 删除 (2-4) > 10 & (3-5) > 10
            df = df.drop(df[((df[tickets[2]] - df[tickets[4]] > 10) & (df[tickets[3]] - df[tickets[5]] > 10))].index)
            if df.empty:
                self.handle_signal_and_log([1, 12], [2, [1, "发电机外冷温差正常"]])

            else:
                # ------------------判断连续性
                result = tool.duration_calculation_to_csv(tickets,
                                                          df,
                                                          600,
                                                          str(self.import_file_path).split(r'/')[-1].split('.')[0] +
                                                          '/发电机外冷温差异常.csv')
                if result[0]:
                    self.handle_signal_and_log([1, 12], [2, [1, "发电机外冷温差正常"]])

                else:
                    self.handle_signal_and_log([0, 12], [2, [0, "发电机外冷温差异常"]])
                    self.handle_signal_and_log([0, 12], [0, [0, "发电机外冷温差异常报警次数{}".format(len(result[1]))]])
                    for i in result[1]:
                        self.signal_ge_write_log.emit([2, [0, i]])
                    self.signal_ge_write_log.emit([2, [-1, "*" * 40]])

        del df
        # # 从原数据中删除 发电机外冷温差
        # del self.df[tickets[2]]
        del tickets
        gc.collect()

    def over(self):
        # 第一个线程结束
        self.signal_ge_over.emit([2, 1])


