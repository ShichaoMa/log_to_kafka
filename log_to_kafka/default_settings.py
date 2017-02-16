# -*- coding:utf-8 -*-


# 日志级别
LOG_LEVEL = 'DEBUG'
# 是否标准到控制台
LOG_STDOUT = True
# 是否输出json格式
LOG_JSON = False
# log文件目录
LOG_DIR = "logs"
# 每个log最大大小
LOG_MAX_BYTES = 1024*1024*10
# log备份数量
LOG_BACKUPS = 5
# 是否发送到kafka
TO_KAFKA = False
# kafka地址
KAFKA_HOSTS = "192.168.200.90:9092"
# kafka topic
TOPIC = "jay-cluster-logs"