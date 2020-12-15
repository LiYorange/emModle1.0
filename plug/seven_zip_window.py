# -------------------------------------------------------------------------------
# Name:         7z_window
# Description:
# Author:       A07567
# Date:         2020/12/1
# Description:  
# -------------------------------------------------------------------------------
from PyQt5.QtWidgets import QApplication, QWidget, QFileDialog, QMessageBox
from PyQt5 import uic
from PyQt5.QtCore import QThread, QObject, pyqtSignal
import os
import time
import json
import gc
import logging
import pandas as pd
# 自定义包区
from plug import seven_zip
from config.icon import ico


class UI(QThread):
    signal_write_log = pyqtSignal(str)

    def __init__(self):
        """
            1. UI
            2. 初始化数据
                2.1 解压区
                2.2 合并区
            3. 绑定事件
        """
        # 1 初始化UI
        super(UI, self).__init__()

        self.window = uic.loadUi("UI/7z.ui")
        self.window.setFixedSize(self.window.width(), self.window.height())
        # 2 初始化变量
        # # 2.1 >>> 解压区
        self.seven_zip = None
        self.unpack_merge_files = None
        # # 2.2 >>> 合并区
        self.merge_object = Merge()
        self.csv_files = None
        self.project_name = None
        # # # 定义一个用于对比选择合并数据后得到的项目名称与json文件内的项目的变量
        self.compare_value = None
        # 3 绑定事件
        # # 选择解压文件
        # self.window.file_path_pushButton.clicked.connect(self.select_unpack_file)
        # # 解压并合并
        # self.window.unpack_pushButton.clicked.connect(self.unpack)
        # 选择解压并合并文件
        self.window.select_files_pushButton.clicked.connect(self.select_unpack_merge_files)
        # 解压并合并
        self.window.unpack_merge_pushButton.clicked.connect(self.unpack_merge)
        # 写日志
        self.signal_write_log.connect(self.write_log)

    # 选择解压并合并文件
    def select_unpack_merge_files(self):
        """
        根据文件前5位数字判断项目，根据不同的项目选择不同的数据标签点进行合并
        60004：外罗
        60005:南鹏岛
        60006：沙扒
        :return:
        """
        # 设置解压并合并按钮不可见，防止二次操作时选择不同项目数据合并时此按钮为可见状态

        Dialog = QFileDialog()
        file_names, filetype = Dialog.getOpenFileNames(self.window,
                                                       "选取文件",
                                                       # 获得当前路径
                                                       os.getcwd(),  # 起始路径
                                                       "zip文件 (*.zip);;"
                                                       "gz文件 (*.gz);;"
                                                       "rar文件 (*.rar);;"
                                                       "7z文件(*.7z);;"
                                                       "tar文件 (*.gz);;"
                                                       "所有文件 (*)")  # 设置文件扩展名过滤,用双分号间隔
        if not file_names:
            QMessageBox.warning(self.window, "警告", "请选择文件！")
        else:

            flag = []
            for file in file_names:
                """
                创建一个list 存放切分的文件名前5位数，判断是否为同一个项目
                """
                try:
                    # 判断文件命名是否规范
                    # flag.append(str(os.path.basename(file)).split(".")[-2].split("_")[0][:5])
                    flag.append(str(os.path.basename(file)).split("\\")[-1].split("_")[0][:5])
                except Exception as e:
                    QMessageBox.warning(self.window, "警告", "文件名称包含非法字符！")
                    print(e)
                    return
            # 判断是否为同一个项目，如果不同则提示，如果同则显示合并按钮
            one = len(set(flag))
            # print(flag)
            if one != 1:
                QMessageBox.warning(self.window, "警告", "请选择同一项目的数据!")
                return
            else:
                # 取第0项
                self.window.unpack_merge_pushButton.setEnabled(True)
                self.compare_value = flag[0]
                self.unpack_merge_files = file_names
                self.window.file_path_line.setText(str(file_names))

    def unpack_merge(self):
        self.window.plainTextEdit.clear()
        self.signal_write_log.emit("正在解压数据，这将耗费大量的时间，请稍等！")
        QApplication.processEvents()
        time.sleep(1)
        self.seven_zip = seven_zip.SevenZip(self.unpack_merge_files)
        result = self.seven_zip.unpack()
        if all(result) == 0:
            self.signal_write_log.emit("解压成功！")
            self.signal_write_log.emit("正在合并数据，这将耗费大量的时间，请稍等！")
            self.merge_object = Merge(self.compare_value)
            self.merge_object.signal_log.connect(self.write_log)
            self.merge_object.start()
            self.window.unpack_merge_pushButton.setEnabled(False)
        else:
            self.signal_write_log.emit("解压失败，原文件可能损坏或尝试用其他解压软件解压")



    def write_log(self, text):
        self.window.plainTextEdit.appendPlainText(text)


