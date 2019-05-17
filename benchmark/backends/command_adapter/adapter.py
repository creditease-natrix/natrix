# -*- coding: utf-8 -*-

from __future__ import unicode_literals, absolute_import
import logging, time, copy

import pprint

from natrix.common import exception as natrix_exceptions

from . import serializers as adapter_serializers

from .store import store_message
from .terminalapi import TerminalAPI

logger = logging.getLogger(__name__)

class CommandProcessor(object):
    """Command Processor

    Entrance of command adapter, it includes all methods about command-related process.
    There are three types of command-related message:
    - command info message
      High-level command message, it includes three attributes: command, timestamp and terminals_info.
      This type messages can generate many comamnd-request messages.
    - command request message

    - command response message


    """

    STAGES = ('distribute', 'dead', 'response')

    def __init__(self, stage, command):
        if not stage in self.STAGES:
            raise natrix_exceptions.ParameterException(parameter='stage')
        else:
            self.stage = stage

        self.command = command

    def distribute_command(self):
        """distribute command

        :return:
        """
        command_adapter = adapter_serializers.CommandAdapter(data=self.command)
        if not command_adapter.is_valid():
            logger.error('Receive an invaid data : {}'.format(command_adapter.format_errors()))
            raise natrix_exceptions.TriggerBugException(
                message=u'command is invalid: {}'.format(command_adapter.format_errors()))

        command_adapter.process()

    def process_dead_command(self):
        """process dead-command

        The command-reqeust message has a expirate time

        :return:
        """
        command_terminal = adapter_serializers.CommandTerminal(data=self.command)
        if not command_terminal.is_valid():
            logger.error('Receive an invaid data : {}'.format(command_terminal.format_errors()))
            raise natrix_exceptions.TriggerBugException(
                message=u'command is invalid: {}'.format(command_terminal.format_errors())
            )

        if not command_terminal.process():
            # TODO:
            logger.error('failed')
        else:
            logger.info('success')

    def process_dial_response(self):
        command_response = adapter_serializers.CommandResponse(data=self.command)
        if not command_response.is_valid():
            logger.error('Receive an invaid data : {}'.format(command_response.format_errors()))
            logger.error('Error format data info: {}'.format(self.command))
            raise natrix_exceptions.TriggerBugException(
                message=u'command is invalid: {}'.format(command_response.format_errors())
            )

        if not command_response.process():
            # TODO:
            pass

    @staticmethod
    def process_unresponse():
        messages = []
        message = {
            'errorcode': 2408,
            'errorinfo': u'Terminal response timeout'
        }
        message['command_response_process_time'] = int(time.time() * 1000)

        unresponse_info = adapter_serializers.AdapterCommandStatus.clean_command_cache()
        for command_uuid, command_info in unresponse_info.items():
            message['command_uuid'] = command_uuid
            for timestamp, terminals in command_info.items():
                message['command_generate_time'] = int(timestamp * 1000)
                for terminal in terminals:
                    temp_message = copy.copy(message)

                    temp_message['terminal'] = terminal

                    terminal_api = TerminalAPI(terminal)

                    temp_message['organization_id'] = terminal_api.get_org_ids()
                    temp_message['organization_name'] = terminal_api.get_org_names()
                    temp_message['organization_isp'] = terminal_api.get_register_isp()

                    temp_message['province'] = terminal_api.get_register_province()
                    temp_message['city'] = terminal_api.get_register_city()
                    messages.append(temp_message)
        # store message
        pprint.pprint(messages)
        for data in messages:
            store_message(type='error', data=data)

    def do(self):
        if self.stage == 'distribute':
            self.distribute_command()
        elif self.stage == 'dead':
            self.process_dead_command()
        elif self.stage == 'response':
            self.process_dial_response()
        else:
            # TODO:
            pass
