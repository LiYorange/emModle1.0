# -------------------------------------------------------------------------------
# Name:         read
# Description:
# Author:       A07567
# Date:         2020/12/9
# Description:  
# -------------------------------------------------------------------------------
from DAL import import_data
from DAL import base_setting
from BLL import tool
# 自定义模块区结束
import time
from PyQt5.QtCore import QThread, pyqtSignal, QObject
import gc
import copy
import numpy as np
import pandas as pd

# 模式1 小文件绘图
class GearBox1(QObject):
    """
    齿轮箱预警模型
    """

    # 类变量

    def __init__(self, tickets_file_path=None, import_data_path=None, project_index=None,
                 plt_list=None,
                 draw=False):
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
        # ------------------------------------------->>>实例变量初始化
        if tickets_file_path is not None:
            self.tickets_file_path = tickets_file_path
        if import_data_path is not None:
            self.import_file_path = import_data_path
        if project_index is not None:
            self.project_index = project_index
        if plt_list is not None:
            self.plt_list = plt_list

    def run(self):
        self.get_df()

    def get_df(self):
        """
        通过调用 base_setting.AutoSelectTickets得到英文标签
        通过调用import_data.ImportData得到df
        :return:
        """
        # 中文标签
        print("开始")
        tickets_list = [
            # 齿轮箱 1
            "时间",
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
            # 发电机 2
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
            "发电机空空冷外循环出口温度2",
            # 变流器 3
            "时间",
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
            "变频器从机冷却液压力",
            # 变桨 4
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
            "变桨后备电源柜温度3",
            # 液压 5
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
            "叶轮锁蓄能器压力2",
            # 传感器 6
            "时间",
            "机组运行模式",
            "箱式变压器温度",
            "塔筒第一层平台温度",
            "塔基柜温度",
            "机舱高压柜温度",
            "机舱温度",
            "机舱低压柜温度",
            "变频器温度1",
            "变频器温度2",
            "变频器温度3",
            "变频器温度4",
            "变频器温度5",
            "变频器温度6",
            "变频器温度7",
            "变频器温度8",
            "变频器温度9",
            "变频器温度10",
            "变频器温度11",
            "变频器温度12",
            "变频器温度13",
            "变频器温度14",
            "变频器温度15",
            "变频器温度16",
            "变频器温度17"
        ]
        auto_select_tickets = base_setting.AutoSelectTickets(self.tickets_file_path)
        # 得到英文标签，可能存在缺失情况！
        self.tickets = auto_select_tickets.select_tickets_by_project(self.project_index, tickets_list)

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
        print(self.df.info())
        print("结束")


if __name__ == '__main__':
    one = GearBox1('../config/tickets.json', '60004036_20200930（外罗）.csv', 0, None, False)
    one.run()
