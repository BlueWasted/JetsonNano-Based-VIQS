#!coding=utf-8

import os
import difflib
import shutil
import pymysql

# '/home/ubuntu/Nano/txt'
# '/home/ubuntu/Nano/img'

# 获取绝对路径
abs_path = os.path.abspath(__file__)

# 获取目录路径
dir_name = os.path.dirname(abs_path)
path_t = os.path.join(dir_name, 'Nano/txt')
path_img = os.path.join(dir_name, 'Nano/img')
match_list = []
final_list = []


#   遍历函数
def ergodic(mode, path):
    fileList = os.listdir(path)
    if path[-3:].upper() == 'TXT':
        dir_build(os.path.join(path, 'Processed'))
    dir_build(os.path.join(path, 'Result'))
    for filename in fileList:
        if filename[-4:].upper() == '.TXT':
            pathTmp = os.path.join(path, filename)
            with open(pathTmp, 'r+', encoding='utf-8') as fp:
                linesList = fp.readlines()
            fp.close()

            # True则使用文本处理模式
            if mode:
                format_text(pathTmp, linesList)
                print('完成txt内容格式处理！')
            # False则为分析文本模式
            else:
                analyze_text(linesList, filename)
                if os.path.exists(os.path.join(path, 'Processed/'+filename)):
                    os.remove(os.path.join(path, 'Processed/'+filename))
                shutil.move(os.path.join(path, filename), os.path.join(path, 'Processed'))
    return fileList


#   将txt文件进行格式化处理
def format_text(pathTmp, linesList):
    with open(pathTmp, 'w+', encoding='utf-8') as fs:
        fs.seek(0, 0)
        for line in linesList:
            temp = '%'.join((line.split('_')))
            fs.write(temp.replace(":", "%", 3))
    fs.close()


#   建立对应的目录文件
def dir_build(Path):
    if not os.path.exists(Path):
        os.mkdir(Path)
        print("{0}目录已创建\n".format(Path))


#   判断识别的车牌字符相似度
def judgeSimi(license, set):
    for elem in set:
        if (difflib.SequenceMatcher(None, license[2], elem).quick_ratio()) >= 0.70:
            return False  # 有相似车牌
    return True  # 无相似车牌


#   获取列表的第二个元素
def takeSecond(elem):
    return elem[1]


#   分析并处理文本
def analyze_text(linesList, filename):
    datalist = []
    for line in linesList:  # 读取文件
        if line == '\n':
            continue
        else:
            temp = line.rstrip('\n')

            # 元组 例子：['car', '0.8', '粤WYL725', '0.971', '2022-03-23%16%56%34']
            tup = (temp.replace(":", "%", 2)).split('%', 4)
            # 根据车型和车牌置信度排除识别结果
            if float(tup[3]) + float(tup[1]) > 1.500:
                datalist.append(tup)
            # print(tup)
    #   按置信度降序排列
    datalist.sort(key=takeSecond, reverse=True)
    # print(datalist)
    license_set = set()
    license_list = []

    for data in datalist:
        if judgeSimi(data, license_set):
            license_list.append(data)
            license_set.add(data[2])
            # print(data[0])
            match_img_Text(data)
    with open(os.path.join(os.path.join(path_t, 'Result'), filename), 'w', encoding='utf-8') as fr:
        fr.seek(0, 0)
        for record in license_list:
            fr.write(str(record).strip('[]') + '\n')
    fr.close()


# print(license_list)


# 置信度筛选阈值应该设在0.75左右


def match_img_Text(data):
    temp_list = ergodic(False, path_img)
    for elem in temp_list:
        if data[4] == elem.strip('.jpg'):
            local_path = os.path.join(path_img, elem)
            #   恢复日期时间格式
            temp = data[4].replace('%', ' ', 1)
            temp = temp.replace('%', ':', 2)
            save_path = os.path.join(path_img, 'Result/'+elem)
            #   以[车型，置信度，车牌，置信度，日期时间，保存路径]为格式的元组
            if len(str(data[2]))>5:
                tuple_license = (data[0], data[1], data[2], data[3], temp, save_path)
                commit_data(tuple_license)
                final_list.append(tuple_license)
                if os.path.exists(save_path):
                    os.remove(save_path)
                shutil.move(local_path, os.path.join(path_img, 'Result'))
            else:
                continue


def commit_data(tuple_license):#写入数据库操作
    connect = pymysql.Connect(host='localhost', user='che_pai',
                              password='yourpassword', database='vehicledb', charset='utf8')
    cursor = connect.cursor(cursor=pymysql.cursors.DictCursor)
    sql = 'insert into info (typ, typ_conf, lic, lic_conf, date, time, path) values(%s, %s, %s, %s, %s, %s, %s);'
    typ = str(tuple_license[0])
    typ_conf = float(tuple_license[1])
    lic = str(tuple_license[2])
    lic_conf = float(tuple_license[3])
    # 将元组的日期时间元素拆分为日期和时间
    date = str(tuple_license[4]).split()[0]
    time = str(tuple_license[4]).split()[1]
    path = str(tuple_license[5])
    try:
        cursor.execute(sql, [typ, typ_conf, lic, lic_conf, date, time, path])
    except Exception as e:
        print('Insert error:', e)
        connect.rollback()
        # 报错反馈
    else:
        connect.commit()
        cursor.close()
        connect.close()


#if __name__ == '__main__':
def database():
    ergodic(True, path_t)  # True则使用文本处理模式
    ergodic(False, path_t)  # 使用遍历模式
    # print(final_list)
    if len(final_list):
        with open(os.path.join(dir_name, 'Nano/Match.txt'), 'a+') as ff:
            for elem in final_list:
                ff.seek(0, 0)
                ff.write(str(elem).strip('()') + '\n')
        ff.close()
        print('完成处理！')
