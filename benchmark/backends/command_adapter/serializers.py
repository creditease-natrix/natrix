# -*- coding: utf-8 -*-
"""All serializer definition for command adapter

"""
from __future__ import unicode_literals
import logging, time, json
import pprint

import pika
from rest_framework import serializers as rest_serializers

from natrix.common.natrix_views import serializers as natrix_serializers
from natrix.common import exception as natrix_exceptions, mqservice

from benchmark.configurations import task_conf

from .states import AdapterCommandStatus
from .adapter_settting import AdapterMQSetting, EXCHANGE_REQUEST_TEMPLATE
from .store import store_message
from .terminalapi import TerminalAPI

logger = logging.getLogger(__name__)
choice_filter = lambda x: (x.get('name'), x.get('verbose_name'))


class CommandInfo(natrix_serializers.NatrixSerializer):
    """

    """
    command_uuid = rest_serializers.UUIDField()
    command_protocol = rest_serializers.ChoiceField(choices=map(choice_filter,
                                                           task_conf.PROTOCOL_INFO.values()))
    command_destination = natrix_serializers.SchemeURLField()
    command_parameters = rest_serializers.DictField()


class TerminalInfo(natrix_serializers.NatrixSerializer):
    mac = rest_serializers.CharField(max_length=32)
    ip = rest_serializers.IPAddressField()


class CommandAdapter(natrix_serializers.NatrixSerializer):
    """请求类型数据处理

    """
    command = CommandInfo()
    timestamp = rest_serializers.FloatField(min_value=0, default=time.time())
    terminals = rest_serializers.ListField(child=TerminalInfo())

    def init_command_status(self):
        """初始化command状态

        :return:
        """
        if not hasattr(self, '_validated_data'):
            raise natrix_exceptions.ClassInsideException(
                message=u'Must call is_valid before using this method')

        terminals = [ t.get('mac') for t in self._validated_data['terminals']]
        command_uuid = self._validated_data.get('command').get('command_uuid')
        command_protocol = self._validated_data.get('command').get('command_protocol')
        timestamp = self._validated_data.get('timestamp')
        AdapterCommandStatus.add_command_cache(str(command_uuid), timestamp,
                                               terminals, command_protocol)

    def distribute_command(self):
        """命令分发

        将command分发到不同的RabbitMQ队列中。

        :return:
        """
        if not hasattr(self, '_validated_data'):
            raise natrix_exceptions.ClassInsideException(
                message=u'Must call is_valid before using this method')

        with mqservice.MQService.get_purge_channel() as channel:
            try:
                terminals = [ t.get('mac') for t in self._validated_data['terminals']]
                command_timestamp = self._validated_data['timestamp']
                command = self._validated_data['command']

                publish_data = {
                    'uuid': str(command.get('command_uuid')),
                    'protocol': command.get('command_protocol'),
                    'destination': command.get('command_destination'),
                    'parameters': command.get('command_parameters'),
                    'generate_timestamp': command_timestamp,
                }

                # TODO: 思考如果取消重复声明、绑定(队列)
                for terminal_tag in terminals:

                    AdapterMQSetting.init_request_queue(channel, terminal_tag)
                    exchange_name = EXCHANGE_REQUEST_TEMPLATE.format(tag=terminal_tag)

                    publish_data['terminal'] = terminal_tag

                    channel.basic_publish(exchange=exchange_name,
                                              routing_key='command',
                                              body=json.dumps(publish_data),
                                              properties=pika.BasicProperties(delivery_mode=2))
            except Exception as e:
                # TODO: 梳理pika的异常
                logger.error(e)
                raise natrix_exceptions.ClassInsideException(message=u'Distribute command failed!')

    def process(self):
        if not hasattr(self, '_validated_data'):
            raise natrix_exceptions.ClassInsideException(
                message=u'Must call is_valid before using this method')

        try:
            # 下发command到终端
            self.distribute_command()
            # 初始化command状态
            self.init_command_status()
        except natrix_exceptions.BaseException as e:
            logger.error('Distribute command failed: {}'.format(e.get_log()))


