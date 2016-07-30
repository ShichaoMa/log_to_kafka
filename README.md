# log_to_kafka
将日志发送到kafka中，做日志分布式管理

├── default_settings.py
├── __init__.py
├── logger.py
└── README.md


ubuntu

INSTALL

    git clone https://github.com/ShichaoMa/log_to_kafka.git

    sudo pip install -r requirements.txt

HELLOWORLD

    demon1

    ```python

from logger import Logger

class MyClass(Logger):
    name = "log_name"
    def __init__(self, settings_file):
        super(MyClass, self).__init__(settings_file)
        self.logger.debug("....")

```
