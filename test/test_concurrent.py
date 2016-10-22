# -*- coding:utf-8 -*-
import os
import sys
sys.path.insert(0, "..")
import errno
import logging
from log_to_kafka.logger import FixedConcurrentRotatingFileHandler
my_dir = "logs"
try:
    os.makedirs(my_dir)
except OSError as exception:
    if exception.errno != errno.EEXIST:
        raise
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
logger.addHandler(
FixedConcurrentRotatingFileHandler(
    os.path.join(my_dir, "test.log"),
    backupCount=5))
logger.info("this is a log. ")
