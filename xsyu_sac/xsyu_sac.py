import json
import time
import datetime #获得日期的时候使用
import multiprocessing as mp #多进程
from multiprocessing import Pool
import pprint as pp
import re
import math
import os
from pymysql import *
from pathlib import Path #判断路径文件是否存在
import random #用来生成随机数
# 爬虫请求时需要的库
import requests
import bs4 #isinstance(tr,bs4.element.Tag)
from bs4 import BeautifulSoup
# 将python的requests库协议改为HTTP/1.0 ，使用HTTP/1.1教务系统可能会发生不兼容的情况
import http.client
http.client.HTTPConnection._http_vsn = 10
http.client.HTTPConnection._http_vsn_str = 'HTTP/1.0'


###########################################################################
# 一些与业务不相关的函数
###########################################################################


def progress(place, end_place, time_str="", width=50):
    '''
    打印进度条

    :param place: 目前的进度位置，类型为数字，不能为0
    :param end_place: 结束位置，类型为数字
    :param time_str: 可选择打印实花费时间和剩余时间，建议配合get_remaining_time使用
    :param width: 进度条宽度

    '''
    percent = place / end_place
    percent = percent * 100
    if percent >= 100:
        percent = 100
    show_str = ('[%%-%ds]' % width) % (int(width * percent / 100) * "#")  # 字符串拼接的嵌套使用
    print('\r%s %.2f%% %s' % (show_str, percent , time_str), end='')

    if percent == 100:
        print('\n')

def print_remaining_time(time_beg, time_now, place, end_place):
    '''
    直接打印花费时间，剩余时间按

    :param time_beg: 开始的时间，time_beg = datetime.datetime.now()获得
    :param time_now: 现在的时间，time_now = datetime.datetime.now()获得
    :param place: 现在进度的位置，类型为数字，不能为0
    :param end_place: 结束的位置，类型为数字
    :return:
    '''
    #

    # 定义空时间
    tmep_time = datetime.datetime.strptime('00:00:00','%H:%M:%S')
    # 计算进度
    persent = place / end_place
    # 计算花费时间
    delta = time_now - time_beg
    # 计算剩余时间
    remnant = delta/persent - delta
    # 格式化花费时间
    delta = tmep_time + delta
    # 格式化剩余时间
    remnant = tmep_time + remnant
    print('\r %s  预计还剩: %s' % (delta.strftime('%H:%M:%S'),remnant.strftime('%H:%M:%S')),end='')

def get_remaining_time(time_beg, time_now, place, end_place):
    '''
    返回花费时间，剩余时间按

    :param time_beg: 开始的时间，time_beg = datetime.datetime.now()获得
    :param time_now: 现在的时间，time_now = datetime.datetime.now()获得
    :param place: 现在进度的位置，类型为数字，不能为0
    :param end_place: 结束的位置，类型为数字
    :return:
    '''

    # 定义空时间
    tmep_time = datetime.datetime.strptime('00:00:00', '%H:%M:%S')
    # 计算进度
    persent = place / end_place
    # 计算花费时间
    delta = time_now - time_beg
    # 计算剩余时间
    remnant = delta / persent - delta
    # 格式化花费时间
    delta = tmep_time + delta
    # 格式化剩余时间
    remnant = tmep_time + remnant

    rst = ' 花费: %s  预计还剩: %s' % (delta.strftime('%H:%M:%S'),remnant.strftime('%H:%M:%S'))
    return rst

def waiting(times=3, sec=1, max_symbol_num=5):
    '''
    手动等待,打印等待效果

    :param times: 等待次数,默认3
    :param sec: 每次间隔时间,默认1秒
    :param max_symbol_num: 动画圆点最大个数,默认5个
    '''
    symbol = '.'
    for i in range(times + 1):
        print('\rwaiting%s' % symbol, end='')
        symbol = symbol + '.'
        if symbol == ('.' * (max_symbol_num + 1)):
            symbol = '.'
        time.sleep(1)
    print('\n')

