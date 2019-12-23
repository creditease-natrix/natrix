# -*- coding: utf-8 -*-

import requests
import json

from django.conf import settings

from natrix.common.config import natrix_config

SERVER_NAME = natrix_config.get_value('COMMON', 'server_name')


class DeepMonitorAlarmManagement():
    deepmonitor_url = settings.DEEPMONITOR_URL + '/alarm'

    def __init__(self, alarm):
        self.alarm = alarm

    def add(self):
        try:
            request_data = self.transform_request()
            res = requests.post(self.deepmonitor_url, json=request_data)
            response = json.loads(res.text)
            if response.get('status', None) == 'ok':
                return response.get('alarm_id')

            # throw exception
        except Exception as e:
            ...

    def modify(self):
        try:
            request_data = self.transform_request()
            request_data['alarm_id'] = str(self.alarm.deepmonitor_uuid)
            res = requests.put(self.deepmonitor_url, json=request_data)

            response = json.loads(res.text)
            if response.get('status', None) == 'ok':
                return response.get('alarm_id')

        except Exception as e:
            ...

    def delete(self):
        if self.alarm:
            request_data = {
                'alarm_id': str(self.alarm.deepmonitor_uuid),
            }
            try:
                res = requests.delete(self.deepmonitor_url, json=request_data)
                response = json.loads(res.text)
                if response.get('status', '')  == 'ok':
                    return True, 'Successfully!'
                else:
                    return False, response.get('reason')
            except Exception as e:
                return False, f'Request Wrong: {e}!'
        else:
            return False, 'Without alarm instance'

    def switch(self):
        if self.alarm:
            request_data = {
                'alarm_id': str(self.alarm.deepmonitor_uuid),
                'status': not self.alarm.status
            }
            try:
                res = requests.put(self.deepmonitor_url, json=request_data)
                response = json.loads(res.text)
                if response.get('status', '')  == 'ok':
                    return True, 'Successfully!'
                else:
                    return False, response.get('reason')
            except Exception as e:
                return False, f'Request Wrong: {e}!'
        else:
            return False, 'Without alarm instance'

    def _window_size_policy(self):
        return self.alarm.task.get_frequency() * 1000 * 1.5

    def transform_request(self):
        request_data = None
        if self.alarm.monitor_type == 'ping_loss_rate':
            if self.alarm.aggregation_type == 'average':
                request_data = {
                    'subscribe': {
                        'tags': [{
                            '_type': 'ping',
                            'task_id': str(self.alarm.task.id)
                        }]
                    },
                    'window': 'Time',
                    'window_params': {
                        'size': self._window_size_policy(),
                        'time_field': 'task_generate_time'
                    },
                    'operation': 'FieldDivideAverage',
                    'operation_params': {
                        'op': self.alarm.operation.upper(),
                        'threshold': self.alarm.threshold,
                        'dividend': 'packet_loss',
                        'divisor': 'packet_send'
                    },
                    'status': True
                }
            elif self.alarm.aggregation_type == 'individuality':
                request_data = {
                    'subscribe': {
                        'tags': [{
                            '_type': 'ping',
                            'task_id': str(self.alarm.task.id)
                        }]
                    },
                    'window': 'UNIQUE_EVENT',
                    'window_params': {
                        'size': self._window_size_policy(),
                        'keys': ['terminal']
                    },
                    'operation': 'FieldDivideCount',
                    'operation_params': {
                        'op': 'GT',
                        'threshold': self.alarm.agg_condition,
                        'dividend': 'packet_loss',
                        'divisor': 'packet_send',
                        'field_op': self.alarm.operation.upper(),
                        'field_threshold': self.alarm.threshold,
                    },
                    'status': True
                }
        elif self.alarm.monitor_type == 'ping_delay':
            if self.alarm.aggregation_type == 'average':
                request_data = {
                    'subscribe': {
                        'tags': [{
                            '_type': 'ping',
                            'task_id': str(self.alarm.task.id)
                        }]
                    },
                    'window': 'Time',
                    'window_params': {
                        'size': self._window_size_policy(),
                        'time_field': 'task_generate_time'
                    },
                    'operation': 'AllAverage',
                    'operation_params': {
                        'op': self.alarm.operation.upper(),
                        'threshold': self.alarm.threshold,
                        'field': 'avg_time'

                    },
                    'status': True
                }
            elif self.alarm.aggregation_type == 'individuality':
                request_data = {
                    'subscribe': {
                        'tags': [{
                            '_type': 'ping',
                            'task_id': str(self.alarm.task.id)
                        }]
                    },
                    'window': 'UNIQUE_EVENT',
                    'window_params': {
                        'size': self._window_size_policy(),
                        'keys': ['terminal']
                    },
                    'operation': 'SingleFieldCount',
                    'operation_params': {
                        'op': 'GT',
                        'threshold': self.alarm.agg_condition,
                        'field': 'avg_time',
                        'field_op': self.alarm.operation.upper(),
                        'field_threshold': self.alarm.threshold,
                    },
                    'status': True
                }
        elif self.alarm.monitor_type == 'http_request_time':
            if self.alarm.aggregation_type == 'average':
                request_data = {
                    'subscribe': {
                        'tags': [{
                            '_type': 'http',
                            'task_id': str(self.alarm.task.id)
                        }]
                    },
                    'window': 'Time',
                    'window_params': {
                        'size': self._window_size_policy(),
                        'time_field': 'task_generate_time'
                    },
                    'operation': 'AllAverage',
                    'operation_params': {
                        'op': self.alarm.operation.upper(),
                        'threshold': self.alarm.threshold,
                        'field': 'total_time'
                    },
                    'status': True
                }
            elif self.alarm.aggregation_type == 'individuality':
                request_data = {
                    'subscribe': {
                        'tags': [{
                            '_type': 'http',
                            'task_id': str(self.alarm.task.id)
                        }]
                    },
                    'window': 'UNIQUE_EVENT',
                    'window_params': {
                        'size': self._window_size_policy(),
                        'keys': ['terminal']
                    },
                    'operation': 'SingleFieldCount',
                    'operation_params': {
                        'op': 'GT',
                        'threshold': self.alarm.agg_condition,
                        'field': 'total_time',
                        'field_op': self.alarm.operation.upper(),
                        'field_threshold': self.alarm.threshold,
                    },
                    'status': True
                }
        elif self.alarm.monitor_type == 'http_status_code':
            request_data = {
                'subscribe': {
                    'tags': [{
                        '_type': 'http',
                        'task_id': str(self.alarm.task.id)
                    }]
                },
                'window': 'UNIQUE_EVENT',
                'window_params': {
                    'size': self._window_size_policy(),
                    'keys': ['terminal']
                },
                'operation': 'SingleFieldCount',
                'operation_params': {
                    'op': 'GT',
                    'threshold': self.alarm.agg_condition,
                    'field': 'status_code',
                    'field_op': self.alarm.operation.upper(),
                    'field_threshold': self.alarm.threshold,
                },
                'status': True
            }
        elif self.alarm.monitor_type == 'parse_time':
            if self.alarm.task.protocol_type == 'http':
                field_name = 'period_nslookup'
            else:
                field_name = 'ptime'
            if self.alarm.aggregation_type == 'average':
                request_data = {
                    'subscribe': {
                        'tags': [{
                            '_type': self.alarm.task.protocol_type,
                            'task_id': str(self.alarm.task.id)
                        }]
                    },
                    'window': 'Time',
                    'window_params': {
                        'size': self._window_size_policy(),
                        'time_field': 'task_generate_time'
                    },
                    'operation': 'AllAverage',
                    'operation_params': {
                        'op': self.alarm.operation.upper(),
                        'threshold': self.alarm.threshold,
                        'field': field_name
                    },
                    'status': True
                }
            elif self.alarm.aggregation_type == 'individuality':
                request_data = {
                    'subscribe': {
                        'tags': [{
                            '_type': 'http',
                            'task_id': str(self.alarm.task.id)
                        }]
                    },
                    'window': 'UNIQUE_EVENT',
                    'window_params': {
                        'size': self._window_size_policy(),
                        'keys': ['terminal']
                    },
                    'operation': 'SingleFieldCount',
                    'operation_params': {
                        'op': 'GT',
                        'threshold': self.alarm.agg_condition,
                        'field': field_name,
                        'field_op': self.alarm.operation.upper(),
                        'field_threshold': self.alarm.threshold,
                    },
                    'status': True
                }
        elif self.alarm.monitor_type == 'error_count':
            request_data = {
                'subscribe': {
                    'tags': [{
                        '_type': 'error',
                        'task_id': str(self.alarm.task.id)
                    }]
                },
                'window': 'UNIQUE_EVENT',
                'window_params': {
                    'size': self._window_size_policy(),
                    'keys': ['terminal']
                },
                'operation': 'BaseCount',
                'operation_params': {
                    'op': 'GT',
                    'threshold': self.alarm.agg_condition
                },
                'status': True
            }

        request_data['status'] = self.alarm.status
        request_data['group_by'] = ''
        request_data['name'] = self.alarm.name
        return request_data


