# -*- coding: utf-8 -*-

from __future__ import unicode_literals, absolute_import
import os
try:
    import ConfigParser as configparser
except ImportError:
    import configparser


NETWORK_TYPE_INFO = {
    'wired': {
        'name': 'wired',
        'verbose_name': u'有线'
    },
    'wireless': {
        'name': 'wireless',
        'verbose_name': u'无线'
    },
    '4G': {
        'name': '4G',
        'verbose_name': u'4G卡'
    },
    'other': {
        'name': 'other',
        'verbose_name': u'其他'
    }
}

DEVICE_STATUS = {
    'active': {
        'name': 'active',
        'verbose_name': u'激活态'
    },
    'maintain': {
        'name': 'maintain',
        'verbose_name': u'维护态'
    },
    'posting': {
        'name': 'posting',
        'verbose_name': u'邮寄中'
    }
}

TERMINAL_STATUS = {
    'active': {
        'name': 'active',
        'verbose_name': u'激活态'
    },
    'maintain': {
        'name': 'maintain',
        'verbose_name': u'维护态'
    }
}

choice_generator = lambda x : (x['name'], x['verbose_name'])

root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
config_file = root_dir + "/natrix.ini"
config = configparser.ConfigParser()
config.read(config_file)

ES_SERVICE_URL = config.get("ELASTICSEARCH", "host")
ES_SERVICE_PORT = config.get("ELASTICSEARCH", "port")
TERMINAL_INDEX = 'terminal2'
TERMINAL_BASIC = 'terminal_basic'
TERMINAL_ADVANCE = 'terminal_advance'