# -*- coding: utf-8 -*-
"""

"""
from __future__ import unicode_literals, absolute_import
import logging, json, time, copy
import pprint
from collections import OrderedDict

from django.db import transaction
from rest_framework import serializers

from natrix.common.natrix_views.serializers import NatrixSerializer
from natrix.common.natrix_views.fields import SchemeURLField
from natrix.common import exception as natrix_exception
from benchmark.models.task_models import PROTOCOL_CHOICES, Task, Command
from benchmark.backends.command_adapter import adapter
from benchmark.backends import command_adapter


from terminal.api.exports import terminalapi

logger = logging.getLogger(__name__)

class TerminalConditionSerializer(NatrixSerializer):

    filter_type = serializers.ChoiceField(choices=(('region', u'区域'), ('organization', u'组织')),
                                          help_text=u'过滤类型')
    filter_condition = serializers.ListField(help_text=u'过滤条件', child=serializers.CharField())
    network_type = serializers.MultipleChoiceField(choices=(('all', u'全部'),
                                                    ('wire', u'有线'),
                                                    ('wireless', u'无线'),
                                                    ('mobile', u'移动')),
                                                   help_text=u'网络类型')
    isp_type = serializers.MultipleChoiceField(choices=(('all', u'全部'), ), help_text=u'运营商')
    terminal_select = serializers.BooleanField(default=False)
    terminals = serializers.ListField(child=serializers.CharField(max_length=12),
                                      allow_empty=True, required=False)


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

    def validate_header_info(self, value):
        try:
            json.loads(value)
            return value
        except ValueError:
            raise serializers.ValidationError('The header_info must be a json string.')

    def validate_body_info(self, value):
        try:
            json.loads(value)
            return value
        except ValueError:
            raise serializers.ValidationError('The body_info must be a json string.')

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
    dns_server = serializers.IPAddressField(help_text=u'自定义DNS IP')
    timeout = serializers.IntegerField(help_text=u'超时时间(s)', default=10)

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
            'timeout': self.validated_data.get('timeout')
        }

        return protocol_conf


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
            alive_terminals = terminalapi.TerminalAPI.get_alive_terminals()
            # terminals is a list, witch item with ip and mac
            terminals = [t.address_info() for t in alive_terminals]
        else:
            terminal_configuration = {
                'filter_type': terminal_configuration['filter_type'],
                'filter_condition': terminal_configuration['filter_condition'],
                'network_type': list(terminal_configuration['network_type']),
                'isp_type': list(terminal_configuration['isp_type']),
                'terminal_select': terminal_configuration['terminal_select'],
                'terminals': list(terminal_configuration['terminals'])
            }
            terminals = []
            if terminal_configuration['terminal_select']:
                for item in terminal_configuration['terminals']:
                    try:
                        terminal = terminalapi.TerminalInfo(pk=item)
                        terminals.append(terminal.address_info())
                    except Exception as e:
                        logger.error('The temrinal ({}) is not exist!'.format(item))
            else:
                filter_terminals = terminalapi.TerminalAPI.filter_available_terminals(
                        type=terminal_configuration['filter_type'],
                        filter_condition=terminal_configuration['filter_condition']
                )
                for item in filter_terminals:
                    terminals.append(item.address_info())

        if not protocol_switch:
            protocol_configuration = dict()

        with transaction.atomic():

            command = Command.objects.create(type='instant',
                                             protocol_type=protocol_type,
                                             method=http_method,
                                             protocol_conf=json.dumps(protocol_configuration),
                                             destination=destination)

            task = Task.objects.create(name='Instant Task',
                                       time_type='instant',
                                       purpose='benchmark',
                                       terminal_condition=json.dumps(terminal_configuration),
                                       command=command,
                                       terminal_count=len(terminals),
                                       terminals = json.dumps(terminals),
                                       )
            # TODO: add access_ip, access_user, access_gorup (for model)

            if hasattr(self, 'protocol_info'):
                command_protocol = copy.deepcopy(self.protocol_info)
            else:
                command_protocol = dict()

            if http_method:
                command_protocol['operation'] = http_method

            distribute_data = {
                'command': {
                    'command_uuid': command.id,
                    'command_protocol': command.protocol_type,
                    'command_destination': command.destination,
                    'command_parameters': command_protocol
                },
                'timestamp': time.time(),
                'terminals': list(terminals)
            }

            pprint.pprint(distribute_data)

            try:
                processor = adapter.CommandProcessor(stage='distribute',
                                                     command=distribute_data)
                processor.do()
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