class CommandTerminal(natrix_serializers.NatrixSerializer):
    """command终端数据

    关于单一终端的command信息

    """
    uuid = rest_serializers.UUIDField()
    protocol = rest_serializers.ChoiceField(choices=map(choice_filter,
                                                   task_conf.PROTOCOL_INFO.values()))
    destination = natrix_serializers.SchemeURLField()
    parameters = rest_serializers.DictField()

    generate_timestamp = rest_serializers.FloatField(min_value=0)
    terminal = rest_serializers.CharField(max_length=12)


    def _update_command_status(self):
        """更新command状态

        :return:
        """

        if not hasattr(self, '_validated_data'):
            raise natrix_exceptions.ClassInsideException(
                message=u'Must call is_valid before using this method')

        terminal_tag = self._validated_data['terminal']
        command_uuid = str(self._validated_data['uuid'])
        timestamp = self._validated_data['generate_timestamp']

        command_exist, record_exist = AdapterCommandStatus.remove_command_cache(
            command_uuid, timestamp, terminal_tag
        )

        if not command_exist:
            logger.error('There is not command instance for this dead message: {command_uuid}-{timestamp}'.format(
                command_uuid=command_uuid, timestamp=timestamp))
            return command_exist

        if not record_exist:
            logger.error('There is not command record for this dead message: {command_uuid}-{timestamp}-{terminal}'.format(
                command_uuid=command_uuid, timestamp=timestamp, terminal=terminal_tag))
            return record_exist

        return True

    def store(self, stage='dead'):
        """持久化存储

        :return:
        """

        if not hasattr(self, '_validated_data'):
            raise natrix_exceptions.ClassInsideException(
                message=u'Must call is_valid before using this method')

        if not hasattr(self, 'is_store'):
            raise natrix_exceptions.ClassInsideException(
                message='Must call _get_message to generate message before store.')

        if self.is_store:
            logger.info('A message(dead) can only store one time')
            return

        res = store_message(type='error', data=self.message)
        logger.info('store result : {}'.format(res))

    def _get_message(self):
        """

        :return:
        """
        if not hasattr(self, '_validated_data'):
            raise natrix_exceptions.ClassInsideException(
                message=u'Must call is_valid before using this method')

        if not hasattr(self, 'is_store'):
            self.is_store = False

        message = {
            'errorcode': 1408,
            'errorinfo': u'Terminal do not consume'
        }
        message['command_uuid'] = self._validated_data['uuid']
        message['command_generate_time'] = int(self._validated_data['generate_timestamp'] * 1000)
        message['terminal'] = self._validated_data['terminal']

        terminal_api = TerminalAPI(message['terminal'])

        message['organization_id'] = terminal_api.get_org_ids()
        message['organization_name'] = terminal_api.get_org_names()
        message['organization_isp'] = terminal_api.get_register_isp()

        message['province'] = terminal_api.get_register_province()
        message['city'] = terminal_api.get_register_city()

        message['command_response_process_time'] = int(time.time() * 1000)

        self.message = message

    def _dead_message_process(self):
        """Dead Message Process

        To process dead message, include:
        - process command status in cache
        - generate message (used to store)
        - store message

        :return:
        """
        if not hasattr(self, '_validated_data'):
            raise natrix_exceptions.ClassInsideException(
                message=u'Must call is_valid before using this method')

        status_res = self._update_command_status()
        if not status_res:
            logger.error('Update command status error, drop this message!')
            return
        self._get_message()
        self.store()

    def process(self, stage='dead'):
        """

        :param stage:
        :return:
        """
        if not hasattr(self, '_validated_data'):
            raise natrix_exceptions.ClassInsideException(
                message=u'Must call is_valid before using this method')

        try:
            if stage == 'dead':
                self._dead_message_process()

        except natrix_exceptions.BaseException as e:
            # TODO: exception process
            logger.error()


class CommandTag(natrix_serializers.NatrixSerializer):
    """Command 标记

    用于Command响应中

    """
    uuid = rest_serializers.UUIDField()
    terminal = rest_serializers.CharField()


class ProtocolSerializer(natrix_serializers.NatrixSerializer):
    """Protocol Serializer


    """

    @property
    def analyse_data(self):
        if not hasattr(self, '_validated_data'):
            msg = 'You must call `.is_valid()` before accessing `.validated_data`.'
            raise AssertionError(msg)

        return self._validated_data


class LocationSerializer(natrix_serializers.NatrixSerializer):
    """

    """
    country = rest_serializers.CharField()
    region = rest_serializers.CharField()
    province = rest_serializers.CharField()
    city = rest_serializers.CharField()
    county = rest_serializers.CharField(required=False, default=None)
    isp = rest_serializers.CharField()


class PingSerializer(ProtocolSerializer):
    """The data part of ping response

    """
    destination = rest_serializers.CharField()
    destination_ip = rest_serializers.IPAddressField()
    destination_location = LocationSerializer(required=False, allow_null=True)
    packet_send = rest_serializers.IntegerField()
    packet_receive = rest_serializers.IntegerField()
    packet_loss = rest_serializers.IntegerField()
    packet_size = rest_serializers.IntegerField()
    avg_time = rest_serializers.FloatField()
    max_time = rest_serializers.FloatField()
    min_time = rest_serializers.FloatField()


