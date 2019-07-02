# -*- coding: utf-8 -*-
"""

"""
from __future__ import unicode_literals
import json, time

from rest_framework import serializers as rest_serializers

from natrix.common.natrix_views import serializers as natrix_serializers
from natrix.common import exception as natrix_exception
from ..states import CommandAPI

class ResponseCommandTag(natrix_serializers.NatrixSerializer):
    """Response Command Tag

    The part of command in terminal response.

    """
    uuid = rest_serializers.UUIDField()
    terminal = rest_serializers.CharField()


class ResponseTimestampTag(natrix_serializers.NatrixSerializer):
    """Response Timestamp Tag

    The information about time.

    """

    server_request_generate_time = rest_serializers.FloatField(min_value=0)
    terminal_request_receive_time = rest_serializers.FloatField(min_value=0)
    terminal_request_send_time = rest_serializers.FloatField(min_value=0)
    terminal_response_receive_time = rest_serializers.FloatField(min_value=0, allow_null=True)
    terminal_response_return_time = natrix_serializers.NullFloatField(min_value=0, allow_null=True)


class LocationSerializer(natrix_serializers.NatrixSerializer):
    """

    """
    country = rest_serializers.CharField()
    region = rest_serializers.CharField()
    province = rest_serializers.CharField()
    city = rest_serializers.CharField()
    county = rest_serializers.CharField(required=False, default=None)
    isp = rest_serializers.CharField()


class ProtocolSerializer(natrix_serializers.NatrixSerializer):
    """Protocol Serializer


    """

    @property
    def analyse_data(self):
        if not hasattr(self, '_validated_data'):
            msg = 'You must call `.is_valid()` before accessing `.validated_data`.'
            raise AssertionError(msg)

        return self._validated_data


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


class TerminalResponse(natrix_serializers.NatrixSerializer):
    command = ResponseCommandTag()
    status = rest_serializers.IntegerField(min_value=0, max_value=1)
    data = rest_serializers.JSONField()
    stamp = ResponseTimestampTag()

    def validate_data(self, value):
        """

        :param value:
        :return:
        """
        status = self.initial_data['status']
        if status == 0:
            command = self.initial_data['command']
            uuid = str(command.get('uuid'))
            command_protocol = CommandAPI.get_command_protocol(uuid)

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
            raise natrix_exception.ClassInsideException(
                message=u'Must call is_valid before using this method')

        return self._validated_data['stamp'].get('server_request_generate_time')

    def get_message_type(self):
        if not hasattr(self, '_validated_data'):
            raise natrix_exception.ClassInsideException(
                message=u'Must call is_valid before using this method')

        if not hasattr(self, '_message_type'):
            raise natrix_exception.ClassInsideException(
                message=u'Must call is_valid before using this method')

        return self._message_type

    def representation(self):
        if not hasattr(self, '_validated_data'):
            raise natrix_exception.ClassInsideException(
                message=u'Must call is_valid before using this method')

        command = self._validated_data['command']
        data = self._validated_data['data']
        stamp = self._validated_data['stamp']

        message = dict()
        # command info
        message['command_uuid'] = str(command.get('uuid'))
        message['command_generate_time'] = int(self._get_command_stamp() * 1000)

        # terminal info
        terminal = command.get('terminal')
        message['terminal'] = terminal

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

        message.update(data)

        return message



