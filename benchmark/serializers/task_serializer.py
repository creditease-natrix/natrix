# -*- coding: utf-8 -*-
"""

"""
from __future__ import unicode_literals, absolute_import
import logging, json, time, copy, datetime
from collections import OrderedDict

import pprint

from django.utils import timezone
from django.db import transaction
from django.db.models import Q
from django.contrib.auth.models import Group
from rest_framework import serializers

from natrix.common.natrix_views.serializers import NatrixSerializer, NatrixQuerySerializer
from natrix.common.natrix_views.fields import SchemeURLField
from natrix.common import exception as natrix_exception
from benchmark.models.task_models import Task, Command, Schedule, FollowedTask
from benchmark.models.task_models import (PROTOCOL_CHOICES, SCOPE_CHOICES)
from benchmark.backends.command_dispatcher import dispatch_command
from benchmark.backends import celery_api
from benchmark.terminalutil import terminal_policy
from benchmark.tasks import timed_task_process



logger = logging.getLogger(__name__)


TIMESTAMP_UTC = lambda timestamp: datetime.datetime.fromtimestamp(timestamp, tz=timezone.utc)


class TerminalConditionSerializer(NatrixSerializer):

    filter_type = serializers.ChoiceField(choices=(('region', u'区域'), ('organization', u'组织')),
                                          help_text=u'过滤类型')
    filter_condition = serializers.ListField(help_text=u'过滤条件', child=serializers.CharField())
    # network_type = serializers.MultipleChoiceField(choices=(('all', u'全部'),
    #                                                 ('wire', u'有线'),
    #                                                 ('wireless', u'无线'),
    #                                                 ('mobile', u'移动')),
    #                                                help_text=u'网络类型')
    # isp_type = serializers.MultipleChoiceField(choices=(('all', u'全部'), ), help_text=u'运营商')
    terminal_select = serializers.BooleanField(required=True)
    terminals = serializers.ListField(child=serializers.CharField(max_length=12),
                                      allow_empty=True, required=False, allow_null=True)

    def is_valid(self, raise_exception=False):
        flag = super(TerminalConditionSerializer, self).is_valid()

        if not flag:
            return flag

        terminal_select = self.initial_data.get('terminal_select')
        terminals = self.initial_data.get('terminals')
        if terminal_select:
            if not isinstance(terminals, list) or not terminals:
                self._errors['terminals'] = ['"terminals" must be a list in terminal_condition if "terminal_select" is true']
                return False

        return True


class PingProcotolSerializer(NatrixSerializer):
    timeout = serializers.IntegerField()
    count = serializers.IntegerField()
    packet_size = serializers.IntegerField()

    def command_representation(self):
        assert hasattr(self, '_errors'), (
            'You must call `.isvalid()` before calling `.command_representation()`'
        )

        assert not self.errors, (
            'You can not call `.command_representtation()` on a serializer with invalid data.'
        )

        protocol_conf = {
            'timeout': self.validated_data.get('timeout'),
            'count': self.validated_data.get('count'),
            'packet_size': self.validated_data.get('packet_size')
        }

        return protocol_conf