def waiting_s(percent,
              words='',max_symbol_num=4,symbol='.'):
    '''
    被动等待,打印动画

    :param percent: 进度百分比
    :param words: 动画字符前跟的文字,默认为空
    :param max_symbol_num: 最大动画字符数量,默认为4
    :param symbol: 动画符号,默认为'.'
    '''

    # 先取余,余数为打印符号的数量
    percent = percent * 100
    num = percent % max_symbol_num
    symbol = symbol * num
    print('\r%s%s' % (words,symbol), end='')

    if percent >= 100:
        print('\n')

def get_time():
    '''
    获得格式为2021-08-11的时间格式,访问请求时用
    :return: 返回'2021-08-11'字符rst
    '''
    i = datetime.datetime.now()
    rst = str(i.year)+'-'+str(i.month)+'-'+str(i.day)
    return rst




###########################################################################
# 以下为学生汇总信息相关函数
###########################################################################


def get_page_num(html,pageSize=100):
    '''
    抓取有多少*有效*的学生，并且计算多少页

    :param html: 网页文本
    :param pageSize: 未来抓取总表信息的时候,每页学生数量,*不建议更改*,默认100
    :return: 返回字典page_dict，包含:学生总数'stu_num'，页数'page_num',异常状态返回404,如网页404,cookie失效等
    '''
    if html != 404:
        print("抓取学生总数...")
        rst = re.search(r"1,20,[0-9]*",html)
        try:
            list = rst.group(0).split(",")
            print("有效学生总数为: " + list[2])
            #计算页数，逢小数点进1
            page_num  = int(list[2])/pageSize
            page_num = math.ceil(page_num)
            page_dict = {
                'stu_num': int(list[2]),
                'page_num': page_num
            }
            return page_dict
        except:
            print("cookie可能失效!请先更换cookie")
            return 404
    else:
        print("网页404！")
        return 404

def get_summary_table_html(cookie,pageNO=1,pageSize=20):
    '''
    解析学生汇总信息网页

    :param cookie: 需要为管理员的cookie,格式为semester.id + JSESSIONID,注意如果没有semester.id默认会打印所有学生包括已经毕业的
    :param pageNO: 第几页,默认1
    :param pageSize: 设置每页多少个学生的信息,只能为10,20,30,40,50,70,100,200,500,1000,默认20
    :return: 返回解析之后的文本r.text，如果解析错误，返回404
    '''
    url = "http://jwxt.xsyu.edu.cn/eams/teach/grade/transcript/printer!stdList.action"
    headers = {
        'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
        'Cache-Control': 'max-age=0',
        'Connection': 'keep-alive',
        'cookie': cookie,
        'Upgrade-Insecure-Requests': '1',
        'host': 'jwxt.xsyu.edu.cn',
        'user-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 Safari/537.36 Edg/92.0.902.67'
    }
    Hpostdata = {
        'orderBy': 'std.code asc',
        'std.project.id': 1,
        'stdActive': 1,
        'pageNo': pageNO,
        'pageSize': pageSize
    }
    try:
        s = requests.session()
        r = s.post(url,data=Hpostdata, headers=headers)
        r.raise_for_status()  # 如果不是返回状态码200，则产生异常
        r.encoding = 'utf-8'
        return r.text
    except:
        return 404

