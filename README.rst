log_to_kafka
============
DESCRIPTION
-----------
- 将日志发送到kafka中，做日志分布式管理
INSTALL
-------
ubuntu & windows
>>>>>>>>>>>>>>>>

::

    git clone https://github.com/ShichaoMa/log_to_kafka.git
    sudo python setup.py  install

    or

    sudo pip install log_to_kafka

HELLOWORLD
----------
demo1
>>>>>
::

    from log_to_kafka import Logger
    class MyClass(Logger):
    name = "log_name"
    def __init__(self, settings_file):
        super(MyClass, self).__init__(settings_file)


    MC = MyClass("default_settings.py")
    MC.set_logger()
    MC.logger.debug("....")

demo2
>>>>>
::

    import os
    from log_to_kafka import LogFactory
    from cloghandler import ConcurrentRotatingFileHandler
    my_dir = "logs"
    try:
    os.makedirs(my_dir)
    except OSError as exception:
    if exception.errno != errno.EEXIST:
        raise
    logger = LogFactory.get_instance(name="test_name")
    logger.set_handler(
    ConcurrentRotatingFileHandler(
        os.path.join(my_dir, "test.log"),
        backupCount=5,
        maxBytes=10240))
    logger.info("this is a log. ")

demo3
>>>>>
::

    from log_to_kafka import LogFactory, KafkaHandler
    settings = {"KAFKA_HOSTS":"192.168.200.90:9092", "TOPIC":"jay-cluster-logs"}
    logger = LogFactory.get_instance(name="test_name", json=True)
    kafka_handler = KafkaHandler(settings)
    logger.set_handler(kafka_handler)
    logger.info("this is a log. ")

demo4
>>>>>
::

    import sys
    import logging
    from log_to_kafka import LogFactory
    logger = LogFactory.get_instance(name="test_name")
    logger.set_handler(logging.StreamHandler(sys.stdout))
    logger.info("this is a log. ")

demo5
>>>>>

- 编写自定义handler
- 请参见KafkaHandler的实现方式
