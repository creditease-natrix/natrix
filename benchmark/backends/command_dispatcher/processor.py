# -*- coding: utf-8 -*-
"""


"""

from __future__ import unicode_literals
import logging, time, json

from natrix.common import exception as natrix_exception
from natrix.common import mqservice

from .serializers.task import TaskCommandInfo, ExpiredResponseInfo
from .serializers.command import TerminalCommand
from .serializers.response import TerminalResponse

from .states import CommandAPI
from .channels.rabbitmq import RabbitMQChannel
from .store import store_message
from .terminalapi import TerminalAPI

logger = logging.getLogger(__name__)

class Processor(object):
    pass


class DispatchProcessor(Processor):

    def __init__(self, data):
        self.data = data
        serializer = TaskCommandInfo(data=data)
        if serializer.is_valid():
            self.serializer = serializer
        else:
            logger.error('Dispatch task with wrong format data: {}'.format(
                    serializer.format_errors()))
            raise natrix_exception.ClassInsideException('Dispatch task error !')

        self.command_timestamp = time.time()
        self.fail_records = []

    def __add_fail_record(self, terminal, command_uuid, error):
        self.fail_records.append({
            'terminal': terminal,
            'command_uuid': command_uuid,
            'error': u'Publish command with error: {}'.format(error)
        })

    def get_fail_record(self):
        return self.fail_records

    def command_dispatch(self, terminal, data):
        try:
            with mqservice.MQService.get_purge_channel() as channel:
                terminal_channel = RabbitMQChannel(channel=channel, type='request')
                data['terminal'] = terminal
                terminal_channel.publish_request(data=data, terminal=terminal)
        except Exception as e:
            natrix_exception.natrix_traceback()
            logger.error('Dispatch command with error: {}'.format(e))

    def process(self):
        terminals = self.serializer.get_terminals()
        command_info = self.serializer.get_terminal_command(self.command_timestamp)
        task_tag = self.serializer.get_task_tag()
        command_uuid = command_info.get('uuid')
        for terminal in terminals:
            mac = terminal.get('mac', None)
            try:
                available_response = CommandAPI.available_response(command_uuid, mac)
                if not(available_response is None):
                    protocol_type = CommandAPI.get_command_protocol(command_uuid)

                    available_response['taks_id'] = task_tag.get('task_id', None)
                    available_response['task_generate_time'] = int(task_tag.get('task_generate_time') * 1000)
                    store_message(protocol_type, available_response)
                    continue

                registry_result = CommandAPI.registry_command(command_uuid=command_uuid,
                                                              terminal=mac,
                                                              command_timestamp=self.command_timestamp,
                                                              command_info=command_info,
                                                              task_info=task_tag)
                if registry_result is None:
                    logger.error('Registry command failed.')
                    self.__add_fail_record(mac, command_uuid, 'Registry command error!')
                elif registry_result == 'update':
                    pass
                elif registry_result == 'create':
                    self.command_dispatch(mac, command_info)
                else:
                    logger.error('Registry command with an unexpected result: {}'.format(registry_result))
                    self.__add_fail_record(mac, command_uuid, 'Registry command error!')

            except Exception as e:
                natrix_exception.natrix_traceback()
                logger.error('Dispatch terminal({mac}) command({command_uuid}) with error'.format(
                    mac=mac, command_uuid=command_uuid
                ))
                self.__add_fail_record(mac, command_uuid, e)


class CommandExpiredProcessor(Processor):

    def __init__(self, data):
        self.data = data
        serializer = TerminalCommand(data=data)
        if serializer.is_valid():
            self.serializer = serializer
        else:
            logger.error('Process expired command with wrong format data: {}'.format(
                serializer.format_errors()))
            raise natrix_exception.ClassInsideException('Process expired command error !')

    def store_expired_result(self, task_tags, data_template):

        for task_info in task_tags:
            data_template['task_id'] = task_info.get('task_id', None)
            data_template['task_generate_time'] = int(task_info.get('task_generate_time', 0) * 1000)

            store_message(type='error', data=data_template)

    def process(self):
        command_uuid = str(self.serializer.validated_data.get('uuid'))
        command_generate_time = self.serializer.validated_data.get('generate_timestamp')
        terminal = self.serializer.validated_data.get('terminal')

        terminal_info = TerminalAPI(terminal)

        data_template = {
            'errorcode': 1408,
            'errorinfo': u'Terminal do not consume',
            'command_uuid': command_uuid,
            'command_generate_time': int(command_generate_time * 1000),
            'terminal': terminal,
            'command_response_process_time': int(time.time() * 1000)
        }

        data_template['province'] = terminal_info.get_register_province()
        data_template['city'] = terminal_info.get_register_city()

        task_tags = CommandAPI.erase_command(command_uuid, terminal, command_generate_time)
        if task_tags is None:
            logger.error('Expired consuming command without task info!')
        else:
            self.store_expired_result(task_tags, data_template)