def get_summary_table_info(html):
    '''
    解析总表信息

    :param html: 总表的网页
    :return: 列表info_list,里边包含将每个学生的信息字典info_dict,如果访问过快会提示"访问过快，触发教务系统限制:请不要过快点击"，并且返回0
    '''
    rst = re.search(r"请不要过快点击", html)
    if rst == None:
        info_list = []
        soup = BeautifulSoup(html,'html.parser')
        for tabels in soup.find_all('table',class_="gridtable"):
            for table in tabels.contents[3].contents:
                # 判断这次的列表是否有效
                if len(table) < 5:
                    continue
                else:
                    # 匹配专业方向
                    if table.contents[9].string==None:
                        prof_d = "无"
                    else:
                        prof_d = table.contents[9].string
                    #匹配教务系统的顺序id
                    esa_id = int(re.search(r"[0-9]+", str(table)).group(0))
                    info_dict = {
                        "esa_id" : esa_id,
                        "stuid" : table.contents[1].a.string,
                        "name": table.contents[2].contents[1].string,
                        "gender": table.contents[4].string, #性别
                        "grede": int(table.contents[5].string), #年级
                        "faculty": table.contents[6].string, #学院
                        "major": table.contents[7].string, #专业
                        "_class": table.contents[8].string,  # 班级
                        "prof_d": prof_d  # 专业方向
                    }
                    info_list.append(info_dict)
        return info_list
    else:
        print("访问过快，触发教务系统限制:请不要过快点击")
        return 0

def insert_summary_database(_lists, _database_info):
    '''
    将学生汇总信息的列表写入数据库

    :param _lists: 写入学生信息的列表
    :param _database_info: 数据库基本信息

    :return: 正常返回0，写入发生异常返回-1
    '''
    try:
        print("连接数据库...")
        # 创建Connection连接
        conn = connect(host=_database_info['host'], port= _database_info['port'],
                       database=_database_info['database'],user=_database_info['user'],
                       password=_database_info['password'],charset=_database_info['charset'])
        cs1 = conn.cursor()# 获得Cursor对象
        print("写入数据...")
        i = 1
        _len = len(_lists)
        #定义sql语句模版
        sql = "insert into students_summary_table values(%s,%s,%s,%s,%s,%s,%s,%s,%s);"
        for _list in _lists:
            try:
                param = (_list["esa_id"], _list["stuid"], _list["name"], _list["gender"],
                         _list["grede"], _list["faculty"], _list["major"], _list["_class"], _list["prof_d"])
                count = cs1.execute(sql, param)
                # 打印进度
                i = i + 1
                progress(i,_len)
            except:
                print("写入数据库发生错误,可能主键冲突！自动跳过这条信息")
                continue
        conn.commit()  # 提交之前的操作，如果之前已经之执行过多次的execute，那么就都进行提交
        cs1.close()# 关闭Cursor对象
        conn.close()# 关闭Connection对象
    except:
        print("数据库发生错误！请检查填写的信息！\n")
        return -1

    return 0

def xsyu_summary(cookie, database_info,
                 get_table=True, insert_table=True):

    '''
    抓取学生成绩总表

    :param cookie: 需要为管理员的cookie,格式为semester.id + JSESSIONID,注意如果没有semester.id默认会打印所有学生包括已经毕业的
    :param database_info: 数据库基本信息
    :param get_table: 是否抓取学生汇总
    :param insert_table: 是否插入数据库，如果不插入，则返回汇总列表lists

    database_info格式:
        databsae_info = {
            'host':'XXX.XXX.XXX.XXX', #主机

            'port':3306, #端口

            'database':'XXXX',#数据库名称

            'user':'XXXXX',#用户名

            'password':'XXXXX',#密码

            'charset':'utf8' #字符编码
        }

    :return: 如果插入数据库，成功之后返回0,如果不插入，则返回汇总列表lists
    '''
    #先解析一下网页，计算需要翻多少页
    summary_table_html = get_summary_table_html(cookie)
    page_rst = get_page_num(summary_table_html)

    if page_rst!=404:
        if get_table == True:
            waiting()  # 过快访问教务系统会显示“请不要过快点击”,先等待

            lists = [] #创建列表用于存储所有学生信息
            print("抓取学生汇总信息中...")
            for i in range(1,page_rst['page_num']+1):
                summary_table_html = get_summary_table_html(cookie,i,100)
                # 得到含有学生信息的列表
                list_temp = get_summary_table_info(summary_table_html)
                lists = lists + list_temp
                #打印进度
                progress(i,page_rst['page_num'])
                time.sleep(0.1)
            #如果不写入数据库就返回信息的列表_list
            if insert_table == True and lists != 0:
                insert_summary_database(lists, database_info)
                return 0
            else:
                return lists
    return 0



