# -------------------------------------------------------------------------------
# Name:         grConverter1
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


class Converter1(QObject):
    """
    变频器预警模型
    """
    # 类变量
    signal_co_color = pyqtSignal(list)
    signal_co_show_message = pyqtSignal(str)
    signal_co_progress = pyqtSignal(dict)
    signal_co_write_log = pyqtSignal(list)
    signal_co_over = pyqtSignal(list)

    def __init__(self, tickets_file_path=None, import_data_path=None, df=None,
                 project_index=None, plt_list=None, draw=False):
        """
        :param tickets_file_path: 将中文标签转化为英文标签的list
        :param import_data_path: 需要处理的数据路径
        :param project_index: 选区的项目序号
        :param plt_list: 绘图对象

        """
        super(Converter1, self).__init__()

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
            self.converter_igbt1_temperature,
            self.converter_igbt2_temperature,
            self.converter_generator_speed,
            self.converter1_water_temperature,
            self.converter2_water_temperature,
            self.converter1_water_pressure,
            self.converter2_water_pressure,
            self.over
        ]
        # ------------------------------------------->>>实例变量初始化结束

    # def __del__(self):
    #     self.wait()

    def run(self):
        self.signal_co_show_message.emit("变频器模块已启动！")
        self.signal_co_write_log.emit(
            [4, [-1, time.strftime('%Y{y}%m{m}%d{d} %H{h}%M{f}%S{s}').format(y='年', m='月', d='日',
                                                                             h='时', f='分', s='秒') + ":变频器模块进程开始运行"]])

        for (func, i) in zip(self.function_list, range(len(self.function_list))):
            func()
            del func
            # print(int((i + 1) / len(self.function_list) * 100))
            self.signal_co_progress.emit({"converter": int((i + 1) / len(self.function_list) * 100)})
        self.signal_co_show_message.emit("变频器模块计算完成！")
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
                        "变频器主机igbt温度",
                        "变频器从机igbt温度",
                        "变流器发电机转速",
                        "叶轮速度2",
                        "变频器主机冷却液温度",
                        "变频器主机风扇运行1",
                        "变频器主机水泵运行",
                        "变频器从机冷却液温度",
                        "变频器从机风扇运行1",
                        "变频器从机水泵运行",
                        "变频器主机冷却液压力",
                        "变频器从机冷却液压力"
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
        self.signal_co_color.emit(color_signal)
        log_signal[1][1] = time.strftime('%Y{y}%m{m}%d{d} %H{h}%M{f}%S{s}').format(y='年', m='月', d='日',
                                                                                   h='时', f='分', s='秒') + ":" + \
                           log_signal[1][1]
        self.signal_co_write_log.emit(log_signal)

    # 1 变频器主机IGBT温度异常
    def converter_igbt1_temperature(self):

        """
        ：变频器主机IGBT温度异常
        ：变频器主机IGBT温度 ≠ 0 且 ( >60℃ 或 <-10℃ )
        """
        try:
            # 获取 1 时间 3 变频器主机igbt温度
            # print(self.tickets)
            tickets = [self.tickets[0], self.tickets[2]]
            # tickets = self.tickets

            df = self.df[['time', tickets[0], tickets[1]]]
            df.set_index(df['time'], inplace=True)
        except Exception as e:
            print(e)
            print("变频器跳过函数1")
            self.handle_signal_and_log([-1, 0], [4, [-1, "变频器主机IGBT温度英文标签丢失"]])
            return

        if self.draw:
            print("变频器绘图1")
            df1 = df.copy()
            df1.resample('30T').mean()
            df1['timestamp'] = df[tickets[0]].apply(lambda x: time.mktime(time.strptime(x, '%Y-%m-%d %H:%M:%S')))
            self.drawing(graphicsView=self.plt_list[0],
                         canvas_setting={"title": "变频器主机IGBT温度时间图"},
                         data=[
                             {"pen": "g", "name": "变频器主机IGBT温度", "x": df1['timestamp'], "y": df1[tickets[1]]},
                         ])
            del df1
            gc.collect()

        # 删除温度等于0
        df = df.drop(df[(df[tickets[1]] == 0)].index)
        if df.empty:
            self.handle_signal_and_log([1, 0], [4, [1, "变频器主机IGBT温度正常"]])

        else:
            # 删除温度小于等于60且大于等于-10
            df = df.drop(df[(df[tickets[1]] >= -10) & (df[tickets[1]] <= 60)].index)
            if df.empty:
                self.handle_signal_and_log([1, 0], [4, [1, "变频器主机IGBT温度正常"]])

            else:
                # ------------------判断连续性
                result = tool.duration_calculation_to_csv(tickets,
                                                          df,
                                                          1,
                                                          str(self.import_file_path).split(r'/')[-1].split('.')[0] +
                                                          '/变频器主机IGBT温度.csv')
                if result[0]:
                    self.handle_signal_and_log([1, 0], [4, [1, "变频器主机IGBT温度正常"]])

                else:
                    self.handle_signal_and_log([0, 0], [4, [0, "变频器主机IGBT温度异常"]])
                    self.handle_signal_and_log([0, 0], [0, [0, "变频器主机IGBT温度异常报警次数{}".format(len(result[1]))]])
                    for i in result[1]:
                        self.signal_co_write_log.emit([4, [0, i]])
                    self.signal_co_write_log.emit([4, [-1, "*" * 40]])

        del df
        # # 从原数据中删除变频器主机IGBT温度
        # del self.df[tickets[2]]
        del tickets
        gc.collect()

    # 2 变频器从机IGBT温度异常
    def converter_igbt2_temperature(self):

        """
        ：变频器从机IGBT温度异常
        ：变频器从机IGBT温度 ≠ 0 且 ( >60℃ 或 <-10℃ )
        """
        try:
            # 获取 1 时间 4 变频器从机igbt温度
            # print(self.tickets)
            tickets = [self.tickets[0], self.tickets[3]]
            # tickets = self.tickets

            df = self.df[['time', tickets[0], tickets[1]]]
            df.set_index(df['time'], inplace=True)
        except Exception as e:
            print(e)
            print("变频器跳过函数2")
            self.handle_signal_and_log([-1, 1], [4, [-1, "变频器从机IGBT温度英文标签丢失"]])
            return

        if self.draw:
            print("变频器绘图2")
            df1 = df.copy()
            df1.resample('30T').mean()
            df1['timestamp'] = df[tickets[0]].apply(lambda x: time.mktime(time.strptime(x, '%Y-%m-%d %H:%M:%S')))
            self.drawing(graphicsView=self.plt_list[1],
                         canvas_setting={"title": "变频器从机IGBT温度时间图"},
                         data=[
                             {"pen": "g", "name": "变频器从机IGBT温度", "x": df1['timestamp'], "y": df1[tickets[1]]},
                         ])
            del df1
            gc.collect()

        # 删除温度等于0
        df = df.drop(df[(df[tickets[1]] == 0)].index)
        if df.empty:
            self.handle_signal_and_log([1, 1], [4, [1, "变频器从机IGBT温度正常"]])

        else:
            # 删除温度小于等于60且大于等于-10
            df = df.drop(df[(df[tickets[1]] >= -10) & (df[tickets[1]] <= 60)].index)
            if df.empty:
                self.handle_signal_and_log([1, 1], [4, [1, "变频器从机IGBT温度正常"]])

            else:
                # ------------------判断连续性
                result = tool.duration_calculation_to_csv(tickets,
                                                          df,
                                                          1,
                                                          str(self.import_file_path).split(r'/')[-1].split('.')[0] +
                                                          '/变频器从机IGBT温度.csv')
                if result[0]:
                    self.handle_signal_and_log([1, 1], [4, [1, "变频器从机IGBT温度正常"]])

                else:
                    self.handle_signal_and_log([0, 1], [4, [0, "变频器从机IGBT温度异常"]])
                    self.handle_signal_and_log([0, 1], [0, [0, "变频器从机IGBT温度异常报警次数{}".format(len(result[1]))]])
                    for i in result[1]:
                        self.signal_co_write_log.emit([4, [0, i]])
                    self.signal_co_write_log.emit([4, [-1, "*" * 40]])

        del df
        # # 从原数据中删除变频器从机IGBT温度
        # del self.df[tickets[2]]
        del tickets
        gc.collect()

    # 3 变流器发电机转速异常
    def converter_generator_speed(self):
        """
        变流器发电机转速异常
        原理：
        1、机组运行模式=14，（变流器发电机转速/齿轮箱变比（23.187）-叶轮转速2）>1.5，持续10s；
        2、变流器发电机转速>300rpm
        满足以上其一报出变流器发电机转速异常
        :return:
        """
        try:
            # 获取 1"时间", 2"机组运行模式",5"变流器发电机转速",6"叶轮转速2"英文标签
            tickets = [self.tickets[0], self.tickets[1], self.tickets[4], self.tickets[5]]
            df = self.df[['time', tickets[0], tickets[1], tickets[2], tickets[3]]]
            df.set_index(df['time'], inplace=True)
        except Exception as e:
            print(e)
            print("变频器跳过函数3")
            self.handle_signal_and_log([-1, 2], [4, [-1, "变流器发电机转速英文标签丢失"]])
            return

        if self.draw:
            print("变频器绘图3")
            df1 = df.copy()
            df1.resample('30T').mean()
            df1['timestamp'] = df[tickets[0]].apply(lambda x: time.mktime(time.strptime(x, '%Y-%m-%d %H:%M:%S')))
            self.drawing(graphicsView=self.plt_list[2],
                         canvas_setting={"title": "变流器发电机转速时间图"},
                         data=[
                             {"pen": "g", "name": "变流器发电机转速", "x": df1['timestamp'], "y": df1[tickets[2]]},
                             {"pen": "r", "name": "叶轮转速2", "x": df1['timestamp'], "y": df1[tickets[3]]}
                         ])
            del df1
            gc.collect()

        # 情况1 1=14，（2/23.187 - 3）>1.5，持续10s
        df_h = df[(df[tickets[1]] == 14) & (df[tickets[2]] / 23.187 - df[tickets[3]] > 1.5)].copy()
        # 情况2 2 > 300rpm
        df_l = df[(df[tickets[2]] > 300)].copy()
        # 判断是否未空
        if df_h.empty and df_l.empty:
            self.handle_signal_and_log([1, 2], [4, [1, "变流器发电机转速正常"]])
        else:
            # ------------------判断连续性
            # 高速模式连续时长判断
            if not df_h.empty:
                result = tool.duration_calculation_to_csv(tickets,
                                                          df_h,
                                                          10,
                                                          str(self.import_file_path).split(r'/')[-1].split('.')[0] +
                                                          '/变流器发电机转速异常-.csv')
                if result[0]:
                    self.handle_signal_and_log([1, 2], [4, [1, "变流器发电机转速正常"]])
                else:
                    self.handle_signal_and_log([0, 2], [4, [0, "变流器发电机转速异常"]])
                    for i in result[1]:
                        self.signal_co_write_log.emit([4, [0, i]])
                    self.signal_co_write_log.emit([4, [-1, "*" * 40]])
            if not df_l.empty:
                result = tool.duration_calculation_to_csv(tickets,
                                                          df_l,
                                                          1,
                                                          str(self.import_file_path).split(r'/')[-1].split('.')[0] +
                                                          '/变流器发电机转速异常.csv')
                if result[0]:
                    self.handle_signal_and_log([1, 2], [4, [1, "变流器发电机转速正常"]])
                else:
                    self.handle_signal_and_log([0, 2], [4, [0, "变流器发电机转速异常"]])
                    self.handle_signal_and_log([0, 2], [0, [0, "变流器发电机转速异常报警次数{}".format(len(result[1]))]])
                    for i in result[1]:
                        self.signal_co_write_log.emit([4, [0, i]])
                    self.signalcowrite_log.emit("*" * 40)
        del df_h
        del df_l
        del df
        del tickets
        gc.collect()

    # 4 变频器主机冷却液温度异常
    def converter1_water_temperature(self):
        """
        变频器主机冷却液温度异常
        原理：
        1、变频器主机冷却液温度 > 45℃ 且 变频器主机外循环风扇运行 = 1,变频器主机循环水泵运行 = 1时，持续10min
        2、任何情况下，变频器主机冷却液温度 > 48℃
        满足其一，报出变频器主机冷却液温度异常
        :return:
        """
        try:
            # 获取 1“时间”， 7“变频器主机冷却液温度”， 8“变频器主机风扇运行1”, 9”变频器主机水泵运行“英文标签
            tickets = [self.tickets[0], self.tickets[6], self.tickets[7], self.tickets[8]]
            df = self.df[['time', tickets[0], tickets[1], tickets[2], tickets[3]]]
            df.set_index(df['time'], inplace=True)
        except Exception as e:
            print(e)
            print("变频器跳过函数4")
            self.handle_signal_and_log([-1, 3], [4, [-1, "变频器主机冷却液温度英文标签丢失"]])
            return

        if self.draw:
            print("变频器绘图4")
            df1 = df.copy()
            df1.resample('30T').mean()
            df1['timestamp'] = df[tickets[0]].apply(lambda x: time.mktime(time.strptime(x, '%Y-%m-%d %H:%M:%S')))
            self.drawing(graphicsView=self.plt_list[3],
                         canvas_setting={"title": "变频器主机冷却液温度时间图"},
                         data=[
                             {"pen": "g", "name": "变频器主机冷却液温度", "x": df1['timestamp'], "y": df1[tickets[1]]}
                         ])
            del df1
            gc.collect()

        # 情况1 1>45℃ 且 2=1,3=1时，持续10min
        df_h = df[(df[tickets[1]] > 45) & (df[tickets[2]] == 1) & (df[tickets[3]] == 1)].copy()
        # 情况2 1>48℃ 
        df_l = df[(df[tickets[1]] > 48)].copy()
        # 判断是否未空
        if df_h.empty and df_l.empty:
            self.handle_signal_and_log([1, 3], [4, [1, "变频器主机冷却液温度正常"]])
        else:
            # ------------------判断连续性
            # 高速模式连续时长判断
            if not df_h.empty:
                result = tool.duration_calculation_to_csv(tickets,
                                                          df_h,
                                                          600,
                                                          str(self.import_file_path).split(r'/')[-1].split('.')[0] +
                                                          '/变频器主机冷却液温度异常.csv')
                if result[0]:
                    self.handle_signal_and_log([1, 3], [4, [1, "变频器主机冷却液温度正常"]])
                else:
                    self.handle_signal_and_log([0, 3], [4, [0, "变频器主机冷却液温度异常"]])
                    for i in result[1]:
                        self.signal_co_write_log.emit([4, [0, i]])
                    self.signal_co_write_log.emit([4, [-1, "*" * 40]])
            if not df_l.empty:
                result = tool.duration_calculation_to_csv(tickets,
                                                          df_l,
                                                          1,
                                                          str(self.import_file_path).split(r'/')[-1].split('.')[0] +
                                                          '/变频器主机冷却液温度异常.csv')
                if result[0]:
                    self.handle_signal_and_log([1, 3], [4, [1, "变频器主机冷却液温度正常"]])
                else:
                    self.handle_signal_and_log([0, 3], [4, [0, "变频器主机冷却液温度异常"]])
                    self.handle_signal_and_log([0, 3], [0, [0, "变频器主机冷却液温度异常报警次数{}".format(len(result[1]))]])
                    for i in result[1]:
                        self.signal_co_write_log.emit([4, [0, i]])
                    self.signal_co_write_log.emit([4, [-1, "*" * 40]])
        del df_h
        del df_l
        del df
        del tickets
        gc.collect()

    # 5 变频器从机冷却液温度异常
    def converter2_water_temperature(self):
        """
        变频器从机冷却液温度异常
        原理：
        1、变频器从机冷却液温度 > 45℃ 且 变频器从机外循环风扇运行 = 1,变频器从机循环水泵运行 = 1时，持续10min
        2、任何情况下，变频器从机冷却液温度 > 48℃
        满足其一，报出变频器从机冷却液温度异常
        :return:
        """
        try:
            # 获取 1“时间”， 10“变频器从机冷却液温度”，11“变频器从机风扇运行1”, 12”变频器从机水泵运行“英文标签
            tickets = [self.tickets[0], self.tickets[9], self.tickets[10], self.tickets[11]]
            df = self.df[['time', tickets[0], tickets[1], tickets[2], tickets[3]]]
            df.set_index(df['time'], inplace=True)
        except Exception as e:
            print(e)
            print("变频器跳过函数5")
            self.handle_signal_and_log([-1, 4], [4, [-1, "变频器从机冷却液温度英文标签丢失"]])
            return

        if self.draw:
            print("变频器绘图5")
            df1 = df.copy()
            df1.resample('30T').mean()
            df1['timestamp'] = df[tickets[0]].apply(lambda x: time.mktime(time.strptime(x, '%Y-%m-%d %H:%M:%S')))
            self.drawing(graphicsView=self.plt_list[4],
                         canvas_setting={"title": "变频器从机冷却液温度时间图"},
                         data=[
                             {"pen": "g", "name": "变频器从机冷却液温度", "x": df1['timestamp'], "y": df1[tickets[1]]}
                         ])
            del df1
            gc.collect()

        # 情况1 1>45℃ 且 2=1,3=1时，持续10min
        df_h = df[(df[tickets[1]] > 45) & (df[tickets[2]] == 1) & (df[tickets[3]] == 1)].copy()
        # 情况2 1>48℃
        df_l = df[(df[tickets[1]] > 48)].copy()
        # 判断是否未空
        if df_h.empty and df_l.empty:
            self.handle_signal_and_log([1, 4], [4, [1, "变频器从机冷却液温度正常"]])
        else:
            # ------------------判断连续性
            # 最终报警次数
            total_alarm_number = 0
            # 高速模式连续时长判断
            if not df_h.empty:
                result = tool.duration_calculation_to_csv(tickets,
                                                          df_h,
                                                          600,
                                                          str(self.import_file_path).split(r'/')[-1].split('.')[0] +
                                                          '/变频器从机冷却液温度异常.csv')
                if result[0]:
                    self.handle_signal_and_log([1, 4], [4, [1, "变频器从机冷却液温度正常"]])
                else:
                    self.handle_signal_and_log([0, 4], [4, [0, "变频器从机冷却液温度异常"]])
                    total_alarm_number = len(result[1])
                    for i in result[1]:
                        self.signal_co_write_log.emit([4, [0, i]])
                    self.signal_co_write_log.emit([4, [-1, "*" * 40]])
            if not df_l.empty:
                result = tool.duration_calculation_to_csv(tickets,
                                                          df_l,
                                                          1,
                                                          str(self.import_file_path).split(r'/')[-1].split('.')[0] +
                                                          '/变频器从机冷却液温度异常.csv')
                if result[0]:
                    self.handle_signal_and_log([1, 4], [4, [1, "变频器从机冷却液温度正常"]])
                else:
                    self.handle_signal_and_log([0, 4], [4, [0, "变频器从机冷却液温度异常"]])
                    total_alarm_number += len(result[1])
                    self.handle_signal_and_log([0, 4], [0, [0, "变频器从机冷却液温度异常报警次数{}".format(total_alarm_number)]])
                    for i in result[1]:
                        self.signal_co_write_log.emit([4, [0, i]])
                    self.signal_co_write_log.emit([4, [-1, "*" * 40]])
        del df_h
        del df_l
        del df
        del tickets
        gc.collect()

    # 6 变频器主机冷却液压力异常
    def converter1_water_pressure(self):
        """
        变频器主机冷却液压力异常
        原理：
        1、变频器主机循环水泵运行=1时，变频器主机冷却液压力>5.5bar或<3.5bar，持续10min
        2、变频器主机循环水泵运行=0时，变频器主机冷却液压力>3bar或<1.2bar，持续10min
        满足其一，报出变频器主机冷却液压力异常
        :return:
        """
        try:
            # 获取 1“时间”， 9”变频器主机水泵运行“  13“变频器主机冷却液压力”，英文标签
            tickets = [self.tickets[0], self.tickets[8], self.tickets[12]]
            df = self.df[['time', tickets[0], tickets[1], tickets[2]]]
            df.set_index(df['time'], inplace=True)
        except Exception as e:
            print(e)
            print("变频器跳过函数6")
            self.handle_signal_and_log([-1, 5], [4, [-1, "变频器主机冷却液压力英文标签丢失"]])
            return

        if self.draw:
            print("变频器绘图6")
            df1 = df.copy()
            df1.resample('30T').mean()
            df1['timestamp'] = df[tickets[0]].apply(lambda x: time.mktime(time.strptime(x, '%Y-%m-%d %H:%M:%S')))
            self.drawing(graphicsView=self.plt_list[5],
                         canvas_setting={"title": "变频器主机冷却液压力时间图"},
                         data=[
                             {"pen": "g", "name": "变频器主机冷却液压力", "x": df1['timestamp'], "y": df1[tickets[2]]}
                         ])
            del df1
            gc.collect()

        # 情况1 2=1时，1>5.5bar或<3.5bar，持续10min
        df_h = df[(df[tickets[1]] == 1) & ((df[tickets[2]] > 5.5) | (df[tickets[2]] < 3.5))].copy()
        # 情况2 2=0时，1>3bar或<1.2bar，持续10min
        df_l = df[(df[tickets[1]] == 0) & ((df[tickets[2]] > 3) | (df[tickets[2]] < 1.2))].copy()
        # 判断是否未空
        if df_h.empty and df_l.empty:
            self.handle_signal_and_log([1, 5], [4, [1, "变频器主机冷却液压力正常"]])
        else:
            # ------------------判断连续性
            # 最终报警次数
            total_alarm_number = 0
            # 高速模式连续时长判断
            if not df_h.empty:
                result = tool.duration_calculation_to_csv(tickets,
                                                          df_h,
                                                          600,
                                                          str(self.import_file_path).split(r'/')[-1].split('.')[0] +
                                                          '/变频器主机冷却液压力异常.csv')
                if result[0]:
                    self.handle_signal_and_log([1, 5], [4, [1, "变频器主机冷却液压力正常"]])
                else:
                    self.handle_signal_and_log([0, 5], [4, [0, "变频器主机冷却液压力异常"]])
                    total_alarm_number = len(result[1])
                    for i in result[1]:
                        self.signal_co_write_log.emit([4, [0, i]])
                    self.signal_co_write_log.emit([4, [-1, "*" * 40]])
            if not df_l.empty:
                result = tool.duration_calculation_to_csv(tickets,
                                                          df_l,
                                                          600,
                                                          str(self.import_file_path).split(r'/')[-1].split('.')[0] +
                                                          '/变频器主机冷却液压力异常.csv')
                if result[0]:
                    self.handle_signal_and_log([1, 5], [4, [1, "变频器主机冷却液压力正常"]])
                else:
                    self.handle_signal_and_log([0, 5], [4, [0, "变频器主机冷却液压力异常"]])
                    total_alarm_number += len(result[1])
                    self.handle_signal_and_log([0, 5], [0, [0, "变频器从机冷却液温度异常报警次数{}".format(total_alarm_number)]])
                    for i in result[1]:
                        self.signal_co_write_log.emit([4, [0, i]])
                    self.signal_co_write_log.emit([4, [-1, "*" * 40]])
        del df_h
        del df_l
        del df
        del tickets
        gc.collect()

    # 7 变频器从机冷却液压力异常
    def converter2_water_pressure(self):
        """
        变频器从机冷却液压力异常
        原理：
        1、变频器从机循环水泵运行=1时，变频器从机冷却液压力>5.5bar或<3.5bar，持续10min
        2、变频器从机循环水泵运行=0时，变频器从机冷却液压力>3bar或<1.2bar，持续10min
        满足其一，报出变频器从机冷却液压力异常
        :return:
        """
        try:
            # 获取 1“时间”， 12”变频器从机水泵运行“  14变频器从机冷却液压力”, 英文标签
            tickets = [self.tickets[0], self.tickets[11], self.tickets[13]]
            df = self.df[['time', tickets[0], tickets[1], tickets[2]]]
            df.set_index(df['time'], inplace=True)
        except Exception as e:
            print(e)
            print("变频器跳过函数7")
            self.handle_signal_and_log([-1, 6], [4, [-1, "变频器从机冷却液压力英文标签丢失"]])
            return

        if self.draw:
            print("变频器绘图7")
            df1 = df.copy()
            df1.resample('30T').mean()
            df1['timestamp'] = df[tickets[0]].apply(lambda x: time.mktime(time.strptime(x, '%Y-%m-%d %H:%M:%S')))
            self.drawing(graphicsView=self.plt_list[6],
                         canvas_setting={"title": "变频器从机冷却液压力时间图"},
                         data=[
                             {"pen": "g", "name": "变频器从机冷却液压力", "x": df1['timestamp'], "y": df1[tickets[2]]}
                         ])
            del df1
            gc.collect()

        # 情况1 1=1时，2>5.5bar或<3.5bar，持续10min
        df_h = df[(df[tickets[1]] == 1) & ((df[tickets[2]] > 5.5) | (df[tickets[2]] < 3.5))].copy()
        # 情况2 1=0时，2>3bar或<1.2bar，持续10min
        df_l = df[(df[tickets[1]] == 0) & ((df[tickets[2]] > 3) | (df[tickets[2]] < 1.2))].copy()
        # 判断是否未空
        if df_h.empty and df_l.empty:
            self.handle_signal_and_log([1, 6], [4, [1, "变频器从机冷却液压力正常"]])
        else:
            # ------------------判断连续性
            # 最终报警次数
            total_alarm_number = 0
            # 高速模式连续时长判断
            if not df_h.empty:
                result = tool.duration_calculation_to_csv(tickets,
                                                          df_h,
                                                          600,
                                                          str(self.import_file_path).split(r'/')[-1].split('.')[0] +
                                                          '/变频器从机冷却液压力异常.csv')
                if result[0]:
                    self.handle_signal_and_log([1, 6], [4, [1, "变频器从机冷却液压力正常"]])
                else:
                    self.handle_signal_and_log([0, 6], [4, [0, "变频器从机冷却液压力异常"]])
                    total_alarm_number = len(result[1])
                    for i in result[1]:
                        self.signal_co_write_log.emit([4, [0, i]])
                    self.signal_co_write_log.emit([4, [-1, "*" * 40]])
            if not df_l.empty:
                result = tool.duration_calculation_to_csv(tickets,
                                                          df_l,
                                                          600,
                                                          str(self.import_file_path).split(r'/')[-1].split('.')[0] +
                                                          '/变频器从机冷却液压力异常.csv')
                if result[0]:
                    self.handle_signal_and_log([1, 6], [4, [1, "变频器从机冷却液压力正常"]])
                else:
                    self.handle_signal_and_log([0, 6], [4, [0, "变频器从机冷却液压力异常"]])
                    total_alarm_number += len(result[1])
                    self.handle_signal_and_log([0, 6], [0, [0, "变频器从机冷却液压力异常报警次数{}".format(total_alarm_number)]])
                    for i in result[1]:
                        self.signal_co_write_log.emit([4, [0, i]])
                    self.signal_co_write_log.emit([4, [-1, "*" * 40]])
        del df_h
        del df_l
        del df
        del tickets
        gc.collect()

    def over(self):
        # 第一个线程结束
        self.signal_co_over.emit([4, 1])