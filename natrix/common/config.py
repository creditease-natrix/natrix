# -*- coding: utf-8 -*-
"""

"""
import os
import io
try:
    import configparser
except ImportError:
    import ConfigParser as configparser

# for python2, IOError; for python3 FileNotFoundError
try:
    FileNotFoundError = FileNotFoundError
except NameError:
    FileNotFoundError = IOError
# for python2, OSError; for python3 FileNotFoundError
try:
    PermissionError = PermissionError
except NameError:
    PermissionError = OSError

from django.conf import settings


class NatrixConfig(object):
    """
    配置信息主要来自3个地方, 按照优先级如下
    1. 命令行设置 / API参数 / RABBITMQ获取数据
    2. configuration file (default /etc/natrix/natrix.ini)
    3. const.py
    """
    def __init__(self, config_path=None):
        if config_path is None:
            self.config_path = settings.BASE_DIR + '/natrix.ini'
            # TODO: add the config file validation
            # self.config_path = os.path.dirname(os.path.realpath(__file__)) + '/../../natrix.ini'

        else:
            self.config_path = config_path

        try:
            # TODO: validate is not great way
            fnatrix = io.open(self.config_path, "r", encoding='utf-8')
            fnatrix.close()
            # configuration parser
            pconfig = configparser.ConfigParser()
            pconfig.read(self.config_path)
            self.config_parser = pconfig
        except FileNotFoundError:
            # TODO, throw exception
            print("ERROR: Cannot find File {}".format(self.config_path))
            # raise FileNotFoundError()
        except PermissionError:
            # TODO, throw exception
            print("ERROR: Do not have permission to access File {}".format(self.config_path))
            # raise PermissionError()

    def get_value(self, section=None, option=None):
        if self.config_parser:
            try:
                conf_value = self.config_parser[section][option]
            except AttributeError:
                # python 2
                # TODO, add try ... except ...
                conf_value = self.config_parser.get(section, option)
            except KeyError as k:
                raise KeyError("Config Key Error:{}".format(k))
        else:
            conf_value = None
        return conf_value


natrix_config = NatrixConfig()