###########################################################################
# 以下为学生成绩详细信息相关函数
###########################################################################

def do_not_access_fast(html):
    '''
    "请不要过快点击",顾名思义，请求过快得到的网页为”请不要过快点击“，内容为空的，需要等会儿重新请求

    :param html:
    :return:
    '''
    rst = re.search(r"请不要过快点击", html)
    if rst == None:
        return 0
    else:
        time.sleep(4)
        return -1



def get_asc_id(_database_info):
    '''
    在数据库查询每个人的

    :param _database_info: 数据库信息
    :return: ,返回asc_id列表,查询失败返回0
    '''
    try:
        # 创建Connection连接
        conn = connect(host=_database_info['host'], port=_database_info['port'],
                       database=_database_info['database'], user=_database_info['user'],
                       password=_database_info['password'], charset=_database_info['charset'])
        # 获得Cursor对象
        cs1 = conn.cursor()
        print("读取数据库asc_id信息...")
        try:
            # 执行select语句，并返回受影响的行数：查询一条数据
            count = cs1.execute('select * from students_summary_table')

            if count != 0:
                # 生成列表
                asc_id_list = []
                for i in range(count):
                    # 获取查询的结果,返回的结果是元组
                    result = cs1.fetchone()
                    # 将结果添加进列表
                    asc_id_list.append(result[0])

                    # 打印进度
                    progress(i+1,count)

                # 关闭Cursor对象
                cs1.close()
                conn.close()
                return  asc_id_list

            else:
                print("数据库结果为0,请检查汇总列表时候有学生的信息!")
                return 0
        except:
            print("数据库查询错误,请检查是否存在数据库!")
            return 0
    except:
        print("数据库连接发生错误,请检查数据库配置!")
        return 0

def cut_asc_id(_sac_id_list,step=20):
    '''
    切片asc_id,每组以字符的形式传入列表

    :param _sac_id_list: 学生sac_id列表
    :param step: 步长,默认20

    :return: 返回分组并且合成字符之后的列表
    '''
    cut_num = len(_sac_id_list)/step
    cut_num = math.ceil(cut_num) #有小数位进一

    print("asc_id分组...")
    beg = 0 #定义第一个列表的开始
    end = step #定义第一个列表的结束
    sac_ids = []
    for i in range(1,cut_num+1):
        # 判断是否为最后一组，如果为最后一组，那么切片结尾为列表的最后
        if end >= len(_sac_id_list):
            end = len(_sac_id_list)

        sac_str_temp = '' #定义一个临时字符，把一组数字写入里边
        for temp in _sac_id_list[beg:end:]:
            sac_str_temp = sac_str_temp + str(temp)
            if temp != _sac_id_list[end-1]:
                sac_str_temp =  sac_str_temp + ','

        sac_ids.append(sac_str_temp)

        # 移动位置
        beg = end
        end = end + step

        # 打印进度
        progress(i,cut_num)


    return sac_ids

