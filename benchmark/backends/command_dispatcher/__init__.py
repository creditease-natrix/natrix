# -*- coding: utf-8 -*-
"""

"""
from __future__ import unicode_literals
import pprint

from .processor import DispatchProcessor, ResponseExpiryProcessor
from .channels.rabbitmq import RabbitMQChannel
from .states import CommandAPI
from .query import get_command_data, get_task_data

def dispatch_command(data):
    """
    {
        'command': {
            'command_uuid': '1111',
            'command_protocol': 'http',
            'command_destination': '',
            'command_parameters': {}
        },
        'task_tag': {
            'task_id': 'aaaa',
            'task_generate_time': 111111
        },
        'terminals': [
            {'mac': 'a', 'ip': '1.1.1.1'}, ....
        ]

    }

    :param data:
    :return:
    """
    processor = DispatchProcessor(data)
    processor.process()

    fail_record = processor.get_fail_record()


def get_process_client(channel, type):
    return RabbitMQChannel(channel, type)


def response_expired_process(freshness=300000):
    expired_list = CommandAPI.clean_expired_commands(freshness=freshness)
    for command in expired_list:
        processor = ResponseExpiryProcessor(data=command)
        processor.process()


def test():
    terminal_info = {
        'command': {
            'command_uuid': '78b05299-8f64-4d0b-af42-b3df4ab9046b',
            'command_protocol': 'ping',
            'command_destination': 'www.baidu.com',
            'command_parameters': {}
        },
        'task_tag': {
            'task_id': '78b05299-8f64-4d0b-af42-b3df4ab90461',
            'task_generate_time': 111111
        },
        'terminals': [
            {'mac': '28d2442aac27', 'ip': '1.1.1.1'},
            # {'mac': '0a01a7984d49', 'ip': '1.1.1.1'},
            # {'mac': 'f2cb92b3ec9a', 'ip': '1.1.1.1'},
        ]

    }

    dispatch_command(terminal_info)