class HttpProtocolSerializer(NatrixSerializer):
    protocol = serializers.ChoiceField(choices=(('HTTP1.1', u'HTTP 1.1版本')))
    timeout = serializers.IntegerField(help_text=u'超时时间', default=600)
    is_redirect = serializers.BooleanField(default=True)
    redirect_count = serializers.IntegerField(default=5)
    is_snapshot = serializers.BooleanField(default=False)

    auth_info = serializers.CharField(required=False, allow_blank=True,
                                      allow_null=True, help_text=u'认证信息JSON')
    header_info = serializers.CharField(required=False, allow_blank=True,
                                        allow_null=True, help_text=u'HTTP头部')
    body_info = serializers.CharField(required=False, allow_blank=True,
                                      allow_null=True, help_text=u'HTTP主体')

    def validate_auth_info(self, value):
        """validate auth_info field

        There are two fields in auth_info json string:
         - auth_type: only support basic type
         - auth_user:

        :param value:
        :return:
        """
        try:
            auth_conf = json.loads(value)
            if auth_conf:
                auth_type = auth_conf.get('auth_type', None)
                auth_user = auth_conf.get('auth_user', None)

                if auth_type is None:
                    raise serializers.ValidationError('The auth_type is required.')

                if not (auth_type in ('basic', )):
                    raise serializers.ValidationError('The auth_type must in [basic, ])')

                if auth_user is None:
                    raise serializers.ValidationError('The auth_user is required.')

            return value

        except ValueError:
            raise serializers.ValidationError('The auth_info must be a json string.')
        except TypeError:
            raise serializers.ValidationError('The auth_info must be a string or buffer')

    def validate_header_info(self, value):
        try:
            json.loads(value)
            return value
        except ValueError:
            raise serializers.ValidationError('The header_info must be a json string.')
        except TypeError:
            raise serializers.ValidationError('The header_info must be a string or buffer')


    def validate_body_info(self, value):
        try:
            json.loads(value)
            return value
        except ValueError:
            raise serializers.ValidationError('The body_info must be a json string.')
        except TypeError:
            raise serializers.ValidationError('The body_info must be a string or buffer')

    def command_representation(self):
        assert hasattr(self, '_errors'), (
            'You must call `.isvalid()` before calling `.command_representation()`'
        )

        assert not self.errors, (
            'You can not call `.command_representtation()` on a serializer with invalid data.'
        )

        protocol_conf = {
            'prototol': self.validated_data.get('protocol'),
            'timeout': self.validated_data.get('timeout'),
            'allow_redirects': self.validated_data.get('is_redirect'),
            'max_redirects': self.validated_data.get('redirect_count'),
            'save_response_body': self.validated_data.get('is_snapshot'),
        }

        if self.validated_data.get('auth_info'):
            auth_conf = json.loads(self.validated_data.get('auth_info'))
            if auth_conf:
                protocol_conf['auth_type'] = auth_conf.get('auth_type')
                protocol_conf['auth_user'] = auth_conf.get('auth_user')

        if self.validated_data.get('header_info'):
            header_conf = json.loads(self.validated_data.get('header_info'))
            if header_conf:
                protocol_conf['http_header'] = self.validated_data.get('header_info')

        if self.validated_data.get('body_info'):
            body_conf = json.loads(self.validated_data.get('body_info'))
            if body_conf:
                protocol_conf['http_body'] = self.validated_data.get('body_info')


        return protocol_conf


class DnsProtocolSerializer(NatrixSerializer):
    is_default = serializers.BooleanField(help_text=u'是否使用默认DNS', default=True)
    dns_server = serializers.IPAddressField(help_text=u'自定义DNS IP', required=False,
                                            allow_null=True)
    timeout = serializers.IntegerField(help_text=u'超时时间(s)', default=10)

    def is_valid(self, raise_exception=False):
        flag = super(DnsProtocolSerializer, self).is_valid()

        if not flag:
            return flag

        is_default = self.initial_data.get('is_default')
        dns_server = self.initial_data.get('dns_server')
        if not is_default and dns_server is None:
            self._errors['dns_server'] = ['"dns_server" cant not be None if is_default is False.']
            return False

        return flag

    def command_representation(self):
        assert hasattr(self, '_errors'), (
            'You must call `.isvalid()` before calling `.command_representation()`'
        )

        assert not self.errors, (
            'You can not call `.command_representtation()` on a serializer with invalid data.'
        )

        protocol_conf = {
            'is_default': self.validated_data.get('is_default', True),
            'dns_server': self.validated_data.get('dns_server'),
            'timeout': self.validated_data.get('timeout', 10)
        }

        return protocol_conf


def natrix_protocol_validator(type, value):
    """Validate protocol configuration

    :param type: the type of protocol, include ping, http, dns
    :param value:
    :return:
    """
    # TODO: 对协议参数进行判断
    flag = True
    errors = {}
    if type == 'ping':
        serializer = PingProcotolSerializer(data=value)
    elif type == 'http':
        serializer = HttpProtocolSerializer(data=value)
    elif type == 'dns':
        serializer = DnsProtocolSerializer(data=value)
    else:
        return flag, errors

    if serializer.is_valid():
        return True, serializer.command_representation()
    else:
        return False, serializer.errors


