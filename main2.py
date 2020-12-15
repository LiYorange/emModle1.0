from PyQt5.QtWidgets import QApplication, QFileDialog, QMessageBox, QVBoxLayout, QGroupBox, QLabel, QPlainTextEdit
# 导入右击事件
from PyQt5.QtCore import pyqtSignal, QObject, QTimer, QVariant
# 导入颜色
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from PyQt5 import uic
import os, time, sys
# 显示占用内存
import psutil
import gc
# sip 用于彻底删除控件回收内存 C++编写
import sip
import pyqtgraph as pg
# ————————————————————————————————————自定义模块区开始
from DAL import base_setting


# from BLL import grGearBox
# from BLL import grGenerator
# from BLL import grConverter
#
# import globalvar as gl
# from BLL import tool


# ————————————————————————————————————自定义模块区结束


class Ui(QObject):
    signal_draw_model = pyqtSignal(bool)
    signal_reset_draw_base_data = pyqtSignal(bool)

    def __init__(self):
        super(Ui, self).__init__()
        # 1 ----------------------------------------载入UI
        self.window = uic.loadUi("UI/main.ui")
        self.gb_plt_list = [None] * 36
        self.gb_layout = [None] * 36
        self.gb_vLine = [None] * 36
        self.gb_hLine = [None] * 36
        self.gb_vb = [None] * 36

        self.ge_plt_list = [None] * 14
        self.ge_layout = [None] * 14
        self.ge_vLine = [None] * 14
        self.ge_hLine = [None] * 14
        self.ge_vb = [None] * 14

        self.pitch_plt_list = [None] * 9
        self.pitch_layout = [None] * 9
        self.pitch_vLine = [None] * 9
        self.pitch_hLine = [None] * 9
        self.pitch_vb = [None] * 9

        self.co_plt_list = [None] * 8
        self.co_layout = [None] * 8
        self.co_vLine = [None] * 8
        self.co_hLine = [None] * 8
        self.co_vb = [None] * 8
        # self.generator = grGenerator.Generator()

        # # 4.5 hydraulic 区
        # # # 4.5.1 hydraulic绘图区
        self.hy_plt_list = [None] * 12
        self.hy_layout = [None] * 12
        self.hy_vLine = [None] * 12
        self.hy_hLine = [None] * 12
        self.hy_vb = [None] * 12
        # self.generator = grGenerator.Generator()

        # # 4.6 sensor 区
        # # # 4.6.1 sensor绘图区
        self.se_plt_list = [None] * 9
        self.se_layout = [None] * 9
        self.se_vLine = [None] * 9
        self.se_hLine = [None] * 9
        self.se_vb = [None] * 9
        self.load_plot()

    def load_plot(self):
        # gearbox
        for i in range(1, 36):
            date_axis = pg.DateAxisItem(orientation='bottom')
            self.gb_plt_list[i] = pg.PlotWidget(axisItems={'bottom': date_axis})
            self.gb_layout[i] = QVBoxLayout(self.window.findChild(QGroupBox, "gb%d_groupBox" % i))
            self.gb_layout[i].addWidget(self.gb_plt_list[i])
            self.gb_vLine[i] = pg.InfiniteLine(angle=90, movable=False, )  # 创建一个垂直线条
            self.gb_hLine[i] = pg.InfiniteLine(angle=0, movable=False, )  # 创建一个水平线条
            self.gb_plt_list[i].addItem(self.gb_vLine[i], ignoreBounds=True)  # 在图形部件中添加垂直线条
            self.gb_plt_list[i].addItem(self.gb_hLine[i], ignoreBounds=True)  # 在图形部件中添加水平线条
            self.gb_vb[i] = self.gb_plt_list[i].plotItem.vb  # 得到鼠标位置

            self.gb_plt_list[i].scene().sigMouseMoved.connect(self.mouse_moved)
            del date_axis
            self.window.statusBar.showMessage("齿轮箱绘图加载完成")
        # generator
        for i in range(1, 14):
            date_axis = pg.DateAxisItem(orientation='bottom')
            self.ge_plt_list[i] = pg.PlotWidget(axisItems={'bottom': date_axis})
            self.ge_layout[i] = QVBoxLayout(self.window.findChild(QGroupBox, "ge%d_groupBox" % i))
            self.ge_layout[i].addWidget(self.ge_plt_list[i])
            self.ge_vLine[i] = pg.InfiniteLine(angle=90, movable=False, )  # 创建一个垂直线条
            self.ge_hLine[i] = pg.InfiniteLine(angle=0, movable=False, )  # 创建一个水平线条
            self.ge_plt_list[i].addItem(self.ge_vLine[i], ignoreBounds=True)  # 在图形部件中添加垂直线条
            self.ge_plt_list[i].addItem(self.ge_hLine[i], ignoreBounds=True)  # 在图形部件中添加水平线条
            self.ge_vb[i] = self.ge_plt_list[i].plotItem.vb  # 得到鼠标位置
            self.ge_plt_list[i].scene().sigMouseMoved.connect(self.mouse_moved)
            self.window.statusBar.showMessage("发电机绘图加载完成")
        # pitch
        for i in range(1, 9):
            date_axis = pg.DateAxisItem(orientation='bottom')
            self.pitch_plt_list[i] = pg.PlotWidget(axisItems={'bottom': date_axis})
            self.pitch_layout[i] = QVBoxLayout(self.window.findChild(QGroupBox, "pitch%d_groupBox" % i))
            self.pitch_layout[i].addWidget(self.pitch_plt_list[i])
            self.pitch_vLine[i] = pg.InfiniteLine(angle=90, movable=False, )  # 创建一个垂直线条
            self.pitch_hLine[i] = pg.InfiniteLine(angle=0, movable=False, )  # 创建一个水平线条
            self.pitch_plt_list[i].addItem(self.pitch_vLine[i], ignoreBounds=True)  # 在图形部件中添加垂直线条
            self.pitch_plt_list[i].addItem(self.pitch_hLine[i], ignoreBounds=True)  # 在图形部件中添加水平线条
            self.pitch_vb[i] = self.pitch_plt_list[i].plotItem.vb  # 得到鼠标位置
            self.pitch_plt_list[i].scene().sigMouseMoved.connect(self.mouse_moved)
            self.window.statusBar.showMessage("变桨绘图加载完成")
            # pitch
        # converter
        for i in range(1, 8):
            date_axis = pg.DateAxisItem(orientation='bottom')
            self.co_plt_list[i] = pg.PlotWidget(axisItems={'bottom': date_axis})
            self.co_layout[i] = QVBoxLayout(self.window.findChild(QGroupBox, "co%d_groupBox" % i))
            self.co_layout[i].addWidget(self.co_plt_list[i])
            self.co_vLine[i] = pg.InfiniteLine(angle=90, movable=False, )  # 创建一个垂直线条
            self.co_hLine[i] = pg.InfiniteLine(angle=0, movable=False, )  # 创建一个水平线条
            self.co_plt_list[i].addItem(self.co_vLine[i], ignoreBounds=True)  # 在图形部件中添加垂直线条
            self.co_plt_list[i].addItem(self.co_hLine[i], ignoreBounds=True)  # 在图形部件中添加水平线条
            self.co_vb[i] = self.co_plt_list[i].plotItem.vb  # 得到鼠标位置
            self.co_plt_list[i].scene().sigMouseMoved.connect(self.mouse_moved)
            self.window.statusBar.showMessage("变流器绘图加载完成")
        # hydraulic
        for i in range(1, 12):
            date_axis = pg.DateAxisItem(orientation='bottom')
            self.hy_plt_list[i] = pg.PlotWidget(axisItems={'bottom': date_axis})
            self.hy_layout[i] = QVBoxLayout(self.window.findChild(QGroupBox, "hy%d_groupBox" % i))
            self.hy_layout[i].addWidget(self.hy_plt_list[i])
            self.hy_vLine[i] = pg.InfiniteLine(angle=90, movable=False, )  # 创建一个垂直线条
            self.hy_hLine[i] = pg.InfiniteLine(angle=0, movable=False, )  # 创建一个水平线条
            self.hy_plt_list[i].addItem(self.hy_vLine[i], ignoreBounds=True)  # 在图形部件中添加垂直线条
            self.hy_plt_list[i].addItem(self.hy_hLine[i], ignoreBounds=True)  # 在图形部件中添加水平线条
            self.hy_vb[i] = self.hy_plt_list[i].plotItem.vb  # 得到鼠标位置
            self.hy_plt_list[i].scene().sigMouseMoved.connect(self.mouse_moved)
            self.window.statusBar.showMessage("液压系统绘图加载完成")
        # sensor
        for i in range(1, 9):
            date_axis = pg.DateAxisItem(orientation='bottom')
            self.se_plt_list[i] = pg.PlotWidget(axisItems={'bottom': date_axis})
            self.se_layout[i] = QVBoxLayout(self.window.findChild(QGroupBox, "se%d_groupBox" % i))
            self.se_layout[i].addWidget(self.se_plt_list[i])
            self.se_vLine[i] = pg.InfiniteLine(angle=90, movable=False, )  # 创建一个垂直线条
            self.se_hLine[i] = pg.InfiniteLine(angle=0, movable=False, )  # 创建一个水平线条
            self.se_plt_list[i].addItem(self.se_vLine[i], ignoreBounds=True)  # 在图形部件中添加垂直线条
            self.se_plt_list[i].addItem(self.se_hLine[i], ignoreBounds=True)  # 在图形部件中添加水平线条
            self.se_vb[i] = self.se_plt_list[i].plotItem.vb  # 得到鼠标位置
            self.se_plt_list[i].scene().sigMouseMoved.connect(self.mouse_moved)
            self.window.statusBar.showMessage("传感器绘图加载完成")

        self.window.statusBar.showMessage("绘图模块加载完成！！！")

    def mouse_moved(self, evt):
        # gearbox
        if self.window.tabWidget.currentIndex() == 0:
            i = self.window.gb_tabWidget.currentIndex() + 1  # 得到当前页的序号+1 用于绑定十字
            mousePoint = self.gb_vb[i].mapSceneToView(evt)
            self.gb_vLine[i].setPos(mousePoint.x())
            self.gb_hLine[i].setPos(mousePoint.y())
        # generator
        elif self.window.tabWidget.currentIndex() == 1:
            i = self.window.ge_tabWidget.currentIndex() + 1  # 得到当前页的序号+1 用于绑定十字
            mousePoint = self.ge_vb[i].mapSceneToView(evt)
            self.ge_vLine[i].setPos(mousePoint.x())
            self.ge_hLine[i].setPos(mousePoint.y())
        # pitch
        elif self.window.tabWidget.currentIndex() == 2:
            i = self.window.pitch_tabWidget.currentIndex() + 1  # 得到当前页的序号+1 用于绑定十字
            mousePoint = self.pitch_vb[i].mapSceneToView(evt)
            self.pitch_vLine[i].setPos(mousePoint.x())
            self.pitch_hLine[i].setPos(mousePoint.y())
        # converter
        elif self.window.tabWidget.currentIndex() == 3:
            i = self.window.co_tabWidget.currentIndex() + 1  # 得到当前页的序号+1 用于绑定十字
            mousePoint = self.co_vb[i].mapSceneToView(evt)
            self.co_vLine[i].setPos(mousePoint.x())
            self.co_hLine[i].setPos(mousePoint.y())
        # hydraulic
        elif self.window.tabWidget.currentIndex() == 4:
            i = self.window.hy_tabWidget.currentIndex() + 1  # 得到当前页的序号+1 用于绑定十字
            mousePoint = self.hy_vb[i].mapSceneToView(evt)
            self.hy_vLine[i].setPos(mousePoint.x())
            self.hy_hLine[i].setPos(mousePoint.y())
        # sensor
        elif self.window.tabWidget.currentIndex() == 5:
            i = self.window.se_tabWidget.currentIndex() + 1  # 得到当前页的序号+1 用于绑定十字
            mousePoint = self.se_vb[i].mapSceneToView(evt)
            self.se_vLine[i].setPos(mousePoint.x())
            self.se_hLine[i].setPos(mousePoint.y())


if __name__ == '__main__':
    app = QApplication([])
    win = Ui()
    win.window.show()
    app.exec_()