class DeepMonitorNotificationManagement():
    deepmonitor_url = settings.DEEPMONITOR_URL + '/notify'

    def __init__(self, notify):
        self.notify = notify
        self.alarm = notify.alarm

    def add(self):
        if self.alarm is None:
            raise Exception('Missing alarm for creating notification!')

        notification, operation = self.transform_request()
        try:
            res = requests.post(self.deepmonitor_url, json=notification)
            response = json.loads(res.text)

            if response.get('status', None) == 'ok':
                notify_id =  response.get('notify_id')
            else:
                # TODO: ...
                raise Exception()

            operation['notify_id'] = notify_id
            res = requests.post(self.deepmonitor_url + '/operation', json=operation)
            response = json.loads(res.text)
            if response.get('status', None) == 'ok':
                operation_id = response.get('operation_id')
            else:
                # TODO: ...
                raise Exception()
            return notify_id, operation_id
        except Exception as e:
            ...

    def modify(self):
        notification, operation = self.transform_request()
        try:
            operation['operation_id'] = str(self.notify.deepmonitor_operation)
            res = requests.put(self.deepmonitor_url + '/operation', json=operation)

            response = json.loads(res.text)
            if response.get('status', None) == 'ok':
                # TODO:
                return
            else:
                raise Exception('Modify notification error!')

        except Exception as e:
            ...

    def delete(self):
        if self.notify:
            request_data = {
                'notify_id': str(self.notify.deepmonitor_uuid),
            }
            try:
                res = requests.delete(self.deepmonitor_url, json=request_data)
                response = json.loads(res.text)
                if response.get('status', '') == 'ok':
                    return True, 'Successfully!'
                else:
                    return False, response.get('reason')
            except Exception as e:
                return False, f'Request Wrong: {e}!'
        else:
            return False, 'Without alarm instance'

    def switch(self):
        if self.alarm:
            request_data = {
                'notify_id': str(self.notify.deepmonitor_uuid)
            }
            try:
                res = requests.post(self.deepmonitor_url + '/switch', json=request_data)
                response = json.loads(res.text)
                if response.get('status', '')  == 'ok':
                    return True, 'Successfully!'
                else:
                    return False, response.get('reason')
            except Exception as e:
                return False, f'Request Wrong: {e}!'
        else:
            return False, 'Without alarm instance'

    def transform_request(self):
        notification_data = {
            'alarm_id': str(self.alarm.deepmonitor_uuid),
            'template': '',
            'template_parser': 'SimpleTemplateParser',
            'template_params': {}
        }

        operation_data = {
            'frequency': self.notify.frequency,
            'on_recovery': self.notify.is_recovery,
            'operation': self.notify.notify_type,
            'operation_parser': 'RestfulOperationParser',
            'operation_params': {
                'destination': f'{SERVER_NAME}/natrix/rbac/user/contacts/v1',
                'users': [str(u.userinfo.uuid) for u in self.notify.users.all() if u.userinfo]
            },
        }

        return notification_data, operation_data