class InstantTaskSerializer(NatrixSerializer):
    id = serializers.UUIDField(read_only=True, help_text=u'任务ID')
    status = serializers.BooleanField(read_only=True, help_text=u'任务状态')
    protocol_type = serializers.ChoiceField(choices=PROTOCOL_CHOICES, help_text=u'协议类型')
    http_method = serializers.ChoiceField(choices=[('get', 'GET'),
                                                ('post', 'POST'),
                                                ('put', 'PUT'),
                                                ('delete', 'DELETE')],
                                        help_text=u'HTTP方法',
                                        required=False)
    destination = SchemeURLField(help_text=u'目标地址')
    advanced_switch = serializers.BooleanField(default=False, help_text=u'高级功能开关')
    terminal_configuration = TerminalConditionSerializer(allow_null=True, required=False)
    protocol_switch = serializers.BooleanField(default=False, help_text=u'协议配置功能开关')
    protocol_configuration = serializers.DictField(allow_null=True, required=False)

    def natrix_protocol_validator(self, value, type):
        """validate protocol configuration

        :param value:
        :param type: string,
        :return:
        """
        # TODO: 对协议参数进行判断
        flag = True
        errors = {}
        if type == 'ping':
            serializer = PingProcotolSerializer(data=value)
        elif type == 'http':
            serializer = HttpProtocolSerializer(data=value)
        elif type == 'dns':
            serializer = DnsProtocolSerializer(data=value)
        else:
            return flag, errors

        flag = serializer.is_valid()
        errors = serializer.errors

        if flag:
            self.protocol_info = serializer.command_representation()

        return flag, errors

    def is_valid(self, raise_exception=False):
        flag = super(InstantTaskSerializer, self).is_valid()

        if not flag:
            return flag

        advanced_switch = self.initial_data.get('advanced_switch')
        terminal_configuration = self.initial_data.get('terminal_configuration')
        if advanced_switch:
            if terminal_configuration is None:
                self.initial_data['terminal_configuration'] = {}
        else:
            self.initial_data['terminal_configuration'] = None

        protocol_switch = self.initial_data.get('protocol_switch')
        protocol_type = self.initial_data.get('protocol_type')
        protocol_configuration = self.initial_data.get('protocol_configuration')

        if protocol_type == 'http':
            http_method = self.initial_data.get('http_method')
            if http_method is None:
                flag = False
                self._errors['http_method'] = ['The http_method field is required for http protocol!']
                return flag

        if protocol_switch:
            if protocol_configuration is None:
                self.initial_data['protocol_configuration'] = {}
            # validate protocol_configuration
            flag, errors = self.natrix_protocol_validator(protocol_configuration, protocol_type)
            if not flag:
                self._errors['protocol_configuration'] = errors
                return flag
        else:
            self.initial_data['protocol_configuration'] = None

        return flag

    def create(self, validated_data):
        protocol_type = validated_data.get('protocol_type')
        http_method = validated_data.get('http_method')
        destination = validated_data.get('destination')
        advanced_switch = validated_data.get('advanced_switch')
        terminal_configuration = validated_data.get('terminal_configuration')
        protocol_switch = validated_data.get('protocol_switch')
        protocol_configuration = validated_data.get('protocol_configuration')

        if not advanced_switch:
            terminal_configuration = dict()
        else:
            terminal_configuration = {
                'filter_type': terminal_configuration['filter_type'],
                'filter_condition': terminal_configuration['filter_condition'],
                # 'network_type': list(terminal_configuration['network_type']),
                # 'isp_type': list(terminal_configuration['isp_type']),
                'terminal_select': terminal_configuration['terminal_select'],
                'terminals': list(terminal_configuration['terminals'])
            }

        terminals = terminal_policy(advanced_switch, terminal_configuration)

        if not protocol_switch:
            protocol_configuration = dict()

        with transaction.atomic():
            # Generate procotol-related information
            if hasattr(self, 'protocol_info'):
                command_protocol = copy.deepcopy(self.protocol_info)
            else:
                command_protocol = dict()

            if http_method:
                command_protocol['operation'] = http_method


            command = Command.command_generator(protocol_type,
                                                command_protocol,
                                                destination)

            task = Task.objects.create(name='Instant Task',
                                       time_type='instant',
                                       purpose='benchmark',
                                       destination=destination,
                                       terminal_switch=advanced_switch,
                                       protocol_switch=advanced_switch and protocol_switch,
                                       terminal_condition=json.dumps(terminal_configuration),
                                       protocol_type=protocol_type,
                                       method=http_method,
                                       protocol_condition=json.dumps(protocol_configuration),
                                       command=command,
                                       terminal_count=len(terminals),
                                       terminals = json.dumps(terminals))
            # TODO: add access_ip, access_user, access_gorup (for model)

            distribute_data = task.task_command_represent()

            try:
                res = dispatch_command(distribute_data)
            except Exception as e:
                logger.error(e)
                natrix_exception.natrix_traceback()

            return task

    def to_representation(self, instance):
        if not isinstance(instance, Task):
            raise natrix_exception.ParameterTypeException(parameter='instance')

        try:
            ret = OrderedDict()
            ret['id'] = instance.id
            ret['status'] = instance.status
            ret['protocol_type'] = instance.command.protocol_type
            ret['destination'] = instance.command.destination

            ret['terminal_configuration'] = json.loads(instance.terminal_condition)
            ret['advanced_switch'] = True if ret['terminal_configuration'] else False

            ret['protocol_configuration'] = json.loads(instance.command.protocol_conf)
            ret['protocol_switch'] = True if ret['protocol_configuration'] else False
            return ret
        except Exception as e:
            logger.error(u'Serializer Instant Task ERROR: {}'.format(e))
            raise natrix_exception.ClassInsideException(message=u'{}'.format(e))


