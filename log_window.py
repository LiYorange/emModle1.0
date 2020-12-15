# -------------------------------------------------------------------------------
# Name:         log_window
# Description:
# Author:       A07567
# Date:         2020/11/22
# Description:  
# -------------------------------------------------------------------------------
from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5 import uic


# 绘图


class UI(QWidget):
    def __init__(self):
        super(UI, self).__init__()
        self.window = uic.loadUi("UI/log.ui")

    # 重写绘图函数
    def paintEvent(self, event):
        pass


if __name__ == '__main__':
    app = QApplication([])
    win = UI()
    win.window.show()
    app.exec_()
