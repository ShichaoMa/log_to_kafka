# -*- coding:utf-8 -*-
import copy
import datetime
import errno
import logging
import os
import sys
import time

from functools import wraps
from portalocker import lock, unlock, LOCK_EX

from cloghandler import ConcurrentRotatingFileHandler, NullLogRecord
from kafka import KafkaClient, SimpleProducer
from kafka.common import FailedPayloadsError
from pythonjsonlogger import jsonlogger

from . import default_settings
from .settings_wrapper import SettingsWrapper

class FixedConcurrentRotatingFileHandler(ConcurrentRotatingFileHandler):
    """
    修正windows多次调用进程间lock产生的死锁问题
    """
    def acquire(self):
        """ Acquire thread and file locks.  Re-opening log for 'degraded' mode.
        """
        # handle thread lock
        logging.Handler.acquire(self)
        # Issue a file lock.  (This is inefficient for multiple active threads
        # within a single process. But if you're worried about high-performance,
        # you probably aren't using this log handler.)
        if self.stream_lock:
            # If stream_lock=None, then assume close() was called or something
            # else weird and ignore all file-level locks.
            if self.stream_lock.closed:
                # Daemonization can close all open file descriptors, see
                # https://bugzilla.redhat.com/show_bug.cgi?id=952929
                # Try opening the lock file again.  Should we warn() here?!?
                try:
                    self._open_lockfile()
                except Exception:
                    self.handleError(NullLogRecord())
                    # Don't try to open the stream lock again
                    self.stream_lock = None
                    return
            unlock(self.stream_lock)
            lock(self.stream_lock, LOCK_EX)


def failedpayloads_wrapper(max_iter_times, _raise=False):

    def out_wrapper_method(func):

        @wraps(func)
        def inner_wrapper_method(*args):
            count = 0
            while count <= max_iter_times:
                try:
                    func(*args)
                    break
                except Exception as e:
                    if _raise and not isinstance(e, FailedPayloadsError):
                        raise e
                    count += 1
                    if count > max_iter_times and _raise:
                        raise
                    time.sleep(0.1)

        return inner_wrapper_method

    return out_wrapper_method


class LogFactory(object):

    _instance = None

    @classmethod
    def get_instance(self, **kwargs):
        if self._instance is None:
            self._instance = LogObject(**kwargs)

        return self._instance


class KafkaHandler(logging.Handler):

    def __init__(self, settings):
        self.settings = settings
        self.client = KafkaClient(settings.get("KAFKA_HOSTS"))
        self.producer = SimpleProducer(self.client)
        self.producer.send_messages = failedpayloads_wrapper(
            settings.get("KAFKA_RETRY_TIME", 5))(self.producer.send_messages)
        super(KafkaHandler, self).__init__()

    def emit(self, record):
        self.client.ensure_topic_exists(self.settings.get("TOPIC"))
        buf = self.formatter.format(record)
        if hasattr(buf, "encode"):
            buf = buf.encode(sys.getdefaultencoding())
        self.producer.send_messages(self.settings.get("TOPIC"), buf)

    def close(self):
        self.acquire()
        super(KafkaHandler, self).close()
        self.client.close()
        self.release()


def extras_wrapper(self, item):

    def logger_func_wrapper(func):

        @wraps(func)
        def wrapper(*args, **kwargs):
            if len(args) > 2:
                extras = args[1]
            else:
                extras = kwargs.pop("extras", {})
            extras = self.add_extras(extras, item)
            return func(args[0], extra=extras)

        return wrapper

    return logger_func_wrapper


class LogObject(object):


    def __init__(self, json=False, name='scrapy-cluster', level='INFO',
                 format='%(asctime)s [%(name)s] %(levelname)s: %(message)s',
                 propagate=False):
        self.logger = logging.getLogger(name)
        root = logging.getLogger()
        # 将的所有使用Logger模块生成的logger设置一样的logger level
        for log in root.manager.loggerDict.keys():
            root.getChild(log).setLevel(getattr(logging, level, 10))
        self.logger.propagate = propagate
        self.json = json
        self.name = name
        self.format_string = format

    def set_handler(self, handler):
        handler.setLevel(logging.DEBUG)
        formatter = self._get_formatter(self.json)
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.debug("Logging to %s"%handler.__class__.__name__)

    def __getattr__(self, item):
        if item.upper() in logging._nameToLevel:
            return extras_wrapper(self, item)(getattr(self.logger, item))
        raise AttributeError

    def _get_formatter(self, json):
        if json:
            return jsonlogger.JsonFormatter()
        else:
            return logging.Formatter(self.format_string)

    def add_extras(self, dict, level):
        my_copy = copy.deepcopy(dict)
        if 'level' not in my_copy:
            my_copy['level'] = level
        if 'timestamp' not in my_copy:
            my_copy['timestamp'] = datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        if 'logger' not in my_copy:
            my_copy['logger'] = self.name
        return my_copy


class Logger(object):

    name = "root"

    setting_wrapper = SettingsWrapper()

    def __init__(self, settings=None):

        if isinstance(settings, dict):
            self.settings = settings
        else:
            self.settings = self.setting_wrapper.load(settings, default_settings)

    def set_logger(self, logger=None):
        if logger:
            self.logger = logger
            return
        my_level = self.settings.get('LOG_LEVEL', 'INFO')
        my_name = self.name
        my_output = self.settings.get('LOG_STDOUT', False)
        my_json = self.settings.get('LOG_JSON', True)
        my_dir = self.settings.get('LOG_DIR', 'logs')
        my_bytes = self.settings.get('LOG_MAX_BYTES', '10MB')
        my_file = "%s.log" % self.name
        my_backups = self.settings.get('LOG_BACKUPS', 5)
        to_kafka = self.settings.get("TO_KAFKA", False)
        self.logger = LogFactory.get_instance(json=my_json,
                                                    name=my_name,
                                                    level=my_level)
        if to_kafka:
            self.logger.set_handler(KafkaHandler(self.settings))
        elif my_output:
            self.logger.set_handler(logging.StreamHandler(sys.stdout))
        else:
            try:
                # try to make dir
                os.makedirs(my_dir)
            except OSError as exception:
                if exception.errno != errno.EEXIST:
                    raise
            if os.name == "nt":
                handler = FixedConcurrentRotatingFileHandler
            else:
                handler = ConcurrentRotatingFileHandler
            self.logger.set_handler(
                handler(
                    os.path.join(my_dir, my_file),
                    backupCount=my_backups,
                    maxBytes=my_bytes))


if __name__ == "__main__":
    # my_dir = settings.get("LOG_DIR")
    # try:
    #     os.makedirs(my_dir)
    # except OSError as exception:
    #     if exception.errno != errno.EEXIST:
    #         raise
    # logger = CustomLogFactory.get_instance(name="test_name")
    # logger.set_handler(
    #     ConcurrentRotatingFileHandler(
    #         os.path.join(my_dir, "test.log"),
    #         backupCount=5,
    #         maxBytes=10240))
    # logger.info("this is a log. ")
    #################################################
    # logger = CustomLogFactory.get_instance(name="test_name", json=True)
    # kafka_handler = KafkaHandler(settings)
    # logger.set_handler(kafka_handler)
    # logger.info("this is a log. ")
    #################################################
    # logger = CustomLogFactory.get_instance(name="test_name")
    # logger.set_handler(logging.StreamHandler(sys.stdout))
    # logger.info("this is a log. ")
    #################################################
    obj = Logger("defaut_settings.py")
    obj.logger.info("this is a log. ")
