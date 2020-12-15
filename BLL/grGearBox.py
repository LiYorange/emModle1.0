# -------------------------------------------------------------------------------
# Name:         grGearBox1
# Description:
# Author:       A07567
# Date:         2020/11/8
# -------------------------------------------------------------------------------
# 自定义模块区

from DAL import base_setting
from DAL import import_data
from BLL import tool

# 自定义模块区结束
import time
from PyQt5.QtCore import pyqtSignal, QObject
import gc

import pandas as pd
import numpy as np
import pyqtgraph as pg
import copy

pd.set_option('display.max_columns', None)



class GearBox1(QObject):
    """
    齿轮箱预警模型
    """
    # 类变量
    signal_gb_color = pyqtSignal(list)
    signal_gb_show_message = pyqtSignal(str)
    signal_gb_progress = pyqtSignal(dict)
    signal_gb_write_log = pyqtSignal(list)
    signal_gb_over = pyqtSignal(list)

    def __init__(self, tickets_file_path=None, import_data_path=None, df=None,
                 project_index=None, plt_list=None, draw=False):
        """
        :param tickets_file_path: 将中文标签转化为英文标签的list
        :param import_data_path: 需要处理的数据路径
        :param project_index: 选区的项目序号
        :param plt_list: 绘图对象

        """
        super(GearBox1, self).__init__()

        # 初始化一个df
        self.df = pd.DataFrame()
        # 初始化标签列表
        self.tickets = []
        # 初始化缺失标签列表
        self.missing_tickets = []
        # 默认绘图关闭
        self.draw = False
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
            self.gearbox_main_bearing_temperature,
            self.gearbox_hub_side_bearing_temperature,
            self.gearbox_generator_side_bearing_temperature,
            self.gearbox_oil_temperature,
            self.gearbox_cooler_inlet_oil_temperature,
            self.gearbox_cooler_outlet_oil_temperature,
            self.gearbox_water_pump_outlet_temperature,
            self.gearbox_water_pump_inlet_temperature,
            self.gearbox_A1_port_temperature,
            self.gearbox_A2_port_temperature,
            self.gearbox_A3_port_temperature,
            self.gearbox_A4_port_temperature,
            self.gearbox_A1_port_pressure,
            self.gearbox_A2_port_pressure,
            self.gearbox_A3_port_pressure,
            self.gearbox_A4_port_pressure,
            self.gearbox_main_pump1_1_outlet_oil_pressure,
            self.gearbox_main_pump1_2_outlet_oil_pressure,
            self.gearbox_main_pump2_1_outlet_oil_pressure,
            self.gearbox_main_pump2_2_outlet_oil_pressure,
            self.gearbox_main_pump_filter1_1_oil_pressure_difference,
            self.gearbox_main_pump_filter1_2_oil_pressure_difference,
            self.gearbox_main_pump_filter2_1_oil_pressure_difference,
            self.gearbox_main_pump_filter2_2_oil_pressure_difference,
            self.gearbox_cooling_pump_outlet_oil_pressure,
            self.gearbox_bypass_pump_outlet_oil_pressure,
            self.gearbox_oil_level,
            self.gearbox_water_pump1_temperature_difference,
            self.gearbox_water_pump2_temperature_difference,
            self.gearbox_water_pump1_outlet_oil_pressure,
            self.gearbox_water_pump1_inlet_oil_pressure,
            self.gearbox_water_pump2_outlet_oil_pressure,
            self.gearbox_water_pump2_inlet_oil_pressure,
            self.gearbox_water_pump1_oil_pressure_difference,
            self.gearbox_water_pump2_oil_pressure_difference,
            self.over
        ]
        # ------------------------------------------->>>实例变量初始化结束

    def run(self):
        print("齿轮箱模块已启动！")
        self.signal_gb_show_message.emit("齿轮箱模块已启动！")
        self.signal_gb_write_log.emit([1, [-1,
                                           time.strftime('%Y{y}%m{m}%d{d} %H{h}%M{f}%S{s}').format(y='年', m='月', d='日',
                                                                                                   h='时', f='分',
                                                                                                   s='秒') + ":齿轮箱模块进程开始运行"]])

        for (func, i) in zip(self.function_list, range(len(self.function_list))):
            func()
            del func
            # print(int((i + 1) / len(self.function_list) * 100))
            self.signal_gb_progress.emit({"gearbox": int((i + 1) / len(self.function_list) * 100)})
        self.signal_gb_show_message.emit("齿轮箱模块计算完成！")
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
        self.signal_gb_color.emit(color_signal)
        log_signal[1][1] = time.strftime('%Y{y}%m{m}%d{d} %H{h}%M{f}%S{s}').format(y='年', m='月', d='日',
                                                                                   h='时', f='分', s='秒') + ":" + \
                           log_signal[1][1]
        self.signal_gb_write_log.emit(log_signal)

    # 1 齿轮箱主轴承温度高
    def gearbox_main_bearing_temperature(self):

        """
        ：齿轮箱主轴承温度高
        ：12 ≤ 机组运行模式 ≤ 14，齿轮箱主轴承温度 > 67.5℃，持续 10min
        """

        try:
            # 获取 1 时间 2 机组模式 3 齿轮箱主轴承温度英文标签
            # print(self.tickets)
            tickets = [self.tickets[0], self.tickets[1], self.tickets[2]]
            # tickets = self.tickets

            df = self.df[['time', tickets[0], tickets[1], tickets[2]]]
            df.set_index(df['time'], inplace=True)
        except Exception as e:
            print(e)
            print("齿轮箱齿轮箱跳过函数1")
            self.handle_signal_and_log([-1, 0], [1, [-1, "齿轮箱主轴承英文标签丢失"]])
            return

        if self.draw:
            print("齿轮箱绘图1")
            df1 = df.copy()
            df1.resample('30T').mean()
            df1['timestamp'] = df[tickets[0]].apply(lambda x: time.mktime(time.strptime(x, '%Y-%m-%d %H:%M:%S')))
            self.drawing(graphicsView=self.plt_list[0],
                         canvas_setting={"title": "齿轮箱主轴承温度时间图"},
                         data=[
                             {"pen": "g", "name": "齿轮箱主轴承温度", "x": df1['timestamp'], "y": df1[tickets[2]]},
                         ])
            del df1
            gc.collect()

        # 删除不在12-14之间
        df = df.drop(df[(df[tickets[1]] > 14) | (df[tickets[1]] < 12)].index)
        if df.empty:
            self.handle_signal_and_log([1, 0], [1, [1, "齿轮箱主轴承温度正常"]])

        else:
            # 删除温度小于67.5
            df = df.drop(df[(df[tickets[2]] < 67.5)].index)
            if df.empty:
                self.handle_signal_and_log([1, 0], [1, [1, "齿轮箱主轴承温度正常"]])

            else:
                # ------------------判断连续性
                result = tool.duration_calculation_to_csv(tickets,
                                                          df,
                                                          600,
                                                          str(self.import_file_path).split(r'/')[-1].split('.')[0] +
                                                          '/齿轮箱主轴承温度高.csv')
                if result[0]:
                    self.handle_signal_and_log([1, 0], [1, [1, "齿轮箱主轴承温度正常"]])

                else:
                    self.handle_signal_and_log([0, 0], [1, [0, "齿轮箱主轴承温度高"]])
                    self.handle_signal_and_log([0, 0], [0, [0, "齿轮箱主轴承温度高报警次数{}".format(len(result[1]))]])
                    for i in result[1]:
                        self.signal_gb_write_log.emit([1, [0, i]])
                    self.signal_gb_write_log.emit([1, [-1, "*" * 40]])

        del df
        # # 从原数据中删除 齿轮箱主轴承温度
        # del self.df[tickets[2]]
        del tickets
        gc.collect()

    # 2 齿轮箱轮毂侧轴承温度高
    def gearbox_hub_side_bearing_temperature(self):
        """
            齿轮箱轮毂侧轴承温度高
            12≤机组运行模式≤14，齿轮箱轮毂侧轴承温度>67.5℃，持续10min
        """

        try:
            # 获取 时间 模式 齿轮箱轮毂侧轴承温度英文标签
            tickets = [self.tickets[0], self.tickets[1], self.tickets[3]]
            df = self.df[['time', tickets[0], tickets[1], tickets[2]]]
            df.set_index(df['time'], inplace=True)
            # 1 时间 2 机组模式 4 齿轮箱轮毂侧轴承温度
        except Exception as e:
            print(e)
            print("齿轮箱跳过函数2")
            self.signal_gb_color.emit([-1, 1])
            self.handle_signal_and_log([-1, 1], [1, [-1, "齿轮箱轮毂侧轴承温度标签丢失"]])
            return
        # 绘图
        if self.draw:
            print("齿轮箱绘图2")
            df1 = df.copy()
            df1.resample('30T').mean()
            df1['timestamp'] = df[tickets[0]].apply(lambda x: time.mktime(time.strptime(x, '%Y-%m-%d %H:%M:%S')))
            self.drawing(graphicsView=self.plt_list[1],
                         canvas_setting={"title": "齿轮箱轮毂侧轴承温度时间图"},
                         data=[
                             {"pen": "g", "name": "齿轮箱轮毂侧轴承温度", "x": df1['timestamp'], "y": df1[tickets[2]]}
                         ])

            del df1
            gc.collect()

        # 删除不在12-14之间
        df = df.drop(df[(df[tickets[1]] > 14) | (df[tickets[1]] < 12)].index)
        if df.empty:
            self.handle_signal_and_log([1, 1], [1, [1, "齿轮箱轮毂侧轴承温度正常"]])
        else:
            # 删除温度小于67.5
            df = df.drop(df[(df[tickets[2]] < 67.5)].index)
            if df.empty:
                self.handle_signal_and_log([1, 1], [1, [1, "齿轮箱轮毂侧轴承温度正常"]])
            else:
                # ------------------判断连续性

                result = tool.duration_calculation_to_csv(tickets,
                                                          df,
                                                          600,
                                                          str(self.import_file_path).split(r'/')[-1].split('.')[0] +
                                                          '/齿轮箱轮毂侧轴承温度高.csv')
                if result[0]:
                    self.handle_signal_and_log([1, 1], [1, [1, "齿轮箱轮毂侧轴承温度正常"]])
                else:
                    self.handle_signal_and_log([0, 1], [1, [0, "齿轮箱轮毂侧轴承温度高"]])
                    self.handle_signal_and_log([0, 1], [0, [0, "齿轮箱轮毂侧轴承温度高报警次数{}".format(len(result[1]))]])
                    for i in result[1]:
                        self.signal_gb_write_log.emit([1, [0, i]])
                    self.signal_gb_write_log.emit([1, [-1, "*" * 40]])

        # 内存回收
        del df
        # # 从原数据中删除
        # del self.df[tickets[2]]
        del tickets
        gc.collect()

    # 3齿轮箱发电机侧轴承温度高
    def gearbox_generator_side_bearing_temperature(self):
        """
        齿轮箱发电机侧轴承温度高
        12≤机组运行模式≤14，齿轮箱发电机侧轴承温度>67.5℃，持续10min
        """
        try:
            # 获取 时间 模式 齿轮箱发电机侧轴承温度英文标签
            tickets = [self.tickets[0], self.tickets[1], self.tickets[4]]
            df = self.df[['time', tickets[0], tickets[1], tickets[2]]]
            df.set_index(df['time'], inplace=True)
            # 1 时间 2 机组模式 4 齿轮箱发电机侧轴承温度温度
        except Exception as e:
            print(e)
            print("齿轮箱跳过函数3")
            self.handle_signal_and_log([-1, 2], [1, [-1, "齿轮箱发电机侧轴承温度标签丢失"]])
            return
        # 绘图
        if self.draw:
            print("齿轮箱绘图3")
            df1 = df.copy()
            df1.resample('30T')
            df1['timestamp'] = df[tickets[0]].apply(lambda x: time.mktime(time.strptime(x, '%Y-%m-%d %H:%M:%S')))
            self.drawing(graphicsView=self.plt_list[2],
                         canvas_setting={"title": "齿轮箱发电机侧轴承温度时间图"},
                         data=[
                             {"pen": "g", "name": "齿轮箱发电机侧轴承温度", "x": df1['timestamp'], "y": df1[tickets[2]]}
                         ])
            del df1
            gc.collect()

        # 删除不在12-14之间
        df = df.drop(df[(df[tickets[1]] > 14) | (df[tickets[1]] < 12)].index)
        if df.empty:
            self.handle_signal_and_log([1, 2], [1, [1, "齿轮箱轮毂侧轴承温度正常"]])
        else:
            # 删除温度小于67.5
            df = df.drop(df[(df[tickets[2]] < 67.5)].index)
            if df.empty:
                self.handle_signal_and_log([1, 2], [1, [1, "齿轮箱轮毂侧轴承温度正常"]])
                # self.signal_gb_write_log.emit(
                #     time.strftime('%Y{y}%m{m}%d{d} %H{h}%M{f}%S{s}').format(y='年', m='月', d='日', h='时', f='分',
                #                                                             s='秒') + ":齿轮箱发电机侧轴承温正常"
            else:
                # ------------------判断连续性
                result = tool.duration_calculation_to_csv(tickets,
                                                          df,
                                                          600,
                                                          str(self.import_file_path).split(r'/')[-1].split('.')[0] +
                                                          '/齿轮箱发电机侧轴承温度高.csv')

                if result[0]:
                    self.handle_signal_and_log([1, 2], [1, [1, "齿轮箱发电机侧轴承温度正常"]])
                else:
                    self.handle_signal_and_log([0, 2], [1, [0, "齿轮箱发电机侧轴承温度高"]])
                    self.handle_signal_and_log([0, 2], [0, [0, "齿轮箱发电机侧轴承温度高报警次数{}".format(len(result[1]))]])
                    for i in result[1]:
                        self.signal_gb_write_log.emit([1, [0, i]])
                    self.signal_gb_write_log.emit([1, [-1, "*" * 40]])
        del df

    # 4齿轮箱油温
    def gearbox_oil_temperature(self):
        """
        齿轮箱油温高
        12≤机组运行模式≤14，齿轮箱油温、齿轮箱过滤泵处油温、
        齿轮箱主泵处油温任意一个>58℃，且持续10min
        :return:
        """
        try:
            # 获取 时间 模式 齿轮箱油温 齿轮箱离线过滤泵处油温 齿轮箱主泵处油温英文标签
            tickets = [self.tickets[0], self.tickets[1], self.tickets[5], self.tickets[6], self.tickets[7]]
            df = self.df[['time', tickets[0], tickets[1], tickets[2], tickets[3], tickets[4]]]
            df.set_index(df['time'], inplace=True)
            # 1 时间 2 机组模式 4 齿轮箱轮毂侧轴承温度
        except Exception as e:
            print(e)
            print("齿轮箱跳过函数4")
            self.handle_signal_and_log([-1, 3], [1, [-1, "齿轮箱轮毂侧轴承温度标签丢失"]])
            # self.signal_gb_color.emit([-1, 3])
            return
        # 绘图
        if self.draw:
            print("齿轮箱绘图4")
            df1 = df.copy()
            df1['timestamp'] = df[tickets[0]].apply(lambda x: time.mktime(time.strptime(x, '%Y-%m-%d %H:%M:%S')))
            self.drawing(graphicsView=self.plt_list[3],
                         canvas_setting={"title": "齿轮箱油温时间图"},
                         data=[
                             {"pen": "g", "name": "齿轮箱油温", "x": df1['timestamp'], "y": df1[tickets[2]]},
                             {"pen": "r", "name": "齿轮箱离线过滤泵处油温", "x": df1['timestamp'], "y": df1[tickets[3]]},
                             {"pen": "b", "name": "齿轮箱主泵处油温", "x": df1['timestamp'], "y": df1[tickets[4]]}
                         ])

            del df1
            gc.collect()

        # 删除不在12-14之间
        df = df.drop(df[(df[tickets[1]] > 14) | (df[tickets[1]] < 12)].index)
        if df.empty:
            self.handle_signal_and_log([1, 3], [1, [1, "齿轮箱轮毂侧轴承温度正常"]])

        else:
            # 删除温度小于58
            df = df.drop(df[(df[tickets[2]] < 58) | (df[tickets[3]] < 58) | (df[tickets[4]] < 58)].index)
            if df.empty:
                self.handle_signal_and_log([1, 3], [1, [1, "齿轮箱轮毂侧轴承温度正常"]])

            else:
                # ------------------判断连续性
                result = tool.duration_calculation_to_csv(tickets,
                                                          df,
                                                          600,
                                                          str(self.import_file_path).split(r'/')[-1].split('.')[0] +
                                                          '/齿轮箱油温高.csv')
                if result[0]:
                    self.handle_signal_and_log([1, 3], [1, [1, "齿轮箱轮毂侧轴承温度正常"]])
                else:
                    self.handle_signal_and_log([0, 3], [1, [0, "齿轮箱轮毂侧轴承温度高"]])
                    self.handle_signal_and_log([0, 3], [0, [0, "齿轮箱轮毂侧轴承温度高报警次数{}".format(len(result[1]))]])
                    for i in result[1]:
                        self.signal_gb_write_log.emit([1, [0, i]])
                    self.signal_gb_write_log.emit([1, [-1, "*" * 40]])
        del df

    # 5齿轮箱冷却器入口油温
    def gearbox_cooler_inlet_oil_temperature(self):
        """
        齿轮箱冷却器入口油温高
        12≤机组运行模式≤14，齿轮箱冷却器入口油温>58℃，且持续10min
        :return:
        """
        try:
            # 获取 时间 模式 润滑油冷却器入口油温英文标签
            tickets = [self.tickets[0], self.tickets[1], self.tickets[8]]
            df = self.df[['time', tickets[0], tickets[1], tickets[2]]]
            df.set_index(df['time'], inplace=True)
            # 1 时间 2 机组模式 8 齿轮箱冷却器入口油温
        except Exception as e:
            print(e)
            print("齿轮箱跳过函数5")
            self.handle_signal_and_log([-1, 4], [1, [-1, "齿轮箱冷却器入口油温英文标签丢失"]])
            # self.signal_gb_color.emit([-1, 4])
            return

        # 绘图
        if self.draw:
            print("齿轮箱绘图5")
            df1 = df.copy()
            # df1['timestamp'] = (df1['time'] - np.datetime64('1970-01-01T08:00:00Z')) / np.timedelta64(1, 'ms')
            df1['timestamp'] = df[tickets[0]].apply(lambda x: time.mktime(time.strptime(x, '%Y-%m-%d %H:%M:%S')))
            self.drawing(graphicsView=self.plt_list[4],
                         canvas_setting={"title": "齿轮箱冷却器入口油温时间图"},
                         data=[
                             {"pen": "g", "name": "齿轮箱冷却器入口油温", "x": df1['timestamp'], "y": df1[tickets[2]]}
                         ])
            del df1
            gc.collect()

        # 删除不在12-14之间
        df = df.drop(df[(df[tickets[1]] > 14) | (df[tickets[1]] < 12)].index)
        if df.empty:
            self.handle_signal_and_log([1, 4], [1, [1, "齿轮箱冷却器入口油温度正常"]])

        else:
            # 删除温度小于58
            df = df.drop(df[(df[tickets[2]] < 58)].index)
            if df.empty:
                self.handle_signal_and_log([1, 4], [1, [1, "齿轮箱冷却器入口油温度正常"]])
            else:
                # ------------------判断连续性
                result = tool.duration_calculation_to_csv(tickets,
                                                          df,
                                                          600,
                                                          str(self.import_file_path).split(r'/')[-1].split('.')[0] +
                                                          '/齿轮箱冷却器入口油温高.csv')
                if result[0]:
                    self.handle_signal_and_log([1, 4], [1, [1, "齿轮箱冷却器入口油温度正常"]])

                else:
                    self.handle_signal_and_log([0, 4], [1, [0, "齿轮箱冷却器入口油温度高"]])
                    self.handle_signal_and_log([0, 4], [0, [0, "齿轮箱冷却器入口油温度高报警次数{}".format(len(result[1]))]])
                    for i in result[1]:
                        self.signal_gb_write_log.emit([1, [0, i]])
                    self.signal_gb_write_log.emit([1, [-1, "*" * 40]])
        del df

    # 6齿轮箱冷却器出口油温
    def gearbox_cooler_outlet_oil_temperature(self):
        """
        齿轮箱冷却器出口油温高
        12≤机组运行模式≤14，齿轮箱冷却器出口油温>53℃，且持续10min
        :return:
        """
        try:
            # 获取 时间 模式 润滑油冷却器出口油温英文标签
            tickets = [self.tickets[0], self.tickets[1], self.tickets[9]]
            df = self.df[['time', tickets[0], tickets[1], tickets[2]]]
            df.set_index(df['time'], inplace=True)
            # 1 时间 2 机组模式 9齿轮箱轮毂侧轴承温度
        except Exception as e:
            print(e)
            print("齿轮箱跳过函数6")
            self.handle_signal_and_log([-1, 5], [1, [-1, "润滑油冷却器出口油温英文标签丢失"]])
            return
        # 绘图
        if self.draw:
            print("齿轮箱绘图6")
            df1 = df.copy()
            df1['timestamp'] = df[tickets[0]].apply(lambda x: time.mktime(time.strptime(x, '%Y-%m-%d %H:%M:%S')))
            self.drawing(graphicsView=self.plt_list[5],
                         canvas_setting={"title": "齿轮箱冷却器出口油温时间图"},
                         data=[
                             {"pen": "g", "name": "齿轮箱冷却器出口油温", "x": df1['timestamp'], "y": df1[tickets[2]]}
                         ])
            del df1
            gc.collect()

        # 删除不在12-14之间
        df = df.drop(df[(df[tickets[1]] > 14) | (df[tickets[1]] < 12)].index)
        if df.empty:
            self.handle_signal_and_log([1, 5], [1, [1, "润滑油冷却器出口油温正常"]])

        else:
            # 删除温度小于53
            df = df.drop(df[(df[tickets[2]] < 53)].index)
            if df.empty:
                self.handle_signal_and_log([1, 5], [1, [1, "润滑油冷却器出口油温正常"]])

            else:
                # ------------------判断连续性
                result = tool.duration_calculation_to_csv(tickets,
                                                          df,
                                                          600,
                                                          str(self.import_file_path).split(r'/')[-1].split('.')[0] +
                                                          '/润滑油冷却器出口油温高.csv')
                if result[0]:
                    self.handle_signal_and_log([1, 5], [1, [1, "润滑油冷却器出口油温正常"]])

                else:
                    self.handle_signal_and_log([0, 5], [1, [0, "润滑油冷却器出口油温高"]])
                    self.handle_signal_and_log([0, 5], [0, [0, "润滑油冷却器出口油温高报警次数{}".format(len(result[1]))]])
                    for i in result[1]:
                        self.signal_gb_write_log.emit([1, [0, i]])
                    self.signal_gb_write_log.emit([1, [-1, "*" * 40]])
        del df

    # 7 齿轮箱水泵出口温度
    def gearbox_water_pump_outlet_temperature(self):
        """
        齿轮箱水泵出口温度高
        12≤运行模式≤14，齿轮箱水泵出口温度＞48℃，且持续10min
        :return:
        """
        try:
            # 获取 时间 模式 齿轮箱水泵出口温度英文标签
            tickets = [self.tickets[0], self.tickets[1], self.tickets[10]]
            df = self.df[['time', tickets[0], tickets[1], tickets[2]]]
            df.set_index(df['time'], inplace=True)
        except Exception as e:
            print(e)
            print("齿轮箱跳过函数7")
            self.handle_signal_and_log([-1, 6], [1, [-1, "齿轮箱水泵出口温度英文标签丢失"]])
            return
        # 绘图
        if self.draw:
            print("齿轮箱绘图7")
            df1 = df.copy()
            df1['timestamp'] = df[tickets[0]].apply(lambda x: time.mktime(time.strptime(x, '%Y-%m-%d %H:%M:%S')))
            self.drawing(graphicsView=self.plt_list[6],
                         canvas_setting={"title": "齿轮箱水泵出口温度时间图"},
                         data=[
                             {"pen": "g", "name": "齿轮箱水泵出口温度", "x": df1['timestamp'], "y": df1[tickets[2]]}
                         ])
            del df1
            gc.collect()

        # 删除不在12-14之间
        df = df.drop(df[(df[tickets[1]] > 14) | (df[tickets[1]] < 12)].index)
        if df.empty:
            self.signal_gb_color.emit([True, 6])
            self.signal_gb_write_log.emit(
                time.strftime('%Y{y}%m{m}%d{d} %H{h}%M{f}%S{s}').format(y='年', m='月', d='日', h='时', f='分',
                                                                        s='秒') + ":齿轮箱水泵出口温度正常")
        else:
            # 删除温度小于48
            df = df.drop(df[(df[tickets[2]] < 48)].index)
            if df.empty:
                self.handle_signal_and_log([1, 6], [1, [1, "齿轮箱水泵出口温度正常"]])
            else:
                # ------------------判断连续性
                result = tool.duration_calculation_to_csv(tickets,
                                                          df,
                                                          600,
                                                          str(self.import_file_path).split(r'/')[-1].split('.')[0] +
                                                          '/齿轮箱水泵出口温度高.csv')
                if result[0]:
                    self.handle_signal_and_log([1, 6], [1, [1, "齿轮箱水泵出口温度正常"]])

                else:
                    self.handle_signal_and_log([0, 6], [1, [0, "齿轮箱水泵出口温度高"]])
                    self.handle_signal_and_log([0, 6], [0, [0, "齿轮箱水泵出口温度高报警次数{}".format(len(result[1]))]])
                    for i in result[1]:
                        self.signal_gb_write_log.emit([1, [0, i]])
                    self.signal_gb_write_log.emit([1, [-1, "*" * 40]])

        del df

    # 8 齿轮箱水泵入口温度
    def gearbox_water_pump_inlet_temperature(self):
        """
        齿轮箱水泵入口温度异常
        12≤机组运行模式≤14，齿轮箱水泵入口温度1和齿轮箱水泵入口温度2任意一个＞45℃，
        或齿轮箱水泵入口温度1和齿轮箱水泵入口温度2差值绝对值>5，持续10min
        :return:
        """
        try:
            # 获取 时间 模式 齿轮箱油温 齿轮箱离线过滤泵处油温 齿轮箱主泵处油温英文标签
            tickets = [self.tickets[0], self.tickets[1], self.tickets[11], self.tickets[12]]
            df = self.df[['time', tickets[0], tickets[1], tickets[2], tickets[3]]]
            df.set_index(df['time'], inplace=True)
            # 1 时间 2 机组模式 11 齿轮箱离线过滤泵处油温 12 齿轮箱主泵处油温英文标签
        except Exception as e:
            print(e)
            print("齿轮箱跳过函数8")
            self.handle_signal_and_log([-1, 7], [1, [-1, "齿轮箱水泵入口温度英文标签丢失"]])
            return
        # 绘图
        if self.draw:
            print("齿轮箱绘图8")
            df1 = df.copy()
            df1['timestamp'] = df1[tickets[0]].apply(lambda x: time.mktime(time.strptime(x, '%Y-%m-%d %H:%M:%S')))
            self.drawing(graphicsView=self.plt_list[7],
                         canvas_setting={"title": "齿轮箱水泵入口温度时间图"},
                         data=[
                             {"pen": "g", "name": "齿轮箱水泵入口温度1", "x": df1['timestamp'], "y": df1[tickets[2]]},
                             {"pen": "r", "name": "齿轮箱水泵入口温度2", "x": df1['timestamp'], "y": df1[tickets[3]]}
                         ])
            del df1
            gc.collect()

        # 删除不在12-14之间
        df = df.drop(df[(df[tickets[1]] > 14) | (df[tickets[1]] < 12)].index)
        if df.empty:
            self.handle_signal_and_log([1, 7], [1, [1, "齿轮箱水泵入口温度正常"]])

        else:
            # 删除温度小于45
            df = df.drop(df[(df[tickets[2]] < 45) | (df[tickets[3]] < 45)].index)
            if df.empty:
                self.handle_signal_and_log([1, 7], [1, [1, "齿轮箱水泵入口温度正常"]])
            else:
                # ------------------判断连续性
                result = tool.duration_calculation_to_csv(tickets,
                                                          df,
                                                          600,
                                                          str(self.import_file_path).split(r'/')[-1].split('.')[0] +
                                                          '/齿轮箱水泵入口温度高.csv')
                if result[0]:
                    self.handle_signal_and_log([1, 7], [1, [1, "齿轮箱水泵入口温度正常"]])

                else:
                    self.handle_signal_and_log([0, 7], [1, [0, "齿轮箱水泵入口温度高"]])
                    self.handle_signal_and_log([0, 7], [0, [0, "齿轮箱水泵入口温度高报警次数{}".format(len(result[1]))]])
                    for i in result[1]:
                        self.signal_gb_write_log.emit([1, [0, i]])
                    self.signal_gb_write_log.emit([1, [-1, "*" * 40]])
        del df

    # 9 齿轮箱A1口温度
    def gearbox_A1_port_temperature(self):
        """
        齿轮箱A1口温度高
        12≤机组运行模式≤14，齿轮箱A1口温度>56℃，且持续10min
        :return:
        """
        try:
            # 获取 时间 模式 齿轮箱A1口温度英文标签
            tickets = [self.tickets[0], self.tickets[1], self.tickets[13]]
            df = self.df[['time', tickets[0], tickets[1], tickets[2]]]
            df.set_index(df['time'], inplace=True)
            # 1 时间 2 机组模式 13齿轮箱轮毂侧轴承温度
        except Exception as e:
            print(e)
            print("齿轮箱跳过函数9")
            self.handle_signal_and_log([-1, 8], [1, [-1, "齿轮箱A1口温度英文标签丢失"]])
            return
        # 绘图
        if self.draw:
            print("齿轮箱绘图9")
            df1 = df.copy()
            df1['timestamp'] = df[tickets[0]].apply(lambda x: time.mktime(time.strptime(x, '%Y-%m-%d %H:%M:%S')))
            self.drawing(graphicsView=self.plt_list[8],
                         canvas_setting={"title": "齿轮箱A1口温度时间图"},
                         data=[
                             {"pen": "g", "name": "齿轮箱A1口温度", "x": df1['timestamp'], "y": df1[tickets[2]]}
                         ])
            del df1
            gc.collect()

        # 删除不在12-14之间
        df = df.drop(df[(df[tickets[1]] > 14) | (df[tickets[1]] < 12)].index)
        if df.empty:
            self.handle_signal_and_log([1, 8], [1, [1, "齿轮箱A1口温度正常"]])
        else:
            # 删除温度小于56
            df = df.drop(df[(df[tickets[2]] < 56)].index)
            if df.empty:
                self.handle_signal_and_log([1, 8], [1, [1, "齿轮箱A1口温度正常"]])
            else:
                # ------------------判断连续性
                result = tool.duration_calculation_to_csv(tickets,
                                                          df,
                                                          600,
                                                          str(self.import_file_path).split(r'/')[-1].split('.')[0] +
                                                          '/齿轮箱A1口温度高.csv')
                if result[0]:
                    self.handle_signal_and_log([1, 8], [1, [1, "齿轮箱A1口温度正常"]])
                else:
                    self.handle_signal_and_log([0, 8], [1, [0, "齿轮箱A1口温度高"]])
                    self.handle_signal_and_log([0, 8], [0, [0, "齿轮箱A1口温度高报警次数{}".format(len(result[1]))]])
                    for i in result[1]:
                        self.signal_gb_write_log.emit([1, [0, i]])
                    self.signal_gb_write_log.emit([1, [-1, "*" * 40]])
        del df

    # 10 齿轮箱A2口温度高
    def gearbox_A2_port_temperature(self):
        """
        齿轮箱A2口温度高
        12≤机组运行模式≤14，齿轮箱A1口温度>56℃，且持续10min
        :return:
        """
        try:
            # 获取 时间 模式 齿轮箱A2口温度高英文标签
            tickets = [self.tickets[0], self.tickets[1], self.tickets[14]]
            df = self.df[['time', tickets[0], tickets[1], tickets[2]]]
            df.set_index(df['time'], inplace=True)
            # 1 时间 2 机组模式 14 齿轮箱轮毂侧轴承温度
        except Exception as e:
            print(e)
            print("齿轮箱跳过函数10")
            self.handle_signal_and_log([-1, 9], [1, [-1, "齿轮箱A2口温度英文标签丢失"]])
            return
        # 绘图
        if self.draw:
            print("齿轮箱绘图10")
            df1 = df.copy()
            df1['timestamp'] = df[tickets[0]].apply(lambda x: time.mktime(time.strptime(x, '%Y-%m-%d %H:%M:%S')))
            self.drawing(graphicsView=self.plt_list[9],
                         canvas_setting={"title": "齿轮箱A2口温度时间图"},
                         data=[
                             {"pen": "g", "name": "齿轮箱A2口温度", "x": df1['timestamp'], "y": df1[tickets[2]]}
                         ])
            del df1
            gc.collect()

        # 删除不在12-14之间
        df = df.drop(df[(df[tickets[1]] > 14) | (df[tickets[1]] < 12)].index)
        if df.empty:
            self.signal_gb_color.emit([1, 9])
            self.signal_gb_write_log.emit(
                time.strftime('%Y{y}%m{m}%d{d} %H{h}%M{f}%S{s}').format(y='年', m='月', d='日', h='时', f='分',
                                                                        s='秒') + ":齿轮箱A2口温度正常"
            )
        else:
            # 删除温度小于56
            df = df.drop(df[(df[tickets[2]] < 56)].index)
            if df.empty:
                self.handle_signal_and_log([1, 9], [1, [1, "齿轮箱A2口温度正常"]])
            else:
                # ------------------判断连续性
                result = tool.duration_calculation_to_csv(tickets,
                                                          df,
                                                          600,
                                                          str(self.import_file_path).split(r'/')[-1].split('.')[0] +
                                                          '/齿轮箱A2口温度高.csv')
                if result[0]:
                    self.handle_signal_and_log([1, 9], [1, [1, "齿轮箱A2口温度正常"]])
                else:
                    self.handle_signal_and_log([0, 9], [1, [0, "齿轮箱A2口温度高"]])
                    self.handle_signal_and_log([0, 9], [0, [0, "齿轮箱A2口温度高报警次数{}".format(len(result[1]))]])
                    for i in result[1]:
                        self.signal_gb_write_log.emit([1, [0, i]])
                    self.signal_gb_write_log.emit([1, [-1, "*" * 40]])
        del df

    # 11 齿轮箱A3口温度高
    def gearbox_A3_port_temperature(self):
        """
        齿轮箱A2口温度高
        12≤机组运行模式≤14，齿轮箱A3口温度>56℃，且持续10min
        :return:
        """
        try:
            # 获取 时间 模式 齿轮箱A3口温度高英文标签
            tickets = [self.tickets[0], self.tickets[1], self.tickets[15]]
            df = self.df[['time', tickets[0], tickets[1], tickets[2]]]
            df.set_index(df['time'], inplace=True)
            # 1 时间 2 机组模式 15 齿轮箱A3口温度
        except Exception as e:
            print(e)
            print("齿轮箱跳过函数11")
            self.handle_signal_and_log([-1, 10], [1, [-1, "齿轮箱A3口温度英文标签丢失"]])
            return
        # 绘图
        if self.draw:
            print("齿轮箱绘图11")
            df1 = df.copy()
            df1['timestamp'] = df[tickets[0]].apply(lambda x: time.mktime(time.strptime(x, '%Y-%m-%d %H:%M:%S')))
            self.drawing(graphicsView=self.plt_list[10],
                         canvas_setting={"title": "齿轮箱A3口温度时间图"},
                         data=[
                             {"pen": "g", "name": "齿轮箱A3口温度", "x": df1['timestamp'], "y": df1[tickets[2]]}
                         ])
            del df1
            gc.collect()

        # 删除不在12-14之间
        df = df.drop(df[(df[tickets[1]] > 14) | (df[tickets[1]] < 12)].index)
        if df.empty:
            self.signal_gb_color.emit([1, 10])
            self.signal_gb_write_log.emit(
                time.strftime('%Y{y}%m{m}%d{d} %H{h}%M{f}%S{s}').format(y='年', m='月', d='日', h='时', f='分',
                                                                        s='秒') + ":齿轮箱A3口温度正常"
            )
        else:
            # 删除温度小于56
            df = df.drop(df[(df[tickets[2]] < 56)].index)
            if df.empty:
                self.handle_signal_and_log([1, 10], [1, [1, "齿轮箱A3口温度正常"]])
            else:
                # ------------------判断连续性
                result = tool.duration_calculation_to_csv(tickets,
                                                          df,
                                                          600,
                                                          str(self.import_file_path).split(r'/')[-1].split('.')[0] +
                                                          '/齿轮箱A3口温度高.csv')
                if result[0]:
                    self.handle_signal_and_log([1, 10], [1, [1, "齿轮箱A3口温度正常"]])
                else:
                    self.handle_signal_and_log([0, 10], [1, [0, "齿轮箱A3口温度高"]])
                    self.handle_signal_and_log([0, 10], [0, [0, "齿轮箱A3口温度高报警次数{}".format(len(result[1]))]])
                    for i in result[1]:
                        self.signal_gb_write_log.emit([1, [0, i]])
                    self.signal_gb_write_log.emit([1, [-1, "*" * 40]])
        del df

    # 12 齿轮箱A4口温度高
    def gearbox_A4_port_temperature(self):
        """
        齿轮箱A4口温度高
        12≤机组运行模式≤14，齿轮箱A4口温度>56℃，且持续10min
        :return:
        """
        try:
            # 获取 时间 模式 齿轮箱A4口温度高英文标签
            tickets = [self.tickets[0], self.tickets[1], self.tickets[16]]
            df = self.df[['time', tickets[0], tickets[1], tickets[2]]]
            df.set_index(df['time'], inplace=True)
            # 1 时间 2 机组模式 16 齿轮箱A3口温度
        except Exception as e:
            print(e)
            print("齿轮箱跳过函数12")
            self.handle_signal_and_log([-1, 11], [1, [-1, "齿轮箱A4口温度英文标签丢失"]])
            return
        # 绘图
        if self.draw:
            print("齿轮箱绘图12")
            df1 = df.copy()
            df1['timestamp'] = df[tickets[0]].apply(lambda x: time.mktime(time.strptime(x, '%Y-%m-%d %H:%M:%S')))
            self.drawing(graphicsView=self.plt_list[11],
                         canvas_setting={"title": "齿轮箱A4口温度时间图"},
                         data=[
                             {"pen": "g", "name": "齿轮箱A4口温度", "x": df1['timestamp'], "y": df1[tickets[2]]}
                         ])
            del df1
            gc.collect()

        # 删除不在12-14之间
        df = df.drop(df[(df[tickets[1]] > 14) | (df[tickets[1]] < 12)].index)
        if df.empty:
            self.signal_gb_color.emit([1, 11])
            self.signal_gb_write_log.emit(
                time.strftime('%Y{y}%m{m}%d{d} %H{h}%M{f}%S{s}').format(y='年', m='月', d='日', h='时', f='分',
                                                                        s='秒') + ":齿轮箱A4口温度正常"
            )
        else:
            # 删除温度小于56
            df = df.drop(df[(df[tickets[2]] < 56)].index)
            if df.empty:
                self.handle_signal_and_log([1, 11], [1, [1, "齿轮箱A4口温度正常"]])
            else:
                # ------------------判断连续性
                result = tool.duration_calculation_to_csv(tickets,
                                                          df,
                                                          600,
                                                          str(self.import_file_path).split(r'/')[-1].split('.')[0] +
                                                          '/齿轮箱A4口温度高.csv')
                if result[0]:
                    self.handle_signal_and_log([1, 11], [1, [1, "齿轮箱A4口温度正常"]])
                else:
                    self.handle_signal_and_log([0, 11], [1, [0, "齿轮箱A4口温度高"]])
                    self.handle_signal_and_log([0, 11], [0, [0, "齿轮箱A4口温度高报警次数{}".format(len(result[1]))]])
                    for i in result[1]:
                        self.signal_gb_write_log.emit([1, [0, i]])
                    self.signal_gb_write_log.emit([1, [-1, "*" * 40]])
        del df

    # 13 齿轮箱A1口压力异常
    def gearbox_A1_port_pressure(self):
        """
        齿轮箱A1口压力异常
        原理：
        1、齿轮箱油温>50，齿轮箱主泵1_1高速=1或齿轮箱主泵1_2高速=1，A1口压力<4或>6.5，且持续30s
        2、齿轮箱油温>50，齿轮箱主泵1_1低速=1或齿轮箱主泵1_2低速=1，A1口压力<2.5或>5，且持续30s
        满足以上其一报出A1口压力异常
        :return:
        """
        try:
            # 获取 时间 "齿轮箱油温"5,"齿轮箱主泵1_1高速"17,"齿轮箱主泵1_2高速"18,"齿轮箱主泵1_1低速"19,"齿轮箱主泵1_2低速"20,"齿轮箱A1口压力",21英文标签
            tickets = [self.tickets[0], self.tickets[5], self.tickets[17], self.tickets[18],
                       self.tickets[19], self.tickets[20], self.tickets[21]]
            df = self.df[['time', tickets[0], tickets[1], tickets[2], tickets[3], tickets[4],
                          tickets[5], tickets[6]]]
            df.set_index(df['time'], inplace=True)
        except Exception as e:
            print(e)
            print("齿轮箱跳过函数13")
            self.handle_signal_and_log([-1, 12], [1, [-1, "齿轮箱A1口压力英文标签丢失"]])
            return
        # 绘图
        if self.draw:
            print("齿轮箱绘图13")
            df1 = df.copy()
            df1['timestamp'] = df[tickets[0]].apply(lambda x: time.mktime(time.strptime(x, '%Y-%m-%d %H:%M:%S')))
            self.drawing(graphicsView=self.plt_list[12],
                         canvas_setting={"title": "齿轮箱A1口压力时间图"},
                         data=[
                             {"pen": "g", "name": "齿轮箱油温", "x": df1['timestamp'], "y": df1[tickets[1]]},
                             {"pen": "r", "name": "A1口压力", "x": df1['timestamp'], "y": df1[tickets[6]]}
                         ])
            del df1
            gc.collect()

        # 删除温度低于50的数据
        df = df.drop(df[(df[tickets[1]] < 50)].index)
        if df.empty:
            self.signal_gb_color.emit([1, 12])
            self.signal_gb_write_log.emit(
                time.strftime('%Y{y}%m{m}%d{d} %H{h}%M{f}%S{s}').format(y='年', m='月', d='日', h='时', f='分',
                                                                        s='秒') + ":齿轮箱A1口压力正常"
            )
        else:
            # 情况1 高速模式  1 3 ：1_1 1_2模式高速，6：压力在<4或>6.5
            df_h = df[((df[tickets[1]] == 1) | (df[tickets[3]] == 1)) &
                      ((df[tickets[6]] < 4) | (df[tickets[6]] > 6))].copy()
            # 情况2 低速模式  4 5 ：1_1 1_2模式低速，6：压力在<2.5或>5
            df_l = df[((df[tickets[4]] == 1) | (df[tickets[5]] == 1)) &
                      ((df[tickets[6]] < 2.5) | (df[tickets[6]] > 5))].copy()
            # 判断是否未空
            if df_h.empty and df_l.empty:
                self.handle_signal_and_log([1, 12], [1, [1, "齿轮箱A1口压力正常"]])
            else:
                # ------------------判断连续性
                # 高速模式连续时长判断
                if not df_h.empty:
                    result = tool.duration_calculation_to_csv(tickets,
                                                              df_h,
                                                              30,
                                                              str(self.import_file_path).split(r'/')[-1].split('.')[0] +
                                                              '/齿轮箱A1口高速模式压力异常.csv')
                    if result[0]:
                        self.handle_signal_and_log([1, 12], [1, [1, "齿轮箱A1口高速模式压力正常"]])
                    else:
                        self.handle_signal_and_log([0, 12], [1, [0, "齿轮箱A1口高速模式压力异常"]])
                        self.handle_signal_and_log([0, 12], [0, [0, "齿轮箱A1口高速模式压力异常报警次数{}".format(len(result[1]))]])
                        for i in result[1]:
                            self.signal_gb_write_log.emit([1, [0, i]])
                        self.signal_gb_write_log.emit([1, [-1, "*" * 40]])
                if not df_l.empty:
                    result = tool.duration_calculation_to_csv(tickets,
                                                              df_l,
                                                              30,
                                                              str(self.import_file_path).split(r'/')[-1].split('.')[0] +
                                                              '/齿轮箱A1口低速模式压力异常.csv')
                    if result[0]:
                        self.handle_signal_and_log([1, 12], [1, [1, "齿轮箱A1口低速模式压力正常"]])
                    else:
                        self.handle_signal_and_log([0, 12], [1, [0, "齿轮箱A1口低速模式压力异常"]])
                        self.handle_signal_and_log([0, 12], [0, [0, "齿轮箱A1口低速模式压力异常报警次数{}".format(len(result[1]))]])
                        for i in result[1]:
                            self.signal_gb_write_log.emit([1, [0, i]])
                        self.signal_gb_write_log.emit([1, [-1, "*" * 40]])
            del df_h
            del df_l
        del df

    # 14 齿轮箱A2口压力异常
    def gearbox_A2_port_pressure(self):
        """
        齿轮箱A2口压力异常
        原理：
            1、齿轮箱油温>50，齿轮箱主泵2_1高速=1或齿轮箱主泵2_2高速=1，A2口压力<4或>9，且持续30s
            2、齿轮箱油温>50，齿轮箱主泵2_1低速=1或齿轮箱主泵2_2低速=1，A2口压力<2.5或>7.5，且持续30s
            满足以上其一报出A2口压力异常
        :return:
        """
        try:
            # 获取 时间 "齿轮箱油温"5,"齿轮箱主泵2_1高速22, 齿轮箱主泵2_2高速,23 齿轮箱主泵2_1低速24,齿轮箱主泵2_2低速25,齿轮箱A2口压力26英文标签
            tickets = [self.tickets[0], self.tickets[5], self.tickets[22], self.tickets[23],
                       self.tickets[24], self.tickets[25], self.tickets[26]]
            df = self.df[['time', tickets[0], tickets[1], tickets[2], tickets[3], tickets[4],
                          tickets[5], tickets[6]]]
            df.set_index(df['time'], inplace=True)
        except Exception as e:
            print(e)
            print("齿轮箱跳过函数14")
            self.handle_signal_and_log([-1, 13], [1, [-1, "齿轮箱A2口压力英文标签丢失"]])
            return
        # 绘图
        if self.draw:
            print("齿轮箱绘图14")
            df1 = df.copy()
            df1['timestamp'] = df[tickets[0]].apply(lambda x: time.mktime(time.strptime(x, '%Y-%m-%d %H:%M:%S')))
            self.drawing(graphicsView=self.plt_list[13],
                         canvas_setting={"title": "齿轮箱A2口压力时间图"},
                         data=[
                             {"pen": "g", "name": "齿轮箱油温", "x": df1['timestamp'], "y": df1[tickets[1]]},
                             {"pen": "r", "name": "A2口压力", "x": df1['timestamp'], "y": df1[tickets[6]]}
                         ])
            del df1
            gc.collect()

        # 删除温度低于50的数据
        df = df.drop(df[(df[tickets[1]] <= 50)].index)
        if df.empty:
            self.signal_gb_color.emit([1, 13])
            self.signal_gb_write_log.emit(
                time.strftime('%Y{y}%m{m}%d{d} %H{h}%M{f}%S{s}').format(y='年', m='月', d='日', h='时', f='分',
                                                                        s='秒') + ":齿轮箱A2口压力正常"
            )
        else:
            # 情况1 高速模式  1 3 ：2_1 2_2模式高速，6：压力在<4或>9
            df_h = df[((df[tickets[1]] == 1) | (df[tickets[3]] == 1)) &
                      ((df[tickets[6]] < 4) | (df[tickets[6]] > 9))].copy()
            # 情况2 低速模式  4 5 ：2_1 2_2模式低速，6：压力在<2.5或>7.5
            df_l = df[((df[tickets[4]] == 1) | (df[tickets[5]] == 1)) &
                      ((df[tickets[6]] < 2.5) | (df[tickets[6]] > 7.5))].copy()
            # 判断是否未空
            if df_h.empty and df_l.empty:
                self.handle_signal_and_log([1, 13], [1, [1, "齿轮箱A2口压力正常"]])
            else:
                # ------------------判断连续性
                # 高速模式连续时长判断
                if not df_h.empty:
                    result = tool.duration_calculation_to_csv(tickets,
                                                              df_h,
                                                              30,
                                                              str(self.import_file_path).split(r'/')[-1].split('.')[0] +
                                                              '/齿轮箱A2口高速模式压力异常.csv')
                    if result[0]:
                        self.handle_signal_and_log([1, 13], [1, [1, "齿轮箱A2口高速模式压力正常"]])
                    else:
                        self.handle_signal_and_log([0, 13], [1, [0, "齿轮箱A2口高速模式压力异常"]])
                        self.handle_signal_and_log([0, 13], [0, [0, "齿轮箱A2口高速模式压力异常报警次数{}".format(len(result[1]))]])
                        for i in result[1]:
                            self.signal_gb_write_log.emit([1, [0, i]])
                        self.signal_gb_write_log.emit([1, [-1, "*" * 40]])
                if not df_l.empty:
                    result = tool.duration_calculation_to_csv(tickets,
                                                              df_l,
                                                              30,
                                                              str(self.import_file_path).split(r'/')[-1].split('.')[0] +
                                                              '/齿轮箱A2口低速模式压力异常.csv')
                    if result[0]:
                        self.handle_signal_and_log([1, 13], [1, [1, "齿轮箱A2口低速模式压力正常"]])
                    else:
                        self.handle_signal_and_log([0, 13], [1, [0, "齿轮箱A2口低速模式压力异常"]])
                        self.handle_signal_and_log([0, 13], [0, [0, "齿轮箱A2口低速模式压力异常报警次数{}".format(len(result[1]))]])
                        for i in result[1]:
                            self.signal_gb_write_log.emit([1, [0, i]])
                        self.signal_gb_write_log.emit([1, [-1, "*" * 40]])
            del df_h
            del df_l
        del df

    # 15 齿轮箱A3口压力异常,主轴承润滑
    def gearbox_A3_port_pressure(self):
        """
        齿轮箱A3口压力异常
        原理：
            1、齿轮箱油温>50，齿轮箱主泵2_1高速=1或齿轮箱主泵2_2高速=1，A3口压力<0.4或>0.7，且持续30s
            2、齿轮箱油温>50，齿轮箱主泵2_1低速=1或齿轮箱主泵2_2低速=1，A3口压力<0.25或>0.4，且持续30s
            满足以上其一报出A3口压力异常
        :return:
        """
        try:
            # 获取 时间 "齿轮箱油温"5,"齿轮箱主泵2_1高速22, 齿轮箱主泵2_2高速,23 齿轮箱主泵2_1低速24,齿轮箱主泵2_2低速25,齿轮箱A2口压力26英文标签
            tickets = [self.tickets[0], self.tickets[5], self.tickets[22], self.tickets[23],
                       self.tickets[24], self.tickets[25], self.tickets[27]]
            df = self.df[['time', tickets[0], tickets[1], tickets[2], tickets[3], tickets[4],
                          tickets[5], tickets[6]]]
            df.set_index(df['time'], inplace=True)
        except Exception as e:
            print(e)
            print("齿轮箱跳过函数15")
            self.handle_signal_and_log([-1, 14], [1, [-1, "齿轮箱A3口压力英文标签丢失"]])
            return
        # 绘图
        if self.draw:
            print("齿轮箱绘图15")
            df1 = df.copy()
            df1['timestamp'] = df[tickets[0]].apply(lambda x: time.mktime(time.strptime(x, '%Y-%m-%d %H:%M:%S')))
            self.drawing(graphicsView=self.plt_list[14],
                         canvas_setting={"title": "齿轮箱A3口压力时间图"},
                         data=[
                             {"pen": "g", "name": "齿轮箱油温", "x": df1['timestamp'], "y": df1[tickets[1]]},
                             {"pen": "r", "name": "A3口压力", "x": df1['timestamp'], "y": df1[tickets[6]]}
                         ])
            del df1
            gc.collect()

        # 删除温度低于50的数据
        df = df.drop(df[(df[tickets[1]] <= 50)].index)
        if df.empty:
            self.signal_gb_color.emit([1, 14])
            self.signal_gb_write_log.emit(
                time.strftime('%Y{y}%m{m}%d{d} %H{h}%M{f}%S{s}').format(y='年', m='月', d='日', h='时', f='分',
                                                                        s='秒') + ":齿轮箱A3口压力正常"
            )
        else:
            # 情况1 高速模式  1 3 ：2_1 2_2模式高速，0.4：压力在<4或>0.7
            df_h = df[((df[tickets[1]] == 1) | (df[tickets[3]] == 1)) &
                      ((df[tickets[6]] < 0.4) | (df[tickets[6]] > 0.7))].copy()
            # 情况2 低速模式  4 5 ：2_1 2_2模式低速，0.25：压力在<2.5或>0.4
            df_l = df[((df[tickets[4]] == 1) | (df[tickets[5]] == 1)) &
                      ((df[tickets[6]] < 0.25) | (df[tickets[6]] > 0.4))].copy()
            # 判断是否未空
            if df_h.empty and df_l.empty:
                self.handle_signal_and_log([1, 14], [1, [1, "齿轮箱A3口压力正常"]])
            else:
                # ------------------判断连续性
                # 高速模式连续时长判断
                if not df_h.empty:
                    result = tool.duration_calculation_to_csv(tickets,
                                                              df_h,
                                                              30,
                                                              str(self.import_file_path).split(r'/')[-1].split('.')[
                                                                  0] +
                                                              '/齿轮箱A3口高速模式压力异常.csv')
                    if result[0]:
                        self.handle_signal_and_log([1, 14], [1, [1, "齿轮箱A3口高速模式压力正常"]])
                    else:
                        self.handle_signal_and_log([0, 14], [1, [0, "齿轮箱A3口高速模式压力异常"]])
                        self.handle_signal_and_log([0, 14], [0, [0, "齿轮箱A3口高速模式压力异常报警次数{}".format(len(result[1]))]])
                        for i in result[1]:
                            self.signal_gb_write_log.emit([1, [0, i]])
                        self.signal_gb_write_log.emit([1, [-1, "*" * 40]])
                if not df_l.empty:
                    result = tool.duration_calculation_to_csv(tickets,
                                                              df_l,
                                                              30,
                                                              str(self.import_file_path).split(r'/')[-1].split('.')[
                                                                  0] +
                                                              '/齿轮箱A3口低速模式压力异常.csv')
                    if result[0]:
                        self.handle_signal_and_log([1, 14], [1, [1, "齿轮箱A3口低速模式压力正常"]])
                    else:
                        self.handle_signal_and_log([0, 14], [1, [0, "齿轮箱A3口低速模式压力异常"]])
                        self.handle_signal_and_log([0, 14], [0, [0, "齿轮箱A3口低速模式压力异常报警次数{}".format(len(result[1]))]])
                        for i in result[1]:
                            self.signal_gb_write_log.emit([1, [0, i]])
                        self.signal_gb_write_log.emit([1, [-1, "*" * 40]])
            del df_h
            del df_l
        del df

    # 16 齿轮箱A4口压力异常
    def gearbox_A4_port_pressure(self):
        """
            齿轮箱A4口压力异常
            齿轮箱油温>50，发电机润滑泵3_1或发电机润滑泵3_2=1,A4口压力<2或>5，且持续30s
        :return:
        """
        try:
            # 获取 时间 "齿轮箱油温"5,发电机润滑泵3_1或发电机润滑泵3_2=1  28 29 A4口压力 30英文标签
            tickets = [self.tickets[0], self.tickets[5], self.tickets[28], self.tickets[29],
                       self.tickets[30]]
            df = self.df[['time', tickets[0], tickets[1], tickets[2], tickets[3], tickets[4]]]
            df.set_index(df['time'], inplace=True)
            # 1 时间 2 机组模式 16 齿轮箱A3口温度
        except Exception as e:
            print(e)
            print("齿轮箱跳过函数16")
            self.handle_signal_and_log([-1, 15], [1, [-1, "齿轮箱A4口压力英文标签丢失"]])
            return
        # 绘图
        if self.draw:
            print("齿轮箱绘图16")
            df1 = df.copy()
            df1['timestamp'] = df[tickets[0]].apply(lambda x: time.mktime(time.strptime(x, '%Y-%m-%d %H:%M:%S')))
            self.drawing(graphicsView=self.plt_list[15],
                         canvas_setting={"title": "齿轮箱A1口压力时间图"},
                         data=[
                             {"pen": "g", "name": "齿轮箱油温", "x": df1['timestamp'], "y": df1[tickets[1]]},
                             {"pen": "r", "name": "A4口压力", "x": df1['timestamp'], "y": df1[tickets[4]]}
                         ])
            del df1
            gc.collect()

        # 删除温度低于50的数据
        df = df.drop(df[(df[tickets[1]] <= 50)].index)
        if df.empty:
            self.signal_gb_color.emit([1, 15])
            self.signal_gb_write_log.emit(
                time.strftime('%Y{y}%m{m}%d{d} %H{h}%M{f}%S{s}').format(y='年', m='月', d='日', h='时', f='分',
                                                                        s='秒') + ":齿轮箱A4口压力正常"
            )
        else:
            # 发电机润滑泵3_1或发电机润滑泵3_2=1,A4口压力<2或>5
            df = df[((df[tickets[2]] == 1) | (df[tickets[3]] == 1)) &
                    ((df[tickets[4]] < 2) | (df[tickets[4]] > 5))].copy()

            # 判断是否未空
            if df.empty:
                self.handle_signal_and_log([1, 15], [1, [1, "齿轮箱A4口压力正常"]])
            else:
                # ------------------判断连续性
                # 高速模式连续时长判断
                result = tool.duration_calculation_to_csv(tickets,
                                                          df,
                                                          30,
                                                          str(self.import_file_path).split(r'/')[-1].split('.')[
                                                              0] +
                                                          '/齿轮箱A4口压力异常.csv')
                if result[0]:
                    self.handle_signal_and_log([1, 15], [1, [1, "齿轮箱A4口压力正常"]])
                else:
                    self.handle_signal_and_log([0, 15], [1, [0, "齿轮箱A4口压力异常"]])
                    self.handle_signal_and_log([0, 15], [0, [0, "齿轮箱A4口压力异常报警次数{}".format(len(result[1]))]])
                    for i in result[1]:
                        self.signal_gb_write_log.emit([1, [0, i]])
                    self.signal_gb_write_log.emit([1, [-1, "*" * 40]])

        del df

    # 17 齿轮箱主泵1_1出口压力异常
    def gearbox_main_pump1_1_outlet_oil_pressure(self):
        """
            齿轮箱主泵1_1出口压力异常
            1、齿轮箱油温>50，齿轮箱主泵1_1高速=1，齿轮箱主泵1_1出口压力<4或>6.5，且持续30s
            2、齿轮箱油温>50，齿轮箱主泵1_1低速=1，齿轮箱主泵1_1出口压力<2.5或>5，且持续30s
            满足以上其一报出
        :return:
        """
        try:
            # 获取 时间 "齿轮箱油温"5,"齿轮箱主泵1_1高速"17,"齿轮箱主泵1_1低速"19,"齿轮箱主泵1_1出口压力" 31,英文标签
            tickets = [self.tickets[0], self.tickets[5], self.tickets[17], self.tickets[19], self.tickets[31]]
            df = self.df[['time', tickets[0], tickets[1], tickets[2], tickets[3], tickets[4]]]
            df.set_index(df['time'], inplace=True)
        except Exception as e:
            print(e)
            print("齿轮箱跳过函数17")
            self.handle_signal_and_log([-1, 16], [1, [-1, "齿轮箱主泵1_1出口压力英文标签丢失"]])
            return
            # 绘图
        if self.draw:
            print("齿轮箱绘图17")
            df1 = df.copy()
            df1['timestamp'] = df[tickets[0]].apply(lambda x: time.mktime(time.strptime(x, '%Y-%m-%d %H:%M:%S')))
            self.drawing(graphicsView=self.plt_list[16],
                         canvas_setting={"title": "齿轮箱主泵1_1出口压力时间图"},
                         data=[
                             {"pen": "g", "name": "齿轮箱油温", "x": df1['timestamp'], "y": df1[tickets[1]]},
                             {"pen": "r", "name": "齿轮箱主泵1_1出口压力", "x": df1['timestamp'], "y": df1[tickets[4]]}
                         ])
            del df1
            gc.collect()

            # 删除温度低于50的数据
        df = df.drop(df[(df[tickets[1]] <= 50)].index)
        if df.empty:
            self.signal_gb_color.emit([1, 16])
            self.signal_gb_write_log.emit(
                time.strftime('%Y{y}%m{m}%d{d} %H{h}%M{f}%S{s}').format(y='年', m='月', d='日', h='时', f='分',
                                                                        s='秒') + ":齿轮箱主泵1_1出口压力正常"
            )
        else:
            # 情况1 齿轮箱油温>50，齿轮箱主泵1_1高速=1，齿轮箱主泵1_1出口压力<4或>6.5，且持续30s
            df_h = df[(df[tickets[2]] == 1) &
                      ((df[tickets[4]] < 4) | (df[tickets[4]] > 6.5))].copy()
            # 齿轮箱油温>50，齿轮箱主泵1_1低速=1，齿轮箱主泵1_1出口压力<2.5或>5，且持续30s
            df_l = df[(df[tickets[3]] == 1) &
                      ((df[tickets[4]] < 2.5) | (df[tickets[4]] > 5))].copy()
            # 判断是否未空
            if df_h.empty and df_l.empty:
                self.handle_signal_and_log([1, 16], [1, [1, "齿轮箱主泵1_2出口压力正常"]])
            else:
                # ------------------判断连续性
                # 高速模式连续时长判断
                if not df_h.empty:
                    result = tool.duration_calculation_to_csv(tickets,
                                                              df_h,
                                                              30,
                                                              str(self.import_file_path).split(r'/')[-1].split('.')[0] +
                                                              '/齿轮箱主泵1_1出口高速模式压力异常.csv')
                    if result[0]:
                        self.handle_signal_and_log([1, 16], [1, [1, "齿轮箱主泵1_1出口高速模式压力正常"]])
                    else:
                        self.handle_signal_and_log([0, 16], [1, [0, "齿轮箱主泵1_1出口高速模式压力异常"]])
                        self.handle_signal_and_log([0, 16], [0, [0, "齿轮箱主泵1_1出口高速模式压力异常报警次数{}".format(len(result[1]))]])
                        for i in result[1]:
                            self.signal_gb_write_log.emit([1, [0, i]])
                        self.signal_gb_write_log.emit([1, [-1, "*" * 40]])
                if not df_l.empty:
                    result = tool.duration_calculation_to_csv(tickets,
                                                              df_l,
                                                              30,
                                                              str(self.import_file_path).split(r'/')[-1].split('.')[0] +
                                                              '/齿轮箱主泵1_1出口低速模式压力异常.csv')
                    if result[0]:
                        self.handle_signal_and_log([1, 16], [1, [1, "齿轮箱主泵1_1出口低速模式压力正常"]])
                    else:
                        self.handle_signal_and_log([0, 16], [1, [0, "齿轮箱主泵1_1出口低速模式压力异常"]])
                        self.handle_signal_and_log([0, 16], [0, [0, "齿轮箱主泵1_1出口低速模式压力异常报警次数{}".format(len(result[1]))]])
                        for i in result[1]:
                            self.signal_gb_write_log.emit([1, [0, i]])
                        self.signal_gb_write_log.emit([1, [-1, "*" * 40]])
            del df_h
            del df_l
        del df

    # 18 齿轮箱主泵1_2出口压力异常
    def gearbox_main_pump1_2_outlet_oil_pressure(self):
        """
            齿轮箱主泵1_1出口压力异常
            1、齿轮箱油温>50，齿轮箱主泵1_2高速=1，齿轮箱主泵1_2出口压力<4或>6.5，且持续30s
            2、齿轮箱油温>50，齿轮箱主泵1_2低速=1，齿轮箱主泵1_2出口压力<2.5或>5，且持续30s
            满足以上其一报出
        :return:
        """
        try:
            # 获取 时间 "齿轮箱油温"5,"齿轮箱主泵1_2高速"18,"齿轮箱主泵1_2低速"20,"齿轮箱主泵1_2出口压力" 32,英文标签
            tickets = [self.tickets[0], self.tickets[5], self.tickets[18], self.tickets[20], self.tickets[32]]
            df = self.df[['time', tickets[0], tickets[1], tickets[2], tickets[3], tickets[4]]]
            df.set_index(df['time'], inplace=True)
        except Exception as e:
            print(e)
            print("齿轮箱跳过函数18")
            self.handle_signal_and_log([-1, 17], [1, [-1, "齿轮箱主泵1_2出口压力英文标签丢失"]])
            return
            # 绘图
        if self.draw:
            print("齿轮箱绘图18")
            df1 = df.copy()
            df1['timestamp'] = df[tickets[0]].apply(lambda x: time.mktime(time.strptime(x, '%Y-%m-%d %H:%M:%S')))
            self.drawing(graphicsView=self.plt_list[17],
                         canvas_setting={"title": "齿轮箱主泵1_2出口压力时间图"},
                         data=[
                             {"pen": "g", "name": "齿轮箱油温", "x": df1['timestamp'], "y": df1[tickets[1]]},
                             {"pen": "r", "name": "齿轮箱主泵1_2出口压力", "x": df1['timestamp'], "y": df1[tickets[4]]}
                         ])
            del df1
            gc.collect()

            # 删除温度低于50的数据
        df = df.drop(df[(df[tickets[1]] <= 50)].index)
        if df.empty:
            self.signal_gb_color.emit([1, 17])
            self.signal_gb_write_log.emit(
                time.strftime('%Y{y}%m{m}%d{d} %H{h}%M{f}%S{s}').format(y='年', m='月', d='日', h='时', f='分',
                                                                        s='秒') + ":齿轮箱主泵1_2出口压力正常"
            )
        else:
            # 情况1 齿轮箱油温>50，齿轮箱主泵1_1高速=1，齿轮箱主泵1_1出口压力<4或>6.5，且持续30s
            df_h = df[(df[tickets[2]] == 1) &
                      ((df[tickets[4]] < 4) | (df[tickets[4]] > 6.5))].copy()
            # 齿轮箱油温>50，齿轮箱主泵1_1低速=1，齿轮箱主泵1_1出口压力<2.5或>5，且持续30s
            df_l = df[(df[tickets[3]] == 1) &
                      ((df[tickets[4]] < 2.5) | (df[tickets[4]] > 5))].copy()
            # 判断是否未空
            if df_h.empty and df_l.empty:
                self.handle_signal_and_log([1, 17], [1, [1, "齿轮箱主泵1_2出口压力正常"]])
            else:
                # ------------------判断连续性
                # 高速模式连续时长判断
                if not df_h.empty:
                    result = tool.duration_calculation_to_csv(tickets,
                                                              df_h,
                                                              30,
                                                              str(self.import_file_path).split(r'/')[-1].split('.')[0] +
                                                              '/齿轮箱主泵1_2出口高速模式压力异常.csv')
                    if result[0]:
                        self.handle_signal_and_log([1, 17], [1, [1, "齿轮箱主泵1_2出口高速模式压力正常"]])
                    else:
                        self.handle_signal_and_log([0, 17], [1, [0, "齿轮箱主泵1_2出口高速模式压力异常"]])
                        self.handle_signal_and_log([0, 17], [0, [0, "齿轮箱主泵1_2出口高速模式压力异常报警次数{}".format(len(result[1]))]])
                        for i in result[1]:
                            self.signal_gb_write_log.emit([1, [0, i]])
                        self.signal_gb_write_log.emit([1, [-1, "*" * 40]])
                if not df_l.empty:
                    result = tool.duration_calculation_to_csv(tickets,
                                                              df_l,
                                                              30,
                                                              str(self.import_file_path).split(r'/')[-1].split('.')[0] +
                                                              '/齿轮箱主泵1_2出口低速模式压力异常.csv')
                    if result[0]:
                        self.handle_signal_and_log([1, 17], [1, [1, "齿轮箱主泵1_2出口低速模式压力正常"]])
                    else:
                        self.handle_signal_and_log([0, 17], [1, [0, "齿轮箱主泵1_2出口低速模式压力异常"]])
                        self.handle_signal_and_log([0, 17], [0, [0, "齿轮箱主泵1_2出口低速模式压力异常报警次数{}".format(len(result[1]))]])
                        for i in result[1]:
                            self.signal_gb_write_log.emit([1, [0, i]])
                        self.signal_gb_write_log.emit([1, [-1, "*" * 40]])
            del df_h
            del df_l
        del df

    # 19 齿轮箱主泵2_1出口压力异常
    def gearbox_main_pump2_1_outlet_oil_pressure(self):
        """
            1、齿轮箱油温>50，齿轮箱主泵2_1高速=1，齿轮箱主泵2_1出口压力<4或>8，且持续30s
            2、齿轮箱油温>50，齿轮箱主泵2_1低速=1，齿轮箱主泵2_1出口压力<2或>4，且持续30s
            满足以上其一报出
        :return:
        """
        try:
            # 获取 时间 "齿轮箱油温"5,"齿轮箱主泵2_1高速"22,"齿轮箱主泵2_1低速"24,"齿轮箱主泵2_1出口压力" 33,英文标签
            tickets = [self.tickets[0], self.tickets[5], self.tickets[22], self.tickets[24], self.tickets[33]]
            df = self.df[['time', tickets[0], tickets[1], tickets[2], tickets[3], tickets[4]]]
            df.set_index(df['time'], inplace=True)
        except Exception as e:
            print(e)
            print("齿轮箱跳过函数19")
            self.handle_signal_and_log([-1, 18], [1, [-1, "齿轮箱主泵2_1出口压力英文标签丢失"]])
            return
            # 绘图
        if self.draw:
            print("齿轮箱绘图19")
            df1 = df.copy()
            df1['timestamp'] = df[tickets[0]].apply(lambda x: time.mktime(time.strptime(x, '%Y-%m-%d %H:%M:%S')))
            self.drawing(graphicsView=self.plt_list[18],
                         canvas_setting={"title": "齿轮箱主泵2_1出口压力时间图"},
                         data=[
                             {"pen": "g", "name": "齿轮箱油温", "x": df1['timestamp'], "y": df1[tickets[1]]},
                             {"pen": "r", "name": "齿轮箱主泵2_1出口压力", "x": df1['timestamp'], "y": df1[tickets[4]]}
                         ])
            del df1
            gc.collect()

            # 删除温度低于50的数据
        df = df.drop(df[(df[tickets[1]] <= 50)].index)
        if df.empty:
            self.signal_gb_color.emit([1, 18])
            self.signal_gb_write_log.emit(
                time.strftime('%Y{y}%m{m}%d{d} %H{h}%M{f}%S{s}').format(y='年', m='月', d='日', h='时', f='分',
                                                                        s='秒') + ":齿轮箱主泵2_1出口压力正常"
            )
        else:
            # 情况1 齿轮箱油温>50，齿轮箱主泵2_1高速=1，齿轮箱主泵2_1出口压力<4或>8，且持续30s
            df_h = df[(df[tickets[2]] == 1) &
                      ((df[tickets[4]] < 4) | (df[tickets[4]] > 8))].copy()
            # 情况2 齿轮箱油温>50，齿轮箱主泵2_1低速=1，齿轮箱主泵2_1出口压力<2或>4，且持续30s
            df_l = df[(df[tickets[3]] == 1) &
                      ((df[tickets[4]] < 2) | (df[tickets[4]] > 4))].copy()
            # 判断是否未空
            if df_h.empty and df_l.empty:
                self.handle_signal_and_log([1, 18], [1, [1, "齿轮箱主泵2_1出口压力正常"]])
            else:
                # ------------------判断连续性
                # 高速模式连续时长判断
                if not df_h.empty:
                    result = tool.duration_calculation_to_csv(tickets,
                                                              df_h,
                                                              30,
                                                              str(self.import_file_path).split(r'/')[-1].split('.')[0] +
                                                              '/齿轮箱主泵2_1出口压力高常.csv')
                    if result[0]:
                        self.handle_signal_and_log([1, 18], [1, [1, "齿轮箱主泵2_1出口压力正常"]])
                    else:
                        self.handle_signal_and_log([0, 18], [1, [0, "齿轮箱主泵2_1出口压力高"]])
                        self.handle_signal_and_log([0, 18], [0, [0, "齿轮箱主泵2_1出口压力高报警次数{}".format(len(result[1]))]])
                        for i in result[1]:
                            self.signal_gb_write_log.emit([1, [0, i]])
                        self.signal_gb_write_log.emit([1, [-1, "*" * 40]])
                if not df_l.empty:
                    result = tool.duration_calculation_to_csv(tickets,
                                                              df_l,
                                                              30,
                                                              str(self.import_file_path).split(r'/')[-1].split('.')[0] +
                                                              '/齿轮箱主泵2_1出口压力低.csv')
                    if result[0]:
                        self.handle_signal_and_log([1, 18], [1, [1, "齿轮箱主泵2_1出口压力正常"]])
                    else:
                        self.handle_signal_and_log([0, 18], [1, [0, "齿轮箱主泵2_1出口压力低"]])
                        self.handle_signal_and_log([0, 18], [0, [0, "齿轮箱主泵2_1出口压力低报警次数{}".format(len(result[1]))]])
                        for i in result[1]:
                            self.signal_gb_write_log.emit([1, [0, i]])
                        self.signal_gb_write_log.emit([1, [-1, "*" * 40]])
            del df_h
            del df_l
        del df

    # 20 齿轮箱主泵2_2出口压力异常
    def gearbox_main_pump2_2_outlet_oil_pressure(self):
        """
            1、齿轮箱油温>50，齿轮箱主泵2_2高速=1，齿轮箱主泵2_2出口压力<4或>8，且持续30s
            2、齿轮箱油温>50，齿轮箱主泵2_2低速=1，齿轮箱主泵2_2出口压力<2或>4，且持续30s
            满足以上其一报出
        :return:
        """
        try:
            # 获取 时间 "齿轮箱油温"5,"齿轮箱主泵2_2高速"23,"齿轮箱主泵2_2低速"25,"齿轮箱主泵2_2出口压力" 34,英文标签
            tickets = [self.tickets[0], self.tickets[5], self.tickets[23], self.tickets[25], self.tickets[34]]
            df = self.df[['time', tickets[0], tickets[1], tickets[2], tickets[3], tickets[4]]]
            df.set_index(df['time'], inplace=True)
        except Exception as e:
            print(e)
            print("齿轮箱跳过函数20")
            self.handle_signal_and_log([-1, 19], [1, [-1, "齿轮箱主泵2_2出口压力英文标签丢失"]])
            return
            # 绘图
        if self.draw:
            print("齿轮箱绘图20")
            df1 = df.copy()
            df1['timestamp'] = df[tickets[0]].apply(lambda x: time.mktime(time.strptime(x, '%Y-%m-%d %H:%M:%S')))
            self.drawing(graphicsView=self.plt_list[19],
                         canvas_setting={"title": "齿轮箱主泵2_2出口压力时间图"},
                         data=[
                             {"pen": "g", "name": "齿轮箱油温", "x": df1['timestamp'], "y": df1[tickets[1]]},
                             {"pen": "r", "name": "齿轮箱主泵2_2出口压力", "x": df1['timestamp'], "y": df1[tickets[4]]}
                         ])
            del df1
            gc.collect()

            # 删除温度低于50的数据
        df = df.drop(df[(df[tickets[1]] <= 50)].index)
        if df.empty:
            self.signal_gb_color.emit([1, 19])
            self.signal_gb_write_log.emit(
                time.strftime('%Y{y}%m{m}%d{d} %H{h}%M{f}%S{s}').format(y='年', m='月', d='日', h='时', f='分',
                                                                        s='秒') + ":齿轮箱主泵2_2出口压力正常"
            )
        else:
            # 情况1 齿轮箱油温>50，齿轮箱主泵2_2高速=1，齿轮箱主泵2_2出口压力<4或>8，且持续30s
            df_h = df[(df[tickets[2]] == 1) &
                      ((df[tickets[4]] < 4) | (df[tickets[4]] > 8))].copy()
            # 情况2 齿轮箱油温>50，齿轮箱主泵2_2低速=1，齿轮箱主泵2_2出口压力<2或>4，且持续30s
            df_l = df[(df[tickets[3]] == 1) &
                      ((df[tickets[4]] < 2) | (df[tickets[4]] > 4))].copy()
            # 判断是否未空
            if df_h.empty and df_l.empty:
                self.handle_signal_and_log([1, 19], [1, [1, "齿轮箱主泵2_2出口压力正常"]])
            else:
                # ------------------判断连续性
                # 高速模式连续时长判断
                if not df_h.empty:
                    result = tool.duration_calculation_to_csv(tickets,
                                                              df_h,
                                                              30,
                                                              str(self.import_file_path).split(r'/')[-1].split('.')[
                                                                  0] +
                                                              '/齿轮箱主泵2_2出口压力高常.csv')
                    if result[0]:
                        self.handle_signal_and_log([1, 19], [1, [1, "齿轮箱主泵2_2出口压力正常"]])
                    else:
                        self.handle_signal_and_log([0, 19], [1, [0, "齿轮箱主泵2_2出口压力高"]])
                        self.handle_signal_and_log([0, 19], [0, [0, "齿轮箱主泵2_2出口压力高报警次数{}".format(len(result[1]))]])
                        for i in result[1]:
                            self.signal_gb_write_log.emit([1, [0, i]])
                        self.signal_gb_write_log.emit([1, [-1, "*" * 40]])
                if not df_l.empty:
                    result = tool.duration_calculation_to_csv(tickets,
                                                              df_l,
                                                              30,
                                                              str(self.import_file_path).split(r'/')[-1].split('.')[
                                                                  0] +
                                                              '/齿轮箱主泵2_2出口压力低.csv')
                    if result[0]:
                        self.handle_signal_and_log([1, 19], [1, [1, "齿轮箱主泵2_2出口压力正常"]])
                    else:
                        self.handle_signal_and_log([0, 19], [1, [0, "齿轮箱主泵2_2出口压力低"]])
                        self.handle_signal_and_log([0, 19], [0, [0, "齿轮箱主泵2_2出口压力低报警次数{}".format(len(result[1]))]])
                        for i in result[1]:
                            self.signal_gb_write_log.emit([1, [0, i]])
                        self.signal_gb_write_log.emit([1, [-1, "*" * 40]])
            del df_h
            del df_l
        del df

    # 21 齿轮箱主泵滤芯压差1_1异常
    def gearbox_main_pump_filter1_1_oil_pressure_difference(self):
        """
        齿轮箱油温>45，齿轮箱主泵1_1出口压力≠0，齿轮箱主泵1_1高速=1，齿轮箱主泵1_1出口压力-齿轮箱A1口压力＞3.5，且持续5min
        :return:
        """
        try:
            # 获取 时间 0 齿轮箱油温 5 齿轮箱主泵1_1出口压力 31 齿轮箱主泵1_1高速 17  齿轮箱A1口压力 21 英文标签
            tickets = [self.tickets[0], self.tickets[5], self.tickets[31], self.tickets[17],
                       self.tickets[21]]
            df = self.df[['time', tickets[0], tickets[1], tickets[2], tickets[3], tickets[4]]]
            df.set_index(df['time'], inplace=True)
            # 1 时间 2 机组模式 13齿轮箱轮毂侧轴承温度
        except Exception as e:
            print(e)
            print("齿轮箱跳过函数21")
            self.handle_signal_and_log([-1, 20], [1, [-1, "齿轮箱主泵滤芯压差1_1英文标签丢失"]])
            return
            # 绘图
        # ****************************
        # 绘图部分未写
        # ****************************
        if self.draw:
            print("齿轮箱绘图21")
            df1 = df.copy()
            df1['timestamp'] = df[tickets[0]].apply(lambda x: time.mktime(time.strptime(x, '%Y-%m-%d %H:%M:%S')))
            self.drawing(graphicsView=self.plt_list[20],
                         canvas_setting={"title": "齿轮箱主泵滤芯压差1_1时间图"},
                         data=[
                             {"pen": "g", "name": "齿轮箱油温", "x": df1['timestamp'], "y": df1[tickets[1]]},
                             {"pen": "r", "name": "齿轮箱主泵1_1出口压力", "x": df1['timestamp'], "y": df1[tickets[2]]},
                             {"pen": "b", "name": "齿轮箱A1口压力", "x": df1['timestamp'], "y": df1[tickets[4]]}
                         ])
            del df1
            gc.collect()

        # 删除油温小于45
        df = df.drop(df[(df[tickets[1]] <= 45)].index)
        if df.empty:
            self.handle_signal_and_log([1, 20], [1, [1, "齿轮箱主泵滤芯压差1_1正常"]])
        else:
            # 删除齿轮箱主泵1_1出口压力=0
            df = df.drop(df[(df[tickets[2]] == 0)].index)
            if df.empty:
                self.handle_signal_and_log([1, 20], [1, [1, "齿轮箱主泵滤芯压差1_1正常"]])
            else:
                # 判断压差 齿轮箱主泵1_1高速=1，齿轮箱主泵1_1出口压力-齿轮箱A1口压力＞3.5，且持续5min
                df = df[(df[tickets[3]] == 1) & (df[tickets[2]] - df[tickets[4]] > 3.5)]
                # ------------------判断连续性
                result = tool.duration_calculation_to_csv(tickets,
                                                          df,
                                                          300,
                                                          str(self.import_file_path).split(r'/')[-1].split('.')[0] +
                                                          '/齿轮箱主泵滤芯压差1_1异常.csv')
                if result[0]:
                    self.handle_signal_and_log([1, 20], [1, [1, "齿轮箱主泵滤芯压差1_1正常"]])
                else:
                    self.handle_signal_and_log([0, 20], [1, [0, "齿轮箱主泵滤芯压差1_1异常"]])
                    self.handle_signal_and_log([0, 20], [0, [0, "齿轮箱主泵滤芯压差1_1异常报警次数{}".format(len(result[1]))]])
                    for i in result[1]:
                        self.signal_gb_write_log.emit([1, [0, i]])
                    self.signal_gb_write_log.emit([1, [-1, "*" * 40]])
        del df

    # 22 齿轮箱主泵滤芯压差1_2异常
    def gearbox_main_pump_filter1_2_oil_pressure_difference(self):
        """
        齿轮箱油温>45，齿轮箱主泵1_2出口压力≠0，齿轮箱主泵1_2高速=1，齿轮箱主泵1_2出口压力-齿轮箱A1口压力＞3.5，且持续5min
        :return:
        """
        try:
            # 获取 时间 0 齿轮箱油温 5 齿轮箱主泵1_2出口压力 32 齿轮箱主泵1_2高速 18  齿轮箱A1口压力 21 英文标签
            tickets = [self.tickets[0], self.tickets[5], self.tickets[32], self.tickets[18],
                       self.tickets[21]]
            df = self.df[['time', tickets[0], tickets[1], tickets[2], tickets[3], tickets[4]]]
            df.set_index(df['time'], inplace=True)
        except Exception as e:
            print(e)
            print("齿轮箱跳过函数22")
            self.handle_signal_and_log([-1, 21], [1, [-1, "齿轮箱主泵滤芯压差1_2英文标签丢失"]])
            return
            # 绘图
        # ****************************
        # 绘图部分未写
        # ****************************
        if self.draw:
            print("齿轮箱绘图22")
            df1 = df.copy()
            df1['timestamp'] = df[tickets[0]].apply(lambda x: time.mktime(time.strptime(x, '%Y-%m-%d %H:%M:%S')))
            self.drawing(graphicsView=self.plt_list[21],
                         canvas_setting={"title": "齿轮箱主泵滤芯压差1_2时间图"},
                         data=[
                             {"pen": "g", "name": "齿轮箱油温", "x": df1['timestamp'], "y": df1[tickets[1]]},
                             {"pen": "r", "name": "齿轮箱主泵1_2出口压力", "x": df1['timestamp'], "y": df1[tickets[2]]},
                             {"pen": "b", "name": "齿轮箱A1口压力", "x": df1['timestamp'], "y": df1[tickets[4]]}
                         ])
            del df1
            gc.collect()

        # 删除油温小于45
        df = df.drop(df[(df[tickets[1]] <= 45)].index)
        if df.empty:
            self.handle_signal_and_log([1, 21], [1, [1, "齿轮箱主泵滤芯压差1_2正常"]])
        else:
            # 删除齿轮箱主泵1_1出口压力=0
            df = df.drop(df[(df[tickets[2]] == 0)].index)
            if df.empty:
                self.handle_signal_and_log([1, 21], [1, [1, "齿轮箱主泵滤芯压差1_2正常"]])
            else:
                # 判断压差 齿轮箱主泵1_2高速=1，齿轮箱主泵1_2出口压力-齿轮箱A1口压力＞3.5，且持续5min
                df = df[(df[tickets[3]] == 1) & (df[tickets[2]] - df[tickets[4]] > 3.5)]
                # ------------------判断连续性
                result = tool.duration_calculation_to_csv(tickets,
                                                          df,
                                                          300,
                                                          str(self.import_file_path).split(r'/')[-1].split('.')[0] +
                                                          '/齿轮箱主泵滤芯压差1_2异常.csv')
                if result[0]:
                    self.handle_signal_and_log([1, 21], [1, [1, "齿轮箱主泵滤芯压差1_2正常"]])
                else:
                    self.handle_signal_and_log([0, 21], [1, [0, "齿轮箱主泵滤芯压差1_2异常"]])
                    self.handle_signal_and_log([0, 21], [0, [0, "齿轮箱主泵滤芯压差1_2异常报警次数{}".format(len(result[1]))]])
                    for i in result[1]:
                        self.signal_gb_write_log.emit([1, [0, i]])
                    self.signal_gb_write_log.emit([1, [-1, "*" * 40]])
        del df

    # 23 齿轮箱主泵滤芯压差2_1异常
    def gearbox_main_pump_filter2_1_oil_pressure_difference(self):
        """
        齿轮箱油温>45，齿轮箱主泵2_1出口压力≠0，齿轮箱主泵2_1高速=1，齿轮箱主泵2_1出口压力-齿轮箱A2口压力＞3.5，且持续5min
        :return:
        """
        try:
            # 获取 时间 0 齿轮箱油温 5 齿轮箱主泵2_1出口压力 33 齿轮箱主泵2_1高速 22  齿轮箱A2口压力 26 英文标签
            tickets = [self.tickets[0], self.tickets[5], self.tickets[33], self.tickets[22],
                       self.tickets[26]]
            df = self.df[['time', tickets[0], tickets[1], tickets[2], tickets[3], tickets[4]]]
            df.set_index(df['time'], inplace=True)
        except Exception as e:
            print(e)
            print("齿轮箱跳过函数23")
            self.handle_signal_and_log([-1, 22], [1, [-1, "齿轮箱主泵滤芯压差2_1英文标签丢失"]])
            return
            # 绘图
        # ****************************
        # 绘图部分未写
        # ****************************
        if self.draw:
            print("齿轮箱绘图23")
            df1 = df.copy()
            df1['timestamp'] = df[tickets[0]].apply(lambda x: time.mktime(time.strptime(x, '%Y-%m-%d %H:%M:%S')))
            self.drawing(graphicsView=self.plt_list[22],
                         canvas_setting={"title": "齿轮箱主泵滤芯压差2_1时间图"},
                         data=[
                             {"pen": "g", "name": "齿轮箱油温", "x": df1['timestamp'], "y": df1[tickets[1]]},
                             {"pen": "r", "name": "齿轮箱主泵2_1出口压力", "x": df1['timestamp'], "y": df1[tickets[2]]},
                             {"pen": "b", "name": "齿轮箱A2口压力", "x": df1['timestamp'], "y": df1[tickets[4]]}
                         ])
            del df1
            gc.collect()

        # 删除油温小于45
        df = df.drop(df[(df[tickets[1]] <= 45)].index)
        if df.empty:
            self.handle_signal_and_log([1, 22], [1, [1, "齿轮箱主泵滤芯压差2_1正常"]])
        else:
            # 删除齿轮箱主泵1_1出口压力=0
            df = df.drop(df[(df[tickets[2]] == 0)].index)
            if df.empty:
                self.handle_signal_and_log([1, 22], [1, [1, "齿轮箱主泵滤芯压差2_1正常"]])
            else:
                # 判断压差 齿轮箱主泵2_1高速=1，齿轮箱主泵2_1出口压力-齿轮箱A1口压力＞3.5，且持续5min
                df = df[(df[tickets[3]] == 1) & (df[tickets[2]] - df[tickets[4]] > 3.5)]
                # ------------------判断连续性
                result = tool.duration_calculation_to_csv(tickets,
                                                          df,
                                                          300,
                                                          str(self.import_file_path).split(r'/')[-1].split('.')[0] +
                                                          '/齿轮箱主泵滤芯压差2_1异常.csv')
                if result[0]:
                    self.handle_signal_and_log([1, 22], [1, [1, "齿轮箱主泵滤芯压差2_1正常"]])
                else:
                    self.handle_signal_and_log([0, 22], [1, [0, "齿轮箱主泵滤芯压差2_1异常"]])
                    self.handle_signal_and_log([0, 22], [0, [0, "齿轮箱主泵滤芯压差2_1异常报警次数{}".format(len(result[1]))]])
                    for i in result[1]:
                        self.signal_gb_write_log.emit([1, [0, i]])
                    self.signal_gb_write_log.emit([1, [-1, "*" * 40]])
        del df

    # 24 齿轮箱主泵滤芯压差2_2异常
    def gearbox_main_pump_filter2_2_oil_pressure_difference(self):
        """
        齿轮箱油温>45，齿轮箱主泵2_2出口压力≠0，齿轮箱主泵2_2高速=1，齿轮箱主泵2_2出口压力-齿轮箱A2口压力＞3.5，且持续5min
        :return:
        """
        try:
            # 获取 时间 0 齿轮箱油温 5 齿轮箱主泵2_2出口压力 34 齿轮箱主泵2_2高速 23  齿轮箱A2口压力 26 英文标签
            tickets = [self.tickets[0], self.tickets[5], self.tickets[34], self.tickets[23],
                       self.tickets[26]]
            df = self.df[['time', tickets[0], tickets[1], tickets[2], tickets[3], tickets[4]]]
            df.set_index(df['time'], inplace=True)
        except Exception as e:
            print(e)
            print("齿轮箱跳过函数24")
            self.handle_signal_and_log([-1, 23], [1, [-1, "齿轮箱主泵滤芯压差2_2英文标签丢失"]])
            return
            # 绘图
        # ****************************
        # 绘图部分未写
        # ****************************
        if self.draw:
            print("齿轮箱绘图24")
            df1 = df.copy()
            df1['timestamp'] = df[tickets[0]].apply(lambda x: time.mktime(time.strptime(x, '%Y-%m-%d %H:%M:%S')))
            self.drawing(graphicsView=self.plt_list[23],
                         canvas_setting={"title": "齿轮箱主泵滤芯压差2_2时间图"},
                         data=[
                             {"pen": "g", "name": "齿轮箱油温", "x": df1['timestamp'], "y": df1[tickets[1]]},
                             {"pen": "r", "name": "齿轮箱主泵2_2出口压力", "x": df1['timestamp'], "y": df1[tickets[2]]},
                             {"pen": "b", "name": "齿轮箱A2口压力", "x": df1['timestamp'], "y": df1[tickets[4]]}
                         ])
            del df1
            gc.collect()

        # 删除油温小于45
        df = df.drop(df[(df[tickets[1]] <= 45)].index)
        if df.empty:
            self.handle_signal_and_log([1, 23], [1, [1, "齿轮箱主泵滤芯压差2_2正常"]])
        else:
            # 删除齿轮箱主泵1_1出口压力=0
            df = df.drop(df[(df[tickets[2]] == 0)].index)
            if df.empty:
                self.handle_signal_and_log([1, 23], [1, [1, "齿轮箱主泵滤芯压差2_2正常"]])
            else:
                # 判断压差 齿轮箱主泵2_1高速=1，齿轮箱主泵2_1出口压力-齿轮箱A1口压力＞3.5，且持续5min
                df = df[(df[tickets[3]] == 1) & (df[tickets[2]] - df[tickets[4]] > 3.5)]
                # ------------------判断连续性
                result = tool.duration_calculation_to_csv(tickets,
                                                          df,
                                                          300,
                                                          str(self.import_file_path).split(r'/')[-1].split('.')[0] +
                                                          '/齿轮箱主泵滤芯压差2_2异常.csv')
                if result[0]:
                    self.handle_signal_and_log([1, 23], [1, [1, "齿轮箱主泵滤芯压差2_2正常"]])
                else:
                    self.handle_signal_and_log([0, 23], [1, [0, "齿轮箱主泵滤芯压差2_2异常"]])
                    self.handle_signal_and_log([0, 23], [0, [0, "齿轮箱主泵滤芯压差2_2异常报警次数{}".format(len(result[1]))]])
                    for i in result[1]:
                        self.signal_gb_write_log.emit([1, [0, i]])
                    self.signal_gb_write_log.emit([1, [-1, "*" * 40]])
        del df

    # 25 齿轮箱冷却泵出口压力异常
    def gearbox_cooling_pump_outlet_oil_pressure(self):
        """
        齿轮箱油温>55，齿轮箱冷却泵出口压力≠0，齿轮箱冷却泵=1，齿轮箱冷却泵出口压力<2或>7，且持续30s
        :return:
        """
        try:
            # 获取 时间 齿轮箱油温 5 齿轮箱冷却泵出口压力 35 齿轮箱冷却泵 36 英文标签
            tickets = [self.tickets[0], self.tickets[5], self.tickets[35], self.tickets[36]]
            df = self.df[['time', tickets[0], tickets[1], tickets[2], tickets[3]]]
            df.set_index(df['time'], inplace=True)
        except Exception as e:
            print(e)
            print("齿轮箱跳过函数25")
            self.handle_signal_and_log([-1, 24], [1, [-1, "齿轮箱冷却泵出口压力英文标签丢失"]])
            return
        # 绘图
        if self.draw:
            print("齿轮箱绘图25")
            df1 = df.copy()
            df1['timestamp'] = df[tickets[0]].apply(lambda x: time.mktime(time.strptime(x, '%Y-%m-%d %H:%M:%S')))
            self.drawing(graphicsView=self.plt_list[24],
                         canvas_setting={"title": "齿轮箱冷却泵出口压力时间图"},
                         data=[
                             {"pen": "g", "name": "齿轮箱油温", "x": df1['timestamp'], "y": df1[tickets[1]]},
                             {"pen": "r", "name": "齿轮箱冷却泵出口压力", "x": df1['timestamp'], "y": df1[tickets[3]]}
                         ])
            del df1
            gc.collect()

        # 删除油温小于55
        df = df.drop(df[(df[tickets[1]] <= 55)].index)
        if df.empty:
            self.handle_signal_and_log([1, 24], [1, [1, "齿轮箱冷却泵出口压力正常"]])
        else:
            # 删除齿轮箱冷却泵出口压力=0
            df = df.drop(df[(df[tickets[2]] == 0)].index)
            if df.empty:
                self.handle_signal_and_log([1, 24], [1, [1, "齿轮箱冷却泵出口压力正常"]])
            else:
                # 判断 齿轮箱冷却泵=1，齿轮箱冷却泵出口压力<2或>7，且持续30s
                df = df[(df[tickets[3]] == 1) & ((df[tickets[2]] < 2) | (df[tickets[2]] > 7))]
                # ------------------判断连续性
                result = tool.duration_calculation_to_csv(tickets,
                                                          df,
                                                          30,
                                                          str(self.import_file_path).split(r'/')[-1].split('.')[0] +
                                                          '/齿轮箱冷却泵出口压力异常.csv')
                if result[0]:
                    self.handle_signal_and_log([1, 24], [1, [1, "齿轮箱冷却泵出口压力正常"]])
                else:
                    self.handle_signal_and_log([0, 24], [1, [0, "齿轮箱冷却泵出口压力异常"]])
                    self.handle_signal_and_log([0, 24], [0, [0, "齿轮箱冷却泵出口压力异常报警次数{}".format(len(result[1]))]])
                    for i in result[1]:
                        self.signal_gb_write_log.emit([1, [0, i]])
                    self.signal_gb_write_log.emit([1, [-1, "*" * 40]])
        del df

    # 26 齿轮箱过滤泵出口压力异常
    def gearbox_bypass_pump_outlet_oil_pressure(self):
        """
        齿轮箱油温>50，齿轮箱过滤泵=1，齿轮箱过滤泵出口压力<1或>4，且持续30s
        :return:
        """
        try:
            # 获取 时间 齿轮箱油温 5 齿轮箱过滤泵 37 齿轮箱过滤泵出口压力 38 英文标签
            tickets = [self.tickets[0], self.tickets[5], self.tickets[37], self.tickets[38]]
            df = self.df[['time', tickets[0], tickets[1], tickets[2], tickets[3]]]
            df.set_index(df['time'], inplace=True)
        except Exception as e:
            print(e)
            print("齿轮箱跳过函数26")
            self.handle_signal_and_log([-1, 25], [1, [-1, "齿轮箱过滤泵出口压力英文标签丢失"]])
            return
            # 绘图
        if self.draw:
            print("齿轮箱绘图26")
            df1 = df.copy()
            df1['timestamp'] = df[tickets[0]].apply(lambda x: time.mktime(time.strptime(x, '%Y-%m-%d %H:%M:%S')))
            self.drawing(graphicsView=self.plt_list[25],
                         canvas_setting={"title": "齿轮箱过滤泵出口压力时间图"},
                         data=[
                             {"pen": "g", "name": "齿轮箱油温", "x": df1['timestamp'], "y": df1[tickets[1]]},
                             {"pen": "r", "name": "齿轮箱过滤泵出口压力", "x": df1['timestamp'], "y": df1[tickets[3]]}
                         ])
            del df1
            gc.collect()

            # 删除油温小于50
        df = df.drop(df[(df[tickets[1]] <= 50)].index)
        if df.empty:
            self.handle_signal_and_log([1, 25], [1, [1, "齿轮箱冷却泵出口压力正常"]])
        else:
            # 判断 齿轮箱过滤泵=1，齿轮箱过滤泵出口压力<1或>4，且持续30s
            df = df[(df[tickets[2]] == 1) & ((df[tickets[3]] < 1) | (df[tickets[3]] > 4))]
            # ------------------判断连续性
            result = tool.duration_calculation_to_csv(tickets,
                                                      df,
                                                      30,
                                                      str(self.import_file_path).split(r'/')[-1].split('.')[0] +
                                                      '/齿轮箱过滤泵出口压力异常.csv')
            if result[0]:
                self.handle_signal_and_log([1, 25], [1, [1, "齿轮箱过滤泵出口压力正常"]])
            else:
                self.handle_signal_and_log([0, 25], [1, [0, "齿轮箱过滤泵出口压力异常"]])
                self.handle_signal_and_log([0, 25], [0, [0, "齿轮箱过滤泵出口压力异常报警次数{}".format(len(result[1]))]])
                for i in result[1]:
                    self.signal_gb_write_log.emit([1, [0, i]])
                self.signal_gb_write_log.emit([1, [-1, "*" * 40]])
        del df

    # 27 齿轮箱油位异常
    def gearbox_oil_level(self):
        """
        12≤运行模式≤14，齿轮箱油位>80%或<30%，持续30s
        :return:
        """
        try:
            # 获取 1 时间 2 机组模式 3 齿轮箱主轴承温度英文标签
            tickets = [self.tickets[0], self.tickets[1], self.tickets[39]]
            # print([self.tickets[0], self.tickets[1], self.tickets[39]])
            df = self.df[['time', tickets[0], tickets[1], tickets[2]]]
            df.set_index(df['time'], inplace=True)
        except Exception as e:
            print(e)
            print("齿轮箱跳过函数27")
            self.handle_signal_and_log([-1, 26], [1, [-1, "齿轮箱油位英文标签丢失"]])
            return

        if self.draw:
            print("齿轮箱绘图27")
            df1 = df.copy()
            df1['timestamp'] = df[tickets[0]].apply(lambda x: time.mktime(time.strptime(x, '%Y-%m-%d %H:%M:%S')))
            self.drawing(graphicsView=self.plt_list[26],
                         canvas_setting={"title": "齿轮箱油位时间图"},
                         data=[
                             {"pen": "g", "name": "齿轮箱油位", "x": df1['timestamp'], "y": df1[tickets[1]]}
                         ])
            del df1
            gc.collect()

        # 删除不在12-14之间
        df = df.drop(df[(df[tickets[1]] > 14) | (df[tickets[1]] < 12)].index)
        if df.empty:
            self.handle_signal_and_log([1, 26], [1, [1, "齿轮箱油位正常"]])

        else:
            # 删除齿轮箱油位<=80%且>=30%
            df = df.drop(df[(df[tickets[2]] >= 30 & (df[tickets[2]] <= 80))].index)

            if df.empty:
                self.handle_signal_and_log([1, 26], [1, [1, "齿轮箱油位正常"]])

            else:
                # ------------------判断连续性
                result = tool.duration_calculation_to_csv(tickets,
                                                          df,
                                                          30,
                                                          str(self.import_file_path).split(r'/')[-1].split('.')[0] +
                                                          '/齿轮箱油位异常.csv')
                if result[0]:
                    self.handle_signal_and_log([1, 26], [1, [1, "齿轮箱油位正常"]])

                else:
                    self.handle_signal_and_log([0, 26], [1, [0, "齿轮箱油位异常"]])
                    self.handle_signal_and_log([0, 26], [0, [0, "齿轮箱油位异常报警次数{}".format(len(result[1]))]])

                    for i in result[1]:
                        self.signal_gb_write_log.emit([1, [0, i]])
                    self.signal_gb_write_log.emit([1, [-1, "*" * 40]])

        del df
        del tickets
        gc.collect()

    # ******************************************
    # 此函数没有持续时长判断
    # ******************************************
    # 28 齿轮箱水泵1温差异常
    def gearbox_water_pump1_temperature_difference(self):
        """
        齿轮箱水泵1启动=1，齿轮箱水冷风扇1高速启动=1，齿轮箱水泵出口温度-齿轮箱水泵入口温度1＜2.2
        :return:
        """
        try:
            # 获取 时间 0 齿轮箱水泵1启动 40 齿轮箱水冷风扇1高速启动 41 齿轮箱水泵出口温度 10 齿轮箱水泵入口温度1 11 英文标签
            tickets = [self.tickets[0], self.tickets[40], self.tickets[41], self.tickets[10],
                       self.tickets[11]]
            df = self.df[['time', tickets[0], tickets[1], tickets[2], tickets[3], tickets[4]]]
            df.set_index(df['time'], inplace=True)
        except Exception as e:
            print(e)
            print("齿轮箱跳过函数28")
            self.handle_signal_and_log([-1, 27], [1, [-1, "齿轮箱水泵1温差英文标签丢失"]])
            return
            # 绘图
        # ****************************
        # 绘图部分未写
        # ****************************
        if self.draw:
            print("齿轮箱绘图28")
            df1 = df.copy()
            df1['timestamp'] = df[tickets[0]].apply(lambda x: time.mktime(time.strptime(x, '%Y-%m-%d %H:%M:%S')))
            self.drawing(graphicsView=self.plt_list[27],
                         canvas_setting={"title": "齿轮箱水泵1温差时间图"},
                         data=[
                             {"pen": "g", "name": "齿轮箱水泵出口温度 ", "x": df1['timestamp'], "y": df1[tickets[3]]},
                             {"pen": "r", "name": "齿轮箱水泵入口温度1 ", "x": df1['timestamp'], "y": df1[tickets[4]]}
                         ])
            del df1
            gc.collect()

        # 删除 齿轮箱水泵1启动 =1
        df = df.drop(df[(df[tickets[1]] != 1)].index)
        if df.empty:
            self.handle_signal_and_log([1, 27], [1, [1, "齿轮箱水泵1温差正常"]])
        else:
            # 判断 齿轮箱水冷风扇1高速启动=1，齿轮箱水泵出口温度-齿轮箱水泵入口温度1＜2.2
            df = df[(df[tickets[2]] == 1) & (df[tickets[3]] - df[tickets[4]] < 2.2)]
            # ------------------判断连续性
            result = tool.duration_calculation_to_csv(tickets,
                                                      df,
                                                      1,
                                                      str(self.import_file_path).split(r'/')[-1].split('.')[0] +
                                                      '/齿轮箱水泵1温差异常.csv')
            if result[0]:
                self.handle_signal_and_log([1, 27], [1, [1, "齿轮箱水泵1温差正常"]])
            else:
                self.handle_signal_and_log([0, 27], [1, [0, "齿轮箱水泵1温差异常"]])
                self.handle_signal_and_log([0, 27], [0, [0, "齿轮箱水泵1温差异常报警次数{}".format(len(result[1]))]])
                for i in result[1]:
                    self.signal_gb_write_log.emit([1, [0, i]])
                self.signal_gb_write_log.emit([1, [-1, "*" * 40]])
        del df

    # ******************************************
    # 此函数没有持续时长判断
    # ******************************************
    # 29 齿轮箱水泵2温差异常
    def gearbox_water_pump2_temperature_difference(self):
        """
        齿轮箱水泵2启动=1，齿轮箱水冷风扇2高速启动=1，齿轮箱水泵出口温度-齿轮箱水泵入口温度2＜2.2
        :return:
        """
        try:
            # 获取 时间 0 齿轮箱水泵2启动 42 齿轮箱水冷风扇2高速启动 43 齿轮箱水泵出口温度 10 齿轮箱水泵入口温度2 12 英文标签
            tickets = [self.tickets[0], self.tickets[42], self.tickets[43], self.tickets[10],
                       self.tickets[12]]
            df = self.df[['time', tickets[0], tickets[1], tickets[2], tickets[3], tickets[4]]]
            df.set_index(df['time'], inplace=True)
        except Exception as e:
            print(e)
            print("齿轮箱跳过函数29")
            self.handle_signal_and_log([-1, 27], [1, [-1, "齿轮箱水泵2温差英文标签丢失"]])
            return
        # 绘图
        if self.draw:
            print("齿轮箱绘图29")
            df1 = df.copy()
            df1['timestamp'] = df[tickets[0]].apply(lambda x: time.mktime(time.strptime(x, '%Y-%m-%d %H:%M:%S')))
            self.drawing(graphicsView=self.plt_list[28],
                         canvas_setting={"title": "齿轮箱水泵2温差时间图"},
                         data=[
                             {"pen": "g", "name": "齿轮箱水泵出口温度 ", "x": df1['timestamp'], "y": df1[tickets[3]]},
                             {"pen": "r", "name": "齿轮箱水泵入口温度2 ", "x": df1['timestamp'], "y": df1[tickets[4]]}
                         ])
            del df1
            gc.collect()

        # 删除 齿轮箱水泵1启动 =1
        df = df.drop(df[(df[tickets[1]] != 1)].index)
        if df.empty:
            self.handle_signal_and_log([1, 28], [1, [1, "齿轮箱水泵2温差正常"]])
        else:
            # 判断 齿轮箱水冷风扇2高速启动=1，齿轮箱水泵出口温度-齿轮箱水泵入口温度2＜2.2
            df = df[(df[tickets[2]] == 1) & (df[tickets[3]] - df[tickets[4]] < 2.2)]
            # ------------------判断连续性
            result = tool.duration_calculation_to_csv(tickets,
                                                      df,
                                                      1,
                                                      str(self.import_file_path).split(r'/')[-1].split('.')[0] +
                                                      '/齿轮箱水泵2温差.csv')
            if result[0]:
                self.handle_signal_and_log([1, 28], [1, [1, "齿轮箱水泵2温差正常"]])
            else:
                self.handle_signal_and_log([0, 28], [1, [0, "齿轮箱水泵2温差异常"]])
                self.handle_signal_and_log([0, 28], [0, [0, "齿轮箱水泵2温差异常报警次数{}".format(len(result[1]))]])
                for i in result[1]:
                    self.signal_gb_write_log.emit([1, [0, i]])
                self.signal_gb_write_log.emit([1, [-1, "*" * 40]])
        del df

    # 30 齿轮箱水泵1出口压力异常
    def gearbox_water_pump1_outlet_oil_pressure(self):
        """
        齿轮箱水泵1启动=1，齿轮箱水泵1出口压力小于3或者大于6，持续30s
        :return:
        """
        try:
            # 获取  时间 0 齿轮箱水泵1启动 40 齿轮箱水泵1出口压力 44 英文标签
            tickets = [self.tickets[0], self.tickets[40], self.tickets[44]]
            # print([self.tickets[0], self.tickets[1], self.tickets[39]])
            df = self.df[['time', tickets[0], tickets[1], tickets[2]]]
            df.set_index(df['time'], inplace=True)
        except Exception as e:
            print(e)
            print("齿轮箱跳过函数30")
            self.handle_signal_and_log([-1, 29], [1, [-1, "齿轮箱水泵1出口压力英文标签丢失"]])
            return

        # 绘图
        if self.draw:
            print("齿轮箱绘图30")
            df1 = df.copy()
            df1['timestamp'] = df[tickets[0]].apply(lambda x: time.mktime(time.strptime(x, '%Y-%m-%d %H:%M:%S')))
            self.drawing(graphicsView=self.plt_list[29],
                         canvas_setting={"title": "齿轮箱水泵1出口压力时间图"},
                         data=[
                             {"pen": "g", "name": "齿轮箱水泵1出口压力 ", "x": df1['timestamp'], "y": df1[tickets[2]]}
                         ])
            del df1
            gc.collect()

        # 删除齿轮箱水泵1启动 !=1
        df = df.drop(df[(df[tickets[1]] != 1)].index)
        if df.empty:
            self.handle_signal_and_log([1, 29], [1, [1, "齿轮箱油位正常"]])
        else:
            # 齿轮箱水泵1出口压力小于3或者大于6，持续30s
            # 删除3-6之间
            df = df.drop(df[(df[tickets[2]] >= 3 & (df[tickets[2]] <= 6))].index)

            if df.empty:
                self.handle_signal_and_log([1, 29], [1, [1, "齿轮箱水泵1出口压力正常"]])
            else:
                # ------------------判断连续性
                result = tool.duration_calculation_to_csv(tickets,
                                                          df,
                                                          30,
                                                          str(self.import_file_path).split(r'/')[-1].split('.')[0] +
                                                          '/齿轮箱水泵1出口压力异常.csv')
                if result[0]:
                    self.handle_signal_and_log([1, 29], [1, [1, "齿轮箱水泵1出口压力正常"]])

                else:
                    self.handle_signal_and_log([0, 29], [1, [0, "齿轮箱水泵1出口压力异常"]])
                    self.handle_signal_and_log([0, 29], [0, [0, "齿轮箱水泵1出口压力异常报警次数{}".format(len(result[1]))]])
                    for i in result[1]:
                        self.signal_gb_write_log.emit([1, [0, i]])
                    self.signal_gb_write_log.emit([1, [-1, "*" * 40]])

        del df
        del tickets
        gc.collect()

    # 31 齿轮箱水泵1入口压力异常
    def gearbox_water_pump1_inlet_oil_pressure(self):
        """
        齿轮箱水泵1启动=1，齿轮箱水泵1入口压力小于1或大于3，持续30s
        :return:
        """
        try:
            # 获取  时间 0 齿轮箱水泵1启动 40 齿轮箱水泵1入口压力 45 英文标签
            tickets = [self.tickets[0], self.tickets[40], self.tickets[45]]
            df = self.df[['time', tickets[0], tickets[1], tickets[2]]]
            df.set_index(df['time'], inplace=True)
        except Exception as e:
            print(e)
            print("齿轮箱跳过函数31")
            self.handle_signal_and_log([-1, 30], [1, [-1, "齿轮箱水泵1入口压力英文标签丢失"]])
            return

        # 绘图
        if self.draw:
            print("齿轮箱绘图31")
            df1 = df.copy()
            df1['timestamp'] = df[tickets[0]].apply(lambda x: time.mktime(time.strptime(x, '%Y-%m-%d %H:%M:%S')))
            self.drawing(graphicsView=self.plt_list[30],
                         canvas_setting={"title": "齿轮箱水泵1入口压力时间图"},
                         data=[
                             {"pen": "g", "name": "齿轮箱水泵1入口压力 ", "x": df1['timestamp'], "y": df1[tickets[2]]}
                         ])
            del df1
            gc.collect()

        # 删除齿轮箱水泵1启动 !=1
        df = df.drop(df[(df[tickets[1]] != 1)].index)
        if df.empty:
            self.handle_signal_and_log([1, 30], [1, [1, "齿轮箱水泵1入口压力正常"]])
        else:
            # 齿轮箱水泵1入口压力小于1或大于3，持续30s
            # 删除1-3之间
            df = df.drop(df[(df[tickets[2]] >= 1 & (df[tickets[2]] <= 3))].index)

            if df.empty:
                self.handle_signal_and_log([1, 30], [1, [1, "齿轮箱水泵1入口压力正常"]])
            else:
                # ------------------判断连续性
                result = tool.duration_calculation_to_csv(tickets,
                                                          df,
                                                          30,
                                                          str(self.import_file_path).split(r'/')[-1].split('.')[0] +
                                                          '/齿轮箱水泵1入口压力异常.csv')
                if result[0]:
                    self.handle_signal_and_log([1, 30], [1, [1, "齿轮箱水泵1入口压力正常"]])

                else:
                    self.handle_signal_and_log([0, 30], [1, [0, "齿轮箱水泵1入口压力异常"]])
                    self.handle_signal_and_log([0, 30], [0, [0, "齿轮箱水泵1入口压力异常报警次数{}".format(len(result[1]))]])
                    for i in result[1]:
                        self.signal_gb_write_log.emit([1, [0, i]])
                    self.signal_gb_write_log.emit([1, [-1, "*" * 40]])

        del df
        del tickets
        gc.collect()

    # 32 齿轮箱水泵2出口压力异常
    def gearbox_water_pump2_outlet_oil_pressure(self):
        """
        齿轮箱水泵2启动=1，齿轮箱水泵2出口压力小于3或者大于6，持续30s
        :return:
        """
        try:
            # 获取  时间 0 齿轮箱水泵2启动 42 齿轮箱水泵2出口压力 46 英文标签
            tickets = [self.tickets[0], self.tickets[42], self.tickets[46]]
            df = self.df[['time', tickets[0], tickets[1], tickets[2]]]
            df.set_index(df['time'], inplace=True)
        except Exception as e:
            print(e)
            print("齿轮箱跳过函数32")
            self.handle_signal_and_log([-1, 32], [1, [-1, "齿轮箱水泵2出口压力英文标签丢失"]])
            return

        # 绘图
        if self.draw:
            print("齿轮箱绘图32")
            df1 = df.copy()
            df1['timestamp'] = df[tickets[0]].apply(lambda x: time.mktime(time.strptime(x, '%Y-%m-%d %H:%M:%S')))
            self.drawing(graphicsView=self.plt_list[31],
                         canvas_setting={"title": "齿轮箱水泵2出口压力时间图"},
                         data=[
                             {"pen": "g", "name": "齿轮箱水泵2出口压力 ", "x": df1['timestamp'], "y": df1[tickets[2]]}
                         ])
            del df1
            gc.collect()

        # 删除齿轮箱水泵1启动 !=1
        df = df.drop(df[(df[tickets[1]] != 1)].index)
        if df.empty:
            self.handle_signal_and_log([1, 31], [1, [1, "齿轮箱水泵2出口压力正常"]])
        else:
            # 齿轮箱水泵1出口压力小于3或者大于6，持续30s
            # 删除3-6之间
            df = df.drop(df[(df[tickets[2]] >= 3 & (df[tickets[2]] <= 6))].index)

            if df.empty:
                self.handle_signal_and_log([1, 31], [1, [1, "齿轮箱水泵2出口压力正常"]])
            else:
                # ------------------判断连续性
                result = tool.duration_calculation_to_csv(tickets,
                                                          df,
                                                          30,
                                                          str(self.import_file_path).split(r'/')[-1].split('.')[0] +
                                                          '/齿轮箱水泵2出口压力异常.csv')
                if result[0]:
                    self.handle_signal_and_log([1, 31], [1, [1, "齿轮箱水泵2出口压力正常"]])

                else:
                    self.handle_signal_and_log([0, 31], [1, [0, "齿轮箱水泵2出口压力异常"]])
                    self.handle_signal_and_log([0, 31], [0, [0, "齿轮箱水泵2出口压力异常报警次数{}".format(len(result[1]))]])
                    for i in result[1]:
                        self.signal_gb_write_log.emit([1, [0, i]])
                    self.signal_gb_write_log.emit([1, [-1, "*" * 40]])

        del df
        del tickets
        gc.collect()

    # 33 齿轮箱水泵2入口压力异常
    def gearbox_water_pump2_inlet_oil_pressure(self):
        """
        齿轮箱水泵2启动=1，齿轮箱水泵2入口压力小于1或者大于3，持续30s
        :return:
        """
        try:
            # 获取  时间 0 齿轮箱水泵2启动 42 齿轮箱水泵2入口压力 47 英文标签
            tickets = [self.tickets[0], self.tickets[42], self.tickets[47]]
            df = self.df[['time', tickets[0], tickets[1], tickets[2]]]
            df.set_index(df['time'], inplace=True)
        except Exception as e:
            print(e)
            print("齿轮箱跳过函数33")
            self.handle_signal_and_log([-1, 32], [1, [-1, "齿轮箱水泵2入口压力英文标签丢失"]])
            return

        # 绘图
        if self.draw:
            print("齿轮箱绘图33")
            df1 = df.copy()
            df1['timestamp'] = df[tickets[0]].apply(lambda x: time.mktime(time.strptime(x, '%Y-%m-%d %H:%M:%S')))
            self.drawing(graphicsView=self.plt_list[32],
                         canvas_setting={"title": "齿轮箱水泵2入口压力时间图"},
                         data=[
                             {"pen": "g", "name": "齿轮箱水泵2入口压力 ", "x": df1['timestamp'], "y": df1[tickets[2]]}
                         ])
            del df1
            gc.collect()

        # 删除齿轮箱水泵1启动 !=1
        df = df.drop(df[(df[tickets[1]] != 1)].index)
        if df.empty:
            self.handle_signal_and_log([1, 32], [1, [1, "齿轮箱水泵2入口压力正常"]])
        else:
            # 齿轮箱水泵1入口压力小于1或大于3，持续30s
            # 删除1-3之间
            df = df.drop(df[(df[tickets[2]] >= 1 & (df[tickets[2]] <= 3))].index)

            if df.empty:
                self.handle_signal_and_log([1, 32], [1, [1, "齿轮箱水泵2入口压力正常"]])
            else:
                # ------------------判断连续性
                result = tool.duration_calculation_to_csv(tickets,
                                                          df,
                                                          30,
                                                          str(self.import_file_path).split(r'/')[-1].split('.')[0] +
                                                          '/齿轮箱水泵2入口压力异常.csv')
                if result[0]:
                    self.handle_signal_and_log([1, 32], [1, [1, "齿轮箱水泵2入口压力正常"]])

                else:
                    self.handle_signal_and_log([0, 32], [1, [0, "齿轮箱水泵2入口压力异常"]])
                    self.handle_signal_and_log([0, 32], [0, [0, "齿轮箱水泵2入口压力异常报警次数{}".format(len(result[1]))]])
                    for i in result[1]:
                        self.signal_gb_write_log.emit([1, [0, i]])
                    self.signal_gb_write_log.emit([1, [-1, "*" * 40]])

        del df
        del tickets
        gc.collect()

    # 34 齿轮箱水泵1压力差异常
    def gearbox_water_pump1_oil_pressure_difference(self):
        """
        齿轮箱水泵1启动=1，齿轮箱水泵1出口压力减去入口压力＜1或者齿轮箱水泵1出口压力减去入口压力＞4，持续30s
        :return:
        """
        try:
            # 获取 时间 0 齿轮箱水泵1启动 40 齿轮箱水泵1出口压力 44 齿轮箱水泵1入口压力 45 英文标签
            tickets = [self.tickets[0], self.tickets[40], self.tickets[44], self.tickets[45]]
            df = self.df[['time', tickets[0], tickets[1], tickets[2], tickets[3]]]
            df.set_index(df['time'], inplace=True)
        except Exception as e:
            print(e)
            print("齿轮箱跳过函数34")
            self.handle_signal_and_log([-1, 33], [1, [-1, " 齿轮箱水泵1压力差英文标签丢失"]])
            return

        # 绘图
        if self.draw:
            print("齿轮箱绘图34")
            df1 = df.copy()
            df1['timestamp'] = df[tickets[0]].apply(lambda x: time.mktime(time.strptime(x, '%Y-%m-%d %H:%M:%S')))
            self.drawing(graphicsView=self.plt_list[33],
                         canvas_setting={"title": "齿轮箱水泵1压力差时间图"},
                         data=[
                             {"pen": "g", "name": "齿轮箱水泵1出口压力 ", "x": df1['timestamp'], "y": df1[tickets[2]]},
                             {"pen": "r", "name": "齿轮箱水泵1出口压力 ", "x": df1['timestamp'], "y": df1[tickets[3]]}
                         ])
            del df1
            gc.collect()

        # 删除 齿轮箱水泵1启动 !=1
        df = df.drop(df[(df[tickets[1]] != 1)].index)
        if df.empty:
            self.handle_signal_and_log([1, 33], [1, [1, "齿轮箱水泵1压力差正常"]])
        else:
            # 判断 齿轮箱水泵1出口压力减去入口压力＜1或者齿轮箱水泵1出口压力减去入口压力＞4，持续30s
            df = df[(df[tickets[2]] - df[tickets[3]] < 1) | (df[tickets[2]] - df[tickets[3]] > 4)]
            # ------------------判断连续性
            result = tool.duration_calculation_to_csv(tickets,
                                                      df,
                                                      1,
                                                      str(self.import_file_path).split(r'/')[-1].split('.')[0] +
                                                      '/齿轮箱水泵1压力差异常.csv')
            if result[0]:
                self.handle_signal_and_log([1, 33], [1, [1, "齿轮箱水泵1压力差正常"]])
            else:
                self.handle_signal_and_log([0, 33], [1, [0, "齿轮箱水泵1压力差异常"]])
                self.handle_signal_and_log([0, 33], [0, [0, "齿轮箱水泵1压力差异常报警次数{}".format(len(result[1]))]])
                for i in result[1]:
                    self.signal_gb_write_log.emit([1, [0, i]])
                self.signal_gb_write_log.emit([1, [-1, "*" * 40]])
        del df

    # 35 齿轮箱水泵2压力差异常
    def gearbox_water_pump2_oil_pressure_difference(self):
        """
        齿轮箱水泵2启动=1，齿轮箱水泵2出口压力减去入口压力＜1或者齿轮箱水泵2出口压力减去入口压力＞4，持续30s
        :return:
        """
        try:
            # 获取 时间 0 齿轮箱水泵1启动 40 齿轮箱水泵2出口压力 44 齿轮箱水泵2入口压力 45 英文标签
            tickets = [self.tickets[0], self.tickets[40], self.tickets[46], self.tickets[47]]
            df = self.df[['time', tickets[0], tickets[1], tickets[2], tickets[3]]]
            df.set_index(df['time'], inplace=True)
        except Exception as e:
            print(e)
            print("齿轮箱跳过函数35")
            self.handle_signal_and_log([-1, 34], [1, [-1, " 齿轮箱水泵2压力差英文标签丢失"]])
            return

        # 绘图
        if self.draw:
            print("齿轮箱绘图35")
            df1 = df.copy()
            df1['timestamp'] = df[tickets[0]].apply(lambda x: time.mktime(time.strptime(x, '%Y-%m-%d %H:%M:%S')))
            self.drawing(graphicsView=self.plt_list[34],
                         canvas_setting={"title": "齿轮箱水泵2压力差时间图"},
                         data=[
                             {"pen": "g", "name": "齿轮箱水泵2出口压力 ", "x": df1['timestamp'], "y": df1[tickets[2]]},
                             {"pen": "r", "name": "齿轮箱水泵2出口压力 ", "x": df1['timestamp'], "y": df1[tickets[3]]}
                         ])
            del df1
            gc.collect()

        # 删除 齿轮箱水泵1启动 !=1
        df = df.drop(df[(df[tickets[1]] != 1)].index)
        if df.empty:
            self.handle_signal_and_log([1, 34], [1, [1, "齿轮箱水泵2压力差正常"]])
        else:
            # 判断 齿轮箱水泵1出口压力减去入口压力＜1或者齿轮箱水泵1出口压力减去入口压力＞4，持续30s
            df = df[(df[tickets[2]] - df[tickets[3]] < 1) | (df[tickets[2]] - df[tickets[3]] > 4)]
            # ------------------判断连续性
            result = tool.duration_calculation_to_csv(tickets,
                                                      df,
                                                      1,
                                                      str(self.import_file_path).split(r'/')[-1].split('.')[0] +
                                                      '/齿轮箱水泵2压力差异常.csv')
            if result[0]:
                self.handle_signal_and_log([1, 34], [1, [1, "齿轮箱水泵2压力差正常"]])
            else:
                self.handle_signal_and_log([0, 34], [1, [0, "齿轮箱水泵2压力差异常"]])
                self.handle_signal_and_log([0, 34], [0, [0, "齿轮箱水泵2压力差异常报警次数{}".format(len(result[1]))]])
                for i in result[1]:
                    self.signal_gb_write_log.emit([1, [0, i]])
                self.signal_gb_write_log.emit([1, [-1, "*" * 40]])
        del df

    def over(self):
        # 第一个线程结束
        self.signal_gb_over.emit([1, 1])
        print("结束线程1.0")




