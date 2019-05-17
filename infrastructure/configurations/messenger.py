# -*- coding: utf-8 -*-
"""
"""

from __future__ import unicode_literals
import os
try:
    import ConfigParser as configparser
except ImportError:
    import configparser

from natrix.settings import SMS_URL, SMS_ORGNO, SMS_TYPENO
from natrix.settings import DEFAULT_FROM_EMAIL


root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
config_file = root_dir + "/natrix.ini"
config = configparser.ConfigParser()
config.read(config_file)
BROKER_SERVER = config.get("RABBITMQ", "host")

NOTIFY_TYPE = {
    'email': {
        'name': 'email',
        'verbose_name': u'邮件通知'
    },
    'sms': {
        'name': 'sms',
        'verbose_name': u'短信通知'
    }
}

NOTIFY_LEVEL = {
    'warning': {
        'name': 'warning',
        'verbose_name': u'警告'
    },
    'critical': {
        'name': 'critical',
        'verbose_name': u'危险'
    },
    'normal': {
        'name': 'normal',
        'verbose_name': u'正常'
    }
}

# 队列名称
queue_name = 'natrix_notification_queue'
