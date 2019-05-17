# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import

import logging

from elasticsearch import Elasticsearch

from terminal.configurations.terminal_conf import ES_SERVICE_URL, ES_SERVICE_PORT

logger = logging.getLogger(__name__)


es_conn = Elasticsearch(hosts=ES_SERVICE_URL, port=ES_SERVICE_PORT)



def push(index, type, data):

    res = es_conn.index(index=index,
                        doc_type=type,
                        body=data)
    logger.info('push data to ES: {}'.format(res))



def pull(index, condition):
    res = es_conn.search(index=index,
                         body=condition)
    records = res.get('hits', {}).get('hits', [])

    return records




