from xsyu_sac.xsyu_sac import *

# cookie信息
cookie = {
    # semester.id学期代码,只会抓取这学期有效的人数
    # 注意，如果直接以'JSESSIONID=XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX'形式传入students_summary_table(_cookie,database_info)
    # 而不传入semester.id，那么将会爬取数据库所有学生的信息
    'semester.id': 122,
    'JSESSIONID': '7BB471BC4B03C9BE297A0DC55EC15949.-node1'
}

# 数据库信息
database_info = {
    'host': '192.168.123.5',  # 主机
    'port': 3306,  # 端口
    'database': 'study',  # 数据库名称
    'user': 'study',  # 用户名
    'password': 'sditr',  # 密码
    'charset': 'utf8'  # 字符编码
}

if __name__ == '__main__':
    _cookie = 'semester.id=' + str(cookie['semester.id']) + '; JSESSIONID=' + cookie['JSESSIONID']

    # # 学生汇总列表
    # xsyu_summary(_cookie,databsae_info)

    # # 学生详细列表
    xsyu_detailed(_cookie, database_info)
