# -*- coding: utf-8 -*-
"""

"""

import logging, json

from rest_framework import serializers
from django.db.models import Q

from natrix.common.natrix_views.serializers import NatrixSerializer
from natrix.common import exception as natrix_exception

from benchmark.models.task_models import Task
from benchmark.backends import command_dispatcher

from . import datasearch

logger = logging.getLogger(__name__)


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
            raise serializers.ValidationError('The task is not exist(task_id: {})'.format(value))

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
            self.dial_data = command_dispatcher.get_task_data(self.instance.id)
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
            analyse_data[province]['total_packet_loss_rate'] += (packet_loss * 1.0 /packet_send if packet_send else 0.0) * 100
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

        distribution_axis = list(map(lambda x: '{}-{}'.format(round(interval * x, 2),
                                                         round(interval * (x + 1), 2)),
                                     range(slice_count + 1)))

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
            'x-axis': list(map(lambda x: x[0], org_avg[0: 10])),
            'viewpoints': [
                {
                    'name': 'avg_value',
                    'values': list(map(lambda x: x[1], org_avg[0: 10]))
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
                'x-axis': list(map(lambda x: x[0], org_avg[0: 10])),
                'viewpoints': [
                    {
                        'name': 'avg_value',
                        'values': list(map(lambda x: x[1], org_avg[0: 10]))
                    }
                ]
            }

        def get_ping_distribution(max_values, min_values, avg_values):
            max_time = self.get_max_value(max_values)

            slice_count = 10

            interval = max_time / slice_count

            distribution_axis = list(map(lambda x: '{}-{}'.format(interval*x, interval*(x+1)),
                                         range(slice_count+1)))

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
            'error': list(map(lambda record: {
                'terminal': record.get('terminal', None),
                'organizations': record.get('organization_name', []),
                'province': record.get('province', None),
                'city': record.get('city', None),
                'operator': record.get('operator', None),
                'errorinfo': record.get('errorinfo', None)

            }, error)),
            'success': list(map(lambda record:{
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

            }, success))
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

            distribution_axis = list(map(lambda x: '{}-{}'.format(round(interval * x, 2),
                                                             round(interval * (x + 1), 2)),
                                    range(slice_count + 1)))

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

        error_list = list(map(lambda record: {'terminal': record.get('terminal', None),
                                         'organizations': record.get('organization_name', []),
                                         'province': record.get('province', None),
                                         'city': record.get('city', None),
                                         'operator': record.get('operator', None),
                                         'errorinfo': record.get('errorinfo', None)
                                         }, error))

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
            'error': list(map(lambda record: {
                'terminal': record.get('terminal', None),
                'organizations': record.get('organization_name', []),
                'province': record.get('province', None),
                'city': record.get('city', None),
                'operator': record.get('operator', None),
                'errorinfo': record.get('errorinfo', None)
            }, error)),
            'success': list(map(lambda record: {
                'terminal': record.get('terminal', None),
                'organizations': record.get('organization_name', []),
                'province': record.get('province', None),
                'city': record.get('city', None),
                'operator': record.get('operator', None),
                'hop': record.get('hop', None),
                'paths': record.get('paths', {})

            }, success))
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
        top_analyse.sort(key=lambda x: x['value'], reverse=False)
        top_data = {
            'name': 'dns parse top region analyse',
            'x-axis': list(map(lambda x: x['name'], top_analyse[0: 10])),
            'viewpoints': [
                {
                    'name': 'parse_time',
                    'values': list(map(lambda x: x['value'], top_analyse[0: 10]))
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

        parse_time_data = list(map(lambda record: (record['name'],
                                              record['total_ptime'] / record['count']if record['count'] else 0),
                              parse_time_analyse.values()))

        return {
            'name': 'dns parse_time org analyse',
            'x-axis': list(map(lambda x: x[0], parse_time_data)),
            'viewpoints': [
                {
                    'name': 'parse_time',
                    'values': list(map(lambda x: x[1], parse_time_data))
                }
            ]
        }

    def dns_organization_distribution(self):
        success = self.dial_data.get('success', [])

        ptime_list = list(map(lambda x: x['ptime'], success))
        slice_count = self.SLICE_COUNT

        max_time = self.get_max_value(ptime_list)
        interval = max_time / slice_count

        distribution_axis = list(map(lambda x: '{}-{}'.format(round(interval * x, 2),
                                                         round(interval * (x + 1), 2)),
                                range(slice_count + 1)))
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

        parse_time_data = list(map(lambda record: (record['name'],
                                              record['total_ptime'] / record['count'] if record['count'] else 0),
                              parse_time_analyse.values()))

        parse_time_data.sort(key=lambda x: x[1], reverse=True)

        return {
            'name': 'dns parse_time top org analyse',
            'x-axis': list(map(lambda x: x[0], parse_time_data[0: 10])),
            'viewpoints': [
                {
                    'name': 'parse_time',
                    'values': list(map(lambda x: x[1], parse_time_data[0: 10]))
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
            'error': list(map(lambda record: {
                'terminal': record.get('terminal', None),
                'organizations': record.get('organization_name', []),
                'province': record.get('province', None),
                'city': record.get('city', None),
                'operator': record.get('operator', None),
                'errorinfo': record.get('errorinfo', None)
            }, error)),

            'success': list(map(lambda record: {
                'terminal': record.get('terminal', None),
                'organizations': record.get('organization_name', []),
                'province': record.get('province', None),
                'city': record.get('city', None),
                'operator': record.get('operator', None),
                'ptime': record.get('ptime', None),
                'destination': record.get('destination', None),
                'ips': record.get('ips', [])

            }, success))
        }


class TimedTaskAnalyseSerializer(NatrixSerializer):
    task_id = serializers.UUIDField(help_text=u'任务ID')
    view_point = serializers.CharField(help_text=u'分析视角', max_length=32)
    chart_name = serializers.CharField(help_text=u'图表名称（类型）',
                                       max_length=32, required=False, allow_null=True,
                                       allow_blank=True)
    start_time = serializers.FloatField(help_text=u'开始时间', min_value=0)
    end_time = serializers.FloatField(help_text=u'结束时间', min_value=0)

    ANALYSE_CONFIGURATION = {
        'ping': {
            'region': {
                'packet_loss': {
                    'analyse': 'ping_region_packet_loss'
                },
                'delay': {
                    'analyse': 'ping_region_delay'
                },
            },
            'time': {
                'packet_loss': {
                    'analyse': 'ping_timed_packet_loss'
                },
                'delay': {
                    'analyse': 'ping_timed_delay'
                },
                'exception': {
                    'analyse': 'ping_timed_exception'
                },
            },
            'comprehensiveness': {
                'delay': {
                    'analyse': 'ping_com_delay'
                }
            }
        },
        'http': {
            'region': {
                'request': {
                    'analyse': 'http_region_request'
                },
                'parse_time': {
                    'analyse': 'http_region_parsetime'
                }
            },
            'time': {
                'request': {
                    'analyse': 'http_timed_request'
                },
                'exception': {
                    'analyse': 'http_timed_exception'
                }
            },
            'comprehensiveness': {
                'result_distribution': {
                    'analyse': 'http_com_result_distribution'
                },
                'stage_distribution': {
                    'analyse': 'http_com_stage_distribution'
                },
            }
        },
        'dns': {
            'region': {
                'parse_time': {
                    'analyse': 'dns_region_parse_time'
                },
                'parse_result': {
                    'analyse': 'dns_region_parse_result'
                },
            },
            'time': {
                'parse_time': {
                    'analyse': 'dns_timed_parse_time'
                },
                'exception': {
                    'analyse': 'dns_timed_exception'
                },
            },
        },
    }

    SLICE_COUNT = 10

    def validate_task_id(self, value):
        try:
            task = Task.objects.get(Q(id=value) &
                                   Q(time_type='timed'))
            if task.group != self.group and task.scope != 'public':
                raise serializers.ValidationError('The task is not exist(task_id : {})'.format(value))

            self.instance = task
        except Task.DoesNotExist:
            raise serializers.ValidationError('The task is not exist(task_id: {})'.format(value))

        return value

    def is_valid(self, raise_exception=False):
        flag = super(TimedTaskAnalyseSerializer, self).is_valid()

        if not flag:
            return flag

        protocol_type = self.instance.command.protocol_type

        view_point = self.initial_data['view_point']
        chart_name = self.initial_data['chart_name']

        restriction_chartnames = self.ANALYSE_CONFIGURATION[protocol_type][view_point].keys()

        if not (chart_name in restriction_chartnames):
            self._errors['chart_name'] = ['There is not chart_name({}) for task({})'.format(
                chart_name, self.instance.id
            )]
            flag = False
            return flag

        return flag

    def analyse(self):
        view_point = self.validated_data.get('view_point')
        protocol_type = self.instance.command.protocol_type
        chart_name = self.validated_data.get('chart_name')

        self.start_time = int(self.validated_data.get('start_time'))
        self.end_time = int(self.validated_data.get('end_time'))

        analyse_function = getattr(self,
                                   self.ANALYSE_CONFIGURATION.get(
                                       protocol_type).get(view_point).get(chart_name).get('analyse'))

        if not callable(analyse_function):
            raise natrix_exception.ClassInsideException(
                'There is not analyse logic({}, {})'.format(view_point, chart_name))

        return analyse_function()

    def ping_region_packet_loss(self):
        analyse_data = {
            'name': 'ping packet_loss analysis base on region',
            'values': datasearch.ping_loss_region(str(self.instance.id),
                                                  self.start_time,
                                                  self.end_time)
        }

        return analyse_data

    def ping_region_delay(self):
        analyse_data = {
            'name': 'ping delay analysis base on region',
            'values': datasearch.ping_delay_region(str(self.instance.id),
                                                   self.start_time,
                                                   self.end_time)
        }

        return analyse_data

    def ping_timed_packet_loss(self):

        x_axis, viewpoints = datasearch.ping_loss_time(
            str(self.instance.id),
            self.start_time, self.end_time,
            self.instance.schedule.frequency * 1000)

        analyse_data = {
            'name': 'ping packet_loss analysis base on time',
            'x-axis': x_axis,
            'viewpoints': viewpoints
        }

        return analyse_data

    def ping_timed_delay(self):
        x_axis, viewpoints = datasearch.ping_delay_time(
            str(self.instance.id),
            self.start_time, self.end_time,
            self.instance.schedule.frequency * 1000)
        analyse_data = {
            'name': 'ping delay region analysis base on time',
            'x-axis': x_axis,
            'viewpoints': viewpoints
        }

        return analyse_data

    def ping_timed_exception(self):
        x_axis, viewpoints = datasearch.ping_exception_time(
            str(self.instance.id),
            self.start_time, self.end_time,
            self.instance.schedule.frequency * 1000)

        analyse_data = {
            'name': 'ping exception analysis base on time',
            'x-axis': x_axis,
            'viewpoints': viewpoints
        }

        return analyse_data

    def ping_com_delay(self):
        x_axis, viewpoints = datasearch.ping_delay_dist(
            str(self.instance.id),
            self.start_time, self.end_time,
            50)

        analyse_data = {
            'name': 'ping delay analysis base on distribution',
            'x-axis': x_axis,
            'viewpoints': viewpoints
        }

        return analyse_data

    def http_region_request(self):

        analyse_data = {
            'name': 'http request analysis base on region',
            'values': datasearch.http_request_region(
                    str(self.instance.id), self.start_time, self.end_time)
        }

        return analyse_data

    def http_region_parsetime(self):
        analyse_data = {
            'name': 'http parsetime analysis base on region',
            'values': datasearch.http_parsetime_region(
                str(self.instance.id), self.start_time, self.end_time)
        }

        return analyse_data

    def http_timed_request(self):
        x_axis, viewpoints = datasearch.http_request_time(
            str(self.instance.id),
            self.start_time, self.end_time,
            self.instance.schedule.frequency * 1000)

        analyse_data = {
            'name': 'http request analysis base on time',
            'x-axis': x_axis,
            'viewpoints': viewpoints
        }

        return analyse_data

    def http_timed_exception(self):
        x_axis, viewpoints = datasearch.http_exception_time(
            str(self.instance.id),
            self.start_time, self.end_time,
            self.instance.schedule.frequency * 1000)

        analyse_data = {
            'name': 'http exception analysis base on time',
            'x-axis': x_axis,
            'viewpoints': viewpoints
        }
        return analyse_data

    def http_com_result_distribution(self):
        analyse_data = {
            'name': 'http result analysis base on distribution',
            'values': datasearch.http_result_dist(
                str(self.instance.id),
                self.start_time, self.end_time)
        }

        return analyse_data

    def http_com_stage_distribution(self):
        analyse_data = {
            'name': 'http stage analysis base on distribution',
            'values': datasearch.http_stage_dist(
                str(self.instance.id),
                self.start_time, self.end_time,
            )
        }

        return analyse_data

    def dns_region_parse_time(self):
        analyse_data = {
            'name': 'dns parse time analysis base on region',
            'values': datasearch.dns_parsetime_region(
                str(self.instance.id), self.start_time, self.end_time)
        }

        return analyse_data

    def dns_region_parse_result(self):
        analyse_data = {
            'name': 'dns parse result analysis base on region',
            'values': datasearch.dns_parseresult_region(
                str(self.instance.id), self.start_time, self.end_time)
        }

        return analyse_data

    def dns_timed_parse_time(self):
        x_axis, viewpoints = datasearch.dns_parsetime_time(
            str(self.instance.id),
            self.start_time, self.end_time,
            self.instance.schedule.frequency * 1000)

        analyse_data = {
            'name': 'dns parse time analysis base on time',
            'x-axis': x_axis,
            'viewpoints': viewpoints
        }

        return analyse_data

    def dns_timed_exception(self):
        x_axis, viewpoints = datasearch.dns_exception_time(
            str(self.instance.id),
            self.start_time, self.end_time,
            self.instance.schedule.frequency * 1000)

        analyse_data = {
            'name': 'dns exception analysis base on time',
            'x-axis': x_axis,
            'viewpoints': viewpoints
        }

        return analyse_data