TIMED_PROTOCOL_CHOICES = (('ping', 'PING'), ('http', 'HTTP'), ('dns', 'DNS'))


class TimedTaskSerializer(NatrixSerializer):
    """Timed task form.

    """
    id = serializers.UUIDField(read_only=True, help_text=u'任务ID')
    name = serializers.CharField(max_length=64, help_text=u'任务名称')
    description = serializers.CharField(max_length=255, help_text=u'任务描述')
    scope = serializers.ChoiceField(choices=SCOPE_CHOICES, help_text=u'任务范围')
    destination = SchemeURLField(help_text=u'目标地址')
    frequency = serializers.IntegerField(min_value=1, help_text=u'任务频率（分钟）')
    terminal_switch = serializers.BooleanField(default=False, help_text=u'终端配置开关')
    terminal_configuration = TerminalConditionSerializer(allow_null=True,
                                                         required=False,
                                                         help_text=u'终端配置')

    protocol_type = serializers.ChoiceField(choices=TIMED_PROTOCOL_CHOICES, help_text=u'协议类型')
    http_method = serializers.ChoiceField(choices=[('get', 'GET'),
                                                   ('post', 'POST'),
                                                   ('put', 'PUT'),
                                                   ('delete', 'DELETE')],
                                          help_text=u'HTTP方法',
                                          required=False)
    protocol_switch = serializers.BooleanField(default=False, help_text=u'协议配置开关')
    protocol_configuration = serializers.DictField(allow_null=True, required=False)

    effective_time = serializers.FloatField(min_value=0, help_text=u'生效时间')
    expiry_time = serializers.FloatField(min_value=0, help_text=u'失效时间')

    def validate_protocol_type(self, value):
        if hasattr(self, 'instance') and self.instance:
            if self.instance.command.protocol_type != value:
                raise serializers.ValidationError('Can not change protocol_type in update operations')

        return value

    def validate_destination(self, value):
        if hasattr(self, 'instance') and self.instance:
            if self.instance.command.destination != value:
                raise serializers.ValidationError('Can not change destination in update operations')

        return value

    def is_valid(self):
        flag = super(TimedTaskSerializer, self).is_valid()
        if not flag:
            return flag

        terminal_switch = self.initial_data.get('terminal_switch')
        terminal_configuration = self.initial_data.get('terminal_configuration')
        if terminal_switch:
            if terminal_configuration is None:
                flag = False
                self.errors['terminal_configuration'] = [
                    u'terminal_configuation can not be None if terminal_switch is True.']

        protocol_switch = self.initial_data.get('protocol_switch')
        protocol_type = self.initial_data.get('protocol_type')
        protocol_configuration = self.initial_data.get('protocol_configuration')

        if protocol_type == 'http':
            http_method = self.initial_data.get('http_method')
            if http_method is None:
                flag = False
                self._errors['http_method'] = ['The http_method field is required for http protocol!']
                return flag
        if protocol_switch:
            if protocol_configuration is None:
                self.initial_data['protocol_configuration'] = {}
            # validate protocol_configuration
            flag, res_data = natrix_protocol_validator(protocol_type, protocol_configuration)
            if not flag:
                self._errors['protocol_configuration'] = res_data
                return flag
            else:
                self.protocol_info = res_data

        return flag

    def create(self, validated_data):
        name = validated_data.get('name')
        description = validated_data.get('description')
        scope = validated_data.get('scope')
        destination = validated_data.get('destination')
        frequency = validated_data.get('frequency')
        terminal_switch = validated_data.get('terminal_switch')
        terminal_configuration = validated_data.get('terminal_configuration')
        protocol_type = validated_data.get('protocol_type')
        http_method = validated_data.get('http_method')
        protocol_switch = validated_data.get('protocol_switch')
        protocol_configuration = validated_data.get('protocol_configuration')
        effective_time = validated_data.get('effective_time')
        expiry_time = validated_data.get('expiry_time')

        if not terminal_switch:
            terminal_configuration = dict()
        else:
            terminal_configuration = {
                'filter_type': terminal_configuration['filter_type'],
                'filter_condition': terminal_configuration['filter_condition'],
                'terminal_select': terminal_configuration['terminal_select'],
                'terminals': terminal_configuration.get('terminals', None)
            }

        if not protocol_switch:
            protocol_configuration = {}
        if hasattr(self, 'protocol_info'):
            command_protocol = copy.deepcopy(self.protocol_info)
        else:
            command_protocol = dict()
        if http_method:
            command_protocol['operation'] = http_method

        with transaction.atomic():
            schedule = Schedule.objects.create(
                frequency=frequency * 60,
                effective_time=TIMESTAMP_UTC(effective_time / 1000),
                expiry_time=TIMESTAMP_UTC(expiry_time / 1000))

            celery_api.add_beat_schedule(frequency * 60,
                                         task='benchmark.tasks.timed_task_process')

            command = Command.command_generator(protocol_type,
                                                command_protocol,
                                                destination)

            task = Task.objects.create(name=name,
                                       description=description,
                                       purpose='benchmark',
                                       status=True,
                                       scope=scope,
                                       time_type='timed',
                                       destination=destination,
                                       terminal_switch=terminal_switch,
                                       protocol_switch=protocol_switch,
                                       terminal_condition=json.dumps(terminal_configuration),
                                       protocol_type=protocol_type,
                                       method=http_method,
                                       protocol_condition=json.dumps(protocol_configuration),
                                       command=command,
                                       schedule=schedule)
            if self.user:
                task.owner = self.user
            if self.group:
                task.group = self.group

            task.save()

            return task

    def update(self, instance, validated_data):
        name = validated_data.get('name')
        description = validated_data.get('description')
        scope = validated_data.get('scope')
        frequency = validated_data.get('frequency')
        terminal_switch = validated_data.get('terminal_switch')
        terminal_configuration = validated_data.get('terminal_configuration')
        http_method = validated_data.get('http_method', None)
        protocol_switch = validated_data.get('protocol_switch')
        protocol_configuration = validated_data.get('protocol_configuration')
        effective_time = validated_data.get('effective_time')
        expiry_time = validated_data.get('expiry_time')

        if not terminal_switch:
            terminal_configuration = dict()
        else:
            terminal_configuration = {
                'filter_type': terminal_configuration['filter_type'],
                'filter_condition': terminal_configuration['filter_condition'],
                'terminal_select': terminal_configuration['terminal_select'],
                'terminals': terminal_configuration.get('terminals', None)
            }

        if not protocol_switch:
            protocol_configuration = dict()

        if hasattr(self, 'protocol_info'):
            command_protocol = copy.deepcopy(self.protocol_info)
        else:
            command_protocol = dict()
        if http_method:
            command_protocol['operation'] = http_method

        with transaction.atomic():
            instance.name = name if name else instance.name
            instance.description = description if description else instance.description
            instance.scope = scope if scope else instance.scope

            # schedule related
            if frequency and instance.schedule.frequency != frequency * 60:
                instance.schedule.frequency = frequency * 60
                celery_api.add_beat_schedule(frequency * 60, task=timed_task_process)

            instance.schedule.effective_time = TIMESTAMP_UTC(effective_time/1000) if effective_time \
                                                else instance.schedule.effective_time
            instance.schedule.expiry_time = TIMESTAMP_UTC(expiry_time/1000) if expiry_time \
                                                else instance.schedule.expiry_time
            # protocol related
            command = Command.command_generator(instance.command.protocol_type,
                                                command_protocol,
                                                instance.command.destination)
            if command != instance.command:
                instance.protocol_switch = protocol_switch
                instance.protocol_condition = json.dumps(protocol_configuration)
                instance.method = http_method
                instance.command = command

            # terminal related
            instance.terminal_swtich = terminal_switch
            instance.terminal_condition = json.dumps(terminal_configuration)

            instance.schedule.save()
            instance.save()

        return instance