class HttpSerializer(ProtocolSerializer):
    """The data part of http response

    """
    url = natrix_serializers.SchemeURLField()
    last_url = natrix_serializers.SchemeURLField()
    status_code = rest_serializers.IntegerField()
    redirect_count = rest_serializers.IntegerField()
    redirect_time = rest_serializers.FloatField()

    remote_ip = rest_serializers.IPAddressField()
    remote_location = LocationSerializer()
    remote_port = rest_serializers.IntegerField()

    local_ip = rest_serializers.IPAddressField()
    local_location = LocationSerializer()
    local_port = rest_serializers.IntegerField()

    total_time = rest_serializers.FloatField()
    period_nslookup = rest_serializers.FloatField()
    period_tcp_connect = rest_serializers.FloatField()
    period_ssl_connect = rest_serializers.FloatField()
    period_request = rest_serializers.FloatField()
    period_response = rest_serializers.FloatField()
    period_transfer = rest_serializers.FloatField()
    size_upload = rest_serializers.FloatField()
    size_download = rest_serializers.FloatField()
    speed_upload = rest_serializers.FloatField()
    speed_download = rest_serializers.FloatField()
    response_header = rest_serializers.CharField(required=False)
    response_body = rest_serializers.CharField(required=False)


class IPLocationSerializer(natrix_serializers.NatrixSerializer):
    """IP and Location information

    """
    ip = rest_serializers.IPAddressField()
    location = LocationSerializer(required=False, allow_null=True)


class DnsSerializer(ProtocolSerializer):
    """The data part of dns response

    """
    ips = rest_serializers.ListField(child=IPLocationSerializer())
    destination = rest_serializers.CharField()
    ptime = rest_serializers.FloatField()
    dns_server = IPLocationSerializer()


class PathNodeSerialzier(natrix_serializers.NatrixSerializer):
    """Path Node Serializer

    The node in the path of network, used by TraceroutePathSerializer class.

    """
    ip = rest_serializers.CharField()
    hostname = rest_serializers.CharField()
    location = LocationSerializer(required=False, allow_null=True)
    response_times = rest_serializers.FloatField()


class TraceroutePathSerializer(ProtocolSerializer):
    """The data part of traceroute response

    """
    routes = rest_serializers.ListField(child=PathNodeSerialzier())
    seq = rest_serializers.IntegerField(min_value=1)


class TracerouteSerializer(ProtocolSerializer):
    """

    """
    paths = rest_serializers.ListField(child=TraceroutePathSerializer())

    @property
    def analyse_data(self):
        data = super(TracerouteSerializer, self).analyse_data

        paths_list = data.get('paths')

        return {
            'hop': len(paths_list),
            'paths': paths_list
        }


class ErrorSerializer(ProtocolSerializer):
    """The data part of error response

    """
    errorcode = rest_serializers.IntegerField()
    errorinfo = rest_serializers.CharField()


class ResponseStampTag(natrix_serializers.NatrixSerializer):
    """

    """

    server_request_generate_time = rest_serializers.FloatField(min_value=0)
    terminal_request_receive_time = rest_serializers.FloatField(min_value=0)
    terminal_request_send_time = rest_serializers.FloatField(min_value=0)
    terminal_response_receive_time = rest_serializers.FloatField(min_value=0, allow_null=True)
    terminal_response_return_time = natrix_serializers.NullFloatField(min_value=0, allow_null=True)


