# -------------------------------------------------------------------------------
# Name:         seven_zip
# Description:
# Author:       A07567
# Date:         2020/12/1
# Description:  
# -------------------------------------------------------------------------------
import os
import shutil


class SevenZip:
    """
        调用7za.exe 进行解压

    """

    def __init__(self, files=None):
        """
        :param files: 需要解压的文件
        """
        if files is not None:
            self.files = files
        else:
            return

    def unpack(self):
        """
        生成一个data文件夹，用于存放解压数据，每次打开程序先清空该文件夹
        :return:
        """
        # 获得上一层目录
        # print(os.path.abspath(os.path.dirname(os.getcwd())))
        # data = os.path.abspath(os.path.dirname(os.getcwd())) + "\\data"
        # 主程序调用，不需要得到上层目录
        data = os.getcwd() + "\\data"
        # 不存在则创建，存在则清空
        if not os.path.exists(data):
            os.makedirs(data)
        else:
            shutil.rmtree(data)
            # os.mkdir(data)
        result = []
        for file in self.files:
            print(file)
            os.system("chcp 65001")

            cmd = str(os.getcwd() + '/plug/7za.exe x {} -o{}'.format(file, data))
            print(cmd)
            print(data)
            print("*" * 40)
            result.append(os.system(cmd))
        return result

if __name__ == '__main__':
    SevenZip()
