# -*- coding: utf-8 -*-
import logging

from elasticsearch import Elasticsearch

from natrix.common.config import natrix_config

logger = logging.getLogger(__name__)


ES_SERVICE_URL = natrix_config.get_value('ELASTICSEARCH', 'host')
ES_SERVICE_PORT = natrix_config.get_value('ELASTICSEARCH', 'port')


# TODO: optimize
class NatrixESClient:

    def __init__(self, app):
        self.es_conn = Elasticsearch(hosts=ES_SERVICE_URL, port=ES_SERVICE_PORT)
        self.es_index = natrix_config.get_value('ELASTICSEARCH', f'{app}_index')

    def push(self, type, data):
        res = self.es_conn.index(index=self.es_index,
                                 doc_type=type,
                                 body=data)
        logger.info('push data to ES: {}'.format(res))

    def pull(self, condition, size=None):
        if size:
            condition['size'] = size

        res = self.es_conn.search(index=self.es_index,
                                  body=condition)
        if res['hits']['total'] == 0:
            return []

        records = res.get('hits', {}).get('hits', [])

        return records

    def origin_search(self, condition, size=1000):
        res = self.es_conn.search(index=self.es_index,
                                  body=condition,
                                  size=size)

        return res


