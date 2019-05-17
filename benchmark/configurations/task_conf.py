# -*- coding: utf-8 -*-

from __future__ import unicode_literals


# 协议配置
PROTOCOL_INFO = {
    'ping': {
        'name': u'ping',
        'verbose_name': u'PING'
    },
    'http': {
        'name': u'http',
        'verbose_name': u'HTTP'
    },
    'traceroute':{
        'name': u'traceroute',
        'verbose_name': 'TRACEROUTE'
    },
    'dns':{
        'name': u'dns',
        'verbose_name': 'DNS'
    }
}


# -----Task-----

TASK_SCOPE = {
    'private': {
        'name': 'private',
        'verbose_name': u'私有任务'
    },
    'public': {
        'name': 'public',
        'verbose_name': u'公共任务'
    },
    'inactive': {
        'name': 'inactive',
        'verbose_name': u'失效任务'
    }
}

TASK_TIME_TYPE = {
    'instant':{
        'name': 'instant',
        'verbose_name': u'即时测'
    },
    'timing':{
        'name': 'timing',
        'verbose_name': u'定时测'
    }
}

TASK_PURPOSE = {
    'benchmark': {
        'name': 'benchmark',
        'verbose_name': u'宜信测'
    },
    'monitorline': {
        'name': 'monitorline',
        'verbose_name': u'线路监控'
    },
    'flowduck': {
        'name': 'flowduck',
        'verbose_name': u'统一流程',
    },
    'guard': {
        'name': 'guard',
        'verbose_name': u'职场卫士'
    }
}