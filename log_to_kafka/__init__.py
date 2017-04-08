# -*- coding:utf-8 -*-

VERSION = '1.0.9'

AUTHOR = "cn"

AUTHOR_EMAIL = "cnaafhvk@foxmail.com"

HOME_PAGE = "https://www.github.com/ShichaoMa/log_to_kafka"

from .logger import LogFactory, Logger, LogObject, KafkaHandler, FixedConcurrentRotatingFileHandler, ConcurrentRotatingFileHandler

__all__ = ["LogFactory", "Logger", "LogObject", "KafkaHandler",
           "FixedConcurrentRotatingFileHandler", "ConcurrentRotatingFileHandler",
           "HOME_PAGE", "AUTHOR_EMAIL", "VERSION", "AUTHOR"]