def get_detailed_table_html(cookie,sac_ids_str):
    '''
    请求学生详细网页

    :param cookie: 管理员账号的cookie
    :param sac_ids_str: sac id,一次应该是100个,提前转换成字符

    :return: 如果请求成功返回网页内容,失败则返回404
    '''
    url = "http://jwxt.xsyu.edu.cn/eams/teach/grade/transcript/printer!report.action"
    headers = {
        'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
        'Cache-Control': 'max-age=0',
        'Connection': 'keep-alive',
        'Cookie': cookie,
        'Upgrade-Insecure-Requests': '1',
        'Host': 'jwxt.xsyu.edu.cn',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 Safari/537.36 Edg/92.0.902.67',
        'Referer':'http://jwxt.xsyu.edu.cn/eams/teach/grade/transcript/printer!stdList.action',
        'Content-Length':'570'
    }
    # 得到发送的日期
    postime = get_time()
    Hpostdata = {
        'orderBy': 'std.code asc',
        'reportSetting.template': 'default',
        'reportSetting.gradeFilters': 'passGrade',
        'reportSetting.pageSize': 100,
        'reportSetting.fontSiz': 1,
        'reportSetting.printGpa': 1,
        'reportSetting.published': 1,
        'reportSetting.order.property': 'semester.beginOn',
        'reportSetting.order.ascending': 1,
        'reportSetting.gradeType.id': 3,
        'reportSetting.printBy': '',
        'reportSetting.printAt': postime,
        'template': 'grade.stdTotalGrade',# 'grade.stdTotalGrade','grade.stdArchivesGrade'
        'std.ids': sac_ids_str
    }
    try:
        while(True):
            s = requests.session()
            r = s.post(url,data=Hpostdata, headers=headers,stream=True)
            r.raise_for_status()  # 如果不是返回状态码200，则产生异常
            r.encoding = 'utf-8'
            # 防止访问过快
            if do_not_access_fast(r.text) != 0:
                continue
            else:
                return r.text
    except:
        print("\n网页解析错误!")
        return 404

def get_stu_basic_info(html):
    '''
    获得表格中学生的学号stuid，姓名name，班级class

    :param html: 传入的网页，建议为文本
    :return: 返回信息的字典
    '''
    soup = BeautifulSoup(html, 'html.parser')
    _list = []
    for child in soup.find_all('td'):
        _list.append(str(child))
    try:
        class_ = re.search(r"[^(<td>)(</td>)(班级:)]+", _list[2]).group(0)
    except:
        class_ = ''
    basic_info = {
        "stuid": re.search(r"[^(<td>)(</td>)(学号:)]+", _list[0]).group(0),
        "name": re.search(r"[^(<td>)(</td>)(姓名:)]+", _list[1]).group(0),
        "class": class_
    }
    return basic_info

def get_stu_detail_info(html):
    '''
    解析网页内容,洗数据

    :param html: 网页文本
    :return: 返回解析完成得到的内容
    '''
    soup = BeautifulSoup(html, 'html.parser')

    detail_info = [] #用来存储学生所有信息
    flag = 0 #标识排除第一行信息
    semester = "" #标志学期
    for child in soup.find_all('tr'):
        if flag == 0:
            flag = 1
            continue #跳过表格第一个

        _list = [] # 定义一个临时的列表用来存储信息
        for td in child.find_all('td'):
            _list.append(str(td.string).replace("\n","").replace("\t","").replace("\r",""))

        try:
            # 选出课程病编号,例如：A010340
            courses_id = re.search(r"\([A-Z][0-9]+\)", _list[1]).group(0)
            # 判断学年字段
            if _list[0] == '\xa0':
                _list[0] = semester
            else:
                semester = _list[0]

            _info = {
                "school_year": _list[0], #学期学年
                "courses_id": courses_id.replace("(","").replace(")",""), #课程/环节 id
                "courses": _list[1].replace(courses_id,""), #课程/环节 名称
                "courses_p": _list[2], #课程/环节 性质
                "score": _list[3], #分数、等级
                "credit": float(_list[4]), #学分
                "gp": float(_list[5]), #绩点
                "ac": float(_list[6]), #学分绩点
                "nos": _list[7], #修读性质
                "remark": _list[8].replace(" ",""), #备注
            }
            detail_info.append(_info)
        except:
            pass

    return detail_info

