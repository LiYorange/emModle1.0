# -------------------------------------------------------------------------------
# Name:         grHydraulic1
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


class Hydraulic1(QObject):
    """
    液压系统预警模型
    """
    # 类变量
    signal_hy_color = pyqtSignal(list)
    signal_hy_show_message = pyqtSignal(str)
    signal_hy_progress = pyqtSignal(dict)
    signal_hy_write_log = pyqtSignal(list)
    signal_hy_over = pyqtSignal(list)

    def __init__(self, tickets_file_path=None, import_data_path=None, df=None,
                 project_index=None, plt_list=None, draw=False):
        """
        :param tickets_file_path: 将中文标签转化为英文标签的list
        :param import_data_path: 需要处理的数据路径
        :param project_index: 选区的项目序号
        :param plt_list: 绘图对象

        """
        super(Hydraulic1, self).__init__()
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
            self.hydraulic_sys,
            self.hydraulic_stop,
            self.hydraulic_yaw_brake_open_half_pressure1,
            self.hydraulic_yaw_brake_open_half_pressure2,
            self.hydraulic_oil_temperature,
            self.hydraulic_pump_outlet_pressure,
            self.hydraulic_rotor_lock_pressure,
            self.hydraulic_rotor_lock_actived_accumlator_pressure,
            self.yaw_brake_pressure,
            self.hydraulic_yaw_brake1,
            self.hydraulic_yaw_brake2,
            self.over
        ]
        # ------------------------------------------->>>实例变量初始化结束

    def run(self):
        self.signal_hy_show_message.emit("液压系统模块已启动！")
        self.signal_hy_write_log.emit(
            [5, [1, time.strftime('%Y{y}%m{m}%d{d} %H{h}%M{f}%S{s}').format(y='年', m='月', d='日',
                                                                            h='时', f='分', s='秒') + ":液压系统模块进程开始运行"]])

        for (func, i) in zip(self.function_list, range(len(self.function_list))):
            func()
            del func
            # print(int((i + 1) / len(self.function_list) * 100))
            self.signal_hy_progress.emit({"hydraulic": int((i + 1) / len(self.function_list) * 100)})
        self.signal_hy_show_message.emit("液压系统模块计算完成！")
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
            "液压系统压力",
            "液压泵1开",
            "液压泵2开",
            "顺时针偏航",
            "逆时针偏航",
            "偏航制动出口压力1",
            "偏航制动出口压力2",
            "偏航制动入口压力1",
            "偏航制动入口压力2",
            "偏航半释放阀",
            "液压主泵处油温",
            "液压泵出口压力",
            "液压回油口油温",
            "叶轮锁定压力1",
            "叶轮锁定压力2",
            "叶轮锁蓄能器压力1",
            "叶轮锁蓄能器压力2"
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
        self.signal_hy_color.emit(color_signal)

        log_signal[1][1] = time.strftime('%Y{y}%m{m}%d{d} %H{h}%M{f}%S{s}').format(y='年', m='月', d='日',
                                                                                   h='时', f='分', s='秒') + ":" + \
                           log_signal[1][1]
        self.signal_hy_write_log.emit(log_signal)

    # 1 液压系统压力异常
    def hydraulic_sys(self):

        """
        ：液压系统压力异常
        ：12≤ 机组运行模式 ≤14，液压系统压力 < 150ba r或 > 175bar, 持续20s
        """

        try:
            # 获取 1 时间 2 机组运行模式 3 液压系统压力 英文标签
            # print(self.tickets)
            tickets = [self.tickets[0], self.tickets[1], self.tickets[2]]
            # tickets = self.tickets

            df = self.df[['time', tickets[0], tickets[1], tickets[2]]]
            df.set_index(df['time'], inplace=True)
        except Exception as e:
            print(e)
            print("液压跳过函数1")
            self.handle_signal_and_log([-1, 0], [5, [-1, "液压系统压力英文标签丢失"]])
            return
        if self.draw:
            print("液压绘图1")
            df1 = df.copy()
            df1.resample('30T').mean()
            df1['timestamp'] = df[tickets[0]].apply(lambda x: time.mktime(time.strptime(x, '%Y-%m-%d %H:%M:%S')))
            self.drawing(graphicsView=self.plt_list[0],
                         canvas_setting={"title": "液压系统压力时间图"},
                         data=[
                             {"pen": "g", "name": "液压系统压力", "x": df1['timestamp'], "y": df1[tickets[2]]},
                         ])
            del df1
            gc.collect()

        # 删除 1 < 12 | 1 > 14
        df = df.drop(df[((df[tickets[1]] > 14) | (df[tickets[1]] < 12))].index)
        if df.empty:
            self.handle_signal_and_log([1, 0], [5, [1, "液压系统压力正常"]])

        else:
            # 删除 2<=175 & 2>=150
            df = df.drop(df[(
                    (df[tickets[2]] <= 175) & (df[tickets[2]] >= 150))].index)
            if df.empty:
                self.handle_signal_and_log([1, 0], [5, [1, "液压系统压力正常"]])
            else:
                # ------------------判断连续性
                result = tool.duration_calculation_to_csv(tickets,
                                                          df,
                                                          20,
                                                          str(self.import_file_path).split(r'/')[-1].split('.')[0] +
                                                          '/液压系统压力异常.csv')
                if result[0]:
                    self.handle_signal_and_log([1, 0], [5, [1, "液压系统压力正常"]])

                else:
                    self.handle_signal_and_log([0, 0], [5, [0, "液压系统压力异常"]])
                    self.handle_signal_and_log([0, 0], [0, [0, "液压系统压力异常报警次数{}".format(len(result[1]))]])
                    for i in result[1]:
                        self.signal_hy_write_log.emit([5, [0, i]])
                    self.signal_hy_write_log.emit([5, [-1, "*" * 40]])

        del df
        # # 从原数据中删除 液压系统压力
        # del self.df[tickets[2]]
        del tickets
        gc.collect()

    # 2 液压泵频繁启停异常
    def hydraulic_stop(self):
        """
        1、机组运行模式=14
        2、机组未偏航期间（偏航CW和偏航CCW都为0）
        3、液压泵未启动
        4、液压系统压力值的瞬时值与上一秒瞬时值差值的绝对值≥0.1bar，持续1min
        :return:
        """
        try:
            # 获取 时间 0 机组运行模式 1 液压系统压力 2 液压泵1开 3 液压泵2开 4 顺时针偏航 5 逆时针偏航 6 英文标签
            # print(self.tickets)
            tickets = [self.tickets[0], self.tickets[1], self.tickets[2], self.tickets[3],
                       self.tickets[4], self.tickets[5], self.tickets[6]]
            # tickets = self.tickets

            df = self.df[['time', tickets[0], tickets[1], tickets[2], tickets[3],
                          tickets[4], tickets[5], tickets[6]]]
            df.set_index(df['time'], inplace=True)
        except Exception as e:
            print(e)
            print("液压跳过函数2")
            self.handle_signal_and_log([-1, 1], [5, [-1, "液压泵频繁启停英文标签丢失"]])
            return
        if self.draw:
            print("液压绘图2")
            df1 = df.copy()
            df1.resample('30T').mean()
            df1['timestamp'] = df[tickets[0]].apply(lambda x: time.mktime(time.strptime(x, '%Y-%m-%d %H:%M:%S')))
            self.drawing(graphicsView=self.plt_list[1],
                         canvas_setting={"title": "液压系统压力时间图"},
                         data=[
                             {"pen": "g", "name": "液压系统压力", "x": df1['timestamp'], "y": df1[tickets[2]]},
                         ])
            del df1
            gc.collect()

        # 删除 机组模式 != 14 且液压泵开任意一个
        df = df.drop(df[((df[tickets[1]] != 14) & ((df[tickets[3]] == 1) | (df[tickets[4]] == 1)))].index)
        if df.empty:
            self.handle_signal_and_log([1, 1], [5, [1, "液压泵频繁启正常"]])
        else:
            # 删除 未开启偏航的反面
            df = df.drop(df[(df[tickets[5]] != 0) | (df[tickets[6]] != 0)].index)
            if df.empty:
                self.handle_signal_and_log([1, 1], [5, [1, "液压泵频繁启正常"]])
            else:
                # 液压系统压力值的瞬时值与上一秒瞬时值差值的绝对值≥0.1bar, 持续1min
                df['shift'] = df[tickets[2]].shift(1)
                df = df.drop(df[df['shift'] < 0.1].index)
                if df.empty:
                    self.handle_signal_and_log([1, 1], [5, [1, "液压泵频繁启正常"]])
                else:
                    # ------------------判断连续性
                    result = tool.duration_calculation_to_csv(tickets,
                                                              df,
                                                              60,
                                                              str(self.import_file_path).split(r'/')[-1].split('.')[0] +
                                                              '/偏航制动器1异常.csv')
                    if result[0]:
                        self.handle_signal_and_log([1, 1], [5, [1, "偏航制动器1正常"]])

                    else:
                        self.handle_signal_and_log([0, 1], [5, [0, "偏航制动器1异常"]])
                        self.handle_signal_and_log([0, 1], [0, [0, "偏航制动器1异常报警次数{}".format(len(result[1]))]])
                        for i in result[1]:
                            self.signal_hy_write_log.emit([5, [0, i]])
                        self.signal_hy_write_log.emit([5, [-1, "*" * 40]])

        del df
        # # 从原数据中删除 偏航制动器1
        # del self.df[tickets[2]]
        del tickets
        gc.collect()

    # 3 偏航半释放压力1异常 YawBrakeOpenHalfPressure1Abnormal
    def hydraulic_yaw_brake_open_half_pressure1(self):

        """
        ：偏航半释放压力1异常
        ：1.偏航半释放阀为1时，液压偏航制动入口压力1和液压偏航制动出口压力1最小值超出[25, 47]范围，
         2.液压偏航制动入口压力1和液压偏航制动出口压力1差值大于2或小于 - 1，持续3秒。
         满足其一
        """

        try:
            # 获取  时间 0 偏航半释放阀 11 偏航制动入口压力1 10  偏航制动出口压力1 8 英文标签
            # print(self.tickets)
            tickets = [self.tickets[0], self.tickets[11], self.tickets[9], self.tickets[7]]
            # tickets = self.tickets

            df = self.df[['time', tickets[0], tickets[1], tickets[2], tickets[3]]]
            df.set_index(df['time'], inplace=True)
        except Exception as e:
            print(e)
            print("液压跳过函数3")
            self.handle_signal_and_log([-1, 2], [5, [-1, "偏航半释放压力1英文标签丢失"]])
            return

        if self.draw:
            print("液压绘图3")
            df1 = df.copy()
            df1.resample('30T').mean()
            df1['timestamp'] = df[tickets[0]].apply(lambda x: time.mktime(time.strptime(x, '%Y-%m-%d %H:%M:%S')))
            self.drawing(graphicsView=self.plt_list[2],
                         canvas_setting={"title": "偏航半释放压力1时间图"},
                         data=[
                             {"pen": "g", "name": "偏航制动入口压力1", "x": df1['timestamp'], "y": df1[tickets[2]]},
                             {"pen": "r", "name": "偏航制动出口压力1", "x": df1['timestamp'], "y": df1[tickets[3]]}
                         ])
            del df1
            gc.collect()

        # 情况1 偏航半释放阀为1时，液压偏航制动入口压力1和液压偏航制动出口压力1最小值超出[25, 47]范围，
        df_1 = df.copy()
        # # 删除 偏航半释放阀不为1
        df_1.drop(df[(df[tickets[1]] != 1)].index)
        # #  获得 每一秒 液压偏航制动入口压力1和液压偏航制动出口压力1最小值
        # # 判断是否在[25, 47]范围
        df_1['min'] = df_1.loc[:, [tickets[2], tickets[3]]].min(axis=1, skipna=True)
        df_1 = df_1.drop(df_1[(df_1['min'] > 47) | (df_1['min'] < 25)].index)
        # df_1 = df_1.drop(df_1[df_1['min'] > 47].index)
        # 情况2 液压偏航制动入口压力1和液压偏航制动出口压力1差值大于2或小于 - 1，持续3秒
        df_2 = df.copy()
        # # 删除压差>=-1 或者<=2 的值
        df_2 = df_2.drop(
            df_2[(df[tickets[2]] - df_2[tickets[3]] >= -1) | (df_2[tickets[2]] - df_2[tickets[3]] <= 2)].index)
        if df_1.empty and df_2.empty:
            self.handle_signal_and_log([1, 2], [5, [1, "偏航半释放压力1正常"]])
        else:
            # 创建一个故障时间的列表，用于汇总两种情况下的故障时间，最后在源数据中筛选故障时间
            finally_fault_time_list = []
            # ------------------如果情况1不为空 得到情况1的故障时间节点
            if not df_1.empty:
                # 此时result 有3个返回值 false, fault_time, fault_time_list
                result = tool.duration_calculation_to_csv(tickets,
                                                          df_1,
                                                          1,
                                                          None)

                # # 得到故障时间的文本，打印在日志文本框内
                # for i in result[2]:
                #     self.signal_hy_write_log.emit([5, [2, i]])
                # 得到故障时间的时间格式，用于与第二个条件的时间进行合并，最后筛选出总的故障时间
                for i in result[1]:
                    finally_fault_time_list.append(i)
            if not df_2.empty:
                result = tool.duration_calculation_to_csv(tickets,
                                                          df_1,
                                                          3,
                                                          None)
                if result[0]:
                    # 如果情况二没有故障
                    pass
                else:
                    # 情况二故障
                    # # 得到故障时间的文本，打印在日志文本框内
                    # for i in result[2]:
                    #     self.signal_hy_write_log.emit([5, [2, i]])
                    # 得到故障时间的时间格式，用于与第二个条件的时间进行合并，最后筛选出总的故障时间
                    for i in result[1]:
                        finally_fault_time_list.append(i)
            # finally_fault_time_list形式为：[['A','B'],['C','D'],['E']]，需要将其转为['A','B','C','D','E']
            # 将嵌套的finally_fault_time_list 转化为1个列表
            finally_fault_time_list = sum(finally_fault_time_list, [])
            # 提取df
            df = df.loc[finally_fault_time_list, :]
            result = tool.duration_calculation_to_csv(tickets,
                                                      df_1,
                                                      1,
                                                      str(self.import_file_path).split(r'/')[-1].split('.')[0] +
                                                      '/偏航半释放压力1异常.csv')
            # 得到故障时间的文本，打印在日志文本框内
            self.handle_signal_and_log([0, 2], [5, [0, "偏航半释放压力1异常"]])
            self.handle_signal_and_log([0, 2], [0, [0, "偏航半释放压力1异常报警次数{}".format(len(result[1]))]])
            for i in result[1]:
                self.signal_hy_write_log.emit([5, [0, i]])
            self.signal_hy_write_log.emit([5, [-1, "*" * 40]])
        del df_1
        del df_2
        del df

    # 4 偏航半释放压力2异常
    def hydraulic_yaw_brake_open_half_pressure2(self):

        """
        ：偏航半释放压力2异常
        ：1.偏航半释放阀为1时，液压偏航制动入口压力2和液压偏航制动出口压力2最小值超出[25, 47]范围，
         2.液压偏航制动入口压力1和液压偏航制动出口压力2差值大于2或小于 - 1，持续3秒。
         满足其一
        """

        try:
            # 获取  时间 0 偏航半释放阀 11 偏航制动入口压力2 11  偏航制动出口压力2 9 英文标签
            # print(self.tickets)
            tickets = [self.tickets[0], self.tickets[11], self.tickets[10], self.tickets[8]]
            # tickets = self.tickets

            df = self.df[['time', tickets[0], tickets[1], tickets[2], tickets[3]]]
            df.set_index(df['time'], inplace=True)
        except Exception as e:
            print(e)
            print("液压跳过函数4")
            self.handle_signal_and_log([-1, 3], [5, [-1, "偏航半释放压力2英文标签丢失"]])
            return

        if self.draw:
            print("液压绘图4")
            df1 = df.copy()
            df1.resample('30T').mean()
            df1['timestamp'] = df[tickets[0]].apply(lambda x: time.mktime(time.strptime(x, '%Y-%m-%d %H:%M:%S')))
            self.drawing(graphicsView=self.plt_list[3],
                         canvas_setting={"title": "偏航半释放压力2时间图"},
                         data=[
                             {"pen": "g", "name": "偏航制动入口压力2", "x": df1['timestamp'], "y": df1[tickets[2]]},
                             {"pen": "r", "name": "偏航制动出口压力2", "x": df1['timestamp'], "y": df1[tickets[3]]}
                         ])
            del df1
            gc.collect()

        # 情况1 偏航半释放阀为1时，液压偏航制动入口压力2和液压偏航制动出口压力2最小值超出[25, 47]范围，
        df_1 = df.copy()
        # # 删除 偏航半释放阀不为1
        df_1.drop(df[(df[tickets[1]] != 1)].index)
        # #  获得 每一秒 液压偏航制动入口压力1和液压偏航制动出口压力1最小值
        # # 判断是否在[25, 47]范围
        df_1['min'] = df_1.loc[:, [tickets[2], tickets[3]]].min(axis=1, skipna=True)
        df_1 = df_1.drop(df_1[(df_1['min'] > 47) | (df_1['min'] < 25)].index)
        # df_1 = df_1.drop(df_1[df_1['min'] > 47].index)
        # 情况2 液压偏航制动入口压力2和液压偏航制动出口压力2差值大于2或小于 - 1，持续3秒
        df_2 = df.copy()
        # # 删除压差>=-1 或者<=2 的值
        df_2 = df_2.drop(
            df_2[(df[tickets[2]] - df_2[tickets[3]] >= -1) | (df_2[tickets[2]] - df_2[tickets[3]] <= 2)].index)
        if df_1.empty and df_2.empty:
            self.handle_signal_and_log([1, 3], [5, [1, "偏航半释放压力2正常"]])
        else:
            # 创建一个故障时间的列表，用于汇总两种情况下的故障时间，最后在源数据中筛选故障时间
            finally_fault_time_list = []
            # ------------------如果情况1不为空 得到情况1的故障时间节点
            if not df_1.empty:
                # 此时result 有3个返回值 false, fault_time, fault_time_list
                result = tool.duration_calculation_to_csv(tickets,
                                                          df_1,
                                                          1,
                                                          None)

                # # 得到故障时间的文本，打印在日志文本框内
                # for i in result[2]:
                #     self.signal_hy_write_log.emit([5, [2, i]])
                # 得到故障时间的时间格式，用于与第二个条件的时间进行合并，最后筛选出总的故障时间
                for i in result[1]:
                    finally_fault_time_list.append(i)
            if not df_2.empty:
                result = tool.duration_calculation_to_csv(tickets,
                                                          df_1,
                                                          3,
                                                          None)
                if result[0]:
                    # 如果情况二没有故障
                    pass
                else:
                    # 情况二故障
                    # # 得到故障时间的文本，打印在日志文本框内
                    # for i in result[2]:
                    #     self.signal_hy_write_log.emit([5, [2, i]])
                    # 得到故障时间的时间格式，用于与第二个条件的时间进行合并，最后筛选出总的故障时间
                    for i in result[1]:
                        finally_fault_time_list.append(i)
            # finally_fault_time_list形式为：[['A','B'],['C','D'],['E']]，需要将其转为['A','B','C','D','E']
            # 将嵌套的finally_fault_time_list 转化为1个列表
            finally_fault_time_list = sum(finally_fault_time_list, [])
            # 提取df
            df = df.loc[finally_fault_time_list, :]
            result = tool.duration_calculation_to_csv(tickets,
                                                      df,
                                                      1,
                                                      str(self.import_file_path).split(r'/')[-1].split('.')[0] +
                                                      '/偏航半释放压力2异常.csv')
            # 得到故障时间的文本，打印在日志文本框内
            self.handle_signal_and_log([0, 3], [5, [0, "偏航半释放压力2异常"]])
            self.handle_signal_and_log([0, 3], [0, [0, "偏航半释放压力2异常报警次数{}".format(len(result[1]))]])
            for i in result[1]:
                self.signal_hy_write_log.emit([5, [0, i]])
            self.signal_hy_write_log.emit([5, [-1, "*" * 40]])
        del df_1
        del df_2
        del df

    # 5 液压系统油温异常
    def hydraulic_oil_temperature(self):
        """
        12≤机组运行模式≤14，液压泵主泵处油温和液压回油口油温≠0，两者最小值<20℃，最大值>60℃，持续1min
        :return:
        """
        try:
            # 获取  时间 0 机组运行模式 1 液压主泵处油温 12 液压回油口油温 14 英文标签
            # print(self.tickets)
            tickets = [self.tickets[0], self.tickets[1], self.tickets[12], self.tickets[14]]
            df = self.df[['time', tickets[0], tickets[1], tickets[2], tickets[3]]]
            df.set_index(df['time'], inplace=True)
        except Exception as e:
            print(e)
            print("液压跳过函数5")
            self.handle_signal_and_log([-1, 4], [5, [-1, "液压系统油温英文标签丢失"]])
            return

        if self.draw:
            print("液压绘图5")
            df1 = df.copy()
            df1.resample('30T').mean()
            df1['timestamp'] = df[tickets[0]].apply(lambda x: time.mktime(time.strptime(x, '%Y-%m-%d %H:%M:%S')))
            self.drawing(graphicsView=self.plt_list[4],
                         canvas_setting={"title": "液压系统油温时间图"},
                         data=[
                             {"pen": "g", "name": "液压主泵处油温", "x": df1['timestamp'], "y": df1[tickets[2]]},
                             {"pen": "r", "name": "液压回油口油温", "x": df1['timestamp'], "y": df1[tickets[3]]}
                         ])
            del df1
            gc.collect()

            # 删除 1 < 12 | 1 > 14
        # 删除机组模式
        df = df.drop(df[((df[tickets[1]] > 14) | (df[tickets[1]] < 12))].index)
        if df.empty:
            self.handle_signal_and_log([1, 4], [5, [1, "液压系统油温正常"]])
        else:
            # 删除 液压泵主泵处油温 或者 液压回油口油温 == 0
            df = df.drop(df[(
                    (df[tickets[2]] == 0) | (df[tickets[3]] == 0))].index)
            if df.empty:
                self.handle_signal_and_log([1, 4], [5, [1, "液压系统油温正常"]])
            else:
                # 判断液压泵主泵处油温和液压回油口油温≠0，两者最小值<20℃，最大值>60℃
                # 删除 两者差 >=20℃，<=60℃
                df = df.drop(df[(
                        (df[tickets[2]] - df[tickets[3]] >= 20) |
                        (df[tickets[2]] - df[tickets[3]] <= 60)
                )].index)
                if df.empty:
                    self.handle_signal_and_log([1, 4], [5, [1, "液压系统油温正常"]])
                else:
                    # ------------------判断连续性 持续1min
                    result = tool.duration_calculation_to_csv(tickets,
                                                              df,
                                                              60,
                                                              str(self.import_file_path).split(r'/')[-1].split('.')[0] +
                                                              '/液压系统油温异常.csv')
                    if result[0]:
                        self.handle_signal_and_log([1, 4], [5, [1, "液压系统油温正常"]])

                    else:
                        self.handle_signal_and_log([0, 4], [5, [0, "液压系统油温异常"]])
                        self.handle_signal_and_log([0, 4], [0, [0, "液压系统油温异常报警次数{}".format(len(result[1]))]])
                        for i in result[1]:
                            self.signal_hy_write_log.emit([5, [0, i]])
                        self.signal_hy_write_log.emit([5, [-1, "*" * 40]])

        del df
        # # 从原数据中删除 液压系统压力
        # del self.df[tickets[2]]
        del tickets
        gc.collect()

    # 6 液压泵出口压力异常
    def hydraulic_pump_outlet_pressure(self):

        """
        ：液压泵出口压力异常
        ：液压泵1启动 或 液压泵2启动 = 1时，液压泵出口压力 <150bar 或 >175bar，持续10s
        """

        try:
            # 获取 1 时间 4 液压泵1开 5 液压泵2开 14 液压泵出口压力 英文标签
            # print(self.tickets)
            tickets = [self.tickets[0], self.tickets[3], self.tickets[4], self.tickets[13]]
            # tickets = self.tickets

            df = self.df[['time', tickets[0], tickets[1], tickets[2], tickets[3]]]
            df.set_index(df['time'], inplace=True)
        except Exception as e:
            print(e)
            print("液压跳过函数6")
            self.handle_signal_and_log([-1, 5], [5, [-1, "液压泵出口压力英文标签丢失"]])
            return

        if self.draw:
            print("液压绘图6")
            df1 = df.copy()
            df1.resample('30T').mean()
            df1['timestamp'] = df[tickets[0]].apply(lambda x: time.mktime(time.strptime(x, '%Y-%m-%d %H:%M:%S')))
            self.drawing(graphicsView=self.plt_list[5],
                         canvas_setting={"title": "液压泵出口压力时间图"},
                         data=[
                             {"pen": "g", "name": "液压泵出口压力", "x": df1['timestamp'], "y": df1[tickets[3]]}
                         ])
            del df1
            gc.collect()

        # 删除 1 != 1 & 2 != 1
        df = df.drop(df[(df[tickets[1]] & df[tickets[2]])].index)
        if df.empty:
            self.handle_signal_and_log([1, 5], [5, [1, "液压泵出口压力正常"]])

        else:
            # 删除 3<=175 & 3>=150
            df = df.drop(df[((df[tickets[3]] <= 175) & (df[tickets[3]] >= 150))].index)
            if df.empty:
                self.handle_signal_and_log([1, 5], [5, [1, "液压泵出口压力正常"]])
            else:
                # ------------------判断连续性
                result = tool.duration_calculation_to_csv(tickets,
                                                          df,
                                                          10,
                                                          str(self.import_file_path).split(r'/')[-1].split('.')[0] +
                                                          '/液压泵出口压力异常.csv')
                if result[0]:
                    self.handle_signal_and_log([1, 5], [5, [1, "液压泵出口压力正常"]])

                else:
                    self.handle_signal_and_log([0, 5], [5, [0, "液压泵出口压力异常"]])
                    self.handle_signal_and_log([0, 5], [0, [0, "液压泵出口压力异常报警次数{}".format(len(result[1]))]])
                    for i in result[1]:
                        self.signal_hy_write_log.emit([5, [0, i]])
                    self.signal_hy_write_log.emit([5, [-1, "*" * 40]])

        del df
        # # 从原数据中删除 液压泵出口压力
        # del self.df[tickets[2]]
        del tickets
        gc.collect()

    # 7 液压叶轮锁定压力异常
    def hydraulic_rotor_lock_pressure(self):

        """
        ：液压叶轮锁定压力异常
        ：液压系统压力 > 150时，液压叶轮锁定压力1 和 液压叶轮锁定压力2 >120bar 或 <80bar，持续1min
        """

        try:
            # 获取 1 时间 3 液压系统压力 16	叶轮锁定压力1 17 叶轮锁定压力2 英文标签
            # print(self.tickets)
            tickets = [self.tickets[0], self.tickets[2], self.tickets[15], self.tickets[16]]
            # tickets = self.tickets

            df = self.df[['time', tickets[0], tickets[1], tickets[2], tickets[3]]]
            df.set_index(df['time'], inplace=True)
        except Exception as e:
            print(e)
            print("液压跳过函数7")
            self.handle_signal_and_log([-1, 6], [5, [-1, "液压叶轮锁定压力英文标签丢失"]])
            return

        if self.draw:
            print("液压绘图7")
            df1 = df.copy()
            df1.resample('30T').mean()
            df1['timestamp'] = df[tickets[0]].apply(lambda x: time.mktime(time.strptime(x, '%Y-%m-%d %H:%M:%S')))
            self.drawing(graphicsView=self.plt_list[6],
                         canvas_setting={"title": "液压叶轮锁定压力时间图"},
                         data=[
                             {"pen": "g", "name": "液压系统压力", "x": df1['timestamp'], "y": df1[tickets[1]]},
                             {"pen": "r", "name": "叶轮锁定压力1", "x": df1['timestamp'], "y": df1[tickets[2]]},
                             {"pen": "b", "name": "叶轮锁定压力2", "x": df1['timestamp'], "y": df1[tickets[3]]}
                         ])
            del df1
            gc.collect()

        # 删除 1 <= 150
        df = df.drop(df[(df[tickets[1]] <= 150)].index)
        if df.empty:
            self.handle_signal_and_log([1, 6], [5, [1, "液压叶轮锁定压力正常"]])

        else:
            # 删除 (2<=120 & 2>=80) | (3<=120 & 3>=80)
            df = df.drop(df[(((df[tickets[2]] <= 120) & (df[tickets[2]] >= 80)) | (
                    (df[tickets[3]] <= 120) & (df[tickets[3]] >= 80)))].index)
            if df.empty:
                self.handle_signal_and_log([1, 6], [5, [1, "液压叶轮锁定压力正常"]])
            else:
                # ------------------判断连续性
                result = tool.duration_calculation_to_csv(tickets,
                                                          df,
                                                          60,
                                                          str(self.import_file_path).split(r'/')[-1].split('.')[0] +
                                                          '/液压叶轮锁定压力异常.csv')
                if result[0]:
                    self.handle_signal_and_log([1, 6], [5, [1, "液压叶轮锁定压力正常"]])

                else:
                    self.handle_signal_and_log([0, 6], [5, [0, "液压叶轮锁定压力异常"]])
                    self.handle_signal_and_log([0, 6], [0, [0, "液压叶轮锁定压力异常报警次数{}".format(len(result[1]))]])
                    for i in result[1]:
                        self.signal_hy_write_log.emit([5, [0, i]])
                    self.signal_hy_write_log.emit([5, [-1, "*" * 40]])

        del df
        # # 从原数据中删除 液压叶轮锁定压力
        # del self.df[tickets[2]]
        del tickets
        gc.collect()

    # 8 叶轮锁定储能罐压力异常
    def hydraulic_rotor_lock_actived_accumlator_pressure(self):
        """
        叶轮锁定储能罐压力异常
        原理：
        1.液压系统压力>150时，叶轮锁定储能罐压力1和叶轮锁定储能罐压力2>120bar或<70bar，持续1min
        2.液压叶轮锁定压力1 < 50bar且≠0时，叶轮锁定储能罐压力1 < 70bar
        3.液压叶轮锁定压力2 < 50bar且≠0时，叶轮锁定储能罐压力2 < 70bar
        满足其一，报出叶轮锁定储能罐压力异常
        :return:
        """
        try:
            # 获取 1时间 3 液压系统压力 16 叶轮锁定压力1 17 叶轮锁定压力2 18 叶轮锁蓄能器压力1 19 叶轮锁蓄能器压力2 英文标签
            tickets = [self.tickets[0], self.tickets[2], self.tickets[15], self.tickets[16], self.tickets[17],
                       self.tickets[18]]
            df = self.df[['time', tickets[0], tickets[1], tickets[2], tickets[3], tickets[4], tickets[5]]]
            df.set_index(df['time'], inplace=True)
        except Exception as e:
            print(e)
            print("液压跳过函数8")
            self.handle_signal_and_log([-1, 7], [5, [-1, "叶轮锁定储能罐压力英文标签丢失"]])
            return

        if self.draw:
            print("液压绘图8")
            df1 = df.copy()
            df1.resample('30T').mean()
            df1['timestamp'] = df[tickets[0]].apply(lambda x: time.mktime(time.strptime(x, '%Y-%m-%d %H:%M:%S')))
            self.drawing(graphicsView=self.plt_list[7],
                         canvas_setting={"title": "叶轮锁定储能罐压力时间图"},
                         data=[
                             {"pen": "g", "name": "液压系统压力", "x": df1['timestamp'], "y": df1[tickets[1]]},
                             {"pen": "r", "name": "叶轮锁定压力1", "x": df1['timestamp'], "y": df1[tickets[2]]},
                             {"pen": "b", "name": "叶轮锁定压力2", "x": df1['timestamp'], "y": df1[tickets[3]]},
                             {"pen": "c", "name": "叶轮锁蓄能器压力1", "x": df1['timestamp'], "y": df1[tickets[4]]},
                             {"pen": "m", "name": "叶轮锁蓄能器压力2", "x": df1['timestamp'], "y": df1[tickets[5]]}
                         ])
            del df1
            gc.collect()

        # 情况1 1>150 & (4>120 | 4<70) & (5>120 | 5<70)
        df_h = df[((df[tickets[1]] > 150) & ((df[tickets[4]] > 120) | (df[tickets[4]] < 70)) & (
                (df[tickets[5]] > 120) | (df[tickets[5]] < 70)))].copy()
        # 情况2 2<50 & 2!=0 & 4<70
        df_l = df[((df[tickets[2]] < 50) & (df[tickets[2]] != 0) & (df[tickets[4]] < 70))].copy()
        # 情况3 3<50 & 3!=0 & 5<70
        df_e = df[((df[tickets[3]] < 50) & (df[tickets[3]] != 0) & (df[tickets[5]] < 70))].copy()
        # 判断是否未空
        if df_h.empty and df_l.empty and df_e.empty:
            self.handle_signal_and_log([1, 7], [5, [1, "叶轮锁定储能罐压力正常"]])
        else:
            # ------------------判断连续性
            # 最终报警次数
            total_alarm_number = 0
            if not df_h.empty:
                result = tool.duration_calculation_to_csv(tickets,
                                                          df_h,
                                                          60,
                                                          str(self.import_file_path).split(r'/')[-1].split('.')[0] +
                                                          '/叶轮锁定储能罐压力异常.csv')
                if result[0]:
                    self.handle_signal_and_log([1, 7], [5, [1, "叶轮锁定储能罐压力正常"]])
                else:
                    self.handle_signal_and_log([0, 7], [5, [0, "叶轮锁定储能罐压力异常"]])
                    for i in result[1]:
                        self.signal_hy_write_log.emit([5, [0, i]])
                    self.signal_hy_write_log.emit([5, [-1, "*" * 40]])
            if not df_l.empty:
                result = tool.duration_calculation_to_csv(tickets,
                                                          df_l,
                                                          1,
                                                          str(self.import_file_path).split(r'/')[-1].split('.')[0] +
                                                          '/叶轮锁定储能罐压力异常.csv')
                if result[0]:
                    self.handle_signal_and_log([1, 7], [5, [1, "叶轮锁定储能罐压力正常"]])
                else:
                    self.handle_signal_and_log([0, 7], [5, [0, "叶轮锁定储能罐压力异常"]])
                    total_alarm_number = len(result[1])
                    for i in result[1]:
                        self.signal_hy_write_log.emit([5, [0, i]])
                    self.signal_hy_write_log.emit([5, [-1, "*" * 40]])
            if not df_e.empty:
                result = tool.duration_calculation_to_csv(tickets,
                                                          df_e,
                                                          1,
                                                          str(self.import_file_path).split(r'/')[-1].split('.')[0] +
                                                          '/叶轮锁定储能罐压力异常.csv')
                if result[0]:
                    self.handle_signal_and_log([1, 7], [5, [1, "叶轮锁定储能罐压力正常"]])
                else:
                    self.handle_signal_and_log([0, 7], [5, [0, "叶轮锁定储能罐压力异常"]])
                    total_alarm_number += len(result[1])
                    self.handle_signal_and_log([0, 7], [0, [0, "叶轮锁定储能罐压力异常报警次数{}".format(total_alarm_number)]])
                    for i in result[1]:
                        self.signal_hy_write_log.emit([5, [0, i]])
                    self.signal_hy_write_log.emit([5, [-1, "*" * 40]])
        del df_h
        del df_l
        del df_e
        del df
        del tickets
        gc.collect()

    # 9 偏航压力异常
    def yaw_brake_pressure(self):
        """
        机组运行模式=14，机组不偏航时（偏航CW和偏航CCW都为0），
        液压偏航制动入口压力1、液压偏航制动出口压力1、
        液压偏航制动入口压力2、液压偏航制动出口压力2
        最小值< 150bar或最大值>175bar，持续20s
        :return:
        """
        try:
            # 获取 时间 0 机组运行模式 1 顺时针偏航 5 逆时针偏航 6  偏航制动出口压力1 7 偏航制动入口压力1 9
            # 偏航制动出口压力2 8 偏航制动入口压力2 10 英文标签
            # print(self.tickets)
            tickets = [self.tickets[0], self.tickets[1], self.tickets[5], self.tickets[6],
                       self.tickets[7], self.tickets[9], self.tickets[8], self.tickets[10]]
            # tickets = self.tickets

            df = self.df[['time', tickets[0], tickets[1], tickets[2], tickets[3],
                          tickets[4], tickets[5], tickets[6], tickets[7]]]
            df.set_index(df['time'], inplace=True)
        except Exception as e:
            print(e)
            print("液压跳过函数9")
            self.handle_signal_and_log([-1, 8], [5, [-1, " 偏航压力英文标签丢失"]])
            return

        if self.draw:
            print("液压绘图9")
            df1 = df.copy()
            df1.resample('30T').mean()
            df1['timestamp'] = df[tickets[0]].apply(lambda x: time.mktime(time.strptime(x, '%Y-%m-%d %H:%M:%S')))
            self.drawing(graphicsView=self.plt_list[8],
                         canvas_setting={"title": "偏航压力时间图"},
                         data=[
                             {"pen": "g", "name": "偏航制动出口压力1", "x": df1['timestamp'], "y": df1[tickets[4]]},
                             {"pen": "r", "name": "偏航制动入口压力1", "x": df1['timestamp'], "y": df1[tickets[5]]},
                             {"pen": "b", "name": "偏航制动出口压力2", "x": df1['timestamp'], "y": df1[tickets[6]]},
                             {"pen": "c", "name": "偏航制动入口压力2", "x": df1['timestamp'], "y": df1[tickets[7]]}
                         ])
            del df1
            gc.collect()

        # 删除 机组模式 != 14 或任意一个方向偏航
        df = df.drop(df[((df[tickets[1]] != 14) | ((df[tickets[2]] != 0) | (df[tickets[3]] != 0)))].index)
        if df.empty:
            self.handle_signal_and_log([1, 8], [5, [1, " 偏航压力正常"]])
        else:
            # 获取4个的最大最小值
            df['max'] = df.loc[:, [tickets[4], tickets[5], tickets[6], tickets[7]]].max(axis=1, skipna=True)
            df['min'] = df.loc[:, [tickets[4], tickets[5], tickets[6], tickets[7]]].min(axis=1, skipna=True)
            # 删除 最小值 >= 150bar 且 最大值 <= 175bar，持续20s
            # 最小值 < 150bar或最大值 > 175bar，持续20s
            df = df.drop(df[((df['min'] >= 150) & (df['max'] <= 175))].index)
            if df.empty:
                self.handle_signal_and_log([1, 8], [5, [1, "偏航压力正常"]])
            else:
                # ------------------判断连续性 20s
                result = tool.duration_calculation_to_csv(tickets,
                                                          df,
                                                          20,
                                                          str(self.import_file_path).split(r'/')[-1].split('.')[0] +
                                                          '/偏航压力正常异常.csv')
                if result[0]:
                    self.handle_signal_and_log([1, 8], [5, [1, "偏航压力正常正常"]])

                else:
                    self.handle_signal_and_log([0, 8], [5, [0, "偏航压力正常异常"]])
                    self.handle_signal_and_log([0, 8], [0, [0, "偏航压力正常异常报警次数{}".format(len(result[1]))]])
                    for i in result[1]:
                        self.signal_hy_write_log.emit([5, [0, i]])
                    self.signal_hy_write_log.emit([5, [-1, "*" * 40]])

        del df
        # # 从原数据中删除 偏航制动器1
        # del self.df[tickets[2]]
        del tickets
        gc.collect()

    # 10 偏航制动器1异常
    def hydraulic_yaw_brake1(self):

        """
        ：偏航制动器1异常
        ：机组运行模式 = 14，液压偏航制动入口压力1 > 150时，液压偏航制动入口压力1 - 液压偏航制动出口压力1 > 2bar，持续 10 s
        """

        try:
            # 获取 1 时间 2 机组运行模式 10 偏航制动入口压力1 8 偏航制动出口压力1  英文标签
            # print(self.tickets)
            tickets = [self.tickets[0], self.tickets[1], self.tickets[9], self.tickets[7]]
            # tickets = self.tickets

            df = self.df[['time', tickets[0], tickets[1], tickets[2], tickets[3]]]
            df.set_index(df['time'], inplace=True)
        except Exception as e:
            print(e)
            print("液压跳过函数10")
            self.handle_signal_and_log([-1, 9], [5, [-1, "偏航制动器1英文标签丢失"]])
            return

        if self.draw:
            print("液压绘图10")
            df1 = df.copy()
            df1.resample('30T').mean()
            df1['timestamp'] = df[tickets[0]].apply(lambda x: time.mktime(time.strptime(x, '%Y-%m-%d %H:%M:%S')))
            self.drawing(graphicsView=self.plt_list[9],
                         canvas_setting={"title": "偏航制动器1时间图"},
                         data=[
                             {"pen": "g", "name": "偏航制动入口压力1", "x": df1['timestamp'], "y": df1[tickets[2]]},
                             {"pen": "r", "name": "偏航制动出口压力1", "x": df1['timestamp'], "y": df1[tickets[3]]}
                         ])
            del df1
            gc.collect()

        # 删除 1 != 14 & 2 <= 150
        df = df.drop(df[((df[tickets[1]] != 14) & (df[tickets[2]] <= 150))].index)
        if df.empty:
            self.handle_signal_and_log([1, 9], [5, [1, "偏航制动器1正常"]])

        else:
            # 删除 2 - 3 <= 2
            df = df.drop(df[(df[tickets[2]] - df[tickets[3]] <= 2)].index)
            if df.empty:
                self.handle_signal_and_log([1, 9], [5, [1, "偏航制动器1正常"]])
            else:
                # ------------------判断连续性
                result = tool.duration_calculation_to_csv(tickets,
                                                          df,
                                                          10,
                                                          str(self.import_file_path).split(r'/')[-1].split('.')[0] +
                                                          '/偏航制动器1异常.csv')
                if result[0]:
                    self.handle_signal_and_log([1, 9], [5, [1, "偏航制动器1正常"]])

                else:
                    self.handle_signal_and_log([0, 9], [5, [0, "偏航制动器1异常"]])
                    self.handle_signal_and_log([0, 9], [0, [0, "偏航制动器1异常报警次数{}".format(len(result[1]))]])
                    for i in result[1]:
                        self.signal_hy_write_log.emit([5, [0, i]])
                    self.signal_hy_write_log.emit([5, [-1, "*" * 40]])

        del df
        # # 从原数据中删除 偏航制动器1
        # del self.df[tickets[2]]
        del tickets
        gc.collect()

    # 11 偏航制动器2异常
    def hydraulic_yaw_brake2(self):

        """
        ：偏航制动器2异常
        ：机组运行模式 = 14，液压偏航制动入口压力1 > 150时，液压偏航制动入口压力1 - 液压偏航制动出口压力1 > 2bar，持续 10 s
        """

        try:
            # 获取 1 时间 2 机组运行模式 11 偏航制动入口压力2 9 偏航制动出口压力2 英文标签
            # print(self.tickets)
            tickets = [self.tickets[0], self.tickets[1], self.tickets[10], self.tickets[8]]
            # tickets = self.tickets

            df = self.df[['time', tickets[0], tickets[1], tickets[2], tickets[3]]]
            df.set_index(df['time'], inplace=True)
        except Exception as e:
            print(e)
            print("液压跳过函数11")
            self.handle_signal_and_log([-1, 10], [5, [-1, "偏航制动器2英文标签丢失"]])
            return

        if self.draw:
            print("液压绘图11")
            df1 = df.copy()
            df1.resample('30T').mean()
            df1['timestamp'] = df[tickets[0]].apply(lambda x: time.mktime(time.strptime(x, '%Y-%m-%d %H:%M:%S')))
            self.drawing(graphicsView=self.plt_list[10],
                         canvas_setting={"title": "偏航制动器2时间图"},
                         data=[
                             {"pen": "g", "name": "偏航制动入口压力2", "x": df1['timestamp'], "y": df1[tickets[2]]},
                             {"pen": "r", "name": "偏航制动出口压力2", "x": df1['timestamp'], "y": df1[tickets[3]]}
                         ])
            del df1
            gc.collect()

        # 删除 1 != 14 & 2 <= 150
        df = df.drop(df[((df[tickets[1]] != 14) & (df[tickets[2]] <= 150))].index)
        if df.empty:
            self.handle_signal_and_log([1, 10], [5, [1, "偏航制动器2正常"]])

        else:
            # 删除 2 - 3 <= 2
            df = df.drop(df[(df[tickets[2]] - df[tickets[3]] <= 2)].index)
            if df.empty:
                self.handle_signal_and_log([1, 10], [5, [1, "偏航制动器2正常"]])
            else:
                # ------------------判断连续性
                result = tool.duration_calculation_to_csv(tickets,
                                                          df,
                                                          10,
                                                          str(self.import_file_path).split(r'/')[-1].split('.')[0] +
                                                          '/偏航制动器2异常.csv')
                if result[0]:
                    self.handle_signal_and_log([1, 10], [5, [1, "偏航制动器2正常"]])

                else:
                    self.handle_signal_and_log([0, 10], [5, [0, "偏航制动器2异常"]])
                    self.handle_signal_and_log([0, 10], [0, [0, "偏航制动器2异常报警次数{}".format(len(result[1]))]])
                    for i in result[1]:
                        self.signal_hy_write_log.emit([5, [0, i]])
                    self.signal_hy_write_log.emit([5, [-1, "*" * 40]])

        del df
        # # 从原数据中删除 偏航制动器2
        # del self.df[tickets[2]]
        del tickets
        gc.collect()

    def over(self):
        # 第一个线程结束
        self.signal_hy_over.emit([5, 1])



