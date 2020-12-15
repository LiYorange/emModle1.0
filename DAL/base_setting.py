

# -------------------------------------------------------------------------------
# Name:         reset_tickets_to_ZH
# Description:
# Author:       A07567
# Date:         2020/11/8
# -------------------------------------------------------------------------------
import json


class AutoSelectTickets:

    def __init__(self, tickets_data_file=None):
        # -------------载入基本数据开始
        self.tickets_data = {}  # 所有的标签数据
        self.tickets_data_project_name = []  # 项目名称
        # -------------载入基本数据结束
        if tickets_data_file:
            self.tickets_data_file = tickets_data_file
            self.load_tickets_data()

    def load_tickets_data(self):
        with open(self.tickets_data_file, 'r', encoding='utf8') as f:
            self.tickets_data = json.load(f)
        f.close()
        self.tickets_data_project_name = list(self.tickets_data.keys())
        # print(self.tickets_data_project_name)

    def select_tickets_by_project(self, i, args):
        """
        :param i: 用于定位list()——self.tickets_data_project_name的index
        :param args: 用于选择需要用到的标签数组
        :return: 返回tickets_list()，用于import_data调用
        """

        """
        传入一个*args list(),对该list进行遍历，赋值该list对应的英文标签给return_list，如果没有找到对应的英文标签则填入false,返回给调用函数
        self.tickets_data[self.tickets_data_project_name[i]]为list
        对该list进行遍历得到多个字典
        判断给定的tickets是否在字典的键中，如果在则返回该键对应的值，否则返回标签点丢失
        """
        return_list = []
        for tickets in args:
            find = False
            # 对项目的子标签进行遍历，判断tickets是否在项目的子标签中
            for j in range(len(self.tickets_data[self.tickets_data_project_name[i]])):
                # 如果在子标签中查找到则添加
                if tickets in self.tickets_data[self.tickets_data_project_name[i]][j].keys():
                    return_list.append(self.tickets_data[self.tickets_data_project_name[i]][j][tickets])
                    find = True
            # 如果遍历完成还没找到则添加false
            if not find:
                return_list.append(False)
        return return_list


if __name__ == '__main__':
    a = AutoSelectTickets("tickets.json")
    a.load_tickets_data()
    x = a.select_tickets_by_project(0, ["时间", "机组运行模式", "齿轮箱主轴承温", "齿轮箱轮毂侧轴承温度"])
    print(x)
