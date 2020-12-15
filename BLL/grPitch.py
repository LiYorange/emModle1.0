# -------------------------------------------------------------------------------
# Name:         grPitch1
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


class Pitch1(QObject):
    """
    变桨系统预警模型
    """
    # 类变量
    signal_pitch_color = pyqtSignal(list)
    signal_pitch_show_message = pyqtSignal(str)
    signal_pitch_progress = pyqtSignal(dict)
    signal_pitch_write_log = pyqtSignal(list)
    signal_pitch_over = pyqtSignal(list)

    def __init__(self, tickets_file_path=None, import_data_path=None, df=None,
                 project_index=None, plt_list=None, draw=False):
        """
        :param tickets_file_path: 将中文标签转化为英文标签的list
        :param import_data_path: 需要处理的数据路径
        :param project_index: 选区的项目序号
        :param plt_list: 绘图对象

        """
        super(Pitch1, self).__init__()

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
            self.pitch_rotor_speed,
            self.pitch_motor_temperature,
            self.pitch_box_temperature,
            self.pitch_box_temperature_difference,
            self.pitch_driver_ratiator_temperature,
            self.pitch_battery_box_temperature,
            self.pitch_battery_box_temperature_difference,
            self.over
        ]
        # ------------------------------------------->>>实例变量初始化结束

    def run(self):
        print(self)
        self.signal_pitch_show_message.emit("变桨系统模块已启动！")
        self.signal_pitch_write_log.emit(
            [3, [-1, time.strftime('%Y{y}%m{m}%d{d} %H{h}%M{f}%S{s}').format(y='年', m='月', d='日',
                                                                             h='时', f='分', s='秒') + ":变桨系统统模块进程开始运行"]])

        for (func, i) in zip(self.function_list, range(len(self.function_list))):
            func()
            del func
            self.signal_pitch_progress.emit({"pitch": int((i + 1) / len(self.function_list) * 100)})
        self.signal_pitch_show_message.emit("变桨系统模块计算完成！")
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
            "变桨驱动柜温度1",
            "变桨驱动柜温度2",
            "变桨驱动柜温度3",
            "桨叶角度1A",
            "桨叶角度2A",
            "桨叶角度3A",
            "桨叶角度1B",
            "桨叶角度2B",
            "桨叶角度3B",
            "叶轮速度1",
            "叶轮速度2",
            "风速",
            "变桨电机温度1",
            "变桨电机温度2",
            "变桨电机温度3",
            "变桨驱动柜散热器温度1",
            "变桨驱动柜散热器温度2",
            "变桨驱动柜散热器温度3",
            "变桨后备电源柜温度1",
            "变桨后备电源柜温度2",
            "变桨后备电源柜温度3"
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
        self.signal_pitch_color.emit(color_signal)
        log_signal[1][1] = time.strftime('%Y{y}%m{m}%d{d} %H{h}%M{f}%S{s}').format(y='年', m='月', d='日',
                                                                                   h='时', f='分', s='秒') + ":" + \
                           log_signal[1][1]
        self.signal_pitch_write_log.emit(log_signal)

    # 2 叶轮转速超速
    def pitch_rotor_speed(self):

        """
        ：叶轮转速超速
        ：11≤ 机组运行模式 ≤14，叶轮转速1 和 叶轮转速2 都≥12.8rpm，持续 5s
        """

        try:
            # 获取 1 时间 2 机组运行模式 12	叶轮速度1 13 叶轮速度2 英文标签
            # print(self.tickets)
            tickets = [self.tickets[0], self.tickets[1], self.tickets[11], self.tickets[12]]
            # tickets = self.tickets

            df = self.df[['time', tickets[0], tickets[1], tickets[2], tickets[3]]]
            df.set_index(df['time'], inplace=True)
        except Exception as e:
            print(e)
            print("变桨跳过函数2")
            self.handle_signal_and_log([-1, 1], [3, [-1, "叶轮转速英文标签丢失"]])
            return

        if self.draw:
            print("变桨绘图2")
            df1 = df.copy()
            df1.resample('30T').mean()
            df1['timestamp'] = df[tickets[0]].apply(lambda x: time.mktime(time.strptime(x, '%Y-%m-%d %H:%M:%S')))
            self.drawing(graphicsView=self.plt_list[1],
                         canvas_setting={"title": "叶轮转速时间图"},
                         data=[
                             {"pen": "g", "name": "叶轮转速1", "x": df1['timestamp'], "y": df1[tickets[2]]},
                             {"pen": "r", "name": "叶轮转速2", "x": df1['timestamp'], "y": df1[tickets[3]]}
                         ])

            del df1
            gc.collect()

        # 删除 1 < 11 | 1 > 14
        df = df.drop(df[((df[tickets[1]] > 14) | (df[tickets[1]] < 11))].index)
        if df.empty:
            self.handle_signal_and_log([1, 1], [3, [1, "叶轮转速正常"]])

        else:
            # 删除 2<12.8 | 3<12.8
            df = df.drop(df[(
                    (df[tickets[2]] < 12.8) | (df[tickets[3]] < 12.8))].index)
            if df.empty:
                self.handle_signal_and_log([1, 1], [3, [1, "叶轮转速正常"]])
            else:
                # ------------------判断连续性
                result = tool.duration_calculation_to_csv(tickets,
                                                          df,
                                                          5,
                                                          str(self.import_file_path).split(r'/')[-1].split('.')[0] +
                                                          '/叶轮转速超速.csv')
                if result[0]:
                    self.handle_signal_and_log([1, 1], [3, [1, "叶轮转速正常"]])

                else:
                    self.handle_signal_and_log([0, 1], [3, [0, "叶轮转速超速"]])
                    self.handle_signal_and_log([0, 1], [0, [0, "叶轮转速超速报警次数{}".format(len(result[1]))]])
                    for i in result[1]:
                        self.signal_pitch_write_log.emit([3, [0, i]])
                    self.signal_pitch_write_log.emit([3, [-1, "*" * 40]])

        del df
        # # 从原数据中删除 叶轮转速
        # del self.df[tickets[2]]
        del tickets
        gc.collect()

    # 3 桨叶电机温度异常
    def pitch_motor_temperature(self):
        """
        桨叶电机温度异常
        11≤ 机组运行模式 ≤14，单个桨叶电机温度 ＞ 120℃， 或两两温差绝对值≥30℃，且持续时间超过1min
        :return:
        """
        try:
            # 获取 1 时间  2机组模式 15-17 变桨电机温度1-3 英文标签
            # print(self.tickets)
            tickets = [self.tickets[0], self.tickets[1], self.tickets[14], self.tickets[15], self.tickets[16]]
            # tickets = self.tickets

            df = self.df[['time', tickets[0], tickets[1], tickets[2], tickets[3], tickets[4]]]
            df.set_index(df['time'], inplace=True)
        except Exception as e:
            print(e)
            print("变桨跳过函数3")
            self.handle_signal_and_log([-1, 2], [3, [-1, "桨叶电机温度英文标签丢失"]])
            return

        if self.draw:
            print("变桨绘图3")
            df1 = df.copy()
            df1.resample('30T').mean()
            df1['timestamp'] = df[tickets[0]].apply(lambda x: time.mktime(time.strptime(x, '%Y-%m-%d %H:%M:%S')))
            self.drawing(graphicsView=self.plt_list[2],
                         canvas_setting={"title": "桨叶电机温度时间图"},
                         data=[
                             {"pen": "g", "name": "变桨电机温度1", "x": df1['timestamp'], "y": df1[tickets[2]]},
                             {"pen": "r", "name": "变桨电机温度2", "x": df1['timestamp'], "y": df1[tickets[3]]},
                             {"pen": "b", "name": "变桨电机温度3", "x": df1['timestamp'], "y": df1[tickets[4]]}
                         ])
            del df1
            gc.collect()

        # 11≤机组运行模式≤14
        df = df.drop(df[(df[tickets[1]] > 14) | (df[tickets[1]] < 11)].index)
        if df.empty:
            self.handle_signal_and_log([1, 2], [3, [1, "桨叶电机温度正常"]])

        else:
            df['桨叶电机1-桨叶电机2'] = (df[tickets[2]] - df[tickets[3]]).abs()
            df['桨叶电机1-桨叶电机3'] = (df[tickets[2]] - df[tickets[4]]).abs()
            df['桨叶电机2-桨叶电机3'] = (df[tickets[3]] - df[tickets[4]]).abs()
            # 情况1 单个桨叶电机温度 ＞ 120℃,1min
            df_h = df[((df[tickets[2]] > 120) | (df[tickets[3]] > 120) | (df[tickets[4]] > 120))].copy()
            # 情况2 两两温差绝对值≥30℃，且持续时间超过1min
            df_l = df[((df['桨叶电机1-桨叶电机2'] >= 30) | (df['桨叶电机1-桨叶电机3'] >= 30) | (df['桨叶电机2-桨叶电机3'] >= 30))].copy()
            # 判断是否未空
            if df_h.empty and df_l.empty:
                self.handle_signal_and_log([1, 2], [3, [1, "桨叶电机温度正常"]])
            else:
                # ------------------判断连续性
                # 高速模式连续时长判断
                if not df_h.empty:
                    result = tool.duration_calculation_to_csv(tickets,
                                                              df_h,
                                                              60,
                                                              str(self.import_file_path).split(r'/')[-1].split('.')[0] +
                                                              '/桨叶电机温度异常.csv')
                    if result[0]:
                        self.handle_signal_and_log([1, 2], [3, [1, "桨叶电机温度正常"]])
                    else:
                        self.handle_signal_and_log([0, 2], [3, [0, "桨叶电机温度异常"]])
                        for i in result[1]:
                            self.signal_pitch_write_log.emit([3, [0, i]])
                        self.signal_pitch_write_log.emit([3, [-1, "*" * 40]])
                if not df_l.empty:
                    result = tool.duration_calculation_to_csv(tickets,
                                                              df_l,
                                                              60,
                                                              str(self.import_file_path).split(r'/')[-1].split('.')[0] +
                                                              '/桨叶电机温度异常.csv')
                    if result[0]:
                        self.handle_signal_and_log([1, 2], [3, [1, "桨叶电机温度正常"]])
                    else:
                        self.handle_signal_and_log([0, 2], [3, [0, "桨叶电机温度异常"]])
                        self.handle_signal_and_log([0, 2], [0, [0, "桨叶电机温度异常报警次数{}".format(len(result[1]))]])
                        for i in result[1]:
                            self.signal_pitch_write_log.emit([3, [0, i]])
                        self.signal_pitch_write_log.emit([3, [-1, "*" * 40]])
            del df_h
            del df_l
        del df

    # 4 桨叶轴控箱温度异常
    def pitch_box_temperature(self):

        """
        ：桨叶轴控箱温度异常
        ：单个桨叶轴控箱温度(变桨驱动柜温度1-3) ＞ 55℃ 或 ＜ -5℃，且 ≠ -40℃，持续1min；
        """

        try:
            # 获取 1 时间 2 机组运行模式 3-5 变桨驱动柜温度1-3 英文标签
            # print(self.tickets)
            tickets = [self.tickets[0], self.tickets[1], self.tickets[2], self.tickets[3], self.tickets[4]]
            # tickets = self.tickets

            df = self.df[['time', tickets[0], tickets[1], tickets[2], tickets[3], self.tickets[4]]]
            df.set_index(df['time'], inplace=True)
        except Exception as e:
            print(e)
            print("变桨跳过函数4")
            self.handle_signal_and_log([-1, 3], [3, [-1, "桨叶轴控箱温度英文标签丢失"]])
            return

        if self.draw:
            print("变桨绘图4")
            df1 = df.copy()
            df1.resample('30T').mean()
            df1['timestamp'] = df[tickets[0]].apply(lambda x: time.mktime(time.strptime(x, '%Y-%m-%d %H:%M:%S')))
            self.drawing(graphicsView=self.plt_list[3],
                         canvas_setting={"title": "桨叶轴控箱温度时间图"},
                         data=[
                             {"pen": "g", "name": "变桨驱动柜温度1", "x": df1['timestamp'], "y": df1[tickets[2]]},
                             {"pen": "r", "name": "变桨驱动柜温度2", "x": df1['timestamp'], "y": df1[tickets[3]]},
                             {"pen": "b", "name": "变桨驱动柜温度3", "x": df1['timestamp'], "y": df1[tickets[4]]}
                         ])
            del df1
            gc.collect()

        # 删除 2=40 | 3=40 | 4=40
        df = df.drop(df[((df[tickets[2]] == 40) | (df[tickets[3]] == 40) | (df[tickets[4]] == 40))].index)
        if df.empty:
            self.handle_signal_and_log([1, 3], [3, [1, "桨叶轴控箱温度正常"]])

        else:
            # 删除 2<=55 & 2>=-5 & 3<=55 & 3>=-5 & 4<=55 & 5>=-5
            df = df.drop(df[((df[tickets[2]] >= -5) & (df[tickets[2]] <= 55) & (df[tickets[3]] >= -5) &
                             (df[tickets[3]] <= 55) & (df[tickets[4]] >= -5) & (df[tickets[4]] <= 55))].index)
            if df.empty:
                self.handle_signal_and_log([1, 3], [3, [1, "桨叶轴控箱温度正常"]])
            else:
                # ------------------判断连续性
                result = tool.duration_calculation_to_csv(tickets,
                                                          df,
                                                          60,
                                                          str(self.import_file_path).split(r'/')[-1].split('.')[0] +
                                                          '/桨叶轴控箱温度异常.csv')
                if result[0]:
                    self.handle_signal_and_log([1, 3], [3, [1, "桨叶轴控箱温度正常"]])

                else:
                    self.handle_signal_and_log([0, 3], [3, [0, "桨叶轴控箱温度异常"]])
                    self.handle_signal_and_log([0, 3], [0, [0, "桨叶轴控箱温度异常报警次数{}".format(len(result[1]))]])
                    for i in result[1]:
                        self.signal_pitch_write_log.emit([3, [0, i]])
                    self.signal_pitch_write_log.emit([3, [-1, "*" * 40]])

        del df
        # # 从原数据中删除 桨叶轴控箱温度
        # del self.df[tickets[2]]
        del tickets
        gc.collect()

    # 5 桨叶轴控箱温差异常
    def pitch_box_temperature_difference(self):
        """
        桨叶轴控箱温差异常
        机组运行模式=14，两两桨叶轴控箱温差绝对值 ≥10℃，并且持续超过1min
        :return:
        """
        try:
            # 获取 1 时间  2机组模式 3-5 变桨驱动柜温度1-3 英文标签
            # print(self.tickets)
            tickets = [self.tickets[0], self.tickets[1], self.tickets[2], self.tickets[3], self.tickets[4]]
            # tickets = self.tickets

            df = self.df[['time', tickets[0], tickets[1], tickets[2], tickets[3], tickets[4]]]
            df.set_index(df['time'], inplace=True)
        except Exception as e:
            print(e)
            print("变桨跳过函数5")
            self.handle_signal_and_log([-1, 4], [3, [-1, "桨叶轴控箱温差英文标签丢失"]])
            return

        if self.draw:
            print("变桨绘图5")
            df1 = df.copy()
            df1.resample('30T').mean()
            df1['timestamp'] = df[tickets[0]].apply(lambda x: time.mktime(time.strptime(x, '%Y-%m-%d %H:%M:%S')))
            self.drawing(graphicsView=self.plt_list[4],
                         canvas_setting={"title": "桨叶轴控箱温差时间图"},
                         data=[
                             {"pen": "g", "name": "变桨驱动柜温度1", "x": df1['timestamp'], "y": df1[tickets[2]]},
                             {"pen": "r", "name": "变桨驱动柜温度2", "x": df1['timestamp'], "y": df1[tickets[3]]},
                             {"pen": "b", "name": "变桨驱动柜温度3", "x": df1['timestamp'], "y": df1[tickets[4]]}
                         ])
            del df1
            gc.collect()

        # 机组运行模式 != 14
        df = df.drop(df[(df[tickets[1]] != 14)].index)
        if df.empty:
            self.handle_signal_and_log([1, 4], [3, [1, "桨叶轴控箱温差正常"]])

        else:
            # 绝对值 ≥10℃，并且持续超过1min
            df['桨叶轴控箱1-桨叶轴控箱2'] = (df[tickets[2]] - df[tickets[3]]).abs()
            df['桨叶轴控箱1-桨叶轴控箱3'] = (df[tickets[2]] - df[tickets[4]]).abs()
            df['桨叶轴控箱2-桨叶轴控箱3'] = (df[tickets[3]] - df[tickets[4]]).abs()
            df = df.drop(df[(
                    (df['桨叶轴控箱1-桨叶轴控箱2'] < 10) | (df['桨叶轴控箱1-桨叶轴控箱3'] < 10) | (df['桨叶轴控箱2-桨叶轴控箱3'] < 10))].index)
            if df.empty:
                self.handle_signal_and_log([1, 4], [3, [1, "桨叶轴控箱温差正常"]])
            else:
                # ------------------判断连续性
                result = tool.duration_calculation_to_csv(tickets,
                                                          df,
                                                          60,
                                                          str(self.import_file_path).split(r'/')[-1].split('.')[0] +
                                                          '/桨叶轴控箱温差异常.csv')
                if result[0]:
                    self.handle_signal_and_log([1, 4], [3, [1, "桨叶轴控箱温差正常"]])

                else:
                    self.handle_signal_and_log([0, 4], [3, [0, "桨叶轴控箱温差异常"]])
                    self.handle_signal_and_log([0, 4], [0, [0, "桨叶轴控箱温差异常报警次数{}".format(len(result[1]))]])
                    for i in result[1]:
                        self.signal_pitch_write_log.emit([3, [0, i]])
                    self.signal_pitch_write_log.emit([3, [-1, "*" * 40]])

        del df
        # # 从原数据中删除 叶轮转速
        # del self.df[tickets[2]]
        del tickets
        gc.collect()

    # 6 变桨驱动器散热器温度异常
    def pitch_driver_ratiator_temperature(self):
        """
        变桨驱动器散热器温度异常
        机组运行模式=14，驱动器1-3散热器温度 最大值与最小值差值超10℃，或最大值超过60℃，或最小值低于-5℃，但是不等于-40℃，并且持续超过1min
        :return:
        """
        try:
            # 获取 1 时间  2机组模式 18-20 驱动器1-3散热器温度 英文标签
            # print(self.tickets)
            tickets = [self.tickets[0], self.tickets[1], self.tickets[17], self.tickets[18], self.tickets[19]]
            # tickets = self.tickets

            df = self.df[['time', tickets[0], tickets[1], tickets[2], tickets[3], tickets[4]]]
            df.set_index(df['time'], inplace=True)
        except Exception as e:
            print(e)
            print("变桨跳过函数6")
            self.handle_signal_and_log([-1, 5], [3, [-1, "变桨驱动器散热器温度英文标签丢失"]])
            return

        if self.draw:
            print("变桨绘图6")
            df1 = df.copy()
            df1.resample('30T').mean()
            df1['timestamp'] = df[tickets[0]].apply(lambda x: time.mktime(time.strptime(x, '%Y-%m-%d %H:%M:%S')))
            self.drawing(graphicsView=self.plt_list[5],
                         canvas_setting={"title": "变桨驱动器散热器温度时间图"},
                         data=[
                             {"pen": "g", "name": "驱动器1散热器温度", "x": df1['timestamp'], "y": df1[tickets[2]]},
                             {"pen": "r", "name": "驱动器2散热器温度", "x": df1['timestamp'], "y": df1[tickets[3]]},
                             {"pen": "b", "name": "驱动器3散热器温度", "x": df1['timestamp'], "y": df1[tickets[4]]}
                         ])
            del df1
            gc.collect()

        # 机组运行模式 != 14
        df = df.drop(df[(df[tickets[1]] != 14)].index)
        if df.empty:
            self.handle_signal_and_log([1, 5], [3, [1, "变桨驱动器散热器温度正常"]])

        else:
            # max-min >10 | max > 60 | (min < -5 & min != -40) 1min
            df['maxvalue'] = df[[tickets[2], tickets[3], tickets[4]]].max(axis=1)
            df['minvalue'] = df[[tickets[2], tickets[3], tickets[4]]].min(axis=1)
            df = df.drop(df[((df['maxvalue'] - df['minvalue'] <= 10) & (df['maxvalue'] <= 60) & (
                        (df['minvalue'] >= -5) | (df['minvalue'] == -40)))].index)
            if df.empty:
                self.handle_signal_and_log([1, 5], [3, [1, "变桨驱动器散热器温度正常"]])
            else:
                # ------------------判断连续性
                result = tool.duration_calculation_to_csv(tickets,
                                                          df,
                                                          60,
                                                          str(self.import_file_path).split(r'/')[-1].split('.')[0] +
                                                          '/变桨驱动器散热器温度异常.csv')
                if result[0]:
                    self.handle_signal_and_log([1, 5], [3, [1, "变桨驱动器散热器温度正常"]])

                else:
                    self.handle_signal_and_log([0, 5], [3, [0, "变桨驱动器散热器温度异常"]])
                    self.handle_signal_and_log([0, 5], [0, [0, "变桨驱动器散热器温度异常报警次数{}".format(len(result[1]))]])
                    for i in result[1]:
                        self.signal_pitch_write_log.emit([3, [0, i]])
                    self.signal_pitch_write_log.emit([3, [-1, "*" * 40]])

        del df
        # # 从原数据中删除 叶轮转速
        # del self.df[tickets[2]]
        del tickets
        gc.collect()

    # 桨叶电池箱温度异常
    def pitch_battery_box_temperature(self):

        """
        ：桨叶电池箱温度异常
        ：单个桨叶电池箱温度(变桨后备电源柜温度1-3) ＞ 55℃ 或 ＜ -5℃，且 ≠ -40℃，持续1min；
        """

        try:
            # 获取 1 时间 2 机组运行模式 21-23 变桨后备电源柜温度1-3 英文标签
            # print(self.tickets)
            tickets = [self.tickets[0], self.tickets[1], self.tickets[20], self.tickets[21], self.tickets[22]]
            # tickets = self.tickets

            df = self.df[['time', tickets[0], tickets[1], tickets[2], tickets[3], tickets[4]]]
            df.set_index(df['time'], inplace=True)
        except Exception as e:
            print(e)
            print("变桨跳过函数7")
            self.handle_signal_and_log([-1, 6], [3, [-1, "桨叶电池箱温度英文标签丢失"]])
            return

        if self.draw:
            print("变桨绘图7")
            df1 = df.copy()
            df1.resample('30T').mean()
            df1['timestamp'] = df[tickets[0]].apply(lambda x: time.mktime(time.strptime(x, '%Y-%m-%d %H:%M:%S')))
            self.drawing(graphicsView=self.plt_list[6],
                         canvas_setting={"title": "桨叶电池箱温度时间图"},
                         data=[
                             {"pen": "g", "name": "变桨后备电源柜温度1", "x": df1['timestamp'], "y": df1[tickets[2]]},
                             {"pen": "r", "name": "变桨后备电源柜温度2", "x": df1['timestamp'], "y": df1[tickets[3]]},
                             {"pen": "b", "name": "变桨后备电源柜温度3", "x": df1['timestamp'], "y": df1[tickets[4]]}
                         ])
            del df1
            gc.collect()

        # 删除 2=40 | 3=40 | 4=40
        df = df.drop(df[((df[tickets[2]] == 40) | (df[tickets[3]] == 40) | (df[tickets[4]] == 40))].index)
        if df.empty:
            self.handle_signal_and_log([1, 6], [3, [1, "桨叶电池箱温度正常"]])

        else:
            # 删除 2<=55 & 2>=-5 & 3<=55 & 3>=-5 & 4<=55 & 5>=-5
            df = df.drop(df[((df[tickets[2]] >= -5) & (df[tickets[2]] <= 55) & (df[tickets[3]] >= -5) &
                             (df[tickets[3]] <= 55) & (df[tickets[4]] >= -5) & (df[tickets[4]] <= 55))].index)
            if df.empty:
                self.handle_signal_and_log([1, 6], [3, [1, "桨叶电池箱温度正常"]])
            else:
                # ------------------判断连续性
                result = tool.duration_calculation_to_csv(tickets,
                                                          df,
                                                          60,
                                                          str(self.import_file_path).split(r'/')[-1].split('.')[0] +
                                                          '/桨叶电池箱温度异常.csv')
                if result[0]:
                    self.handle_signal_and_log([1, 6], [3, [1, "桨叶电池箱温度正常"]])

                else:
                    self.handle_signal_and_log([0, 6], [3, [0, "桨叶电池箱温度异常"]])
                    self.handle_signal_and_log([0, 6], [0, [0, "桨叶电池箱温度异常报警次数{}".format(len(result[1]))]])
                    for i in result[1]:
                        self.signal_pitch_write_log.emit([3, [0, i]])
                    self.signal_pitch_write_log.emit([3, [-1, "*" * 40]])

        del df
        # # 从原数据中删除 桨叶电池箱温度
        # del self.df[tickets[2]]
        del tickets
        gc.collect()

    # 8 桨叶电池箱温差异常
    def pitch_battery_box_temperature_difference(self):
        """
        桨叶电池箱温差异常
        机组运行模式=14，两两桨叶电池箱温差绝对值 ≥10℃，并且持续超过1min
        :return:
        """
        try:
            # 获取 1 时间  2机组模式 21-23 变桨后备电源柜温度1-3 英文标签
            # print(self.tickets)
            tickets = [self.tickets[0], self.tickets[1], self.tickets[20], self.tickets[21], self.tickets[22]]
            # tickets = self.tickets

            df = self.df[['time', tickets[0], tickets[1], tickets[2], tickets[3], tickets[4]]]
            df.set_index(df['time'], inplace=True)
        except Exception as e:
            print(e)
            print("变桨跳过函数8")
            self.handle_signal_and_log([-1, 7], [3, [-1, "桨叶电池箱温差英文标签丢失"]])
            return

        if self.draw:
            print("变桨绘图8")
            df1 = df.copy()
            df1.resample('30T').mean()
            df1['timestamp'] = df[tickets[0]].apply(lambda x: time.mktime(time.strptime(x, '%Y-%m-%d %H:%M:%S')))
            self.drawing(graphicsView=self.plt_list[7],
                         canvas_setting={"title": "桨叶电池箱温差时间图"},
                         data=[
                             {"pen": "g", "name": "变桨后备电源柜温度1", "x": df1['timestamp'], "y": df1[tickets[2]]},
                             {"pen": "r", "name": "变桨后备电源柜温度2", "x": df1['timestamp'], "y": df1[tickets[3]]},
                             {"pen": "b", "name": "变桨后备电源柜温度3", "x": df1['timestamp'], "y": df1[tickets[4]]}
                         ])
            del df1
            gc.collect()

        # 机组运行模式 != 14
        df = df.drop(df[(df[tickets[1]] != 14)].index)
        if df.empty:
            self.handle_signal_and_log([1, 7], [3, [1, "桨叶电池箱温差正常"]])

        else:
            # 绝对值 ≥10℃，并且持续超过1min
            df['电源柜1-电源柜2'] = (df[tickets[2]] - df[tickets[3]]).abs()
            df['电源柜1-电源柜3'] = (df[tickets[2]] - df[tickets[4]]).abs()
            df['电源柜2-电源柜3'] = (df[tickets[3]] - df[tickets[4]]).abs()
            df = df.drop(df[(
                    (df['电源柜1-电源柜2'] < 10) | (df['电源柜1-电源柜3'] < 10) | (df['电源柜2-电源柜3'] < 10))].index)
            if df.empty:
                self.handle_signal_and_log([1, 7], [3, [1, "桨叶电池箱温差正常"]])
            else:
                # ------------------判断连续性
                result = tool.duration_calculation_to_csv(tickets,
                                                          df,
                                                          60,
                                                          str(self.import_file_path).split(r'/')[-1].split('.')[0] +
                                                          '/桨叶电池箱温差异常.csv')
                if result[0]:
                    self.handle_signal_and_log([1, 7], [3, [1, "桨叶电池箱温差正常"]])

                else:
                    self.handle_signal_and_log([0, 7], [3, [0, "桨叶电池箱温差异常"]])
                    self.handle_signal_and_log([0, 7], [0, [0, "桨叶电池箱温差异常报警次数{}".format(len(result[1]))]])
                    for i in result[1]:
                        self.signal_pitch_write_log.emit([3, [0, i]])
                    self.signal_pitch_write_log.emit([3, [-1, "*" * 40]])

        del df
        # # 从原数据中删除 叶轮转速
        # del self.df[tickets[2]]
        del tickets
        gc.collect()

    def over(self):
        # 第一个线程结束
        self.signal_pitch_over.emit([3, 1])


