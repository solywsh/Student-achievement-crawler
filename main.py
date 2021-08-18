from xsyu_sac.xsyu_sac import *

# cookie信息
cookie = "semester.id=142; JSESSIONID=XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
# 数据库信息
database_info = {
    'host': '',  # 主机
    'port': 3306,  # 端口
    'database': '',  # 数据库名称
    'user': '',  # 用户名
    'password': '',  # 密码
    'charset': 'utf8'  # 字符编码
}


def main():
    temp_time = datetime.datetime.strptime('00:00:00', '%H:%M:%S')
    time_beg = datetime.datetime.now()

    # 学生汇总列表
    xsyu_summary(cookie, database_info)
    # # 学生详细列表
    xsyu_detailed(cookie, database_info)

    time_now = datetime.datetime.now()
    time_spend = time_now - time_beg
    time_spend = temp_time + time_spend
    print("完成!共花费:{}".format(time_spend.strftime('%H:%M:%S')))


if __name__ == '__main__':
    main()
