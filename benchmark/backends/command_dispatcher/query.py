# -*- coding: utf-8 -*-
"""

"""

from __future__ import unicode_literals, absolute_import

import logging


from .store import search_messages

logger = logging.getLogger(__name__)


def get_command_data(command_uuid):

    query_body = {
        'query': {
            'bool': {
                'must': [
                    {
                        'term': {
                            'command_uuid': command_uuid
                        }
                    }
                ]
            }
        }
    }

    record_list = search_messages(body=query_body)

    successful_records = []
    failed_records = []
    for record in record_list:
        record_type = record.get('_type')
        if record_type == 'error':
            failed_records.append(record.get('_source'))
        else:
            successful_records.append(record.get('_source'))

    return {
        'success': successful_records,
        'error': failed_records
    }


def get_task_data(task_uuid):

    query_body = {
        'query': {
            'bool': {
                'must': [
                    {
                        'term': {
                            'task_id': task_uuid
                        }
                    }
                ]
            }
        }
    }

    record_list = search_messages(body=query_body)

    successful_records = []
    failed_records = []
    for record in record_list:
        record_type = record.get('_type')
        if record_type == 'error':
            failed_records.append(record.get('_source'))
        else:
            successful_records.append(record.get('_source'))

    return {
        'success': successful_records,
        'error': failed_records
    }