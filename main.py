from PyQt5.QtWidgets import QApplication, QFileDialog, QLabel, QMessageBox, QWidget, QInputDialog, QLineEdit
# 导入右击事件
from PyQt5.QtCore import pyqtSignal, QObject, QTimer, QVariant, QThread
# 导入颜色
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from PyQt5 import uic
import os
import subprocess
import shutil
# 显示占用内存
import psutil
import gc
# sip 用于彻底删除控件回收内存 C++编写
import sip
# 绘图
import pyqtgraph as pg

# ————————————————————————————————————自定义模块区开始
import log_window
from DAL import base_setting
from BLL import grGearBox
from BLL import grGenerator
from BLL import grConverter
from BLL import grHydraulic
from BLL import grPitch
from BLL import grSensor
from BLL import model_manager
from plug import seven_zip_window
from config.icon import ico


# ————————————————————————————————————自定义模块区结束


class Ui(QWidget):
    # 开启的线程数量
    signal_thread_number = pyqtSignal(int)
    signal_draw_model = pyqtSignal(bool)
    signal_reset_draw_base_data = pyqtSignal(bool)

    def __init__(self):
        """
            1.载入UI
                1.1 显示内存情况
                1.2给工具栏添加日志文本框
            2.配置界面基本信息
                2.1 导入项目名称
                2.2 初始化导入数据
                2.3 初始化选择项目
                2.4 初始化模式
                2.5 绘图数据
                2.6 配置进度条初始值
                2.7 初始化解压界面
                2.8 是否绘图按钮
            3.绑定事件
                3.1 绑定左击事件
                    3.1.1 绑定导入数据事件
                    3.1.2 绑定选择项目事件
                    3.1.3 绑定运行按钮
                    3.1.4 绑定解压事件
                    3.1.5 绑定添加项目事件
                    3.1.6 绑定修改项目事件
                    3.1.7 绑定帮助事件
                    3.1.8 绑定关于事件
                    3.1.9 绑定列表与tab对应事件
                    3.1.10 绑定是否绘图事件
                3.2绑定右击事件
                3.3 退出事件
            4.自定义信号反馈
                4.1 gearbox区
                    4.1.1 创建gearbox区的绘图
                4.2 generator区
                4.1 pitch区
                4.2 converter区
                4.1 hydraulic区
                4.1 sensor区
            5.创建线程
                5.1 定义新线程
                5.2 定义需要创建线程数量的信号
        """
        super(Ui, self).__init__()
        # from PyQt5.QtWidgets import QGraphicsView
        # QGraphicsView.update()
        # 1 ----------------------------------------载入UI
        self.window = uic.loadUi("UI/main.ui")
        # # 1.1 显示内存情况
        self.window.memory_label = QLabel(self.window)
        self.window.memory_label.setStyleSheet("color:blue")
        self.window.memory_label.setText("")
        self.window.toolBar.addWidget(self.window.memory_label)
        self.timer = QTimer()
        self.refresh_ui()
        # # >>> 1.2 工具栏
        """
        创建log窗口
        默认情况不显示
        绑定工具栏action
        """
        self.log = log_window.UI()
        self.show_log = False
        self.window.Log.triggered.connect(self.open_log)
        # # <<<工具栏结束
        # 2 ----------------------------------------载入界面基础数据开始
        self.base_setting = base_setting.AutoSelectTickets(os.getcwd() + r"/config/tickets.json")
        self.window.select_project_comboBox.addItems(self.base_setting.tickets_data_project_name)
        # # 2.1 设置默认情况下不选择项目，不选择模式
        self.window.select_project_comboBox.setCurrentIndex(-1)
        self.window.mode_comboBox.setCurrentIndex(-1)
        # # 2.2 导入数据初始化
        self.need_deal_data = None
        # # 2.3 选择项目
        self.select_project_index = None
        # # 2.4 初始化模式
        self.mode = 0
        # # 2.5 配置进度条初始值
        self.gb_process = 0
        self.ge_process = 0
        self.pitch_process = 0
        self.co_process = 0
        self.hy_process = 0
        self.se_process = 0
        # #　2.7 初始化解压界面
        # #２.８
        self.is_plot = False
        self.unpack_ui = seven_zip_window.UI()
        # # 2.９ 定义结束线程变量
        self.over = 0
        # 3----------------------------------------绑定事件
        # # >>>3.1 左击事件
        # # # 3.1.1 绑定导入数据事件
        self.window.import_data_action.triggered.connect(self.load_data)
        # # # 3.1.2 绑定选择项目事件,选择模式事件
        self.window.select_project_comboBox.currentIndexChanged.connect(self.select_project)
        self.window.mode_comboBox.currentIndexChanged.connect(self.select_mode)
        # # # 3.1.3 绑定运行按钮
        self.window.run_pushButton.clicked.connect(self.run)
        # # # >>> 3.1.4 绑定解压
        self.window.unpack_action.triggered.connect(self.load_unpack)
        # # # >>> 3.1.5 绑定添加项目事件
        self.window.add_project_action.triggered.connect(self.add_project)
        # # # >>> 3.1.6 绑定修改项目事件
        self.window.refactor_project_action.triggered.connect(self.refactor_project)
        # # # >>> 3.1.7 绑定帮助事件
        self.window.help_action.triggered.connect(self.help)
        # # # >>> 3.1.8 绑定关于事件
        self.window.about_action.triggered.connect(self.about)

        # # # >>> 3.1.9 绑定左击列表与页列表对应事件
        self.window.gb_listWidget.itemClicked.connect(self.select_gb_tabWidget_items)
        self.window.ge_listWidget.itemClicked.connect(self.select_ge_tabWidget_items)
        self.window.pitch_listWidget.itemClicked.connect(self.select_pitch_tabWidget_items)
        self.window.co_listWidget.itemClicked.connect(self.select_co_tabWidget_items)
        self.window.hy_listWidget.itemClicked.connect(self.select_hy_tabWidget_items)
        self.window.se_listWidget.itemClicked.connect(self.select_se_tabWidget_items)
        # # #　>>> 3.1.10是否绘图
        self.window.plot_comboBox.currentIndexChanged.connect(self.is_draw)
        self.window.plot_comboBox.setCurrentIndex(-1)

        # # <<< 左击事件结束

        # # 3.2 >>>绑定右击事件
        self.window.gb_listWidget.setContextMenuPolicy(3)  # 设置菜单
        # # 3.3 >>> 绑定退出事件
        self.window.closeEvent = self.closeEvent

        # self.window.gb_listWidget.customContextMenuRequested[QPoint].connect(self.change_gearbox_list_color)  # 设置菜单

        # 4 ----------------------------------------自定义信号区
        # # 模型管理
        self.model_manager = model_manager.Manager()
        # # 4.1 gearbox 区
        # # # 4.2.1 gearbox绘图区
        self.gb_graphicsViews = None
        # # # 4.1.2 >>>初始化gearbox线程
        """
            1. 初始化空gearbox
            2.绑定gearbox模块的信号：修改列表框颜色，更新进度
        """
        self.gearbox = grGearBox.GearBox1()
        self.gearbox.signal_gb_progress.connect(self.progress)
        self.gearbox.signal_gb_color.connect(self.change_gearbox_list_color)
        self.gearbox.signal_gb_write_log.connect(self.write_log)
        self.gearbox.signal_gb_over.connect(self.over_threading)

        # # 4.2 generator 区
        # # # 4.2.1 generator绘图区
        self.ge_graphicsViews = None
        # # # 4.2.2 >>>初始化generator线程
        self.generator = grGenerator.Generator1()
        self.generator.signal_ge_progress.connect(self.progress)
        self.generator.signal_ge_color.connect(self.change_generator_list_color)
        self.generator.signal_ge_write_log.connect(self.write_log)
        self.generator.signal_ge_over.connect(self.over_threading)

        # # 4.3 pitch 区
        # # # 4.3.1 pitch绘图区
        self.pitch_graphicsViews = None
        # # # 4.3.2 >>>初始化pitch线程
        self.pitch = grPitch.Pitch1()
        self.pitch.signal_pitch_progress.connect(self.progress)
        self.pitch.signal_pitch_color.connect(self.change_pitch_list_color)
        self.pitch.signal_pitch_write_log.connect(self.write_log)
        self.pitch.signal_pitch_over.connect(self.over_threading)

        # # 4.4 converter 区
        # # # 4.4.1 converter绘图区
        self.co_graphicsViews = None
        # # # 4.4.2 >>>初始化converter线程
        self.converter = grConverter.Converter1()
        self.converter.signal_co_progress.connect(self.progress)
        self.converter.signal_co_color.connect(self.change_converter_list_color)
        self.converter.signal_co_write_log.connect(self.write_log)
        self.converter.signal_co_over.connect(self.over_threading)

        # # 4.5 hydraulic 区
        # # # 4.5.1 hydraulic绘图区
        self.hy_graphicsViews = None
        # # # 4.5.2 >>>初始化hydraulic线程
        self.hydraulic = grHydraulic.Hydraulic1()
        self.hydraulic.signal_hy_progress.connect(self.progress)
        self.hydraulic.signal_hy_color.connect(self.change_hydraulic_list_color)
        self.hydraulic.signal_hy_write_log.connect(self.write_log)
        self.hydraulic.signal_hy_over.connect(self.over_threading)

        # # 4.6 sensor 区
        # # # 4.6.1 sensor绘图区
        self.se_graphicsViews = None
        # # # 4.6.2 >>>初始化sensor线程
        self.sensor = grSensor.Sensor1()
        self.sensor.signal_se_progress.connect(self.progress)
        self.sensor.signal_se_color.connect(self.change_sensor_list_color)
        self.sensor.signal_se_write_log.connect(self.write_log)
        self.sensor.signal_se_over.connect(self.over_threading)

        self.load_draw_timer = QTimer()
        # # # <<<初始化结束

        # # ------------------------------>>>测试区域
        # self.window.run_pushButton.setEnabled(True)
        # self.window.run_pushButton.setEnabled(True)
        self.window.statusBar.showMessage("主界面加载完成")
        # self.load_draw_timer.singleShot(1000, self.load_plot)
        self.window.statusBar.showMessage("请等待绘图界面加载！")
        # # ------------------------------>>>测试区域结束
        # 5 创建线程
        # # 5.1 定义新线程
        # *********************************************************************************###
        # self.gearbox_thread = self.generator_thread = self.pitch_thread = \                #
        #     self.converter_thread = self.hydraulic_thread = self.sensor_thread = QThread() #
        #               此处不能用这种创建方式，不然创建的是同一个进程！！！只是引用了多次               #
        # *********************************************************************************###
        self.gearbox_thread = QThread()
        self.generator_thread = QThread()
        self.pitch_thread = QThread()
        self.converter_thread = QThread()
        self.hydraulic_thread = QThread()
        self.sensor_thread = QThread()
        # # 5.2 定义需要创建线程数量的信号
        self.signal_thread_number.connect(self.start_thread)

        # # 测试区
        # self.window.test_pushButton.clicked.connect(self.closeEvent)
        # self.gb_graphicsViews = list(self.window.gb_tabWidget.findChildren((pg.GraphicsLayoutWidget,)))
        # self.gb_graphicsViews.reverse()
        # self.drawing(self.gb_graphicsViews[0],
        #              canvas_setting={"title": "ss"},
        #              data=[
        #                  {"x": [1, 2, 3, 4, 5], "y": [6, 7, 8, 9, 10], 'pen': 'g', "name": "o"},
        #                  {"x": [1, 2, 3, 4, 5], "y": [2, 4, 9, 16, 25]}
        #              ])

    def is_draw(self):
        self.window.run_pushButton.setEnabled(True)
        if self.window.plot_comboBox.currentIndex() == 0:
            self.is_plot = True
        else:
            self.is_plot = False

    def load_plot(self):
        """
        1.分模块获取绘图对象
        2.为绘图对象添加画布
        :return:
        """
        self.gb_graphicsViews = list(self.window.gb_tabWidget.findChildren((pg.GraphicsLayoutWidget,)))
        self.gb_graphicsViews.reverse()
        self.ge_graphicsViews = list(self.window.ge_tabWidget.findChildren((pg.GraphicsLayoutWidget,)))
        self.ge_graphicsViews.reverse()
        self.pitch_graphicsViews = list(self.window.pitch_tabWidget.findChildren((pg.GraphicsLayoutWidget,)))
        self.pitch_graphicsViews.reverse()
        self.co_graphicsViews = list(self.window.co_tabWidget.findChildren((pg.GraphicsLayoutWidget,)))
        self.co_graphicsViews.reverse()
        self.hy_graphicsViews = list(self.window.hy_tabWidget.findChildren((pg.GraphicsLayoutWidget,)))
        self.hy_graphicsViews.reverse()
        self.se_graphicsViews = list(self.window.se_tabWidget.findChildren((pg.GraphicsLayoutWidget,)))
        self.se_graphicsViews.reverse()
        self.window.statusBar.showMessage("绘图模块加载完成！！！")

    # 载入解压界面
    def load_unpack(self):
        self.unpack_ui.window.show()

    def mouse_moved(self, evt):
        # gearbox
        if self.window.tabWidget.currentIndex() == 0:
            i = self.window.gb_tabWidget.currentIndex() + 1  # 得到当前页的序号+1 用于绑定十字
            mousePoint = self.vb.mapSceneToView(evt)
            print(self.vLine)
            self.vLine.setPos(mousePoint.x())
            self.hLine.setPos(mousePoint.y())
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

    def refresh_ui(self):
        self.timer.start(1000)
        self.timer.timeout.connect(self.get_memory)

    def get_memory(self):
        mem = psutil.virtual_memory()
        # round方法进行四舍五入，然后转换成字符串 字节/1024得到kb 再/1024得到M
        total = str(round(mem.total / 1024 / 1024))
        used = str(round(mem.used / 1024 / 1024))
        use_per = str(round(mem.percent))
        free = str(round(mem.free / 1024 / 1024))
        process = psutil.Process(os.getpid())
        memInfo = process.memory_info()
        me = str(round(memInfo.rss / 1024 / 1024))
        self.window.memory_label.setText(
            "本机内存：{}M，已使用：{}M({}%)，本程序占用：{}M,可使用:{}M)".format(total, used, use_per, me, free))

    # ----------------------->>>载入基本数据事件区
    def load_data(self):
        self.window.mode_comboBox.setItemData(0, QVariant(1 | 32), Qt.UserRole - 1)
        self.window.mode_comboBox.setItemData(1, QVariant(1 | 32), Qt.UserRole - 1)
        self.window.mode_comboBox.setItemData(2, QVariant(1 | 32), Qt.UserRole - 1)
        Dialog = QFileDialog()
        file_names, filetype = Dialog.getOpenFileNames(self.window,
                                                       "选取文件",
                                                       # 获得当前路径
                                                       os.getcwd(),  # 起始路径
                                                       "CSV文件 (*.csv);;所有文件 (*)")  # 设置文件扩展名过滤,用双分号间隔
        if file_names == []:
            print("\n取消选择")
            Dialog.deleteLater()
            sip.delete(Dialog)
            gc.collect()

        else:
            """
            如果选择单个文件则判断是合并的周级数据还是天级数据
                周级数据：大文件模式
                天级数据：小文件绘图模式
            如果选择多个文件
                多个文件：多文件模式
            """
            if len(file_names) == 1:
                """
               得到文件的大小 单位 kb
               1M = 1024 kb
               300M = 307200 kb
               如果文件小于300M则选择小文件绘图模式 否则大文件模式
               """
                self.need_deal_data = file_names[0]
                self.window.select_project_comboBox.setEnabled(True)
                file_size = os.path.getsize(self.need_deal_data)
                file_size = float(file_size) / float(1024 * 1024)  # M
                if file_size <= 300:
                    # 设置模式为小文件绘图模式，1,2 选项不可选
                    self.window.mode_comboBox.setItemData(1, 0, Qt.UserRole - 1)
                    self.window.mode_comboBox.setItemData(2, 0, Qt.UserRole - 1)
                    # 设置模式1
                    self.mode = 1
                    self.window.mode_comboBox.setCurrentIndex(0)
                    print("mode1")

                else:
                    self.need_deal_data = file_names[0]
                    self.window.select_project_comboBox.setEnabled(True)
                    # 设置模式为大文件，0,2 选项不可选
                    self.window.mode_comboBox.setItemData(0, 0, Qt.UserRole - 1)
                    self.window.mode_comboBox.setItemData(2, 0, Qt.UserRole - 1)
                    # 设置模式2
                    self.mode = 2
                    self.window.mode_comboBox.setCurrentIndex(1)
                    print("mode2")

            else:
                self.window.select_project_comboBox.setEnabled(True)
                # 还未设计多文件选择模式
                self.need_deal_data = file_names
                # 设置模式为多文件模式，0,2 选项不可选
                self.window.mode_comboBox.setItemData(0, 0, Qt.UserRole - 1)
                self.window.mode_comboBox.setItemData(1, 0, Qt.UserRole - 1)
                # 设置模式3
                self.mode = 3
                print("mode3")
            # 设置选择下拉框可见
            Dialog.deleteLater()
            sip.delete(Dialog)
            gc.collect()

    def select_project(self):
        # self.window.run_pushButton.setEnabled(True)
        self.select_project_index = self.window.select_project_comboBox.currentIndex()
        # 管家
        self.model_manager = model_manager.Manager(mode=self.mode,
                                                   tickets_file_path='config/tickets.json',
                                                   import_data_path=self.need_deal_data,
                                                   project_index=self.select_project_index,
                                                   plot_setting={})
        # 开始管家线程
        self.model_manager.signal_return_data.connect(self.start_analyse)
        self.model_manager.signal_manager_over.connect(self.over_threading)

        self.window.plot_comboBox.setEnabled(True)

    def select_mode(self):
        # print(self.mode)

        # print(self.window.mode_comboBox.currentIndex())
        if self.mode == 1:
            self.load_plot()
        elif self.mode == 2:
            self.load_plot()
        else:
            pass

    # 功能区事件
    # --------------------->>>绑定列表与tab界面事件区
    def select_gb_tabWidget_items(self):
        QApplication.processEvents()
        self.window.gb_tabWidget.setCurrentIndex(self.window.gb_listWidget.currentRow())

    def select_ge_tabWidget_items(self):
        self.window.ge_tabWidget.setCurrentIndex(self.window.ge_listWidget.currentRow())

    def select_pitch_tabWidget_items(self):
        self.window.pitch_tabWidget.setCurrentIndex(self.window.pitch_listWidget.currentRow())

    def select_co_tabWidget_items(self):
        self.window.co_tabWidget.setCurrentIndex(self.window.co_listWidget.currentRow())

    def select_hy_tabWidget_items(self):
        self.window.hy_tabWidget.setCurrentIndex(self.window.hy_listWidget.currentRow())

    def select_se_tabWidget_items(self):
        self.window.se_tabWidget.setCurrentIndex(self.window.se_listWidget.currentRow())

    # --------------------->>>改变list颜色类事件区
    def change_gearbox_list_color(self, li):
        """
        :param li: li[0]: 返回一个int 类型数据 -1:数据标签点丢失，0 预警 1 正常 ; li[1]:序号，需要修改的items
        :return:
        """
        item = li[1]
        for i in range(35):
            if i == item:
                if li[0] == -1:
                    self.window.gb_listWidget.item(i).setBackground(QColor('gray'))
                    self.window.gb_listWidget.item(i).setCheckState(1)
                elif li[0] == 0:
                    self.window.gb_listWidget.item(i).setBackground(QColor('red'))
                    self.window.gb_listWidget.item(i).setCheckState(2)
                else:
                    self.window.gb_listWidget.item(i).setBackground(QColor('green'))
                    self.window.gb_listWidget.item(i).setCheckState(0)
            else:
                pass

    def change_generator_list_color(self, li):
        """
        :param li: li[0]: 返回一个int 类型数据 -1:数据标签点丢失，0 预警 1 正常 ; li[1]:序号，需要修改的items
        :return:
        """
        item = li[1]
        for i in range(14):
            if i == item:
                if li[0] == -1:
                    self.window.ge_listWidget.item(i).setBackground(QColor('gray'))
                    self.window.ge_listWidget.item(i).setCheckState(1)
                elif li[0] == 0:
                    self.window.ge_listWidget.item(i).setBackground(QColor('red'))
                    self.window.ge_listWidget.item(i).setCheckState(2)
                else:
                    self.window.ge_listWidget.item(i).setBackground(QColor('green'))
                    self.window.ge_listWidget.item(i).setCheckState(0)
            else:
                pass

    def change_pitch_list_color(self, li):
        """
        :param li: li[0]: 返回一个int 类型数据 -1:数据标签点丢失，0 预警 1 正常 ; li[1]:序号，需要修改的items
        :return:
        """
        item = li[1]
        for i in range(9):
            if i == item:
                if li[0] == -1:
                    self.window.pitch_listWidget.item(i).setBackground(QColor('gray'))
                    self.window.pitch_listWidget.item(i).setCheckState(1)
                elif li[0] == 0:
                    self.window.pitch_listWidget.item(i).setBackground(QColor('red'))
                    self.window.pitch_listWidget.item(i).setCheckState(2)
                else:
                    self.window.pitch_listWidget.item(i).setBackground(QColor('green'))
                    self.window.pitch_listWidget.item(i).setCheckState(0)
            else:
                pass

    def change_converter_list_color(self, li):
        """
        :param li: li[0]: 返回一个int 类型数据 -1:数据标签点丢失，0 预警 1 正常 ; li[1]:序号，需要修改的items
        :return:
        """
        item = li[1]
        for i in range(8):
            if i == item:
                if li[0] == -1:
                    self.window.co_listWidget.item(i).setBackground(QColor('gray'))
                    self.window.co_listWidget.item(i).setCheckState(1)
                elif li[0] == 0:
                    self.window.co_listWidget.item(i).setBackground(QColor('red'))
                    self.window.co_listWidget.item(i).setCheckState(2)
                else:
                    self.window.co_listWidget.item(i).setBackground(QColor('green'))
                    self.window.co_listWidget.item(i).setCheckState(0)
            else:
                pass

    def change_hydraulic_list_color(self, li):
        """
        :param li: li[0]: 返回一个int 类型数据 -1:数据标签点丢失，0 预警 1 正常 ; li[1]:序号，需要修改的items
        :return:
        """
        item = li[1]
        for i in range(12):
            if i == item:
                if li[0] == -1:
                    self.window.hy_listWidget.item(i).setBackground(QColor('gray'))
                    self.window.hy_listWidget.item(i).setCheckState(1)
                elif li[0] == 0:
                    self.window.hy_listWidget.item(i).setBackground(QColor('red'))
                    self.window.hy_listWidget.item(i).setCheckState(2)
                else:
                    self.window.hy_listWidget.item(i).setBackground(QColor('green'))
                    self.window.hy_listWidget.item(i).setCheckState(0)
            else:
                pass

    def change_sensor_list_color(self, li):
        """
        :param li: li[0]: 返回一个int 类型数据 -1:数据标签点丢失，0 预警 1 正常 ; li[1]:序号，需要修改的items
        :return:
        """
        item = li[1]
        for i in range(9):
            if i == item:
                if li[0] == -1:
                    self.window.se_listWidget.item(i).setBackground(QColor('gray'))
                    self.window.se_listWidget.item(i).setCheckState(1)
                elif li[0] == 0:
                    self.window.se_listWidget.item(i).setBackground(QColor('red'))
                    self.window.se_listWidget.item(i).setCheckState(2)
                else:
                    self.window.se_listWidget.item(i).setBackground(QColor('green'))
                    self.window.se_listWidget.item(i).setCheckState(0)
            else:
                pass

    # --------------------->>>选择list项目类事件区

    # -------------------->>>日志区
    # 写日志区
    def write_log(self, li):
        """
        :param li: li[0]:用于判断部件
                    li[1]:li
                            li[0]:判断正常或异常
                            li[1]:日志
        :return:
        """
        if li[0] == 0:
            self.log.window.summary_plainTextEdit.appendHtml("<p><font color='red'>{}</font></p>".format(li[1][1]))
        elif li[0] == 1:
            if li[1][0] == 1:
                self.log.window.gb_plainTextEdit.appendHtml("<p><font color='green'>{}</font></p>".format(li[1][1]))
            elif li[1][0] == 0:
                self.log.window.gb_plainTextEdit.appendHtml("<p><font color='red'>{}</font></p>".format(li[1][1]))
            else:
                self.log.window.gb_plainTextEdit.appendHtml("<p><font color='gray'>{}</font></p>".format(li[1][1]))

        elif li[0] == 2:
            if li[1][0] == 1:
                self.log.window.ge_plainTextEdit.appendHtml("<p><font color='green'>{}</font></p>".format(li[1][1]))
            elif li[1][0] == 0:
                self.log.window.ge_plainTextEdit.appendHtml("<p><font color='red'>{}</font></p>".format(li[1][1]))
            else:
                self.log.window.ge_plainTextEdit.appendHtml("<p><font color='gray'>{}</font></p>".format(li[1][1]))

        elif li[0] == 3:
            if li[1][0] == 1:
                self.log.window.pitch_plainTextEdit.appendHtml("<p><font color='green'>{}</font></p>".format(li[1][1]))
            elif li[1][0] == 0:
                self.log.window.pitch_plainTextEdit.appendHtml("<p><font color='red'>{}</font></p>".format(li[1][1]))
            else:
                self.log.window.pitch_plainTextEdit.appendHtml("<p><font color='gray'>{}</font></p>".format(li[1][1]))
        elif li[0] == 4:
            if li[1][0] == 1:
                self.log.window.co_plainTextEdit.appendHtml("<p><font color='green'>{}</font></p>".format(li[1][1]))
            elif li[1][0] == 0:
                self.log.window.co_plainTextEdit.appendHtml("<p><font color='red'>{}</font></p>".format(li[1][1]))
            else:
                self.log.window.co_plainTextEdit.appendHtml("<p><font color='gray'>{}</font></p>".format(li[1][1]))

        elif li[0] == 5:
            if li[1][0] == 1:
                self.log.window.hy_plainTextEdit.appendHtml("<p><font color='green'>{}</font></p>".format(li[1][1]))
            elif li[1][0] == 0:
                self.log.window.hy_plainTextEdit.appendHtml("<p><font color='red'>{}</font></p>".format(li[1][1]))
            else:
                self.log.window.hy_plainTextEdit.appendHtml("<p><font color='gray'>{}</font></p>".format(li[1][1]))

        elif li[0] == 6:
            if li[1][0] == 1:
                self.log.window.se_plainTextEdit.appendHtml("<p><font color='green'>{}</font></p>".format(li[1][1]))
            elif li[1][0] == 0:
                self.log.window.se_plainTextEdit.appendHtml("<p><font color='red'>{}</font></p>".format(li[1][1]))
            else:
                self.log.window.se_plainTextEdit.appendHtml("<p><font color='gray'>{}</font></p>".format(li[1][1]))

    def open_log(self):
        if not self.show_log:
            self.log.window.show()
            self.show_log = True
        else:
            self.log.window.hide()
            self.show_log = False

    # ----------------------->>>运行区
    # 分析启动几个线程
    def start_analyse(self, signal):
        """
        :param signal: signal 是一个列表
            li[0]:何种模式，大文件还是小文件
            li[1]：df 还是None, 小文件df 大文件None
            li[2]：项目序号
            li[3]: 开启的线程数量，小文件6个线程 0 表示6个全部开启，大文件1个线程
        如果是小文件模式则启动所有的线程，如果是大文件模式则只启动一个线程，等待上一个线程结束再启动下一个线程
        :return:
        """
        # 如果模式1
        if signal[0] == int(1):
            self.window.statusBar.showMessage("读取数据成功！正在计算...")
            # >>> gearbox
            self.gearbox = grGearBox.GearBox1(tickets_file_path='config/tickets.json',
                                              import_data_path=self.need_deal_data,
                                              df=signal[1],
                                              project_index=signal[2],
                                              plt_list=self.gb_graphicsViews,
                                              draw=self.is_plot)

            # >>> generator
            self.generator = grGenerator.Generator1(tickets_file_path='config/tickets.json',
                                                    import_data_path=self.need_deal_data,
                                                    df=signal[1],
                                                    project_index=signal[2],
                                                    plt_list=self.ge_graphicsViews,
                                                    draw=self.is_plot)

            # >>> pitch
            self.pitch = grPitch.Pitch1(tickets_file_path='config/tickets.json',
                                        import_data_path=self.need_deal_data,
                                        df=signal[1],
                                        project_index=signal[2],
                                        plt_list=self.pitch_graphicsViews,
                                        draw=self.is_plot)

            # 　>>>　converter
            self.converter = grConverter.Converter1(tickets_file_path='config/tickets.json',
                                                    import_data_path=self.need_deal_data,
                                                    df=signal[1],
                                                    project_index=signal[2],
                                                    plt_list=self.co_graphicsViews,
                                                    draw=self.is_plot)

            # >>> hydraulic
            self.hydraulic = grHydraulic.Hydraulic1(tickets_file_path='config/tickets.json',
                                                    import_data_path=self.need_deal_data,
                                                    df=signal[1],
                                                    project_index=signal[2],
                                                    plt_list=self.hy_graphicsViews,
                                                    draw=self.is_plot)

            # >>> sensor
            self.sensor = grSensor.Sensor1(tickets_file_path='config/tickets.json',
                                           import_data_path=self.need_deal_data,
                                           df=signal[1],
                                           project_index=signal[2],
                                           plt_list=self.se_graphicsViews,
                                           draw=self.is_plot)

            # ----------------开启线程
        elif signal[0] == int(2):
            self.gearbox = grGearBox.GearBox1(tickets_file_path='config/tickets.json',
                                              import_data_path=self.need_deal_data,
                                              df=None,
                                              project_index=self.select_project_index,
                                              plt_list=self.gb_graphicsViews,
                                              draw=self.is_plot)
            self.generator = grGenerator.Generator1(tickets_file_path='config/tickets.json',
                                                    import_data_path=self.need_deal_data,
                                                    df=None,
                                                    project_index=self.select_project_index,
                                                    plt_list=self.ge_graphicsViews,
                                                    draw=self.is_plot)
            self.pitch = grPitch.Pitch1(tickets_file_path='config/tickets.json',
                                        import_data_path=self.need_deal_data,
                                        df=None,
                                        project_index=self.select_project_index,
                                        plt_list=self.pitch_graphicsViews,
                                        draw=self.is_plot)
            self.converter = grConverter.Converter1(tickets_file_path='config/tickets.json',
                                                    import_data_path=self.need_deal_data,
                                                    df=None,
                                                    project_index=self.select_project_index,
                                                    plt_list=self.co_graphicsViews,
                                                    draw=self.is_plot)
            self.hydraulic = grHydraulic.Hydraulic1(tickets_file_path='config/tickets.json',
                                                    import_data_path=self.need_deal_data,
                                                    df=None,
                                                    project_index=self.select_project_index,
                                                    plt_list=self.hy_graphicsViews,
                                                    draw=self.is_plot)
            self.sensor = grSensor.Sensor1(tickets_file_path='config/tickets.json',
                                           import_data_path=self.need_deal_data,
                                           df=None,
                                           project_index=self.select_project_index,
                                           plt_list=self.se_graphicsViews,
                                           draw=self.is_plot)
        # ----------------------信号
        self.gearbox.signal_gb_progress.connect(self.progress)
        self.gearbox.signal_gb_color.connect(self.change_gearbox_list_color)
        self.gearbox.signal_gb_write_log.connect(self.write_log)
        self.gearbox.signal_gb_over.connect(self.over_threading)

        self.generator.signal_ge_progress.connect(self.progress)
        self.generator.signal_ge_color.connect(self.change_generator_list_color)
        self.generator.signal_ge_write_log.connect(self.write_log)
        self.generator.signal_ge_over.connect(self.over_threading)

        self.pitch.signal_pitch_progress.connect(self.progress)
        self.pitch.signal_pitch_color.connect(self.change_pitch_list_color)
        self.pitch.signal_pitch_write_log.connect(self.write_log)
        self.pitch.signal_pitch_over.connect(self.over_threading)

        self.converter.signal_co_progress.connect(self.progress)
        self.converter.signal_co_color.connect(self.change_converter_list_color)
        self.converter.signal_co_write_log.connect(self.write_log)
        self.converter.signal_co_over.connect(self.over_threading)

        self.hydraulic.signal_hy_progress.connect(self.progress)
        self.hydraulic.signal_hy_color.connect(self.change_hydraulic_list_color)
        self.hydraulic.signal_hy_write_log.connect(self.write_log)
        self.hydraulic.signal_hy_over.connect(self.over_threading)

        self.sensor.signal_se_progress.connect(self.progress)
        self.sensor.signal_se_color.connect(self.change_sensor_list_color)
        self.sensor.signal_se_write_log.connect(self.write_log)
        self.sensor.signal_se_over.connect(self.over_threading)

        # ------------------绑定线程
        self.gearbox.moveToThread(self.gearbox_thread)
        self.gearbox_thread.started.connect(self.gearbox.run)

        self.generator.moveToThread(self.generator_thread)
        self.generator_thread.started.connect(self.generator.run)

        self.pitch.moveToThread(self.pitch_thread)
        self.pitch_thread.started.connect(self.pitch.run)

        self.converter.moveToThread(self.converter_thread)
        self.converter_thread.started.connect(self.converter.run)

        self.hydraulic.moveToThread(self.hydraulic_thread)
        self.hydraulic_thread.started.connect(self.hydraulic.run)

        self.sensor.moveToThread(self.sensor_thread)
        self.sensor_thread.started.connect(self.sensor.run)

        # 判断需要开启的线程数量
        if signal[3] == int(6):
            self.signal_thread_number.emit(0)
        elif signal[3] == int(1):
            self.signal_thread_number.emit(1)

    def start_thread(self, thread_number):
        print("thread_number:{}".format(thread_number))
        """
        :param thread_number: 值为int 类型，
            thread_number == -1 结束所有线程
            thread_number == 0 开启所有线程
            thread_number == 1 开启第一个线程
            thread_number == 2 退出第一个线程后，开启第二个线程
            thread_number == 3 退出上一个线程后，开启下一个线程
            ...
        :return:
        """
        if thread_number == int(0):

            self.gearbox_thread.start()
            self.generator_thread.start()
            self.hydraulic_thread.start()
            self.sensor_thread.start()
            self.pitch_thread.start()
            self.converter_thread.start()
            for i in range(self.window.gb_tabWidget.count()):
                self.window.gb_tabWidget.setCurrentIndex(i)
            self.window.gb_tabWidget.setCurrentIndex(0)
            for i in range(self.window.ge_tabWidget.count()):
                self.window.ge_tabWidget.setCurrentIndex(i)
            self.window.ge_tabWidget.setCurrentIndex(0)
            for i in range(self.window.pitch_tabWidget.count()):
                self.window.pitch_tabWidget.setCurrentIndex(i)
            self.window.pitch_tabWidget.setCurrentIndex(0)
            for i in range(self.window.co_tabWidget.count()):
                self.window.co_tabWidget.setCurrentIndex(i)
            self.window.co_tabWidget.setCurrentIndex(0)
            for i in range(self.window.hy_tabWidget.count()):
                self.window.hy_tabWidget.setCurrentIndex(i)
            self.window.hy_tabWidget.setCurrentIndex(0)
            for i in range(self.window.se_tabWidget.count()):
                self.window.se_tabWidget.setCurrentIndex(i)
            self.window.se_tabWidget.setCurrentIndex(0)

        elif thread_number == int(1):
            self.gearbox_thread.start()
        elif thread_number == int(2):
            self.generator_thread.start()
        elif thread_number == int(3):
            self.pitch_thread.start()
        elif thread_number == int(4):
            self.converter_thread.start()
        elif thread_number == int(5):
            self.hydraulic_thread.start()
        elif thread_number == int(6):
            self.sensor_thread.start()

    def over_threading(self, li):

        """
        :param li: li[0]:第几个线程 ，li[1]：是否结束
        总共7个子线程，用变量over记录结束线程的数量，每结束一个子线程over增加1
        :return:
        """
        if self.mode == int(2):
            if li[0] == int(0):

                self.model_manager.exec_()
                self.over += 1
            elif li[0] == int(1):
                print("齿轮箱结束，发电机开始")
                self.over += 1
                # 齿轮箱结束，开启发电机
                self.signal_thread_number.emit(2)
                self.gearbox_thread.quit()

            elif li[0] == 2:
                self.over += 1
                # 发电机结束，开启变桨
                print("发电机结束，开启变桨")
                self.signal_thread_number.emit(3)
                self.generator_thread.quit()
            elif li[0] == 3:
                self.over += 1
                # 变桨结束，开启变频
                print("变桨结束，开启变频")
                self.signal_thread_number.emit(4)
                self.pitch_thread.quit()
            elif li[0] == 4:
                self.over += 1
                # 变频结束，开启液压
                print("变频结束，开启液压")
                self.signal_thread_number.emit(5)
                self.converter_thread.quit()
            elif li[0] == 5:
                self.over += 1
                # 液压结束，开启传感器
                print("液压结束，开启传感器")
                self.signal_thread_number.emit(6)
                self.hydraulic_thread.quit()
            elif li[0] == 6:
                self.over += 1
                self.sensor_thread.quit()
            if self.over == 7:
                # 线程结束，开始写日志
                self.save_log()
                self.window.run_file_name_label.setText("None")
        elif self.mode == int(1):
            if li[0] == 0:
                print("manager")
                # self.model_manager.quit()
                self.over += 1
            elif li[0] == 1:
                print("gb")
                # self.gearbox_thread.quit()
                self.over += 1
            elif li[0] == 2:
                print("ge")
                # self.generator_thread.quit()
                self.over += 1
            elif li[0] == 3:
                print("pi")
                # self.pitch_thread.quit()
                self.over += 1
            elif li[0] == 4:
                print("co")
                # self.converter_thread.quit()
                self.over += 1
            elif li[0] == 5:
                print("hy")
                # self.hydraulic_thread.quit()
                self.over += 1
            elif li[0] == 6:
                print("se")
                # self.sensor_thread.quit()
                self.over += 1
            if self.over == 7:
                # 线程结束，开始写日志
                self.save_log()
                self.window.run_file_name_label.setText("None")

        print(self.over)

    def run(self):

        print("run")
        """
        :多进程
        """
        # 选择模式
        self.model_manager.start()
        self.window.statusBar.showMessage("正在读取数据请稍等！")
        self.window.run_file_name_label.setText(str(self.need_deal_data))

    # ----------------------->>> 进度条区
    def progress(self, dictionary):
        if "gearbox" in dictionary.keys():
            self.gb_process = dictionary['gearbox']
        elif "generator" in dictionary.keys():
            self.ge_process = dictionary['generator']
        elif "pitch" in dictionary.keys():
            self.pitch_process = dictionary['pitch']
        elif "converter" in dictionary.keys():
            self.co_process = dictionary['converter']
        elif "hydraulic" in dictionary.keys():
            self.hy_process = dictionary['hydraulic']
        elif "sensor" in dictionary.keys():
            self.se_process = dictionary['sensor']

        process = int((
                              self.ge_process + self.gb_process + self.pitch_process + self.co_process + self.hy_process + self.se_process) / 6)
        # process = int(self.gb_process)
        # print(process)
        self.window.progressBar.setValue(process)

    # # 3.3 >>> 退出事件
    def closeEvent(self, QCloseEvent):
        res = QMessageBox.question(self, '消息', '是否清除合并后的数据？', QMessageBox.Yes | QMessageBox.No,
                                   QMessageBox.No)  # 两个按钮是否， 默认No则关闭这个提示框
        if res == QMessageBox.Yes:
            QCloseEvent.accept()
            # shutil.rmtree('data')
        else:
            QCloseEvent.accept()
            # QCloseEvent.ignore()

    # ----------------------->>>测试区

    def save_log(self):
        """
        保存日志
        :return:
        """
        import csv

        try:
            file_name = r'/log/' + str(self.need_deal_data).split('/')[-1].split('.')[0]
        except IndexError:
            file_name = r'/log'
        try:
            f = open(os.getcwd() + file_name + r"/日志.txt", mode="w", encoding="gbk")
            f.write(self.log.window.summary_plainTextEdit.toPlainText())
            f.close()

            lines = self.log.window.summary_plainTextEdit.document().lineCount()
            f = open(os.getcwd() + file_name + r"/日志.csv", mode="w", encoding="gbk", newline='')
            csv_writer = csv.writer(f)
            csv_writer.writerow(['模型', '报警次数'])
            for i in range(lines):
                str1 = self.log.window.summary_plainTextEdit.document().findBlockByLineNumber(i).text()
                str1 = str(str1).split(':')[-1]
                result = str1.split('报警次数')
                csv_writer.writerow(result)
            f.close()

            f = open(os.getcwd() + file_name + r"/日志.txt", mode="a", encoding="gbk")
            f.writelines('\r\n')
            f.write(self.log.window.gb_plainTextEdit.toPlainText())
            f.writelines('\r\n')
            f.write(self.log.window.ge_plainTextEdit.toPlainText())
            f.writelines('\r\n')
            f.write(self.log.window.pitch_plainTextEdit.toPlainText())
            f.writelines('\r\n')
            f.write(self.log.window.co_plainTextEdit.toPlainText())
            f.writelines('\r\n')
            f.write(self.log.window.hy_plainTextEdit.toPlainText())
            f.writelines('\r\n')
            f.write(self.log.window.se_plainTextEdit.toPlainText())
            f.close()
            self.window.statusBar.showMessage("日志写入成功！")
        except Exception as e:
            self.window.statusBar.showMessage("日志写入失败！")

    def add_project(self):
        text, okPressed = QInputDialog.getText(self, "添加项目", "输入密码:", QLineEdit.Password, "")
        if okPressed and text == '12345':
            try:
                subprocess.call(['notepad.exe', 'config/tickets.json'])
            except IOError as e:
                QMessageBox.warning(self, '警告', '文件丢失', QMessageBox.Yes)
        elif okPressed and text != '12345':
            QMessageBox.warning(self, '警告', '密码错误！', QMessageBox.Yes)
        else:
            pass

    def refactor_project(self):
        text, okPressed = QInputDialog.getText(self, "添加项目", "输入密码:", QLineEdit.Password, "")
        if okPressed and text == '12345':
            try:
                subprocess.call(['notepad.exe', 'config/tickets.json'])
            except IOError as e:
                QMessageBox.warning(self, '警告', '文件丢失', QMessageBox.Yes)
        elif okPressed and text != '12345':
            QMessageBox.warning(self, '警告', '密码错误！', QMessageBox.Yes)
        else:
            pass

    def help(self):
        pass

    def about(self):
        msg = "预警模型1.0版本\n海上工程技术部"
        QMessageBox.about(self.window, "关于", msg)

    def test1(self):
        print(123)
        # python = sys.executable
        # os.execl(python, python, *sys.argv)

        # self.remove_plot()
        # self.window.child_terminal.window.show()


if __name__ == '__main__':
    app = QApplication([])
    win = Ui()
    win.window.show()
    app.exec_()
