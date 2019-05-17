# Natrix

基于宜信公司的内部需求，开发的一套全网检测和云拨测系统

Based on the requirements of CreaditEase,  develop a global and active monitor system

# 简易安装

## 目的

简易安装主要用来做学习，演示，小规模的使用

简易安装默认会使用缺省的数据库，缓存等，用户只需要很少的配置就能使用natrix系统

## 测试矩阵

| 操作系统     | 测试通过 |
| ------------ | -------- |
| Ubuntu 18    | Y        |
| CentOS7      |          |
| MacOS Mojave |          |

## 先决条件

- 安装 python 2.7
- 使用 root 用户安装

## 安装

### 下载

```
git clone https://github.com/creditease-natrix/natrix.git
```

进入目录

```
cd natrix
```

### 修改配置文件

根据自己的情况修改

```
vim natrix.ini
```

如下项是必须填写的

- RABBITMQ
- ELASTICSEARCH

### 运行

运行如下命令安装natrix系统

```
python manage.py natrix
```

默认的，会执行如下操作

- 检查各项参数
- 初始化数据库
- 初始化ElasticSearch
- 安装， 启动，开机启动各项服务

## 访问

浏览器输入

http://127.0.0.1:8000

即可访问natrix系统

默认的用户名/密码： 

​	natrix/changeme

## 停止服务

```
systemctl stop natrix.service
systemctl stop natrix-celery.service
systemctl stop natrix-celery-beat.service
```

## 设置开机启动

```
systemctl enable natrix.service
systemctl enable natrix-celery.service
systemctl enable natrix-celery-beat.service
```

## 取消开机启动

```
systemctl disable natrix.service
systemctl disable natrix-celery.service
systemctl disable natrix-celery-beat.service
```

## 检查服务状态

    systemctl status natrix.service
    systemctl status natrix-celery.service
    systemctl status natrix-celery-beat.service
## 关于日志

日志存放位置

```
/var/log/natrix/
```

# 高级安装

## 目的

高级安装主要用来大规模的使用，能够承受更多的终端和更大的并发量

高级安装需要用户进行更多的配置

# About Name(关于名称)

取名natrix主要是3个原因

- 致敬电影 黑客帝国(The Matrix)
- 我们认为全网检测就是构建一个网络矩阵(net matrix)
- Natrix是一种游蛇， 这个项目基于python(巨蟒)


# About LOGO(关于LOGO)

Natrix的LOGO是宇宙星空的矩阵图, 代表着未知与联结

