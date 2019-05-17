# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import

from .es_store import push, pull


def save(position, type, data):
    """

    :param position: string,
    :param type: string, document type in ES
    :param data: dict,
    :return:
    """
    push(position, type, data)


def search(position, type, condition):
    """

    :param position:
    :param type:
    :param condition:
    :return:
    """
    records = pull(position, type, condition)
    return records