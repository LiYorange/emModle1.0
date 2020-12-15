# -------------------------------------------------------------------------------
# Name:         LoadData
# Description:
# Author:       A07567
# Date:         2020/11/8
# Description:  按照标签点导入数据
# -------------------------------------------------------------------------------
import pandas as pd
import time


class ImportData:
    def __init__(self, import_file=None, tickets=None):
        if import_file:
            self.file_name = import_file
        if tickets:
            self.pd_read_csv_useecols = tickets

    def handle_import_data(self):
        """
        需要做一两个判断，
            第一：如果没有找到与传入的中文标签对应的英文标签则返回一个false，此判断在各个模块中进行处理
            第二：如果csv文件存在数据缺失现象，为了防止读取df错误，需要先筛选出能读取的数据，再添加丢失的数据，处理方法如下
                1. 读取整个csv的第一行(标签行)，用于与查找到的英文标签对比
                2. 创建一个miss_data_list 用于存放丢失数据的位置，保证插入数据时在指定位置
                3.创建一个exist_data_list 用于真正读取csv文件
                4.在读取好的csv文件中按照丢失数据的位置插入 numpy的NAN数据
        :return: 返回一个df
        """
        df = pd.DataFrame()
        df_head = pd.DataFrame()
        time1 = time.time()
        df_head = pd.read_csv(self.file_name, encoding='gbk', engine='python', nrows=0)

        def judge_miss(li):
            return list(df_head.columns.isin([li]))
        miss_data_list = []
        exist_data_list = []
        # 得到一个列表，如果列表包含true 则未丢失数据，如果全为false则丢失
        result = list(map(judge_miss, self.pd_read_csv_useecols))
        for i in range(len(result)):
            if not any(result[i]):
                # 如果不全为false,则缺失数据，记录此时英文标签的位置
                miss_data_list.append(i)
            else:
                exist_data_list.append(self.pd_read_csv_useecols[i])
        # 开始读取data
        data = pd.read_csv(self.file_name, usecols=exist_data_list, chunksize=10000, encoding='gbk',
                           engine='python')
        time2 = time.time()
        print("选择文件花费时间:", time2 - time1)
        # 将data 整合为df
        df = pd.concat(data, ignore_index=True)
        time3 = time.time()
        print("导入数据花费时间:", time3 - time2)
        return df


if __name__ == '__main__':
    l1 = ImportData('../60004036_20200930（外罗）.csv', ['风机编号', '时间', 'giWindTurbineOperationMode'])
    l1.handle_import_data()
