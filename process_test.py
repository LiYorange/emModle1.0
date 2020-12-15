# -------------------------------------------------------------------------------
# Name:         process_test
# Description:
# Author:       A07567
# Date:         2020/12/9
# Description:  
# -------------------------------------------------------------------------------
import multiprocessing
from PyQt5.QtCore import QObject


class Test(QObject):
    def __init__(self):
        super(Test, self).__init__()
        self.run()

    def run(self):
        p = multiprocessing.Process(target=self.add, args=())
        p.start()

    def add(self):
        print(self.a + self.b)


if __name__ == '__main__':
    one = Test()
