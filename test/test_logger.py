from log_to_kafka import Logger

class MyClass(Logger):
    name = "log_name"
def __init__(self, settings_file):
    super(MyClass, self).__init__(settings_file)


MC = MyClass("default_settings.py")
MC.set_logger()
MC.logger.debug("....")