def insert_detail_database(_lists,_database_info):
    '''
    将数据写入数据库

    :param _lists: 数据的列表
    :param _database_info: 数据库信息
    :return: 成功返回0,失败返回-1
    '''

    try:
        # 创建Connection连接
        conn = connect(host=_database_info['host'], port= _database_info['port'],
                       database=_database_info['database'],user=_database_info['user'],
                       password=_database_info['password'],charset=_database_info['charset'])
        cs1 = conn.cursor()# 获得Cursor对象
        # place = 1
        # _len = end_place(_lists)
        #定义sql语句模版
        # print("正在插入数据库...")
        sql = "insert into students_detailed_table values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s);"
        for _list in _lists:
            # 拆分
            for courses in _list["stu_detail_info"]:
                try:
                    param = ("default",
                             _list["stu_basic_info"]["stuid"],
                             _list["stu_basic_info"]["name"],
                             _list["stu_basic_info"]["class"],
                             courses["school_year"],
                             courses["courses_id"],
                             courses["courses"],
                             courses["courses_p"],
                             courses["score"],
                             courses["credit"],
                             courses["gp"],
                             courses["ac"],
                             courses["nos"],
                             courses["remark"],
                             )
                    count = cs1.execute(sql, param)
                except:
                    print("写入数据库发生错误,可能主键冲突！自动跳过这条信息")
                    continue

        conn.commit()  # 提交之前的操作，如果之前已经之执行过多次的execute，那么就都进行提交
        cs1.close()# 关闭Cursor对象
        conn.close()# 关闭Connection对象
        return 0
    except:
        print("数据库发生错误！请检查填写的信息！\n")
        return -1

def read_file(path,type=0):
    '''
    读取文件信息

    :param path: 文件路径
    :param type: 文件类型,type=0时读取html文本,其他的时候读取json文件并转换成字典

    :return:  成功返回读取到的没内容,失败返回0
    '''
    my_file = Path(path)
    if my_file.is_file():
        # 指定的文件存在
        with open(path, 'r', encoding='utf-8') as f:
            if type == 0:
                file_contents = f.read()
            else:
                file_contents = json.load(f)
        f.close()
        return file_contents
    else:
        print('\n文件不存在...')
        return 0

def get_html_for_file(_cookie,_asc_ids,_file_list,_process_NO):
    '''
    批量获取网页并储存到文件里

    :param _cookie: 管理员的cookie
    :param _asc_ids: asc_id列表
    :param _file_list: 文件序列，用来命名文件
    :param _process_NO: 进程数
    :return: 成功返回0
    '''
    time.sleep(random.randint(2,5)) #
    i = 1
    _len = len(_asc_ids)
    time_beg = datetime.datetime.now()
    process_str = "进程: {}".format(_process_NO + 1)
    for asc_id in _asc_ids:
        html = get_detailed_table_html(_cookie, asc_id)
        if html == 404:
            print("进程{}请求网页失败!位置为{}".format(_process_NO,i))
            return i
        with open(r'./data/html/_detail_table_html_' + str(_file_list[i-1]) + '.html', 'w', encoding='utf-8') as file_object:
            file_object.write(html)
        file_object.close()
        # 打印进度
        time_now = datetime.datetime.now()
        # try:
        progress(i, _len,process_str + get_remaining_time(time_beg, time_now, i, _len))
        # except:
        #     print("请求发生错误,错误位置为{},请检查对应文件时候为空,可能是cookie失效,进程号{}".format(i,_process_NO))
        #     return -1
        i = i + 1
        time.sleep(2)
    return 0



