# -*- coding: utf-8 -*-
"""

"""

from __future__ import unicode_literals
import logging

from rest_framework import serializers as rest_serializers

from natrix.common.natrix_views import serializers as natrix_serializers
from natrix.common import exception as natrix_exception
from benchmark.configurations import task_conf

logger = logging.getLogger(__name__)
choice_filter = lambda x: (x.get('name'), x.get('verbose_name'))

class CommandInfo(natrix_serializers.NatrixSerializer):
    """Command Information.

    """
    command_uuid = rest_serializers.UUIDField()
    command_protocol = rest_serializers.ChoiceField(
                    choices=map(choice_filter, task_conf.PROTOCOL_INFO.values()))
    command_destination = natrix_serializers.SchemeURLField()
    command_parameters = rest_serializers.DictField()


class TerminalInfo(natrix_serializers.NatrixSerializer):
    """Terminal Information.

    """
    mac = rest_serializers.CharField(max_length=32)
    ip = rest_serializers.IPAddressField()


class TaskInfo(natrix_serializers.NatrixSerializer):

    task_id = rest_serializers.UUIDField()
    task_generate_time = rest_serializers.FloatField()


class TaskCommandInfo(natrix_serializers.NatrixSerializer):
    """Task Information.

    In user viewpoint, the unit is a task which contains command, terminals and other configuration
    information. This Object is used to verify task information.

    """
    command = CommandInfo()
    task_tag = TaskInfo()
    terminals = rest_serializers.ListField(child=TerminalInfo())

    def get_task_tag(self):
        if not hasattr(self, '_validated_data'):
            raise natrix_exception.ClassInsideException(
                message=u'Must call is_valid before using this method')

        try:
            task_tag = self._validated_data['task_tag']

            return {
                'task_id': str(task_tag.get('task_id')),
                'task_generate_time': task_tag.get('task_generate_time')
            }
        except Exception as e:
            natrix_exception.natrix_traceback()
            logger.error('Get task tags occur error: {}'.format(e))
            return None

    def get_terminals(self):
        if not hasattr(self, '_validated_data'):
            raise natrix_exception.ClassInsideException(
                message=u'Must call is_valid before using this method')
        try:
            terminals = self._validated_data['terminals']

            return terminals
        except Exception as e:
            natrix_exception.natrix_traceback()
            logger.error('Get terminals occur error: {}'.format(e))
            return None

    def get_terminal_command(self, timestamp):
        """Construct Terminal Command.

        Terminal Command is terminal understanding command structure.

        :param timestamp: timestamp is command generate_timestamp
        :return:
        """
        if not hasattr(self, '_validated_data'):
            raise natrix_exception.ClassInsideException(
                message=u'Must call is_valid before using this method')
        try:
            command = self._validated_data['command']
            terminal_command = {
                'uuid': str(command.get('command_uuid')),
                'protocol': command.get('command_protocol'),
                'destination': command.get('command_destination'),
                'parameters': command.get('command_parameters'),
                'generate_timestamp': timestamp,
            }

            return terminal_command
        except Exception as e:
            natrix_exception.natrix_traceback()
            logger.error('Construct terminal command occur error: {}'.format(e))
            return None


class ExpiredResponseInfo(natrix_serializers.NatrixSerializer):
    """

    """
    command_uuid = rest_serializers.UUIDField()
    terminal = rest_serializers.CharField(max_length=32)
    task_tags = rest_serializers.ListField(child=TaskInfo())
    timestamp = rest_serializers.FloatField()

    def get_task_tags(self):
        if not hasattr(self, '_validated_data'):
            raise natrix_exception.ClassInsideException(
                message=u'Must call is_valid before using this method')

        try:
            task_tags = self._validated_data['task_tags']
            tags_list = []
            for tag in task_tags:
                tags_list.append({
                    'task_id': str(tag.get('task_id')),
                    'task_generate_time': tag.get('task_generate_time')
                })
            return tags_list
        except Exception as e:
            natrix_exception.natrix_traceback()
            logger.error('Get task tags occur error: {}'.format(e))
            return None







