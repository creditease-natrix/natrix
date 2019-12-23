# -*- coding: utf-8 -*-
"""

"""
import logging

from natrix.common import exception as natrix_exception
from utils.elasticsearch import NatrixESClient
from benchmark.backends.stores import eventhub_client


logger = logging.getLogger(__name__)


def store_message(type, data):
    try:
        record = {
            '_type': type
        }
        record.update(data)
        eventhub_client.put(record)
    except natrix_exception.NatrixBaseException as e:
        natrix_exception.natrix_traceback()
        logger.error('store message with exception: {}'.format(e.get_log()))


# TODO: The count of records may exceed 1000
def search_messages(body=None, size=1000):
    """Get all data satisfy the condition.

    :param body:
    :param size:
    :return:
    """
    if body is None:
        body = {}
    natrix_es_client = NatrixESClient(app='benchmark')
    records = natrix_es_client.pull(condition=body, size=size)
    return records


def origin_search(body, size=1000):
    natrix_es_client = NatrixESClient(app='benchmark')
    res = natrix_es_client.origin_search(condition=body, size=size)
    return res

