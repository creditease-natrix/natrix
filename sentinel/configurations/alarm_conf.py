# -*- coding: utf-8 -*-

from __future__ import unicode_literals


AGGREGATION_INFO = {
    'average': {
        'name': 'average',
        'verbose_name': u'平均'
    },
    'individuality': {
        'name': 'individuality',
        'verbose_name': u'任意个体'
    }
}


MONITOR_TYPE = {
    'ping_loss_rate': {
        'name': 'ping_loss_rate',
        'verbose_name': u'PING丢包率',
        'unit': '非百分制',
        'protocol': ['ping'],
        'is_condition': True,
        'is_agg': True,
        'agg_types': [
            'average',
            'individuality'
        ]
    },
    'ping_delay': {
        'name': 'ping_delay',
        'verbose_name': u'PING延时（毫秒）',
        'unit': 'ms',
        'protocol': ['ping'],
        'is_condition': True,
        'is_agg': True,
        'agg_types': [
            'average',
            'individuality'
        ]
    },
    'http_request_time': {
        'name': 'http_request_time',
        'verbose_name': u'HTTP请求时间',
        'unit': 'ms',
        'protocol': ['http'],
        'is_condition': True,
        'is_agg': True,
        'agg_types': [
            'average',
            'individuality'
        ]
    },
    'http_status_code': {
        'name': 'http_status_code',
        'verbose_name': u'HTTP状态码异常',
        'unit': '无',
        'protocol': ['http'],
        'is_condition': True,
        'is_agg': True,
        'agg_types': [
            'individuality'
        ]
    },
    'parse_time': {
        'name': 'parse_time',
        'verbose_name': u'解析时间',
        'unit': 'ms',
        'protocol': ['http', 'dns'],
        'is_condition': True,
        'is_agg': True,
        'agg_types': [
            'average',
            'individuality'
        ]
    },
    'error_count': {
        'name': 'error_count',
        'verbose_name': u'感知错误',
        'unit': '无',
        'protocol': ['ping', 'http', 'dns'],
        'is_condition': False,
        'is_agg': True,
        'agg_types': [
            'individuality'
        ]
    }
}


OPERATION_INFO = {
    'gt': {
        'name': 'gt',
        'verbose_name': u'大于'
    },
    'lt': {
        'name': 'lt',
        'verbose_name': u'小于'
    },
    'eq': {
        'name': 'eq',
        'verbose_name': u'等于'
    }
}