class TimedTaskInfoSerializer(NatrixSerializer):
    task_id = serializers.UUIDField(help_text=u'任务ID')
    info_type = serializers.ChoiceField(choices=(('brief', u'简要的'),
                                                 ('detailed', u'详细的')),
                                        help_text=u'消息类型')

    def validate_task_id(self, value):
        if not isinstance(self.group, Group):
            raise serializers.ValidationError(
                u'The user must join a group when query task info!')

        try:
            task = Task.objects.get(Q(id=value) &
                                    Q(time_type='timed') &
                                    (Q(scope='public') | Q(group=self.group)))

            self.instance = task

            return value
        except Task.DoesNotExist:
            raise serializers.ValidationError('Task ({}) is not exist!'.format(value))

    def to_representation(self, instance, type='detailed'):
        """

        :param instance:
        :param type:
        :return:
        """
        if not isinstance(instance, Task):
            logger.error('instance must be a Task object!')
            raise natrix_exception.ParameterTypeException(parameter='instance')

        if not (instance.time_type == 'timed'):
            logger.error('Task instance must be a timed task!')
            raise natrix_exception.ParameterTypeException(parameter='instance')

        try:
            ret = OrderedDict()
            # common info for detailed and brief type info
            ret['id'] = instance.id
            ret['name'] = instance.name
            ret['description'] = instance.description
            ret['scope'] = instance.scope
            ret['protocol_type'] = instance.protocol_type
            if instance.protocol_type == 'http':
                ret['http_method'] = instance.method
            ret['destination'] = instance.destination
            ret['frequency'] = instance.schedule.frequency / 60

            ret['effective_time'] = (time.mktime(instance.schedule.effective_time.timetuple()) - time.timezone) * 1000
            ret['expiry_time'] = (time.mktime(instance.schedule.expiry_time.timetuple()) - time.timezone) * 1000
            ret['status'] = instance.status_represent()

            ret['create_time'] = (time.mktime(instance.create_time.timetuple()) - time.timezone) * 1000

            if type == 'detailed':
                ret['terminal_switch'] = instance.terminal_switch
                if instance.terminal_switch:
                    ret['terminal_configuration'] = json.loads(instance.terminal_condition)
                # protocol related
                ret['protocol_switch'] = instance.protocol_switch
                if instance.protocol_switch:
                    ret['protocol_configuration'] = json.loads(instance.protocol_condition)

            return ret
        except Exception as e:
            logger.error(u'Serializer Timed Task ERROR: {}'.format(e))
            raise natrix_exception.ClassInsideException(message=u'{}'.format(e))

    def representation(self):
        info_type = self.validated_data.get('info_type')

        return self.to_representation(self.instance, type=info_type)