class CommandResponse(natrix_serializers.NatrixSerializer):
    """Command Response

    """
    command = CommandTag()
    status = rest_serializers.IntegerField(min_value=0, max_value=1)
    data = rest_serializers.JSONField()
    stamp = ResponseStampTag()

    def validate_data(self, value):
        """validate data field

        :param value:
        :return:
        """
        status = self.initial_data['status']
        if status == 0:
            command = self.initial_data['command']
            uuid = str(command.get('uuid'))
            command_protocol = AdapterCommandStatus.get_command_type(uuid)

            self._message_type = command_protocol

            if command_protocol == 'ping':
                data_serializer = PingSerializer(data=value)
            elif command_protocol == 'http':
                data_serializer = HttpSerializer(data=value)
            elif command_protocol == 'traceroute':
                data_serializer = TracerouteSerializer(data={'paths': value})
            elif command_protocol == 'dns':
                data_serializer = DnsSerializer(data=value)
            else:
                raise rest_serializers.ValidationError('Unkown this command({}) protocol type'.format(uuid))
        else:
            data_serializer = ErrorSerializer(data=value)
            self._message_type = 'error'

        if data_serializer.is_valid():
            return data_serializer.analyse_data
        else:
            raise rest_serializers.ValidationError(
                data_serializer.format_errors()
                if hasattr(data_serializer, 'format_errors') else json.dumps(data_serializer.errors)
            )

    def _get_command_stamp(self):
        """Get command timestamp ().

        :return:
        """
        if not hasattr(self, '_validated_data'):
            raise natrix_exceptions.ClassInsideException(
                message=u'Must call is_valid before using this method')

        return self._validated_data['stamp'].get('server_request_generate_time')

    def _update_command_status(self):
        """Update command status in cache.

        Note: be same with CommandTerminal._update_command_status

        :return:
        """
        if not hasattr(self, '_validated_data'):
            raise natrix_exceptions.ClassInsideException(
                message=u'Must call is_valid before using this method')
        command = self._validated_data['command']
        command_uuid = str(command.get('uuid'))
        terminal_tag = command.get('terminal')
        timestamp = self._get_command_stamp()

        command_exist, record_exist = AdapterCommandStatus.remove_command_cache(
            command_uuid, timestamp, terminal_tag
        )

        if not command_exist:
            logger.error('There is not command instance for this response message: {command_uuid}-{timestamp}'.format(
                command_uuid=command_uuid, timestamp=timestamp))
            return command_exist

        if not record_exist:
            logger.error(
                'There is not command record for this dead message: {command_uuid}-{timestamp}-{terminal}'.format(
                    command_uuid=command_uuid, timestamp=timestamp, terminal=terminal_tag))
            return record_exist

        return True

    def store(self):
        if not hasattr(self, '_validated_data'):
            raise natrix_exceptions.ClassInsideException(
                message=u'Must call is_valid before using this method')

        if not hasattr(self, 'is_store'):
            raise natrix_exceptions.ClassInsideException(
                message='Must call _get_message to generate message before store.')

        if self.is_store:
            logger.info('A message(response) can only store one time')

        res = store_message(type=self._message_type, data=self.message)
        logger.debug('store result : {}'.format(res))

    def _get_message(self):
        if not hasattr(self, '_validated_data'):
            raise natrix_exceptions.ClassInsideException(
                message=u'Must call is_valid before using this method')

        if not hasattr(self, 'is_store'):
            self.is_store = False

        command = self._validated_data['command']
        data = self._validated_data['data']
        stamp = self._validated_data['stamp']


        message = dict()
        # command info
        message['command_uuid'] = str(command.get('uuid'))
        message['command_generate_time'] = int(self._get_command_stamp() * 1000)

        # terminal info
        terminal = command.get('terminal')
        message.update(self._get_terminal_info(terminal))

        # timestamp info: from second convert to millisecond
        message['response_process_time'] = int(time.time() * 1000)

        message['terminal_request_receive_time'] = int(stamp.get('terminal_request_receive_time') * 1000)
        message['terminal_request_send_time'] = int(stamp.get('terminal_request_send_time') * 1000)
        if stamp.get('terminal_response_receive_time'):
            response_receive_time = int(stamp.get('terminal_response_receive_time') * 1000)
        else:
            response_receive_time = None
        message['terminal_response_receive_time'] = response_receive_time

        if stamp.get('terminal_response_return_time'):
            response_return_time = int(stamp.get('terminal_response_return_time') * 1000)
        else:
            response_return_time = None
        message['terminal_response_return_time'] = response_return_time

        # response info
        message.update(data)

        self.message = message

    def _get_terminal_info(self, terminal):
        terminal_info = {'terminal': terminal}

        terminal_api = TerminalAPI(terminal)

        terminal_info['organization_id'] = terminal_api.get_org_ids()
        terminal_info['organization_name'] = terminal_api.get_org_names()
        terminal_info['organization_isp'] = terminal_api.get_register_isp()

        terminal_info['province'] = terminal_api.get_register_province()
        terminal_info['city'] = terminal_api.get_register_city()

        return terminal_info


    def _response_message_process(self):
        """

        :return:
        """
        if not hasattr(self, '_validated_data'):
            raise natrix_exceptions.ClassInsideException(
                message=u'Must call is_valid before using this method')

        status_res = self._update_command_status()
        if not status_res:
            logger.error('Update command status errro, drop this response message!')
            return
        self._get_message()
        self.store()


    def process(self):
        if not hasattr(self, '_validated_data'):
            raise natrix_exceptions.ClassInsideException(
                message=u'Must call is_valid before using this method')

        self._response_message_process()