class InstantTaskAnalyseSerializer(NatrixSerializer):
    task_id = serializers.UUIDField(help_text=u'任务ID')
    view_point = serializers.CharField(help_text=u'分析视角', max_length=32)
    chart_name = serializers.CharField(help_text=u'图表名称（类型）',
                                       max_length=32, required=False, allow_null=True,
                                       allow_blank=True)

    ANALYSE_CONFIGURATION = {
        'ping': {
            'region': {
                'packet_loss': {
                    'analyse': 'ping_region_packet_loss'
                },
                'delay': {
                    'analyse': 'ping_region_delay'
                },
                'default': {
                    'analyse': 'ping_region_all'
                }
            },
            'organization': {
                'packet_loss': {
                    'analyse': 'ping_organization_packet_loss'
                },
                'delay': {
                    'analyse': 'ping_organization_delay'
                },
                'distribution': {
                    'analyse': 'ping_organization_distribution'
                },
                'top': {
                    'analyse': 'ping_organization_top'
                },
                'default': {
                    'analyse': 'ping_organization_all'
                }
            },
            'detail': {
                'default': {
                    'analyse': 'ping_detail'
                }
            }
        },
        'http': {
            'region': {
                'request': {
                    'analyse': 'http_region_request'
                },
                'default': {
                    'analyse': 'http_region_all'
                }
            },
            'organization': {
                'request': {
                    'analyse': 'http_organization_request'
                },
                'distribution': {
                    'analyse': 'http_organization_distribution'
                },
                'default': {
                    'analyse': 'http_organization_all'
                }
            },
            'comprehensiveness':{
                'result_distribution': {
                    'analyse': 'http_com_result_distribution'
                },
                'stage_distribution': {
                    'analyse': 'http_com_stage_distribution'
                },
                'default': {
                    'analyse': 'http_comprehensiveness_all'
                }

            },
            'detail': {
                'default': {
                    'analyse': 'http_detail'
                }
            }

        },
        'dns': {
            'region': {
                'parse_time': {
                    'analyse': 'dns_region_parse_time'
                },
                'distribution': {
                    'analyse': 'dns_region_distribution'
                },
                'top': {
                    'analyse': 'dns_region_top'
                },
                'default': {
                    'analyse': 'dns_region_all'
                },

            },
            'organization': {
                'parse_time': {
                    'analyse': 'dns_organization_parse_time'
                },
                'distribution': {
                    'analyse': 'dns_organization_distribution'
                },
                'top': {
                    'analyse': 'dns_organization_top'
                },
                'default': {
                    'analyse': 'dns_organization_all'
                }
            },
            'detail': {
                'default': {
                    'analyse': 'dns_detail'
                }
            }
        },
        'traceroute': {
            'detail': {
                'default': {
                    'analyse': 'traceroute_detail'
                }
            }

        }
    }

    SLICE_COUNT = 10

    def get_max_value(self, values):
        if values:
            return max(values)
        else:
            return 10

    def validate_task_id(self, value):
        try:
            task = Task.objects.get(id=value)
            self.instance = task
        except Task.DoesNotExist:
            raise serializers.ValidationError('Ther task is not exist(task_id: {})'.format(value))

        return value

    def is_valid(self, raise_exception=False):
        flag = super(InstantTaskAnalyseSerializer, self).is_valid()
        if not flag:
            return flag

        protocol_type = self.instance.command.protocol_type

        view_point = self.initial_data['view_point']
        chart_name = self.initial_data.get('chart_name', 'default')
        chart_name = 'default' if chart_name is None else chart_name

        restriction_viewpoints = self.ANALYSE_CONFIGURATION[protocol_type].keys()
        if not (view_point in restriction_viewpoints):
            self._errors['view_piont'] = ['There is not viewpoint({}) for task({})'.format(
                view_point, self.instance.id
            )]
            flag = False
            return flag

        restriction_chartnames = self.ANALYSE_CONFIGURATION[protocol_type][view_point].keys()
        if not (chart_name in restriction_chartnames):
            self._errors['chart_name'] = ['There is not chart_name({}) for task({})'.format(
                chart_name, self.instance.id
            )]
            flag = False
            return flag

        if self.instance.status:
            self.dial_data = command_adapter.get_command_data(self.instance.command.id)
        else:
            self.dial_data = json.loads(self.instance.result_snapshot)
        return flag

    def analyse(self):
        view_point = self.validated_data.get('view_point')
        protocol_type = self.instance.command.protocol_type
        chart_name = self.validated_data.get('chart_name')
        chart_name = 'default' if chart_name is None else chart_name

        analyse_function = getattr(self,
                                   self.ANALYSE_CONFIGURATION.get(
                                       protocol_type).get(view_point).get(chart_name).get('analyse'))

        return analyse_function()

    def ping_region_packet_loss(self):
        success = self.dial_data.get('success', [])
        packet_loss_data = {
            'name': 'ping packet_loss region analyse',
            'values': []
        }
        analyse_data = {}
        for record in success:
            province = record.get('province', '')
            if not (province in analyse_data):
                analyse_data[province] = {
                    'name': province,
                    'total_packet_loss_rate': 0,
                    'count': 0
                }
            packet_send = record.get('packet_send')
            packet_loss = record.get('packet_loss')

            analyse_data[province]['count'] += 1
            analyse_data[province]['total_packet_loss_rate'] += packet_loss * 1.0 /packet_send if packet_send else 0.0
        for info in analyse_data.values():
            packet_loss_data['values'].append(
                {'name': info['name'], 'value': info['total_packet_loss_rate'] / info['count']})

        return packet_loss_data

    def ping_region_delay(self):
        success = self.dial_data.get('success', [])
        delay_data = {
            'name': 'ping delay region analyse',
            'values': []
        }
        analyse_data = {}
        for record in success:
            province = record.get('province', '')
            if not (province in analyse_data):
                analyse_data[province] = {
                    'name': province,
                    'total_avg_time': 0,
                    'count': 0
                }

            analyse_data[province]['count'] += 1
            analyse_data[province]['total_avg_time'] += record.get('avg_time', 0)
        for info in analyse_data.values():
            delay_data['values'].append(
                {'name': info['name'], 'value': info['total_avg_time'] / info['count']})

        return delay_data

    def ping_region_all(self):

        return {
            'packet_loss': self.ping_region_packet_loss(),
            'delay': self.ping_region_delay()
        }

    def _ping_calculate_data(self, records):
        agg_organization = {}
        for record in records:
            orgs = record.get('organization_id')
            names = record.get('organization_name')
            for org_id, org_name in zip(orgs, names):
                if not (org_id in agg_organization):
                    agg_organization[org_id] = {
                        'org_name': org_name,
                        'avg_time': 0,
                        'min_time': 0,
                        'max_time': 0,
                        'packet_send': 0,
                        'packet_loss': 0,
                        'packet_receive': 0,
                        'count': 0
                    }
                if org_name != agg_organization[org_id]['org_name']:
                    logger.error('There is an unmatch organization info, ({org_id}): {old} {new} '.format(
                        org_id=org_id, old=agg_organization[org_id]['org_name'], new=org_name
                    ))
                agg_organization[org_id]['count'] += 1
                for key in ('avg_time', 'min_time', 'max_time', 'packet_send', 'packet_loss', 'packet_receive'):
                    agg_organization[org_id][key] += record.get(key, 0)
        x_axis = []
        packet_loss_values = []
        avg_time_values = []
        min_time_values = []
        max_time_values = []
        for info in agg_organization.values():
            count = info['count']
            x_axis.append(info['org_name'])
            packet_loss_values.append(
                (info['packet_loss'] * 1.0 / info['packet_send'] if info['packet_send'] else 0) / count)
            avg_time_values.append(info['avg_time'] / count)
            min_time_values.append(info['min_time'] / count)
            max_time_values.append(info['max_time'] / count)

        return x_axis, packet_loss_values, avg_time_values, min_time_values, max_time_values

    def ping_organization_packet_loss(self):
        success = self.dial_data.get('success', [])
        x_axis, packet_loss_values, _, _, _ = self._ping_calculate_data(success)
        return {
                'name': 'ping packet_loss org analyse',
                'x-axis': x_axis,
                'viewpoints': [
                    {
                        'name': 'packet_loss',
                        'values': packet_loss_values
                    }
                ]
            }

    def ping_organization_delay(self):
        success = self.dial_data.get('success', [])
        x_axis, _, avg_time_values, min_time_values, max_time_values = self._ping_calculate_data(success)

        return {
            'name': 'ping delay org analyse',
            'x-axis': x_axis,
            'viewpoints': [
                {
                    'name': 'avg_value',
                    'values': avg_time_values
                },{
                    'name': 'min_value',
                    'values': min_time_values
                },{
                    'name': 'max_value',
                    'values': max_time_values
                }
            ]
        }

    def ping_organization_distribution(self):
        success = self.dial_data.get('success', [])
        _, _, avg_time_values, min_time_values, max_time_values = self._ping_calculate_data(success)

        max_time = self.get_max_value(max_time_values)

        slice_count = 10

        interval = max_time / slice_count

        distribution_axis = map(lambda x: '{}-{}'.format(round(interval * x, 2),
                                                         round(interval * (x + 1), 2)),
                                range(slice_count + 1))

        max_list = [0] * (slice_count + 1)
        min_list = [0] * (slice_count + 1)
        avg_list = [0] * (slice_count + 1)

        if interval:
            for max_v in max_time_values:
                index = int(max_v / interval)
                max_list[index] += 1

            for min_v in min_time_values:
                index = int(min_v / interval)
                min_list[index] += 1

            for avg_v in avg_time_values:
                index = int(avg_v / interval)
                avg_list[index] += 1

        return {
            'name': 'ping delay distribution org analyse',
            'x-axis': distribution_axis,
            'viewpoints': [
                {
                    'name': 'max_value',
                    'values': max_list
                }, {
                    'name': 'min_value',
                    'values': min_list
                }, {
                    'name': 'avg_value',
                    'values': avg_list
                }
            ]

        }

    def ping_organization_top(self):
        success = self.dial_data.get('success', [])
        x_axis, _, avg_time_values, _, _ = self._ping_calculate_data(success)

        org_avg = zip(x_axis, avg_time_values)
        org_avg.sort(key=lambda x: x[1], reverse=True)

        return {
            'name': 'top analyse',
            'x-axis': map(lambda x: x[0], org_avg[0: 10]),
            'viewpoints': [
                {
                    'name': 'avg_value',
                    'values': map(lambda x: x[1], org_avg[0: 10])
                }
            ]
        }

    def ping_organization_all(self):

        def get_ping_loss(x_axis, packet_loss_values):
            return {
                'name': 'packet_loss analyse',
                'x-axis': x_axis,
                'viewpoints': [
                    {
                        'name': 'packet_loss',
                        'values': packet_loss_values
                    }
                ]
            }
        def get_ping_delay(x_axis, max_values, min_values, avg_values):
            return {
                'name': 'delay analyse',
                'x-axis': x_axis,
                'viewpoints': [
                    {
                        'name': 'max_value',
                        'values': max_values
                    },{
                        'name': 'min_value',
                        'values': min_values
                    },{
                        'name': 'avg_value',
                        'values': avg_values
                    }
                ]
            }

        def get_ping_top(x_axis, avg_values):
            org_avg = zip(x_axis, avg_values)
            org_avg.sort(key=lambda x: x[1], reverse=True)

            return {
                'name': 'top analyse',
                'x-axis': map(lambda x: x[0], org_avg[0: 10]),
                'viewpoints': [
                    {
                        'name': 'avg_value',
                        'values': map(lambda x: x[1], org_avg[0: 10])
                    }
                ]
            }

        def get_ping_distribution(max_values, min_values, avg_values):
            max_time = self.get_max_value(max_values)

            slice_count = 10

            interval = max_time / slice_count

            distribution_axis = map(lambda x: '{}-{}'.format(interval*x, interval*(x+1)),
                                    range(slice_count+1))

            max_list = [0] * (slice_count+1)
            min_list = [0] * (slice_count+1)
            avg_list = [0] * (slice_count+1)

            if interval:
                for max_v in max_values:
                    index = int(max_v / interval)
                    max_list[index] += 1


                for min_v in min_values:
                    index = int(min_v / interval)
                    min_list[index] += 1

                for avg_v in avg_values:
                    index = int(avg_v / interval)
                    avg_list[index] += 1

            return {
                'name': 'distribution analyse',
                'x-axis': distribution_axis,
                'viewpoints': [
                    {
                        'name': 'max_value',
                        'values': max_list
                    },{
                        'name': 'min_value',
                        'values': min_list
                    },{
                        'name': 'avg_value',
                        'values': avg_list
                    }
                ]

            }


        success = self.dial_data.get('success', [])

        x_axis, packet_loss_values, avg_time_values, min_time_values, max_time_values = self._ping_calculate_data(success)

        packet_loss_data = get_ping_loss(x_axis, packet_loss_values)
        delay_data = get_ping_delay(x_axis, max_time_values, min_time_values, avg_time_values)

        distribution_data = get_ping_distribution(max_time_values, min_time_values, avg_time_values)
        top_data = get_ping_top(x_axis, avg_time_values)

        return {
            'packet_loss': packet_loss_data,
            'delay': delay_data,
            'distribution': distribution_data,
            'top': top_data
        }

    def ping_detail(self):
        error = self.dial_data.get('error', [])
        success = self.dial_data.get('success', [])

        # TODO: validate provice and city
        return {
            'error': map(lambda record: {
                'terminal': record.get('terminal', None),
                'organizations': record.get('organization_name', []),
                'province': record.get('province', None),
                'city': record.get('city', None),
                'operator': record.get('operator', None),
                'errorinfo': record.get('errorinfo', None)

            }, error),
            'success': map(lambda record:{
                'terminal': record.get('terminal', None),
                'organizations': record.get('organization_name', []),
                'province': record.get('province', None),
                'city': record.get('city', None),
                'operator': record.get('operator', None),
                'destination': record.get('destination', None),
                'destination_ip': record.get('destination_ip', None),
                'packet_send': record.get('packet_send', None),
                'packet_loss': record.get('packet_loss', None),
                'packet_receive': record.get('packet_receive', None),
                'avg_time': record.get('avg_time', None),
                'max_time': record.get('max_time', None),
                'min_time': record.get('min_time', None),
                'packet_size': record.get('packet_size', None),

            }, success)
        }

    def http_region_request(self):
        success = self.dial_data.get('success', [])
        request_data = {
            'name': 'http request region analyse',
            'values': []
        }
        analyse_data = {}
        for record in success:
            province = record.get('province', '')
            if not (province in analyse_data):
                analyse_data[province] = {
                    'name': province,
                    'total_time': 0,
                    'count': 0
                }
            analyse_data[province]['count'] += 1
            analyse_data[province]['total_time'] += record.get('total_time')

        for info in analyse_data.values():
            request_data['values'].append(
                {'name': info['name'], 'value': info['total_time'] * 1.0 / info['count']}
            )

        return request_data

    def http_region_all(self):

        return {
            'request': self.http_region_request()
        }

    def _http_org_calculate(self, records):
        agg_organization = {}
        for record in records:
            orgs = record.get('organization_id')
            names = record.get('organization_name')
            for org_id, org_name in zip(orgs, names):
                if not (org_id in agg_organization):
                    agg_organization[org_id] = {
                        'org_name': org_name,
                        'count': 0,
                        'total_time': 0.0,
                        'period_nslookup': 0.0,
                        'period_tcp_connect': 0.0,
                        'period_request': 0.0,
                        'period_response': 0.0,
                        'period_transfer': 0.0
                    }
                if org_name != agg_organization[org_id]['org_name']:
                    logger.error('There is an unmatch organization info, ({org_id}): {old} {new}'.format(
                        org_id=org_id, old=agg_organization[org_id]['org_name'], new=org_name
                    ))
                agg_organization[org_id]['count'] += 1
                for key in ('total_time', 'period_nslookup', 'period_tcp_connect', 'period_request',
                            'period_response', 'period_transfer'):
                    agg_organization[org_id][key] += record.get(key, 0)

        x_axis = []
        total_values = []
        nslookup_values = []
        tcp_connect_values = []
        request_values = []
        response_values = []
        transfer_values = []

        for info in agg_organization.values():
            count = info['count']
            x_axis.append(info['org_name'])
            total_values.append(info['total_time'] / count)
            nslookup_values.append(info['period_nslookup'] / count)
            tcp_connect_values.append(info['period_tcp_connect'] / count)
            request_values.append(info['period_request'] / count)
            response_values.append(info['period_response'] / count)
            transfer_values.append(info['period_transfer'] / count)

        return x_axis, total_values, nslookup_values, tcp_connect_values, request_values, response_values, transfer_values

    def http_organization_request(self):
        success = self.dial_data.get('success', [])
        x_axis, total_values, nslookup_values, tcp_connect_values, _, _, _ = self._http_org_calculate(success)

        return {
            'name': 'http request org analyse',
            'x-axis': x_axis,
            'viewpoints': [
                {
                    'name': 'total_time',
                    'values': total_values
                },{
                    'name': 'namelookup_time',
                    'values': nslookup_values
                },{
                    'name': 'tcp_connect_time',
                    'values': tcp_connect_values
                }
            ]
        }

    def http_organization_distribution(self):
        success = self.dial_data.get('success', [])
        _, total_values, nslookup_values, tcp_connect_values, _, _, _ = self._http_org_calculate(success)

        if not (total_values or nslookup_values or tcp_connect_values):
            distribution_axis = []
            total_list = []
            nslookup_list = []
            tcp_connect_list = []
        else:
            max_time = self.get_max_value(total_values)

            slice_count = self.SLICE_COUNT

            interval = max_time / slice_count

            distribution_axis = map(lambda x: '{}-{}'.format(round(interval * x, 2),
                                                             round(interval * (x + 1), 2)),
                                    range(slice_count + 1))

            # initialize
            total_list = [0] * (slice_count + 1)
            nslookup_list = [0] * (slice_count + 1)
            tcp_connect_list = [0] * (slice_count + 1)

            if interval:
                for item_v in total_values:
                    index = int(item_v / interval)
                    total_list[index] += 1

                for item_v in nslookup_values:
                    index = int(item_v / interval)
                    nslookup_list[index] += 1

                for item_v in tcp_connect_values:
                    index = int(item_v / interval)
                    tcp_connect_list[index] += 1

        return {
            'name': 'http request distribution org analyse',
            'x-axis': distribution_axis,
            'viewpoints': [
                {
                    'name': 'total_time',
                    'values': total_list
                },{
                    'name': 'namelookup_time',
                    'values': nslookup_list
                },{
                    'name': 'tcp_connect_time',
                    'values': tcp_connect_list
                }
            ]
        }

    def http_organization_all(self):
        return {
            'request': self.http_organization_request(),
            'distribution': self.http_organization_distribution()
        }

    def http_com_result_distribution(self):
        success = self.dial_data.get('success', [])
        error = self.dial_data.get('error', [])

        agg_result = {}

        for record in success:
            status_code = record.get('status_code', None)
            if status_code is None:
                logger.error('There is a http response record which status code is None')
                continue

            key = 'status code {}'.format(status_code)
            if not (key in agg_result):
                agg_result[key] = 0
            agg_result[key] += 1

        for record in error:
            error_code = record.get('errorcode', None)
            if error_code is None:
                logger.error('There is a http error response record which errorcode is None')
                continue

            key = 'error code {}'.format(error_code)
            if not (key in agg_result):
                agg_result[key] = 0
            agg_result[key] += 1

        values = []
        for code, value in agg_result.items():
            values.append(
                {'name': code, 'value': value}
            )

        return {
            'name': 'http result distribution analyse',
            'values': values
        }

    def http_com_stage_distribution(self):
        success = self.dial_data.get('success', [])
        metric_list = ('period_nslookup', 'period_tcp_connect', 'period_ssl_connect', 'period_request',
                       'period_response', 'period_transfer')
        request_st = {}
        for key in metric_list:
            request_st[key] = 0.0

        for record in success:
            for key in metric_list:
                request_st[key] += record.get(key, 0.0)

        values = []
        count = len(success)
        for key in metric_list:
            values.append(
                {'name': key, 'value': 0 if count == 0 else request_st[key] / count})

        return {
            'name': 'http request stage distribution analyse',
            'values': values
        }

    def http_comprehensiveness_all(self):
        com_result = self.http_com_result_distribution()
        com_stage = self.http_com_stage_distribution()

        return {
            'result_distribution': com_result,
            'stage_distribution': com_stage
        }

    def http_detail(self):
        success = self.dial_data.get('success', [])
        error = self.dial_data.get('error', [])

        error_list = map(lambda record: {'terminal': record.get('terminal', None),
                                         'organizations': record.get('organization_name', []),
                                         'province': record.get('province', None),
                                         'city': record.get('city', None),
                                         'operator': record.get('operator', None),
                                         'errorinfo': record.get('errorinfo', None)
                                         }, error)

        http_extract = lambda record: {'terminal': record.get('terminal', None),
                                       'organizations': record.get('organization_name', []),
                                       'province': record.get('province', None),
                                       'city': record.get('city', None),
                                       'operator': record.get('operator', None),
                                       'status_code': record.get('status_code', None),
                                       'total_time': record.get('total_time', None),
                                       'period_nslookup': record.get('period_nslookup', None),
                                       'period_tcp_connect': record.get('period_tcp_connect', None),
                                       'period_ssl_connect': record.get('period_ssl_connect', None),
                                       'period_request': record.get('period_request', None),
                                       'period_response': record.get('period_response', None),
                                       'period_transfer': record.get('period_transfer', None),
                                       'size_download': record.get('size_download', None),
                                       'speed_download': record.get('speed_download', None)}
        wrong_list = []
        success_list = []
        for record in success:
            status_code = record.get('status_code')
            try:
                status_code = int(status_code)
                if status_code < 400:
                    success_list.append(http_extract(record))
                else:
                    wrong_list.append(http_extract(record))
            except TypeError:
                logger.error('Thers is a record with an invalid status code({}).'.format(status_code))
        return {
            'error': error_list,
            'wrong': wrong_list,
            'success': success_list
        }

    def traceroute_detail(self):
        error = self.dial_data.get('error', [])
        success = self.dial_data.get('success', [])

        return {
            'error': map(lambda record: {
                'terminal': record.get('terminal', None),
                'organizations': record.get('organization_name', []),
                'province': record.get('province', None),
                'city': record.get('city', None),
                'operator': record.get('operator', None),
                'errorinfo': record.get('errorinfo', None)
            }, error),
            'success': map(lambda record: {
                'terminal': record.get('terminal', None),
                'organizations': record.get('organization_name', []),
                'province': record.get('province', None),
                'city': record.get('city', None),
                'operator': record.get('operator', None),
                'hop': record.get('hop', None),
                'paths': record.get('paths', {})

            }, success)
        }

    def dns_region_parse_time(self):
        success = self.dial_data.get('success', [])

        parse_time_analyse = {}
        for record in success:
            province = record.get('province', '')
            if not (province in parse_time_analyse):
                parse_time_analyse[province] = {
                    'name': province,
                    'parse_time_total': 0.0,
                    'count': 0
                }
            parse_time_analyse[province]['parse_time_total'] += record.get('ptime')
            parse_time_analyse[province]['count'] += 1

        parse_time_data = {
            'name': 'dns parse_time region analyse',
            'values': []
        }
        for record in parse_time_analyse.values():
            parse_time_data['values'].append(
                {'name': record['name'], 'value': record['parse_time_total'] / record['count']})

        return parse_time_data

    def dns_region_distribution(self):
        success = self.dial_data.get('success', [])

        parse_address_analyse = {}
        for record in success:
            ips = record.get('ips', [])
            for parse_record in ips:
                p_province = parse_record.get('location', {}).get('province', '')
                if not (p_province in parse_address_analyse):
                    parse_address_analyse[p_province] = {
                        'name': p_province,
                        'count': 0
                    }
                parse_address_analyse[p_province]['count'] += 1

        parse_address_data = {
            'name': 'dns parse_result region distribution',
            'values': []
        }
        for record in parse_address_analyse.values():
            parse_address_data['values'].append(
                {'name': record['name'], 'value': record['count']}
            )

        return parse_address_data

    def dns_region_top(self):
        parse_time_data = self.dns_region_parse_time()

        top_analyse = parse_time_data.get('values')
        top_analyse.sort(key=lambda x: x['value'], reverse=True)
        top_data = {
            'name': 'dns parse top region analyse',
            'x-axis': map(lambda x: x['name'], top_analyse[0: 10]),
            'viewpoints': [
                {
                    'name': 'parse_time',
                    'values': map(lambda x: x['value'], top_analyse[0: 10])
                }
            ]
        }

        return top_data

    def dns_region_all(self):
        parse_time_data = self.dns_region_parse_time()
        parse_address_data = self.dns_region_distribution()
        top_data = self.dns_region_top()

        return {
            'parse_time': parse_time_data,
            'distribution': parse_address_data,
            'top': top_data
        }

    def _dns_orgnization_analyse(self):
        success = self.dial_data.get('success', [])

        organization_analyse = {}

        for record in success:
            organization_ids = record.get('organization_id')
            organization_names = record.get('organization_name')

            if not organization_ids:
                organization_ids = ['']
                organization_names = ['']

            for org_id, org_name in zip(organization_ids, organization_names):
                if not (org_id in organization_analyse):
                    organization_analyse[org_id] = {
                        'name': org_name,
                        'total_ptime': 0,
                        'count': 0
                    }
                organization_analyse[org_id]['count'] += 1
                organization_analyse[org_id]['total_ptime'] += record['ptime']

        return organization_analyse

    def dns_organization_parse_time(self):

        parse_time_analyse = self._dns_orgnization_analyse()

        parse_time_data = map(lambda record: (record['name'],
                                              record['total_ptime'] / record['count']if record['count'] else 0),
                              parse_time_analyse.values())

        return {
            'name': 'dns parse_time org analyse',
            'x-axis': map(lambda x: x[0], parse_time_data),
            'viewpoints': [
                {
                    'name': 'parse_time',
                    'values': map(lambda x: x[1], parse_time_data)
                }
            ]
        }

    def dns_organization_distribution(self):
        success = self.dial_data.get('success', [])

        ptime_list = map(lambda x: x['ptime'], success)
        slice_count = self.SLICE_COUNT

        max_time = self.get_max_value(ptime_list)
        interval = max_time / slice_count

        distribution_axis = map(lambda x: '{}-{}'.format(round(interval * x, 2),
                                                         round(interval * (x + 1), 2)),
                                range(slice_count + 1))
        ptime_dist = [0] * (slice_count + 1)

        if interval:
            for ptime_v in ptime_list:
                index = int(ptime_v/interval)
                ptime_dist[index] += 1

        return {
            'name': 'dns parse_time distribution org analyse',
            'x-axis': distribution_axis,
            'viewpoints': [
                {
                    'name': 'parse_time',
                    'values': ptime_dist
                }

            ]
        }

    def dns_organization_top(self):
        parse_time_analyse = self._dns_orgnization_analyse()

        parse_time_data = map(lambda record: (record['name'],
                                              record['total_ptime'] / record['count'] if record['count'] else 0),
                              parse_time_analyse.values())

        parse_time_data.sort(key=lambda x: x[1], reverse=True)

        return {
            'name': 'dns parse_time top org analyse',
            'x-axis': map(lambda x: x[0], parse_time_data[0: 10]),
            'viewpoints': [
                {
                    'name': 'parse_time',
                    'values': map(lambda x: x[1], parse_time_data[0: 10])
                }
            ]
        }

    def dns_organization_all(self):
        parse_time_data = self.dns_organization_parse_time()
        distribution_data = self.dns_organization_distribution()
        top_data = self.dns_organization_top()

        return {
            'parse_time': parse_time_data,
            'distribution': distribution_data,
            'top': top_data
        }

    def dns_detail(self):
        error = self.dial_data.get('error', [])
        success = self.dial_data.get('success', [])

        return {
            'error': map(lambda record: {
                'terminal': record.get('terminal', None),
                'organizations': record.get('organization_name', []),
                'province': record.get('province', None),
                'city': record.get('city', None),
                'operator': record.get('operator', None),
                'errorinfo': record.get('errorinfo', None)
            }, error),

            'success': map(lambda record: {
                'terminal': record.get('terminal', None),
                'organizations': record.get('organization_name', []),
                'province': record.get('province', None),
                'city': record.get('city', None),
                'operator': record.get('operator', None),
                'ptime': record.get('ptime', None),
                'destination': record.get('destination', None),
                'ips': record.get('ips', [])

            }, success)
        }