def analyze_html_for_file(_id_list,_process_NO):
    '''
    从文件解析html

    :param _id_list: 分配的文件名列表
    :param _process_NO: 进程数
    :return: 成功返回0
    '''

    _length = len(_id_list)
    time_beg = datetime.datetime.now()
    process_str = "进程: {}".format(_process_NO + 1)
    place = 1

    for i in _id_list:
        html = read_file(r'./data/html/_detail_table_html_' + str(i) + '.html')
        soup = BeautifulSoup(html, 'html.parser')

        flag = 0
        sbi_dict = {}
        sdi_list = []
        all_list = []

        for content in soup.body:
            if content.string == "西安石油大学学生成绩总表":
                flag = 1
                continue
            if flag == 1:
                # 由于学生基本信息和成绩都紧挨着标题“西安石油大学学生成绩总表”，并且类型都为bs4.element.Tag
                # 我们用这种方式将其区分
                if isinstance(content, bs4.element.Tag):
                    # 这里是学生基本信息
                    sbi_dict = get_stu_basic_info(str(content))
                    flag = 2
                    continue
            if flag == 2:
                if isinstance(content, bs4.element.Tag):
                    # 这里是学生的详细的信息
                    sdi_list = get_stu_detail_info(str(content))
                    flag = 0
            # 将这个学生的所有信息汇总到一个表里边
            if len(sdi_list) != 0 and len(sbi_dict) != 0:
                all_info = {
                    "stu_basic_info": sbi_dict,
                    "stu_detail_info": sdi_list
                }
                all_list.append(all_info)
                sbi_dict = {} #清空字典
                sdi_list = [] #清空列表
                if all_info["stu_basic_info"]["name"] == "王世浩" :
                    print(all_info)
                    print("位置为{},进程{}".format(i,_process_NO))

        with open(r'./data/list/_detail_table_list_' + str(i) + '.json', 'w', encoding='utf-8') as file_object:
            file_object.write(json.dumps(all_list, indent=4, ensure_ascii=False))
        file_object.close()

        # 打印进度
        time_now = datetime.datetime.now()
        progress(place, _length, process_str + get_remaining_time(time_beg, time_now, place, _length))
        place = place + 1

    return 0

def insert_database_from_file(_id_list,_database_info,_process_NO):
    '''
    读取解析完成的文件信息，插入数据库

    :param _id_list: 分配文件名列表
    :param _database_info: 数据库信息
    :param _process_NO: 进程数
    :return: 成功返回0
    '''

    _length = len(_id_list)
    time_beg = datetime.datetime.now()
    place = 1

    process_str = "进程: {}".format(_process_NO+1)

    for i in _id_list:

        file_info = read_file(r'./data/list/_detail_table_list_' + str(i) + '.json',1)
        # all_list = json.loads(list_)
        # 插入数据库
        insert_detail_database(file_info, _database_info)
        time_now = datetime.datetime.now()
        progress(place,_length, process_str + get_remaining_time(time_beg, time_now, place, _length))
        place = place + 1

    return 0

def allocation_process(_lists,_process_num):
    '''
    根据进程分配任务

    :param _lists: 需要分配任务的列表
    :param _process_num: 进程数
    :return:
    '''

    all_list = [] #创建一个总列表用来返回
    _lenght = len(_lists)
    # 几个进程往总的列表里边添加几个子列表
    for i in range(_process_num):
        _process_list = []
        all_list.append(_process_list)

    i = 1
    for _list in _lists:
        flag =   i % _process_num # flag = 顺序数 余 进程数
        i = i + 1
        all_list[flag].append(_list)

    return all_list