class ResponseProcessor(Processor):

    def __init__(self, data):
        self.data = data
        serializer = TerminalResponse(data=data)
        if serializer.is_valid():
            self.serializer = serializer
        else:
            logger.error('Process terminal response with wrong format data: {}'.format(
                serializer.format_errors()
            ))
            raise natrix_exception.ClassInsideException('Process terminal response error!')

    def store_response_result(self, protocol_type, task_tags, data_template):
        """

        :param task_tags:
        :param data_template:
        :return:
        """
        for task_info in task_tags:
            data_template['task_id'] = task_info.get('task_id', None)
            data_template['task_generate_time'] = int(task_info.get('task_generate_time', 0) * 1000)

            res = store_message(protocol_type, data_template)
            logger.debug('Store response data : {}'.format(res))

    def process(self):
        try:
            data_template = self.serializer.representation()
            command_uuid = data_template.get('command_uuid')
            command_generate_time = data_template.get('command_generate_time') / 1000.0
            terminal = data_template.get('terminal')

            terminal_info = TerminalAPI(terminal)
            data_template['province'] = terminal_info.get_register_province()
            data_template['city'] = terminal_info.get_register_city()

            # update response data
            CommandAPI.update_response(command_uuid, terminal, data_template)

            task_tags = CommandAPI.erase_command(command_uuid,
                                                 terminal,
                                                 command_generate_time)
            if task_tags is None:
                logger.error('Process response data without task info!')
            else:
                logger.debug('Process response data')
                self.store_response_result(self.serializer.get_message_type(),
                                           task_tags,
                                           data_template)

        except Exception as e:
            natrix_exception.natrix_traceback()
            logger.error('Process response data with error: {}'.format(e))


class ResponseExpiryProcessor(Processor):

    def __init__(self, data):
        self.data = data
        serializer = ExpiredResponseInfo(data=data)
        if serializer.is_valid():
            self.serializer = serializer
        else:
            logger.error('Process expired response with wrong format data: {}'.format(
                serializer.format_errors()
            ))
            raise natrix_exception.ClassInsideException('Process expired response error!')

        self._fail_record = []

    def store_expired_result(self, task_tags, data_template):
        for task_info in task_tags:
            try:
                data_template['task_id'] = task_info.get('task_id', None)
                data_template['task_generate_time'] = int(task_info.get('task_generate_time', 0) * 1000)
                store_message(type='error', data=data_template)
            except Exception as e:
                logger.error('Store ResponseExpired message with error: {}'.format(e))
                natrix_exception.natrix_traceback()
                self._fail_record.append({
                    'task_inf': task_info
                })

    def process(self):
        command_uuid = str(self.serializer.validated_data.get('command_uuid'))
        command_generate_time = int(self.serializer.validated_data.get('timestamp'))
        terminal = self.serializer.validated_data.get('terminal')
        task_tags = self.serializer.get_task_tags()

        try:
            terminal_info = TerminalAPI(terminal)

            data_template = {
                'errorcode': 2408,
                'errorinfo': u'Terminal response timeout',
                'command_uuid': command_uuid,
                'command_generate_time': command_generate_time * 1000,
                'terminal': terminal,
                'command_response_process_time': int(time.time() * 1000),
            }

            data_template['province'] = terminal_info.get_register_province()
            data_template['city'] = terminal_info.get_register_city()

            self.store_expired_result(task_tags, data_template)

        except Exception as e:
            natrix_exception.natrix_traceback()

