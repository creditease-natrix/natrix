# -*- coding: utf-8 -*-
"""初始化ES配置

用于Terminal初次上线

"""
from __future__ import unicode_literals

from elasticsearch.client import Elasticsearch
from elasticsearch.client import IndicesClient

from terminal.configurations.terminal_conf import ES_SERVICE_URL, ES_SERVICE_PORT
from terminal.configurations.terminal_conf import TERMINAL_INDEX, TERMINAL_ADVANCE, TERMINAL_BASIC

es = Elasticsearch(host=ES_SERVICE_URL, port=ES_SERVICE_PORT)

# 终端设备状态
terminal_basic_mapping = {
    'terminal_basic': {
        'properties': {
            'sn': {
                'type': 'keyword'
            },
            'hostname': {
                'type': 'keyword'
            },
            'cpu_percent': {
                'type': 'double'
            },
            'memory_percent': {
                'type': 'double'
            },
            'disk_percent': {
                'type': 'double'
            },

            'natrixclient_version': {
                'type': 'keyword'
            },
            'networks': {
                'type': 'nested'
            },
            'heartbeat': {
                'type': 'double'
            },
            'receive_time': {
                'type': 'double'
            }
        }
    }
}

terminal_advance_mapping = {
    'terminal_advance': {
        'properties': {
            'sn': {
                'type': 'keyword'
            },
            'hostname': {
                'type': 'keyword'
            },
            'product':{
                'type': 'keyword'
            },
            'boot_time':{
                'type': 'double'
            },
            # CPU
            'cpu_model':{
                'type': 'keyword'
            },
            'cpu_core':{
                'type': 'integer'
            },
            'cpu_percent':{
                'type': 'double'
            },
            # memory
            'memory_total':{
                'type': 'long'
            },
            'memory_used':{
                'type': 'long'
            },
            'memory_percent':{
                'type': 'double'
            },
            # disk
            'disk_percent':{
                'type': 'double'
            },

            # OS type
            'type':{
                'type': 'keyword'
            },
            'series':{
                'type': 'keyword'
            },
            'name':{
                'type': 'keyword'
            },
            'codename':{
                'type': 'keyword'
            },
            'major_version':{
                'type': 'keyword'
            },
            'minor_version':{
                'type': 'keyword'
            },
            'kernel_version':{
                'type': 'keyword'
            },
            'architecture':{
                'type': 'keyword'
            },
            'platform':{
                'type': 'keyword'
            },
            'python_version':{
                'type': 'keyword'
            },
            'desktop_version':{
                'type': 'keyword'
            },
            'selenium_version':{
                'type': 'keyword'
            },
            'chrome_version':{
                'type': 'keyword'
            },
            'chrome_webdriver_path':{
                'type': 'keyword'
            },
            'chrome_webdriver_version':{
                'type': 'keyword'
            },
            'firefox_version':{
                'type': 'keyword'
            },
            'firefox_webdriver_path':{
                'type': 'keyword'
            },
            'firefox_webdriver_version':{
                'type': 'keyword'
            },
            'natrixclient_version': {
                'type': 'keyword'
            },


            'networks': {
                'type': 'nested'
            },
            'heartbeat': {
                'type': 'double'
            },
            'receive_time': {
                'type': 'double'
            }
        }
    }

}


def initializer():
    es_index = IndicesClient(es)

    if es_index.exists(TERMINAL_INDEX):
        print('Index ({}) is already exists!'.format(TERMINAL_INDEX))
    else:
        es.indices.create(TERMINAL_INDEX)

    es.indices.put_mapping(index=TERMINAL_INDEX,
                           doc_type=TERMINAL_BASIC,
                           body=terminal_basic_mapping)
    es.indices.put_mapping(index=TERMINAL_INDEX,
                           doc_type=TERMINAL_ADVANCE,
                           body=terminal_advance_mapping)


if __name__ == '__main__':
    initializer()