def operate_detailed_table_info(cookie, asc_ids, database_info,process_num = 6,
                                _get_html=True,_analyze_html=True,_insert_database=True):

    '''
    学习成绩信息业务操作

    :param cookie: 教务系统管理员的cookie
    :param asc_ids: asc_id 列表
    :param database_info: 数据库信息
    :param process_num: 进程数，默认为6
    :param _get_html: 是否请求网页
    :param _analyze_html: 是否解析网页
    :param _insert_database: 是否插入数据库
    :return: 成功返回0
    '''

    _len = len(asc_ids)
    # print("正在抓取学生成绩详细情况,会有多轮解析网页和数据库操作，时间会很长请去干别的事情...")
    # waiting(5)
    ################################################################################
    if _get_html == False:
        print("正在请求网页并且保存...")
        path = r'./data/html'
        if os.path.isdir(path):
            print("发现存在./data/html目录,正在删除")
            ls = os.listdir(path)
            for i in ls:
                c_path = os.path.join(path, i)
                if os.path.isdir(c_path):
                    del_file(c_path)
                else:
                    os.remove(c_path)
            os.rmdir(path)
            print("重新创建./data/html目录")
            os.mkdir(path)

        print("分配多进程任务...进程数:{}".format(process_num))
        get_html_process_list = allocation_process(asc_ids, process_num)  # 给每个进程分配需要请求的asc id列表
        l = []
        for i in range(1, _len + 1):
            l.append(i)
        get_html_process_file_list = allocation_process(l, process_num) # 分配插入文件命名位置

        p = Pool(process_num)
        for i in range(process_num):
            p.apply_async(get_html_for_file, args=(cookie,get_html_process_list[i],get_html_process_file_list[i], i))
        p.close()
        p.join()

        # p = []
        #
        # for i in range(process_num):
        #     print("正在生成进程{}".format(i+1))
        #     waiting(4)  # 等待防止过快请求
        #     p.append(mp.Process(target=get_html_for_file, args=(cookie,get_html_process_list[i],get_html_process_file_list[i], i)))
        #     p[i].start()
        #
        # for i in range(process_num):
        #     p[i].join()

    #################################################################################
    if _analyze_html == False:
        print("所有网页保存完成,现在开始解析数据..")
        path = r'./data/list'
        if os.path.isdir(path):
            print("发现存在./data/list目录,正在删除")
            ls = os.listdir(path)
            for i in ls:
                c_path = os.path.join(path, i)
                if os.path.isdir(c_path):
                    del_file(c_path)
                else:
                    os.remove(c_path)
            os.rmdir(path)
            print("重新创建./data/list目录")
            os.mkdir(path)

        print("分配多进程任务...进程数:{}".format(process_num))
        l = []
        for i in range(1, _len + 1):
            l.append(i)
        analyze_process_list = allocation_process(l, process_num)  # 先分配任务

        # p = []
        # for i in range(process_num):
        #     p.append(mp.Process(target=analyze_html_for_file, args=(analyze_process_list[i],i)))
        #     p[i].start()
        # for i in range(process_num):
        #     p[i].join()

        p = Pool(process_num)
        for i in range(process_num):
            p.apply_async(analyze_html_for_file, args=(analyze_process_list[i],i))
        print("等待解析结束...")
        p.close()
        p.join()

    #################################################################################
    if _insert_database == True:
        print("解析完成正在写入数据库...")
        path = r'./data/list'
        if os.path.isdir(path):
            print("分配多进程任务,进程数:{}".format(process_num))
            l = []
            for i in range(1,_len+1):
                l.append(i)
            database_process_list = allocation_process(l,process_num) #先分配任务

            p = []
            for i in range(process_num):
                p.append(mp.Process(target=insert_database_from_file, args=(database_process_list[i],database_info,i)))
                p[i].start()
            for i in range(process_num):
                p[i].join()

            # p = Pool(process_num)
            # for i in range(process_num):
            #     p.apply_async(insert_database_from_file, args=(database_process_list[i],database_info,i))
            # print("等待写入结束...")
            # p.close()
            # p.join()
            #

            print("写入完成")

        else:
            print("文件不存在")
            return -1
    print("结束")
    return 0

def xsyu_detailed(cookie, database_info,process_num = mp.cpu_count(),
                  get_html=True,analyze_html=True,insert_database=True):
    '''
    学生成绩详细列表

    :param cookie: 需要为管理员的cookie,格式为semester.id + JSESSIONID,注意如果没有semester.id默认会打印所有学生包括已经毕业的
    :param database_info: 数据库基本信息
    :param process_num: 进程数量,默认为CPU内核数量
    :param get_html: 是否请求网页
    :param analyze_html: 是否解析网页
    :param insert_database: 是否写入数据库

    database_info格式:
        databsae_info = {
            'host':'XXX.XXX.XXX.XXX', #主机

            'port':3306, #端口

            'database':'XXXX',#数据库名称

            'user':'XXXXX',#用户名

            'password':'XXXXX',#密码

            'charset':'utf8' #字符编码
        }

    :return:成功回0
    '''

    #先取得asc_id列表
    asc_list = get_asc_id(database_info)
    # 切片分组
    if asc_list != 0:
        # 此时asc_list格式已经转换
        asc_list = cut_asc_id(asc_list,100)
        flag = operate_detailed_table_info(cookie, asc_list, database_info,process_num,
                                           get_html,analyze_html,insert_database)

    else:
        return 0


