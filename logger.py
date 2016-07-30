# -*- coding:utf-8 -*-
import signal
import logging
import socket
import fcntl
import struct
import os
import sys
import errno
import time
import traceback
import ctypes
import inspect
from functools import wraps
from kafka import KafkaClient, SimpleProducer
from argparse import ArgumentParser
from kafka.common import FailedPayloadsError
from cloghandler import ConcurrentRotatingFileHandler
from scutils.log_factory import LogFactory, LogObject
from scutils.settings_wrapper import SettingsWrapper


settings = SettingsWrapper().load("default_settings.py", "default_settings.py")


def failedpayloads_wrapper(max_iter_times, _raise=False):

    def out_wrapper_methed(func):

        @wraps(func)
        def inner_wrapper_methed(*args):
            count = 0
            while count <= max_iter_times:
                try:
                    func(*args)
                    break
                except Exception, e:
                    if _raise and not isinstance(e, FailedPayloadsError):
                        raise e
                    count += 1
                    traceback.print_exc()
                    if count > max_iter_times and _raise:
                        raise
                    time.sleep(0.1)

        return inner_wrapper_methed

    return out_wrapper_methed


class CustomLogFactory(LogFactory):
    '''
    Goal is to manage Simple LogObject instances
    Like a Singleton
    '''
    _instance = None

    @classmethod
    def get_instance(self, **kwargs):
        if self._instance is None:
            self._instance = CustomLogObject(**kwargs)

        return self._instance


class KafkaHandler(logging.Handler):

    def __init__(self, settings):
        self.client = KafkaClient(settings.get("KAFKA_HOSTS"))
        self.producer = SimpleProducer(self.client)
        self.producer.send_messages = failedpayloads_wrapper(5)(self.producer.send_messages)
        super(KafkaHandler, self).__init__()

    def emit(self, record):
        self.client.ensure_topic_exists(settings.get("TOPIC"))
        buf = self.formatter.format(record)
        self.producer.send_messages(settings.get("TOPIC"), buf)

    def close(self):
        self.acquire()
        super(KafkaHandler, self).close()
        self.client.close()
        self.release()


class CustomLogObject(LogObject):

    def __init__(self, json=False, name='scrapy-cluster', level='INFO',
                 format='%(asctime)s [%(name)s] %(levelname)s: %(message)s',
                 propagate=False):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        self.logger.propagate = propagate
        self.json = json
        self.log_level = level
        self.format_string = format

    def set_handler(self, handler):
        handler.setLevel(logging.DEBUG)
        formatter = self._get_formatter(self.json)
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self._check_log_level(self.log_level)
        self.debug("Logging to %s"%handler.__class__.__name__)


class Logger(object):

    name = "root"

    setting_wrapper = SettingsWrapper()

    def __init__(self, settings):
        self.settings = self.setting_wrapper.load(settings, "default_settings.py")
        self.set_logger()

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
        self.logger = CustomLogFactory.get_instance(json=my_json,
                                                    name=my_name,
                                                    level=my_level)
        if to_kafka:
            self.logger.set_handler(KafkaHandler(settings))
        elif my_output:
            self.logger.set_handler(logging.StreamHandler(sys.stdout))
        else:
            try:
                # try to make dir
                os.makedirs(my_dir)
            except OSError as exception:
                if exception.errno != errno.EEXIST:
                    raise
            self.logger.set_handler(
                ConcurrentRotatingFileHandler(
                    os.path.join(my_dir, my_file),
                    backupCount=my_backups,
                    maxBytes=my_bytes))


class SignalLogger(Logger):

    alive = True

    def __init__(self, settings):
        super(SignalLogger, self).__init__(settings)
        self.threads = []
        self.int_signal_count = 1
        self.open()

    def stop(self, *args):
        if self.int_signal_count > 1:
            self.logger.info("force to terminate all the threads...")
            for th in self.threads:
                self.stop_thread(th)
        else:
            self.alive = False
            self.logger.info("close processor %s..." % self.name)
            self.int_signal_count += 1

    def open(self):
        signal.signal(signal.SIGINT, self.stop)
        signal.signal(signal.SIGTERM, self.stop)

    def set_force_interrupt(self, thread):
        self.threads.append(thread)

    @classmethod
    def parse_args(cls):
        parser = ArgumentParser()
        parser.add_argument("-s", "--settings", dest="settings", help="settings", default="settings_kafkadump.py")
        parser.add_argument("-c", "--consumer", required=False, dest="consumer", help="comsumer id")
        parser.add_argument("-t", "--topic", required=True, dest="topic", help="topic")
        return cls(**vars(parser.parse_args()))

    def _async_raise(self, name, tid, exctype):
        """raises the exception, performs cleanup if needed"""
        tid = ctypes.c_long(tid)
        if not inspect.isclass(exctype):
            exctype = type(exctype)
        res = ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, ctypes.py_object(exctype))
        self.logger.info("stop thread %s. "%name)
        if res == 0:
            raise ValueError("invalid thread id")
        elif res != 1:
            ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, None)
            raise SystemError("PyThreadState_SetAsyncExc failed")

    def stop_thread(self, thread):
        self._async_raise(thread.getName(), thread.ident, SystemExit)
        self.threads.remove(thread)


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
