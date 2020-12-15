# ----------------------------------- 处理丢失的csv
# import pandas as pd
# import numpy as np
# import io
#
# df = pd.DataFrame
# li = ["时间", "时间1", "时间2", "时间3", "时间4"]
#
# df_head = pd.read_csv("test.csv", encoding='gbk', nrows=0)
# index = df_head.columns
#
#
# def f(a):
#     return list(index.isin([a]))
#
#
# miss_list = []
# read_list = []
# result = list(map(f, li))
# for i in range(len(result)):
#     if not any(result[i]):
#         # df_head.insert(i, li[i], np.nan)
#         # 创建一个列表用于存放找不到的列的位置
#         miss_list.append(i)
#     else:
#         read_list.append(li[i])
# # print(read_list)
# df = pd.read_csv("test.csv", usecols=read_list, encoding='gbk')
# for loc in miss_list:
#     df.insert(loc, li[loc], np.nan)
# print(df)

# -------------------------------------解压
#
# from PyQt5.QtWidgets import QApplication, QWidget
# from PyQt5 import uic
# from ctypes import *
# import sys
#
#
# # 绘图
#
#
# class UI(QWidget):
#     def __init__(self):
#         super(UI, self).__init__()
#         self.window = uic.loadUi("UI/cmd.ui")
#
#     # 重写绘图函数
#     def paintEvent(self, event):
#         pass
#
#
# if __name__ == '__main__':
#     import os
#
#     FindWindow = windll.user32.FindWindowW
#     SetParent = windll.user32.SetParent
#     SetWindowPos = windll.user32.SetWindowPos
#     os.system("cmd/c start")
#     notepad_handle = FindWindow(0, "C:\Windows\system32\cmd.exe")
#     print(notepad_handle)
#     app = QApplication([])
#     win = UI()
#     win.window.show()
#     SetParent(notepad_handle, int(win.winId()))
#
#     # SetWindowPos(notepad_handle, 0, 100, 100, 100, 100, 0)
#     app.exec_()
# import pandas as pd
#
# df = pd.DataFrame([[1, 2, 3], [4, 5, 6]], columns=['a', 'b', 'c'])
# print(df.index)
# import time

# print(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())) + ":变频器模块进程开始运行")
# print(time.strftime('%Y{y}%m{m}%d{d} %H{h}%M{f}%S{s}').format(y='年', m='月', d='日', h='时', f='分', s='秒') + ":变频器模块进程开始运行")


# import pandas as pd
#
# df = pd.DataFrame({'col1': [1, 2, 3],
#                    'col2': [3, 2, 1],
#                    'col3': [1, 1, 1]},
#                   index=['row1', 'row2', 'row3'])
# print(df)
# print('*' * 40)
# # print(df.loc[:,['col1','col2','col3']].max())
# df.insert(len(df.columns), 'max1', df.loc[:, ['col1', 'col2', 'col3']].max(axis=1))
# df['max2'] = df.loc[:, ['col1', 'col2', 'col3']].max(axis=1)
# df['max3']=pd.Series(df.loc[:, ['col1', 'col2', 'col3']].max(axis=1), index=df.index)
# df['max'] = df[['col1', 'col2', 'col3']].max(axis=1)
# # df['max'] = df['col1']
# print(df)


# importing pandas as pd
# import pandas as pd

# Creating the dataframe
# df = pd.DataFrame({"A": [1, 2, 3, 4, 5],
#                    "B": [3, 5, 4, 3, 2],
#                    "C": [8, 1, 1, 4, 7],
#                    "D": [4, 6, 1, 2, 6]})
# print(df)
# # skip the Na values while finding the maximum
# print('*' * 40)
# # df['max'] = df.max(axis=1, skipna=True)
# df['max'] = df.loc[:, ['A', 'B']].max(axis=1, skipna=True)
# df = df.drop(df[df['max'] < 4].index)
# print(df)
# li = df['max'].tolist()
# print(li)

# import pandas as pd
#
# df = pd.DataFrame({"col1": [1, 2, 3, 4, 5],
#                    "col2": [3, 5, 4, 3, 2],
#                    "col3": [8, 1, 1, 4, 7],
#                    "col4": [4, 6, 1, 2, 6]},
#                   index=['A', 'B', 'C', 'D', 'E'])
# # print(df)
# li = [['A', 'B'], ['C']]
# li = sum(li, [])
# print(li)
# print(df.loc[li, :])

# l1 = ['A', 'B']
# l2 = ['A', 'C', 'D']
# li = l1 + l2
# print(li)
# dic = {1:1}
# x = bool(dic)
# print(x)
import pyqtgraph as pg


class Test:
    def __init__(self, plot_list):
        self.plot_list = plot_list

    def plot(self):
        self.plot_list[0].addPlot(axisItems={'bottom': pg.DateAxisItem(orientation='bottom')})


import sys
from PyQt5.QtWidgets import QApplication, QWidget, QToolTip, QPushButton, QMessageBox, QDesktopWidget
from PyQt5.QtGui import QIcon, QFont
from PyQt5.QtCore import QCoreApplication


# demo_5:重新关闭按钮x关闭事件，给个提示框提示
class Exception(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('添加关闭按钮')
        self.setFont(QFont('微软雅黑', 20))
        self.resize(400, 300)
        self.setWindowIcon(QIcon('1.png'))

        # 居中窗口
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

        self.show()

    def closeEvent(self, QCloseEvent):
        res = QMessageBox.question(self, '消息', '是否关闭这个窗口？', QMessageBox.Yes | QMessageBox.No,
                                   QMessageBox.No)  # 两个按钮是否， 默认No则关闭这个提示框
        if res == QMessageBox.Yes:
            QCloseEvent.accept()
        else:
            QCloseEvent.ignore()


if __name__ == '__main__':
    pp = QApplication(sys.argv)
    example = Exception()
    # example.show()
    sys.exit(pp.exec())