class TimedTaskOperationSerializer(NatrixSerializer):
    task_id = serializers.UUIDField(help_text=u'任务ID')
    operation = serializers.ChoiceField(choices=(('on', u'开始'),
                                                 ('off', u'关闭'),
                                                 ('followed', u'关注'),
                                                 ('unfollowed', u'取关')),
                                        help_text=u'操作类型')

    def validate_task_id(self, value):
        try:
            task = Task.objects.get(id=value)
            self.instance = task

            return value
        except Task.DoesNotExist:
            raise serializers.ValidationError('Task ({}) is not exist!'.format(value))

    def process(self):
        assert hasattr(self, '_errors'), (
            'You must call `.isvalid()` before calling `.process()`'
        )

        assert not self.errors, (
            'You can not call `.process()` on a serializer with invalid data.'
        )

        operation = self.validated_data.get('operation')

        if operation == 'on':
            self.turn_on()
        elif operation == 'off':
            self.turn_off()
        elif operation == 'followed':
            self.followed()
        elif operation == 'unfollowed':
            self.unfollowed()

    def turn_on(self):
        if not isinstance(self.group, Group):
            raise natrix_exception.ClassInsideException('The user must join a group when turn on task!')

        if self.instance.group == self.group:
            self.instance.turn_on()
        else:
            raise natrix_exception.PermissionException(reason='Can only operate task in yourself group')

    def turn_off(self):
        if not isinstance(self.group, Group):
            raise natrix_exception.ClassInsideException(u'The user must join a group when turn off task!')

        if self.instance.group == self.group:
            self.instance.turn_off()
        else:
            raise natrix_exception.PermissionException(reason=u'Can only operate task in yourself group')

    def followed(self):
        if not isinstance(self.group, Group):
            raise natrix_exception.ClassInsideException('The user must join a group when followed task!')

        if self.instance.group == self.group:
            raise natrix_exception.PermissionException(reason='Can not follow tasks in your group!')

        if self.instance.scope == 'private':
            raise natrix_exception.PermissionException(
                reason='Task ({}) is not exist!'.format(self.instance.id))


        with transaction.atomic():
            tasks = FollowedTask.objects.filter(task=self.instance, group=self.group)
            if len(tasks) > 0:
                raise natrix_exception.PermissionException(reason='Can not follow a followed task!')

            FollowedTask.objects.create(task=self.instance, user=self.user, group=self.group)

    def unfollowed(self):
        if not isinstance(self.group, Group):
            raise natrix_exception.ClassInsideException('The user must join a group when operate task!')


        with transaction.atomic():
            count, info = FollowedTask.objects.filter(task=self.instance, group=self.group).delete()
            if count == 0:
                logger.error('unfollowed an non-exist followed task.')
                raise natrix_exception.PermissionException('The followed task is exist!')


