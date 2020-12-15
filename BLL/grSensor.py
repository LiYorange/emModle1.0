# -------------------------------------------------------------------------------
# Name:         grSensor1
# Description:
# Author:       A07567
# Date:         2020/11/8
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


class Sensor1(QObject):
    """
    传感器预警模型
    """
    # 类变量
    signal_se_color = pyqtSignal(list)
    signal_se_show_message = pyqtSignal(str)
    signal_se_progress = pyqtSignal(dict)
    signal_se_write_log = pyqtSignal(list)
    signal_se_over = pyqtSignal(list)

    def __init__(self, tickets_file_path=None, import_data_path=None, df=None,
                 project_index=None, plt_list=None, draw=False):
        """
        :param tickets_file_path: 将中文标签转化为英文标签的list
        :param import_data_path: 需要处理的数据路径
        :param project_index: 选区的项目序号
        :param plt_list: 绘图对象

        """
        super(Sensor1, self).__init__()
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
            self.sensor_tower_base_transformer_temperature,
            self.sensor_tower_base_cabinet_temperature,
            self.sensor_tower_cabin_heart,
            self.sensor_nacelle_power_distribution_cabinet_temperature,
            self.sensor_nacelle_cabin_heart,
            self.sensor_nacelle_signal_cabinet_temperature,
            self.sensor_nacelle_signal_cabinet_heart,
            self.sensor_yaw_driver_cabinet_temperature,
            self.over
        ]
        # ------------------------------------------->>>实例变量初始化结束

    def run(self):

        self.signal_se_show_message.emit("传感器模块已启动！")
        self.signal_se_write_log.emit([6, [-1,
                                           time.strftime('%Y{y}%m{m}%d{d} %H{h}%M{f}%S{s}').format(y='年', m='月', d='日',
                                                                                                   h='时', f='分',
                                                                                                   s='秒') + ":传感器模块进程开始运行"]])

        for (func, i) in zip(self.function_list, range(len(self.function_list))):
            func()
            del func
            # print(int((i + 1) / len(self.function_list) * 100))
            self.signal_se_progress.emit({"sensor": int((i + 1) / len(self.function_list) * 100)})
        self.signal_se_show_message.emit("传感器模块计算完成！")
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
        tickets_list = ["时间",
                        "机组运行模式",
                        "齿轮箱主轴承温度",
                        "齿轮箱轮毂侧轴承温度",
                        "齿轮箱发电机侧轴承温度",
                        "齿轮箱油温",
                        "齿轮箱离线过滤泵处油温",
                        "齿轮箱主泵处油温",
                        "润滑油冷却器入口油温",
                        "润滑油冷却器出口油温",
                        "齿轮箱水泵出口温度",
                        "齿轮箱水泵入口温度1",
                        "齿轮箱水泵入口温度2",
                        "齿轮箱A1口温度",
                        "齿轮箱A2口温度",
                        "齿轮箱A3口温度",
                        "齿轮箱A4口温度",
                        "齿轮箱主泵1_1高速",
                        "齿轮箱主泵1_2高速",
                        "齿轮箱主泵1_1低速",
                        "齿轮箱主泵1_2低速",
                        "齿轮箱A1口压力",
                        "齿轮箱主泵2_1高速",
                        "齿轮箱主泵2_2高速",
                        "齿轮箱主泵2_1低速",
                        "齿轮箱主泵2_2低速",
                        "齿轮箱A2口压力",
                        "齿轮箱A3口压力",
                        "发电机润滑泵3_1",
                        "发电机润滑泵3_2",
                        "齿轮箱A4口压力",
                        "齿轮箱主泵1_1出口压力",
                        "齿轮箱主泵1_2出口压力",
                        "齿轮箱主泵2_1出口压力",
                        "齿轮箱主泵2_2出口压力",
                        "齿轮箱冷却泵出口压力",
                        "齿轮箱冷却泵",
                        "齿轮箱过滤泵",
                        "齿轮箱过滤泵出口压力",
                        "齿轮箱油位",
                        "齿轮箱水泵1启动",
                        "齿轮箱水冷风扇1高速启动",
                        "齿轮箱水泵2启动",
                        "齿轮箱水冷风扇2高速启动",
                        "齿轮箱水泵1出口压力",
                        "齿轮箱水泵1入口压力",
                        "齿轮箱水泵2出口压力",
                        "齿轮箱水泵2入口压力",

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
        self.signal_se_color.emit(color_signal)
        log_signal[1][1] = time.strftime('%Y{y}%m{m}%d{d} %H{h}%M{f}%S{s}').format(y='年', m='月', d='日',
                                                                                   h='时', f='分', s='秒') + ":" + \
                           log_signal[1][1]
        self.signal_se_write_log.emit(log_signal)

    # 1 塔基变压器温度异常
    def sensor_tower_base_transformer_temperature(self):

        """
        ：塔基变压器温度异常
        ：塔基变压器温度≠0时，塔基变压器温度>80℃或者<10℃，持续1min
        """

        try:
            # 获取 1 时间 3 塔基变压器温度 英文标签
            # print(self.tickets)
            tickets = [self.tickets[0], self.tickets[2]]
            # tickets = self.tickets

            df = self.df[['time', tickets[0], tickets[1]]]
            df.set_index(df['time'], inplace=True)
        except Exception as e:
            print(e)
            print("传感器跳过函数1")
            # self.handle_signal_and_log([-1, 0], "塔基变压器温度英文标签丢失")
            self.handle_signal_and_log([-1, 0], [6, [-1, "塔基变压器温度英文标签丢失"]])
            return

        if self.draw:
            print("传感器绘图1")
            df1 = df.copy()
            df1.resample('30T').mean()
            df1['timestamp'] = df[tickets[0]].apply(lambda x: time.mktime(time.strptime(x, '%Y-%m-%d %H:%M:%S')))
            self.drawing(graphicsView=self.plt_list[0],
                         canvas_setting={"title": "塔基变压器温度时间图"},
                         data=[
                             {"pen": "g", "name": "塔基变压器温度", "x": df1['timestamp'], "y": df1[tickets[1]]},
                         ])
            del df1
            gc.collect()

        # 删除 1=0
        df = df.drop(df[(df[tickets[1]] == 0)].index)
        if df.empty:
            # self.handle_signal_and_log([1, 0], "塔基变压器温度正常")
            self.handle_signal_and_log([1, 0], [6, [1, "塔基变压器温度正常"]])

        else:
            # 删除 1>= 10 & 1<= 80
            df = df.drop(df[((df[tickets[1]] <= 80) & (df[tickets[1]] >= 10))].index)
            if df.empty:
                self.handle_signal_and_log([1, 0], [6, [1, "塔基变压器温度正常"]])

            else:
                # ------------------判断连续性
                result = tool.duration_calculation_to_csv(tickets,
                                                          df,
                                                          60,
                                                          str(self.import_file_path).split(r'/')[-1].split('.')[0] +
                                                          '/塔基变压器温度异常.csv')
                if result[0]:
                    # self.handle_signal_and_log([1, 0], "塔基变压器温度正常")
                    self.handle_signal_and_log([1, 0], [6, [1, "塔基变压器温度正常"]])

                else:
                    # self.handle_signal_and_log([0, 0], "塔基变压器温度异常")
                    self.handle_signal_and_log([0, 0], [6, [0, "塔基变压器温度异常"]])
                    self.handle_signal_and_log([0, 0], [0, [0, "塔基变压器温度异常报警次数{}".format(len(result[1]))]])
                    for i in result[1]:
                        self.signal_se_write_log.emit([6, [0, i]])
                    self.signal_se_write_log.emit([6, [-1, "*" * 40]])

        del df
        # # 从原数据中删除 塔基变压器温度
        # del self.df[tickets[2]]
        del tickets
        gc.collect()

    # 2 塔基柜温度异常
    def sensor_tower_base_cabinet_temperature(self):

        """
        ：塔基柜温度异常
        ：11≤ 机组运行模式 ≤14，塔基控制柜温度 > 45°，且塔基第一层温度 < 40°，且异常持续时间超过 5min
        """

        try:
            # 获取 1 时间 2 机组运行模式 4	塔筒第一层平台温度 5 塔基柜温度 英文标签
            # print(self.tickets)
            tickets = [self.tickets[0], self.tickets[1], self.tickets[3], self.tickets[4]]
            # tickets = self.tickets

            df = self.df[['time', tickets[0], tickets[1], tickets[2], tickets[3]]]
            df.set_index(df['time'], inplace=True)
        except Exception as e:
            print(e)
            print("跳过函数2")
            self.handle_signal_and_log([-1, 1], [6, [-1, "塔基柜温度英文标签丢失"]])
            return

        if self.draw:
            print("传感器绘图2")
            df1 = df.copy()
            df1.resample('30T').mean()
            df1['timestamp'] = df[tickets[0]].apply(lambda x: time.mktime(time.strptime(x, '%Y-%m-%d %H:%M:%S')))
            self.drawing(graphicsView=self.plt_list[1],
                         canvas_setting={"title": "塔基柜温度时间图"},
                         data=[
                             {"pen": "g", "name": "塔筒第一层平台温度", "x": df1['timestamp'], "y": df1[tickets[2]]},
                             {"pen": "r", "name": "塔基柜温度", "x": df1['timestamp'], "y": df1[tickets[3]]}
                         ])
            del df1
            gc.collect()

        # 删除 1>14 | 1<11
        df = df.drop(df[((df[tickets[1]] > 14) & (df[tickets[1]] < 11))].index)
        if df.empty:
            self.handle_signal_and_log([1, 1], [6, [1, "塔基柜温度正常"]])

        else:
            # 删除 2<=45 | 3>=40
            df = df.drop(df[((df[tickets[2]] <= 45) & (df[tickets[3]] >= 40))].index)
            if df.empty:
                self.handle_signal_and_log([1, 1], [6, [1, "塔基柜温度正常"]])

            else:
                # ------------------判断连续性
                result = tool.duration_calculation_to_csv(tickets,
                                                          df,
                                                          300,
                                                          str(self.import_file_path).split(r'/')[-1].split('.')[0] +
                                                          '/塔基柜温度异常.csv')
                if result[0]:
                    self.handle_signal_and_log([1, 1], [6, [1, "塔基柜温度正常"]])

                else:
                    self.handle_signal_and_log([0, 1], [6, [0, "塔基柜温度异常"]])
                    self.handle_signal_and_log([0, 1], [0, [0, "塔基柜温度异常报警次数{}".format(len(result[1]))]])
                    for i in result[1]:
                        self.signal_se_write_log.emit([6, [0, i]])
                    self.signal_se_write_log.emit([6, [-1, "*" * 40]])

        del df
        # # 从原数据中删除 塔基柜温度
        # del self.df[tickets[2]]
        del tickets
        gc.collect()

    # 3 塔基柜加热器异常
    def sensor_tower_cabin_heart(self):

        """
        ：塔基柜加热器异常
        ：11≤ 机组运行模式 ≤14，塔基控制柜温度 < 5℃，持续3min
        """

        try:
            # 获取 1 时间 2 机组运行模式 5 塔基柜温度 英文标签
            # print(self.tickets)
            tickets = [self.tickets[0], self.tickets[1], self.tickets[4]]
            # tickets = self.tickets

            df = self.df[['time', tickets[0], tickets[1], tickets[2]]]
            df.set_index(df['time'], inplace=True)
        except Exception as e:
            print(e)
            print("跳过函数3")
            self.handle_signal_and_log([-1, 2], [6, [-1, "塔基柜加热器英文标签丢失"]])
            return

        if self.draw:
            print("传感器绘图3")
            df1 = df.copy()
            df1.resample('30T').mean()
            df1['timestamp'] = df[tickets[0]].apply(lambda x: time.mktime(time.strptime(x, '%Y-%m-%d %H:%M:%S')))
            self.drawing(graphicsView=self.plt_list[2],
                         canvas_setting={"title": "塔基柜加热器时间图"},
                         data=[
                             {"pen": "g", "name": "塔基柜温度", "x": df1['timestamp'], "y": df1[tickets[2]]}
                         ])
            del df1
            gc.collect()

        # 删除 1>14 | 1<11
        df = df.drop(df[((df[tickets[1]] > 14) & (df[tickets[1]] < 11))].index)
        if df.empty:
            self.handle_signal_and_log([1, 2], [6, [1, "塔基柜加热器正常"]])

        else:
            # 删除 2>=5
            df = df.drop(df[(df[tickets[2]] >= 5)].index)
            if df.empty:
                self.handle_signal_and_log([1, 2], [6, [1, "塔基柜加热器正常"]])

            else:
                # ------------------判断连续性
                result = tool.duration_calculation_to_csv(tickets,
                                                          df,
                                                          180,
                                                          str(self.import_file_path).split(r'/')[-1].split('.')[0] +
                                                          '/塔基柜加热器异常.csv')
                if result[0]:
                    self.handle_signal_and_log([1, 2], [6, [1, "塔基柜加热器正常"]])

                else:
                    self.handle_signal_and_log([0, 2], [6, [0, "塔基柜加热器异常"]])
                    self.handle_signal_and_log([0, 2], [0, [0, "塔基柜加热器异常报警次数{}".format(len(result[1]))]])
                    for i in result[1]:
                        self.signal_se_write_log.emit([6, [0, i]])
                    self.signal_se_write_log.emit([6, [-1, "*" * 40]])

        del df
        # # 从原数据中删除 塔基柜加热器
        # del self.df[tickets[2]]
        del tickets
        gc.collect()

    # 4 机舱动力柜温度异常
    def sensor_nacelle_power_distribution_cabinet_temperature(self):

        """
        ：机舱动力柜温度异常
        ：11≤机组运行模式≤14，机舱动力柜温度>45°，且机舱温度<40°，且异常持续时间超过5min
        """

        try:
            # 获取 1 时间 2 机组运行模式 6 机舱高压柜温度 7 机舱温度 英文标签
            # print(self.tickets)
            tickets = [self.tickets[0], self.tickets[1], self.tickets[5], self.tickets[6]]
            # tickets = self.tickets

            df = self.df[['time', tickets[0], tickets[1], tickets[2], tickets[3]]]
            df.set_index(df['time'], inplace=True)
        except Exception as e:
            print(e)
            print("跳过函数4")
            self.handle_signal_and_log([-1, 3], [6, [-1, "机舱动力柜温度英文标签丢失"]])
            return

        if self.draw:
            print("传感器绘图4")
            df1 = df.copy()
            df1.resample('30T').mean()
            df1['timestamp'] = df[tickets[0]].apply(lambda x: time.mktime(time.strptime(x, '%Y-%m-%d %H:%M:%S')))
            self.drawing(graphicsView=self.plt_list[3],
                         canvas_setting={"title": "机舱动力柜温度时间图"},
                         data=[
                             {"pen": "g", "name": "机舱高压柜温度", "x": df1['timestamp'], "y": df1[tickets[2]]},
                             {"pen": "r", "name": "机舱温度", "x": df1['timestamp'], "y": df1[tickets[3]]}
                         ])
            del df1
            gc.collect()

        # 删除 1>14 | 1<11
        df = df.drop(df[((df[tickets[1]] > 14) & (df[tickets[1]] < 11))].index)
        if df.empty:
            self.handle_signal_and_log([1, 3], [6, [1, "机舱动力柜温度正常"]])

        else:
            # 删除 2<=45 | 3>=40
            df = df.drop(df[((df[tickets[2]] <= 45) & (df[tickets[3]] >= 40))].index)
            if df.empty:
                self.handle_signal_and_log([1, 3], [6, [1, "机舱动力柜温度正常"]])

            else:
                # ------------------判断连续性
                result = tool.duration_calculation_to_csv(tickets,
                                                          df,
                                                          300,
                                                          str(self.import_file_path).split(r'/')[-1].split('.')[0] +
                                                          '/机舱动力柜温度异常.csv')
                if result[0]:
                    self.handle_signal_and_log([1, 3], [6, [1, "机舱动力柜温度正常"]])

                else:
                    self.handle_signal_and_log([0, 3], [6, [0, "机舱动力柜温度异常"]])
                    self.handle_signal_and_log([0, 3], [0, [0, "机舱动力柜温度异常报警次数{}".format(len(result[1]))]])
                    for i in result[1]:
                        self.signal_se_write_log.emit([6, [0, i]])
                    self.signal_se_write_log.emit([6, [-1, "*" * 40]])

        del df
        # # 从原数据中删除 机舱动力柜温度
        # del self.df[tickets[2]]
        del tickets
        gc.collect()

    # 5 机舱动力柜加热器异常
    def sensor_nacelle_cabin_heart(self):

        """
        ：机舱动力柜加热器异常
        ：11≤ 机组运行模式 ≤14，塔基控制柜温度 < 5℃，持续3min
        """

        try:
            # 获取 1 时间 2 机组运行模式 6 机舱高压柜温度 英文标签
            # print(self.tickets)
            tickets = [self.tickets[0], self.tickets[1], self.tickets[5]]
            # tickets = self.tickets

            df = self.df[['time', tickets[0], tickets[1], tickets[2]]]
            df.set_index(df['time'], inplace=True)
        except Exception as e:
            print(e)
            print("跳过函数5")
            self.handle_signal_and_log([-1, 4], [6, [-1, "机舱动力柜加热器英文标签丢失"]])
            return

        if self.draw:
            print("传感器绘图5")
            df1 = df.copy()
            df1.resample('30T').mean()
            df1['timestamp'] = df[tickets[0]].apply(lambda x: time.mktime(time.strptime(x, '%Y-%m-%d %H:%M:%S')))
            self.drawing(graphicsView=self.plt_list[4],
                         canvas_setting={"title": "机舱动力柜加热器时间图"},
                         data=[
                             {"pen": "g", "name": "机舱高压柜温度", "x": df1['timestamp'], "y": df1[tickets[2]]}
                         ])
            del df1
            gc.collect()

        # 删除 1>14 | 1<11
        df = df.drop(df[((df[tickets[1]] > 14) & (df[tickets[1]] < 11))].index)
        if df.empty:
            self.handle_signal_and_log([1, 4], [6, [1, "机舱动力柜加热器正常"]])

        else:
            # 删除 2>=5
            df = df.drop(df[(df[tickets[2]] >= 5)].index)
            if df.empty:
                self.handle_signal_and_log([1, 4], [6, [1, "机舱动力柜加热器正常"]])

            else:
                # ------------------判断连续性
                result = tool.duration_calculation_to_csv(tickets,
                                                          df,
                                                          180,
                                                          str(self.import_file_path).split(r'/')[-1].split('.')[0] +
                                                          '/机舱动力柜加热器异常.csv')
                if result[0]:
                    self.handle_signal_and_log([1, 4], [6, [1, "机舱动力柜加热器正常"]])

                else:
                    self.handle_signal_and_log([0, 4], [6, [0, "机舱动力柜加热器异常"]])
                    self.handle_signal_and_log([0, 4], [0, [0, "机舱动力柜加热器异常报警次数{}".format(len(result[1]))]])
                    for i in result[1]:
                        self.signal_se_write_log.emit([6, [0, i]])
                    self.signal_se_write_log.emit([6, [-1, "*" * 40]])

        del df
        # # 从原数据中删除 机舱动力柜加热器
        # del self.df[tickets[2]]
        del tickets
        gc.collect()

    # 6 机舱信号柜温度异常
    def sensor_nacelle_signal_cabinet_temperature(self):

        """
        ：机舱信号柜温度异常
        ：11≤ 机组运行模式 ≤14，机舱信号柜温度 >45°，且机舱温度 <40°，且异常持续时间超过5min
        """

        try:
            # 获取 1 时间 2 机组运行模式 8 机舱低压柜温度 7 机舱温度 英文标签
            # print(self.tickets)
            tickets = [self.tickets[0], self.tickets[1], self.tickets[7], self.tickets[6]]
            # tickets = self.tickets

            df = self.df[['time', tickets[0], tickets[1], tickets[2], tickets[3]]]
            df.set_index(df['time'], inplace=True)
        except Exception as e:
            print(e)
            print("跳过函数6")
            self.handle_signal_and_log([-1, 5], [6, [-1, "机舱信号柜温度英文标签丢失"]])
            return

        if self.draw:
            print("传感器绘图6")
            df1 = df.copy()
            df1.resample('30T').mean()
            df1['timestamp'] = df[tickets[0]].apply(lambda x: time.mktime(time.strptime(x, '%Y-%m-%d %H:%M:%S')))
            self.drawing(graphicsView=self.plt_list[5],
                         canvas_setting={"title": "机舱信号柜温度时间图"},
                         data=[
                             {"pen": "g", "name": "机舱低压柜温度", "x": df1['timestamp'], "y": df1[tickets[2]]},
                             {"pen": "r", "name": "机舱温度", "x": df1['timestamp'], "y": df1[tickets[3]]}
                         ])
            del df1
            gc.collect()

        # 删除 1>14 | 1<11
        df = df.drop(df[((df[tickets[1]] > 14) & (df[tickets[1]] < 11))].index)
        if df.empty:
            self.handle_signal_and_log([1, 5], [6, [1, "机舱信号柜温度正常"]])

        else:
            # 删除 2<=45 | 3>=40
            df = df.drop(df[((df[tickets[2]] <= 45) & (df[tickets[3]] >= 40))].index)
            if df.empty:
                self.handle_signal_and_log([1, 5], [6, [1, "机舱信号柜温度正常"]])

            else:
                # ------------------判断连续性
                result = tool.duration_calculation_to_csv(tickets,
                                                          df,
                                                          300,
                                                          str(self.import_file_path).split(r'/')[-1].split('.')[0] +
                                                          '/机舱信号柜温度异常.csv')
                if result[0]:
                    self.handle_signal_and_log([1, 5], [6, [1, "机舱信号柜温度正常"]])

                else:
                    self.handle_signal_and_log([0, 5], [6, [0, "机舱信号柜温度异常"]])
                    self.handle_signal_and_log([0, 5], [0, [0, "机舱信号柜温度异常报警次数{}".format(len(result[1]))]])
                    for i in result[1]:
                        self.signal_se_write_log.emit([6, [0, i]])
                    self.signal_se_write_log.emit([6, [-1, "*" * 40]])

        del df
        # # 从原数据中删除 机舱信号柜温度
        # del self.df[tickets[2]]
        del tickets
        gc.collect()

    # 7 机舱信号柜加热器异常
    def sensor_nacelle_signal_cabinet_heart(self):

        """
        ：机舱信号柜加热器异常
        ：11≤ 机组运行模式 ≤14，机舱信号柜温度 < 5℃，持续3min
        """

        try:
            # 获取 1 时间 2 机组运行模式 8 机舱低压柜温度 英文标签
            # print(self.tickets)
            tickets = [self.tickets[0], self.tickets[1], self.tickets[7]]
            # tickets = self.tickets

            df = self.df[['time', tickets[0], tickets[1], tickets[2]]]
            df.set_index(df['time'], inplace=True)
        except Exception as e:
            print(e)
            print("跳过函数7")
            self.handle_signal_and_log([-1, 6], [6, [-1, "机舱信号柜加热器英文标签丢失"]])
            return

        if self.draw:
            print("传感器绘图7")
            df1 = df.copy()
            df1.resample('30T').mean()
            df1['timestamp'] = df[tickets[0]].apply(lambda x: time.mktime(time.strptime(x, '%Y-%m-%d %H:%M:%S')))
            self.drawing(graphicsView=self.plt_list[6],
                         canvas_setting={"title": "机舱信号柜加热器时间图"},
                         data=[
                             {"pen": "g", "name": "机舱低压柜温度", "x": df1['timestamp'], "y": df1[tickets[2]]}
                         ])
            del df1
            gc.collect()

        # 删除 1>14 | 1<11
        df = df.drop(df[((df[tickets[1]] > 14) & (df[tickets[1]] < 11))].index)
        if df.empty:
            self.handle_signal_and_log([1, 6], [6, [1, "机舱信号柜加热器正常"]])

        else:
            # 删除 2>=5
            df = df.drop(df[(df[tickets[2]] >= 5)].index)
            if df.empty:
                self.handle_signal_and_log([1, 6], [6, [1, "机舱信号柜加热器正常"]])

            else:
                # ------------------判断连续性
                result = tool.duration_calculation_to_csv(tickets,
                                                          df,
                                                          180,
                                                          str(self.import_file_path).split(r'/')[-1].split('.')[0] +
                                                          '/机舱信号柜加热器异常.csv')
                if result[0]:
                    self.handle_signal_and_log([1, 6], [6, [1, "机舱信号柜加热器正常"]])

                else:
                    self.handle_signal_and_log([0, 6], [6, [0, "机舱信号柜加热器异常"]])
                    self.handle_signal_and_log([0, 6], [0, [0, "机舱信号柜加热器异常报警次数{}".format(len(result[1]))]])
                    for i in result[1]:
                        self.signal_se_write_log.emit([6, [0, i]])
                    self.signal_se_write_log.emit([6, [-1, "*" * 40]])

        del df
        # # 从原数据中删除 机舱信号柜加热器
        # del self.df[tickets[2]]
        del tickets
        gc.collect()

    # 8 偏航驱动柜温度异常
    def sensor_yaw_driver_cabinet_temperature(self):
        """
        偏航驱动柜温度异常
        变频器1温度 至 变频器17温度中 的最大值≠0 且 >60℃，持续10min
        :return:
        """
        try:
            # 获取 1 时间  9-25 变频器1-17温度 英文标签
            # print(self.tickets)
            tickets = [self.tickets[0], self.tickets[8], self.tickets[9], self.tickets[10], self.tickets[11],
                       self.tickets[12], self.tickets[13], self.tickets[14], self.tickets[15], self.tickets[16],
                       self.tickets[17], self.tickets[18], self.tickets[19], self.tickets[20], self.tickets[21],
                       self.tickets[22], self.tickets[23], self.tickets[24]]
            # tickets = self.tickets

            df = self.df[['time', tickets[0], tickets[1], tickets[2], tickets[3], tickets[4], tickets[5],
                          tickets[6], tickets[7], tickets[8], tickets[9], tickets[10], tickets[11], tickets[12],
                          tickets[13], tickets[14], tickets[15], tickets[16], tickets[17]]]
            df.set_index(df['time'], inplace=True)
        except Exception as e:
            print(e)
            print("跳过函数8")
            self.handle_signal_and_log([-1, 7], [6, [-1, "偏航驱动柜温度英文标签丢失"]])
            return

        if self.draw:
            print("传感器绘图8")
            df1 = df.copy()
            df1.resample('30T').mean()
            df1['timestamp'] = df[tickets[0]].apply(lambda x: time.mktime(time.strptime(x, '%Y-%m-%d %H:%M:%S')))
            self.drawing(graphicsView=self.plt_list[7],
                         canvas_setting={"title": "偏航驱动柜温度时间图"},
                         data=[
                             {"pen": "g", "name": "变频器1温度", "x": df1['timestamp'], "y": df1[tickets[1]]}
                         ])
            del df1
            gc.collect()

        # max ==0 | max <= 60
        # df['maxvalue'] = df[[tickets[1], tickets[2], tickets[3], tickets[4], tickets[5], tickets[6],
        #                             tickets[7], tickets[8], tickets[9], tickets[10], tickets[11], tickets[12],
        #                             tickets[13], tickets[14], tickets[15], tickets[16], tickets[17]]].max(axis=1)
        df['maxvalue'] = df.loc[:, [tickets[1], tickets[2], tickets[3], tickets[4], tickets[5], tickets[6],
                                    tickets[7], tickets[8], tickets[9], tickets[10], tickets[11], tickets[12],
                                    tickets[13], tickets[14], tickets[15], tickets[16], tickets[17]]].max(axis=1,
                                                                                                          skipna=True)
        df = df.drop(df[((df['maxvalue'] == 0) | (df['maxvalue'] <= 60))].index)
        if df.empty:
            self.handle_signal_and_log([1, 7], [6, [1, "偏航驱动柜温度正常"]])
        else:
            # ------------------判断连续性
            result = tool.duration_calculation_to_csv(tickets,
                                                      df,
                                                      600,
                                                      str(self.import_file_path).split(r'/')[-1].split('.')[0] +
                                                      '/偏航驱动柜温度异常.csv')
            if result[0]:
                self.handle_signal_and_log([1, 7], [6, [1, "偏航驱动柜温度正常"]])

            else:
                self.handle_signal_and_log([0, 7], [6, [0, "偏航驱动柜温度异常"]])
                self.handle_signal_and_log([0, 7], [0, [0, "偏航驱动柜温度异常报警次数{}".format(len(result[1]))]])
                for i in result[1]:
                    self.signal_se_write_log.emit([6, [0, i]])
                self.signal_se_write_log.emit([6, [-1, "*" * 40]])

        del df
        # # 从原数据中删除 叶轮转速
        # del self.df[tickets[2]]
        del tickets
        gc.collect()

    def over(self):
        # 第一个线程结束
        self.signal_se_over.emit([6, 1])

