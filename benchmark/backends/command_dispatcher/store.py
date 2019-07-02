# -*- coding: utf-8 -*-
"""

"""
from __future__ import unicode_literals

from elasticsearch import Elasticsearch

from benchmark.configurations import adapter_conf


def store_message(type, data, index=adapter_conf.BENCHMARK_INDEX):
    es_conn = Elasticsearch(host=adapter_conf.ES_SERVICE_URL,
                            port=adapter_conf.ES_SERVICE_PORT)

    res = es_conn.index(index=index, doc_type=type, body=data)

    return res

def search_messages(index=adapter_conf.BENCHMARK_INDEX, body={}, size=1000):
    es_conn = Elasticsearch(host=adapter_conf.ES_SERVICE_URL,
                            port=adapter_conf.ES_SERVICE_PORT)

    res = es_conn.search(index=index, size=size, body=body)

    if res['hits']['total'] == 0:
        return []

    return res['hits']['hits']

def origin_search(index=adapter_conf.BENCHMARK_INDEX, body={}, size=1000):
    es_conn = Elasticsearch(host=adapter_conf.ES_SERVICE_URL,
                            port=adapter_conf.ES_SERVICE_PORT)

    res = es_conn.search(index=index, size=size, body=body)

    return res