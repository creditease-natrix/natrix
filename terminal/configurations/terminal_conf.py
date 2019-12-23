# -*- coding: utf-8 -*-

from __future__ import unicode_literals, absolute_import



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


TERMINAL_BASIC = 'terminal_basic'
TERMINAL_ADVANCE = 'terminal_advance'