import time
import datetime #获得日期的时候使用
import requests
import pprint as pp
import re
import math
from bs4 import BeautifulSoup
from pymysql import *
from pathlib import Path #判断路径文件是否存在

###########################################################################
# 一些与业务不相关的函数
###########################################################################


def progress(percent, width=50):
    '''
    打印进度条

    :param percent: 进度百分比
    :param width: 进度条宽,默认50
    '''
    percent = percent * 100
    if percent >= 100:
        percent = 100
    show_str = ('[%%-%ds]' % width) % (int(width * percent / 100) * "#")  # 字符串拼接的嵌套使用
    print('\r%s %.2f%%' % (show_str, percent), end='')

    if percent == 100:
        print('\n')


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


    _database_info格式:
        _databsae_info = {
            'host':'XXX.XXX.XXX.XXX', #主机

            'port':3306, #端口

            'database':'XXXX',#数据库名称

            'user':'XXXXX',#用户名

            'password':'XXXXX',#密码

            'charset':'utf8' #字符编码
        }

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
                percent = i / _len
                i = i + 1
                progress(percent)
            except:
                print("写入数据库发生错误,可能主键冲突！自动跳过这条信息")
                continue
        print('\n')
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
                percent  = i / page_rst['page_num']
                progress(percent)
                time.sleep(0.1)
            print('\n')
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



def get_asc_id(_database_info):
    '''
    在数据库查询每个人的

    :param _database_info: 数据库信息

    _database_info格式:
        _databsae_info = {
            'host':'XXX.XXX.XXX.XXX', #主机

            'port':3306, #端口

            'database':'XXXX',#数据库名称

            'user':'XXXXX',#用户名

            'password':'XXXXX',#密码

            'charset':'utf8' #字符编码
        }

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
                    percent = (i+1) / count
                    progress(percent)

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
        percent = i / cut_num
        progress(percent)


    return sac_ids


def get_detailed_table_html(cookie,sac_ids_str):
    url = "http://jwxt.xsyu.edu.cn/eams/teach/grade/transcript/printer!report.action"
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
        s = requests.session()
        r = s.post(url,data=Hpostdata, headers=headers)
        r.raise_for_status()  # 如果不是返回状态码200，则产生异常
        r.encoding = 'utf-8'
        return r.text
    except:
        print("网页解析错误!")
        return 404

def get_detailed_table_info(cookie,asc_ids):
    # print("正在抓取学生成绩详细情况...")
    # for asc_id in asc_ids:
    #     html = get_detailed_table_html(cookie,asc_id)
    #     soup = BeautifulSoup(html, 'html.parser')
    #     soup.h2.string
    #
    #     print("写入文件...")
    #     with open(r'./总表.html', 'w', encoding='utf-8') as file_object:
    #         file_object.write(html)
    #     file_object.close()
    #     print("写入完成...")
    html = read_html()
    soup = BeautifulSoup(html, 'html.parser')
    soup = soup.body.contents

    flag = 0
    for content in soup:
        if content.string == "西安石油大学学生成绩总表":
            print(content.string)
            flag = 1
        else:
            if flag == 1:
                # 这里是学生基本信息
                print("学生信息{}".format(flag))
                pp.pprint(content)
                print("----------------------")
            if flag == 2:
                print("学生成绩{}".format(flag))
                pp.pprint(content)
                print("----------------------")
            flag = flag + 1




    return 0


def read_html(path=r'./总表.html'):
    my_file = Path(path)
    if my_file.is_file():
        # 指定的文件存在
        with open(path, 'r', encoding='utf-8') as f:
            html = f.read()
        f.close()
        return html
    else:
        print('文件不存在...')
        return 0



def xsyu_detailed(cookie, database_info):
    '''
    学生成绩详细列表

    :param cookie: 需要为管理员的cookie,格式为semester.id + JSESSIONID,注意如果没有semester.id默认会打印所有学生包括已经毕业的
    :param database_info: 数据库基本信息

    database_info格式:
        databsae_info = {
            'host':'XXX.XXX.XXX.XXX', #主机

            'port':3306, #端口

            'database':'XXXX',#数据库名称

            'user':'XXXXX',#用户名

            'password':'XXXXX',#密码

            'charset':'utf8' #字符编码
        }

    :return:暂时返回0
    '''

    # 先取得asc_id列表
    # asc_list = get_asc_id(database_info)
    # # 切片分组
    # if asc_list != 0:
    #     # 此时asc_list格式已经转换
    #     asc_list = cut_asc_id(asc_list)
    #     get_detailed_table_info(cookie,asc_list)
    #
    # else:
    #     return 0

    temp = 0
    temp_1 = 0
    get_detailed_table_info(temp,temp_1)