class TableSearchSerializer(NatrixSerializer):
    search = serializers.CharField(max_length=64, required=False)
    is_paginate = serializers.NullBooleanField(required=True)
    pagenum = serializers.IntegerField(min_value=1, required=False)


class UnfollowedTaskSerializer(NatrixQuerySerializer):

    protocol_type = serializers.ChoiceField(choices=PROTOCOL_CHOICES,
                                            help_text=u'协议类型')

    def query(self, validated_data, **kwargs):
        if not isinstance(self.group, Group):
            raise natrix_exception.ClassInsideException(
                u'The user must join a group when query unfollowed task!')

        protocol_type = validated_data.get('protocol_type')

        public_tasks = set(Task.objects.filter(Q(scope='public') &
                                               Q(command__protocol_type=protocol_type) &
                                               ~Q(group=self.group) &
                                               Q(time_type='timed')))
        followed_tasks = set(map(lambda ft: ft.task,
                                 FollowedTask.objects.filter(group=self.group)))

        unfollowed_tasks = public_tasks.difference(followed_tasks)

        return map(lambda t: {'id': t.id, 'name': t.name},
                   unfollowed_tasks)


TIMED_SELECT_PROTOCOL_CHOICES = (('all', 'ALL'), ('ping', 'PING'), ('http', 'HTTP'), ('dns', 'DNS'))


class TimedTaskSelectSerializer(NatrixQuerySerializer):
    protocol_type = serializers.ChoiceField(choices=TIMED_SELECT_PROTOCOL_CHOICES,
                                            help_text=u'协议类型')

    def query(self, validated_data, **kwargs):
        if not isinstance(self.group, Group):
            raise natrix_exception.ClassInsideException(
                u'The user must join a group when query unfollowed task!')

        protocol_type = validated_data.get('protocol_type')

        if protocol_type == 'all':
            own_tasks = list(Task.objects.filter(Q(group=self.group) &
                                                 Q(time_type='timed')))
        else:
            own_tasks = list(Task.objects.filter(Q(group=self.group) &
                                                 Q(time_type='timed') &
                                                 Q(command__protocol_type=protocol_type)))

        followed_tasks = list(map(lambda ft: ft.task,
                                  FollowedTask.objects.filter(group=self.group)))

        own_tasks.extend(followed_tasks)

        return map(lambda t: {'id': t.id, 'name': t.name},
                   own_tasks)








