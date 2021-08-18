# 西安石油大学学生成绩爬虫

> 此代码仅供学习使用，请勿用于其他用途

## 数据库操作

进入数据库`use 数据库名`之后：

### 创建学生汇总信息表

这张表只包含一些基本的信息，但是需要用来做索引，参数列出：

| 变量                                                 | 英文                                 | 数据库变量名 | 类型                     |
| ---------------------------------------------------- | ------------------------------------ | ------------ | ------------------------ |
| 教务系统ID（教务系统数据库里自增的id，后面操作需要） | Educational Administration System ID | sac_id       | int unsigned             |
| 学号                                                 | student id                           | stuid        | VARCHAR                  |
| 姓名                                                 | name                                 | name         | VARCHAR                  |
| 性别                                                 | gender                               | gender       | enum("男", "女", "未知") |
| 年级                                                 | grade                                | grade        | YEAR                     |
| 院系                                                 | faculty                              | faculty      | VARCHAR                  |
| 专业                                                 | major                                | major        | VARCHAR                  |
| 行政班级                                             | class                                | class        | VARCHAR                  |
| 专业方向                                             | professional direction               | prof_d       | VARCHAR                  |

对应的SQL语句为：

```sql
create table students_summary_table(
    esa_id int unsigned not null primary key,
    stuid varchar(20) not null,
    name varchar(20) not null,
    gender enum("男","女","未知") default "未知",
    grade YEAR,
    faculty varchar(20),
    major varchar(20),
    class varchar(20),
    prof_d varchar(20) default null
);
```

### 创建学生成绩详细表

这张表才是一个详细的成绩的列表，写入规则为`每个学生的一个成绩为一条记录`。参数列出：

| 变量          | 英文                | 数据库变量名 | 类型         |
| ------------- | ------------------- | ------------ | ------------ |
| 顺序ID        | Sequence id         | id           | int unsigned |
| 学号          | student id          | stuid        | VARCHAR      |
| 姓名          | name                | name         | VARCHAR      |
| 行政班级      | class               | class        | VARCHAR      |
| 修读学年学期  | School year         | school_year  | VARCHAR      |
| 课程/环节id   | Courses/sections id | courses_id   | VARCHAR      |
| 课程/环节名称 | Courses/sections    | courses      | VARCHAR      |
| 课程性质      | Courses property    | courses p    | VARCHAR      |
| 成绩          | score               | score        | VARCHAR      |
| 学分          | credit              | credit       | decimal(5,2) |
| 绩点          | Grade point         | gp           | decimal(5,2) |
| 学分绩点      | academic credits    | ac           | decimal(5,2) |
| 修读性质      | Nature of study     | nos          | VARCHAR      |
| 备注          | Remark              | remark       | VARCHAR      |

对应SQL语句为：

```sql
create table students_detailed_table(
    id int unsigned not null primary key auto_increment,
    stuid varchar(20) not null,
    name varchar(20) not null,
    class varchar(20),
    school_year varchar(40),
    courses_id varchar(20),
    courses varchar(30),
    courses_p varchar(20),
    score varchar(10),
    credit decimal(5,2),
    gp decimal(5,2),
    ac decimal(5,2),
    nos varchar(10),
    remark varchar(20)
);
```

## 基本使用

### 环境安装

由于使用的的是`pip freeze > requirements.txt`一键生成的依赖，所以估计环境的所有包都被搞上去了，如果嫌麻烦可以用下面命令把所有包都给装上：

```shell
pip install -r requirement.txt
```

如果你不想装其他包，下面我列举了写可能需要装的：

```
pymysql
requests
BeautifulSoup4
```

### 在主函数调用

大部功能已经封装在`xsyu_summary()`和`xsyu_detailed()`上，一些参数已经带了默认属性，所以在主函数上简单配置即可使用：

**需要注意的是**：我把代码都放在了`./syu_sac/syu_sac.py`文件里，需要import导入。

在main.py里边，填入`cookie信息和数据库信息`

```python
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
```

其中，`cookie`的`semester.id`为学期

#### 主函数DEMO

> demo我已经写在了main.py文件里边了

```python
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
    print("完成!共花费:{}".format(time_spend))


if __name__ == '__main__':
    main()

```

## 详细参数

### xsyu_summary()

> 获取学生汇总信息索引

```python
def xsyu_summary(cookie, database_info,
                 get_table=True, insert_table=True)
```

- param cookie: 需要为管理员的cookie,格式为semester.id + JSESSIONID,注意如果没有semester.id默认会打印所有学生包括已经毕业的
- param database_info: 数据库基本信息
- param get_table: 是否抓取学生汇总
- param insert_table: 是否插入数据库，如果不插入，则返回汇总列表lists

### xsyu_detailed()

> 获取学生成绩详细成绩

```python
def xsyu_detailed(cookie, database_info,
                  process_num = mp.cpu_count(),get_html=True,analyze_html=True,insert_database=True)
```

- param cookie: 需要为管理员的cookie,格式为semester.id + JSESSIONID,注意如果没有semester.id默认会打印所有学生包括已经毕业的
- param database_info: 数据库基本信息，用来读取asc_id信息，所以在运行`xsyu_detailed()`之前**必须运行**`xsyu_summary()`把学生基本信息写入数据库
- param process_num: **进程数量**,默认为CPU内核数量`mp.cpu_count()`
- param get_html: 是否请求网页
- param analyze_html: 是否解析网页
- param insert_database: 是否写入数据库

### 不抓取有效学生而是抓取所有学生

> 注意，由于学校防爬机制等一些原因，虽然我尽可能地让程序稳定，**但是这样仍然可能会降低程序的稳定性**，一些信息将会因为程序的稳定机制而跳过。

由于`xsyu_detailed()`抓取学生详细成绩是根据`xsyu_summary()`得到的asc_id来的，所以我们需要控制`xsyu_summary()`得到教务系统里边所有学生的asc_id，在`./xsyu_sac/xsyu_sac.py`文件下，找到`get_summary_table_html()`函数，将：

```python
Hpostdata = {
        'orderBy': 'std.code asc',
        'std.project.id': 1,
        'stdActive': 1,
        'pageNo': pageNO,
        'pageSize': pageSize
    }
```

改为：

```python
Hpostdata = {
        'pageNo': pageNO,
        'pageSize': pageSize
    }
```

即可。
