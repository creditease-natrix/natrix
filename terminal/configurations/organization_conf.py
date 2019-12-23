# -*- coding: utf-8 -*-
"""

"""
from __future__ import unicode_literals

# The max organization level
MAX_LEVEL = 9

# The network type info.
SEGMENT_TYPES_INFO = {
    'wired': {
        'name': 'wired',
        'verbose_name': u'有线'
    },
    'wireless': {
        'name': 'wireless',
        'verbose_name': u'无线'
    },
    'mix': {
        'name': 'mix',
        'verbose_name': u'混合'
    }
}

# Network type of device interface
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

# The user identification
IDENTITY_TYPE_INFO = {
    'user':{
        'name': 'user',
        'verbose_name': u'普通用户'
    },
    'admin':{
        'name': 'admin',
        'verbose_name': u'管理员'
    }
}


# Operator info
OPERATOR_DICT = {
    'China Telecom': {
        'name': 'China Telecom',
        'verbose_name': u'中国电信'
    },
    'China Mobile': {
        'name': 'China Mobile',
        'verbose_name': u'中国移动'
    },
    'China Unicom': {
        'name': 'China Unicom',
        'verbose_name': u'中国联通'
    },
    'other': {
        'name': 'other',
        'verbose_name': u'其他'
    }
}
