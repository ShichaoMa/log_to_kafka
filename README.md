# log_to_kafka
将日志发送到kafka中，做日志分布式管理
    ├── default_settings.py<div>
    ├── __init__.py
    ├── logger.py
    └── README.md

ubuntu

INSTALL

    git clone https://github.com/ShichaoMa/log_to_kafka.git

    sudo pip install -r requirements.txt

HELLOWORLD

    demon1

    ```
    from logger import Logger
    class MyClass(Logger):
        name = "log_name"
        def __init__(self, settings_file):
            super(MyClass, self).__init__(settings_file)
            self.logger.debug("....")
    ```

    demon2

    ```
    import os
    from logger import CustomLogFactory
    from cloghandler import ConcurrentRotatingFileHandler
    my_dir = "logs"
    try:
        os.makedirs(my_dir)
    except OSError as exception:
        if exception.errno != errno.EEXIST:
            raise
    logger = CustomLogFactory.get_instance(name="test_name")
    logger.set_handler(
        ConcurrentRotatingFileHandler(
            os.path.join(my_dir, "test.log"),
            backupCount=5,
            maxBytes=10240))
    logger.info("this is a log. ")
    ```

    demon3

    ```
    from logger import CustomLogFactory, KafkaHandler
    settings = {"KAFKA_HOSTS":"192.168.200.90:9092", "TOPIC":"jay-cluster-logs"}
    logger = CustomLogFactory.get_instance(name="test_name", json=True)
    kafka_handler = KafkaHandler(settings)
    logger.set_handler(kafka_handler)
    logger.info("this is a log. ")
    ```

    demon4
    ```
    import sys
    import logging
    from logger import CustomLogFactory
    logger = CustomLogFactory.get_instance(name="test_name")
    logger.set_handler(logging.StreamHandler(sys.stdout))
    logger.info("this is a log. ")
    ```

    demon5
    ```
    # 编写自定义handler
    # 请参见KafkaHandler的实现方式
    ```
