# -*- coding:utf-8 -*-
import codecs
import os
try:
    from setuptools import setup, find_packages
except:
    from distutils.core import setup

VERSION = '1.0.2'

AUTHOR = "cn"

AUTHOR_EMAIL = "308299269@qq.com"

URL = "https://www.github.com/ShichaoMa/log_to_kafka"


def read(fname):
    return codecs.open(os.path.join(os.path.dirname(__file__), fname)).read()

NAME = "log-to-kafka"

DESCRIPTION = "log to kafka"

LONG_DESCRIPTION = read("README.rst")

KEYWORDS = "log kafka"

LICENSE = "MIT"

PACKAGES = find_packages()

setup(
    name = NAME,
    version = VERSION,
    description = DESCRIPTION,
    long_description = LONG_DESCRIPTION,
    classifiers = [
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
    ],
    keywords = KEYWORDS,
    author = AUTHOR,
    author_email = AUTHOR_EMAIL,
    url = URL,
    license = LICENSE,
    packages = PACKAGES,
    install_requires=["kafka-python==0.9.5", "python-json-logger>=0.1.2", "ConcurrentLogHandler>=0.9.1"],
    include_package_data=True,
    zip_safe=True,
)