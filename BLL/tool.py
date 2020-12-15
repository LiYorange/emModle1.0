# -------------------------------------------------------------------------------
# Name:         tool
# Description:
# Author:       A07567
# Date:         2020/11/12
# Description:  抽象提取代码整合为工具
# -------------------------------------------------------------------------------
import os
# 回收内存
import gc


def duration_calculation_to_csv(tickets, df, duration, fault_file=None):
    # 两个功能，判断是否故障，是否生成故障文件
    # df.to_csv("df_h.csv", sep=',', encoding='gbk', index=0)
    # 故障时间节点,用于显示的字符串
    fault_time_list = []
    # 故障时间序列，用于返回
    fault_time = []
    """
    :param tickets: 标签名称
    :param df: DataFrame
    :param duration: 持续时长，大于持续时长返回false,否则true
    :param fault_file: 故障文件名
    :return: 故障返回false,否则true
    """

    """
    1. 添加一列，用于时间做差
    2. 将所添加列的时间差为1秒的数值设置为0
    3. 按照所添加的列进行分组
    4. 对分组按照
    5. 
        如果故障：
            生成故障文件夹
            生成故障文件
            返回假和故障时间节点
        否则
            返回真和空
        
    """
    df["second"] = df['time'].diff()
    # 将做差转化为秒
    df["second"] = df["second"].apply(lambda x: x.seconds)
    df['new'] = df["second"].diff().ne(0).cumsum()
    df2 = df.groupby('new').count()
    df2 = df2[df2['second'] > duration]
    if not df2.empty:
        index = df2.index.tolist()
        for item in index:
            d = df[df['new'] == item]
            t = d['time'].astype('str').tolist()
            fault_time_list.append(f'{t[0]} ==> {t[-1]}')
            fault_time.append(t)

        ds = df[df.new.isin(index)]
        if fault_file is not None:
            if not os.path.exists(os.getcwd() + "\\log\\" + fault_file.split("/")[0]):
                file_path = os.getcwd() + "\\log\\" + fault_file.split("/")[0]
                os.makedirs(file_path)
                # print(file_path)
                # print(fault_file.split("/")[1])
            ds.to_csv(os.getcwd() + "\\log\\" + fault_file.split("/")[0] + "/" + fault_file.split("/")[1],
                      sep=',', encoding='gbk', index=0)
        else:
            # 如果不生成故障文件则返回 故障 故障时间序列 故障时间显示文本
            return False, fault_time, fault_time_list
        # 回收内存
        del df
        del tickets
        del df2
        del ds
        gc.collect()

        return False, fault_time_list
    else:
        # 回收内存
        del df
        del tickets
        del df2
        gc.collect()
        return True, fault_time_list