class Merge(QThread):
    """
    传入一个选择的文件对应的项目对比值，如果在json文件中找到该对比值，则载入英文标签，合并数据
    """
    signal_log = pyqtSignal(str)

    def __init__(self, compare_value=None):
        """

        :param csv_files: csv 文件
        :param compare_value: 对比值
        """
        super(Merge, self).__init__()
        # path = os.path.abspath(os.path.dirname(os.getcwd())) + '\\data'
        # self.csv_files = os.listdir(path)
        path = os.path.abspath(os.getcwd()) + '\\data'
        self.csv_files = os.listdir(path)
        for i in range(len(self.csv_files)):
            self.csv_files[i] = os.path.join(path, self.csv_files[i])

        if compare_value is not None:
            self.compare_value = compare_value

        self.tickets_data = None
        self.en_tickets = None
        self.project_name = None
        self.turbld = []  # 机组编号
        self.date = []  # 每台机组的起止时间
        self.dates = {}  # 字典:机组对应的起止时间

    def run(self):
        self.merge()

    def merge(self):
        """
        读取json 得到引文标签
        创建新的csv 将需要处理的csv通过pandas 写入新的csv中
        :return:
        """
        # >>> 移除csv
        # try:
        #     os.remove(os.getcwd() + "/data/合并后的数据.csv")
        # except:
        #     pass

        # 获取英文标签
        self.en_tickets = self.load_en_tickets()
        T = []
        temp = []
        for i in range(len(self.csv_files)):
            temp.append(self.csv_files[i].split('\\')[-1])
        for file in temp:
            t = os.path.splitext(file)[0]  # 将文件名和后缀分开，生成t
            T.append(t)
        for i in T:
            self.turbld.append(i.split('_')[0])  # 将机组编号和日期分开，生成turbld和date
        self.turbld = set(self.turbld)
        for j in self.turbld:
            for m in T:
                if m[0:8] == j:
                    self.date = self.date + [m[9:]]
            self.dates[j] = self.date
            self.date = []
        for k in self.turbld:
            datelist = []
            newName = self.dates[k][0] + '-' + self.dates[k][-1]
            newName = k + '_' + newName + '.csv'  # 合并后的文件名
            newName = os.path.join(r'./data', newName)

            for f in temp:
                if f.split('_')[0] == k:
                    datelist.append(self.csv_files[temp.index(f)])
            try:
                # 读取第一个CSV文件并包含表头
                df = self.handle_csv(datelist[0], self.en_tickets)
                self.signal_log.emit("正在写入csv....")
                # 将读取的第一个CSV文件写入合并后的文件保存
                df.to_csv(newName, mode='a', index=False, sep=',', encoding='gbk')
                os.remove(f'{datelist[0]}')
                # 循环遍历列表中各个CSV文件名，并追加到合并后的文件
                for i in range(1, len(datelist)):
                    df = self.handle_csv(datelist[i], self.en_tickets)
                    df.to_csv(newName, mode='a', header=False, index=False, sep=',', encoding='gbk')
                    os.remove(f'{datelist[i]}')
                self.signal_log.emit("{}已合并".format(newName))
            except Exception as e:
                print(e)
                self.signal_log.emit("合并失败，请勿用其他软件打开需要合并的数据或再次合并")
        self.signal_log.emit("已完成所有合并！")
    def load_en_tickets(self):
        """
        1. 根据得到的self.compare_value与json的项目对比，得到对应的英文标签
        :return:
        """
        # with open(os.path.dirname(os.getcwd()) + "/config/FilterCondition.json", 'r', encoding='utf8') as f:
        with open(os.getcwd() + "/config/FilterCondition.json", 'r', encoding='utf8') as f:
            self.tickets_data = json.load(f)
        f.close()
        self.project_name = list(self.tickets_data.keys())

        # 如果在json的项目中则输出此时的项目序号位置，提取英文标签
        if self.compare_value in self.project_name:
            index = self.project_name.index(self.compare_value)
            # 得到英文标签
            return self.tickets_data[self.project_name[index]]

    def handle_csv(self, file, usecols):
        """
        合并CSV
        合并之前先判断是否存在csv数据缺失现象，如果缺失则补充numpa.nan数值
        :param usecols:
        :return:
        """
        df = pd.DataFrame()
        df_head = pd.DataFrame()
        df_head = pd.read_csv(file, encoding='gbk', engine='python', nrows=0)

        def judge_miss(li):
            return list(df_head.columns.isin([li]))

        # miss_data_list = []
        # exist_data_list = []
        # 得到一个列表，如果列表包含true 则未丢失数据，如果全为false则丢失
        # result = list(map(judge_miss, usecols))
        # for i in range(len(result)):
        #     if not any(result[i]):
        #         # 如果不全为false,则缺失数据，记录此时英文标签的位置
        #         miss_data_list.append(i)
        #     else:
        #         exist_data_list.append(usecols[i])
        # 开始读取data
        data = pd.read_csv(file, usecols=self.en_tickets, chunksize=10000, encoding='gbk',
                           engine='python')
        time1 = time.time()
        # 将data 整合为df
        df = pd.concat(data, ignore_index=True)
        time2 = time.time()
        self.signal_log.emit("导入数据花费时间:{}".format(time2 - time1))
        # ******************************
        # 清空
        # del miss_data_list[:]
        # del exist_data_list[:]
        # ******************************
        return df
