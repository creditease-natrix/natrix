# -*- coding: utf-8 -*-
"""

"""
import logging, json

from django.http.response import JsonResponse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from natrix.common.natrix_views import views as natrix_views
from natrix.common import exception as natrix_exception
from natrix.common.errorcode import ErrorCode

from sentinel.models import Alarm
from sentinel.configurations import alarm_conf
from sentinel.serializers import alarm_serializer
from sentinel.backends.deepmonitor import DeepMonitorAlarmManagement
logger = logging.getLogger(__name__)


class AlarmAPI(natrix_views.RoleBasedAPIView):
    """The alarm management interfaces.

    """

    natrix_roles = ['admin_role', 'alert_role']

    def get(self, request):
        feedback = {
            'permission': True
        }
        try:
            request_data = request.GET
            alarm_id = request_data.get('alarm_id')
            if alarm_id is None:
                feedback['data'] = ErrorCode.parameter_missing('alarm_id')
                raise natrix_exception.ParameterMissingException(parameter='alarm_id')

            try:
                alarm = Alarm.objects.get(id=alarm_id)
                feedback['data'] = {
                    'code': 200,
                    'mesasge': u'The alarm information!',
                    'info': alarm.represent()
                }
            except Alarm.DoesNotExist as e:
                feedback['data'] = ErrorCode.parameter_invalid(
                    'alarm_id', reason=u'Can not search alarm by alarm_id({})'.format(alarm_id))

        except Exception as e:
            natrix_exception.natrix_traceback()
            feedback['data'] = ErrorCode.sp_code_bug(e)

        return JsonResponse(data=feedback)

    def post(self, request, format=None):
        feedback = {
            'permission': True
        }

        if not self.has_permission(self.natrix_roles):
            feedback['data'] = ErrorCode.permission_deny('You dont have permission')
            return JsonResponse(data=feedback)

        try:
            request_data = request.data
            serializer = alarm_serializer.AlarmSerializer(data=request_data,
                                                          user=self.get_user(),
                                                          group=self.get_group())
            if serializer.is_valid():
                serializer.save()
                feedback['data'] = {
                    'code': 200,
                    'message': 'Alarm creation successfully!'
                }
            else:
                logger.info('Create alarm with unavailable parameters: {}'.format(serializer.format_errors()))
                feedback['data'] = ErrorCode.parameter_invalid('Alarm_creation',
                                                               reason=serializer.format_errors())
        except natrix_exception.NatrixBaseException as e:
            logger.info('Create alarm with error in serializer: {}'.format(e))
            feedback['data'] = ErrorCode.sp_code_bug(e)
        except Exception as e:
            natrix_exception.natrix_traceback()
            feedback['data'] = ErrorCode.sp_code_bug(e)

        return JsonResponse(data=feedback)

    def put(self, request, format=None):
        feedback = {
            'permission': True
        }

        if not self.has_permission(self.natrix_roles):
            feedback['data'] = ErrorCode.permission_deny('You dont have permission')
            return JsonResponse(data=feedback)

        try:
            request_data = request.data
            alarm_id = request_data.get('alarm_id')
            if alarm_id is None:
                feedback['data'] = ErrorCode.parameter_missing('alarm_id')
                raise natrix_exception.ParameterMissingException(parameter='alarm_id')

            try:
                alarm = Alarm.objects.get(pk=alarm_id, group=self.get_group())

                serializer = alarm_serializer.AlarmSerializer(instance=alarm,
                                                              data=request_data,
                                                              user=self.get_user(),
                                                              group=self.get_group())
                if serializer.is_valid():
                    serializer.save()
                    feedback['data'] = {
                        'code': 200,
                        'message': 'Alarm update successfully!'
                    }
                else:
                    logger.info('Update alarm with unavailable parameters: {}'.format(serializer.format_errors()))
                    feedback['data'] = ErrorCode.parameter_invalid('Alarm_update',
                                                                   reason=serializer.format_errors())
            except Alarm.DoesNotExist as e:
                feedback['data'] = ErrorCode.parameter_invalid(
                    'alarm_id', reason=u'Can not search alarm by alarm_id({})'.format(alarm_id))
        except natrix_exception.NatrixBaseException as e:
            logger.info('Update alarm with error: {}'.format(e.get_log()))
        except Exception as e:
            natrix_exception.natrix_traceback()
            feedback['data'] = ErrorCode.sp_code_bug(e)

        return JsonResponse(data=feedback)

    def delete(self, request):
        feedback = {
            'permission': True
        }

        if not self.has_permission(self.natrix_roles):
            feedback['data'] = ErrorCode.permission_deny('You dont have permission')
            return JsonResponse(data=feedback)

        try:
            alarm_id = request.GET.get('alarm_id')

            if not alarm_id:
                feedback['data'] = ErrorCode.parameter_missing('alarm_id')
                raise natrix_exception.ParameterMissingException(parameter='alarm_id')

            try:
                alarm = Alarm.objects.get(pk = alarm_id, group=self.get_group())
                alarm_backend = DeepMonitorAlarmManagement(alarm)
                res, desc = alarm_backend.delete()
                print(res, desc)
                if res:
                    alarm.delete()
                    feedback['data'] = {
                        'code': 200,
                        'message': 'Alarm delete successfully!'
                    }
                else:
                    ...
            except Alarm.DoesNotExist:
                feedback['data'] = ErrorCode.parameter_invalid(
                    'alarm_id', reason='The alarm({}) is not exist!'.format(alarm_id)
                )

        except natrix_exception.NatrixBaseException as e:
            logger.info(e.get_log())
        except Exception as e:
            natrix_exception.natrix_traceback()
            feedback['data'] = ErrorCode.sp_code_bug(e)

        return JsonResponse(data=feedback)


class AlarmOperationAPI(natrix_views.RoleBasedAPIView):

    natrix_roles = ['admin_role', 'alert_role']

    def put(self, request):
        feedback = {
            'permission': True
        }

        if not self.has_permission(self.natrix_roles):
            feedback['data'] = ErrorCode.permission_deny('You dont have permission')
            return JsonResponse(data=feedback)

        try:
            request_data = request.data
            serializer = alarm_serializer.AlarmOperationSerializer(data=request_data,
                                                                   user=self.get_user(),
                                                                   group=self.get_group())

            if serializer.is_valid():
                serializer.process()
                feedback['data'] = {
                    'code': 200,
                    'message': 'Operate successfully!'
                }
            else:
                logger.info('Operation with error : {}'.format(serializer.format_errors()))
                feedback['data'] = ErrorCode.parameter_invalid('alarm_operation',
                                                               reason=serializer.format_errors())

        except Exception as e:
            natrix_exception.natrix_traceback()
            feedback['data'] = ErrorCode.sp_code_bug(e)

        return JsonResponse(data=feedback)


class AlarmListAPI(natrix_views.LoginAPIView):

    def get(self, request):
        feedback = {
            'permission': True
        }
        try:
            request_data = request.GET

            serializer = alarm_serializer.AlarmListSerializer(data=request_data)
            if serializer.is_valid():
                is_paginate = serializer.validated_data.get('is_paginate')
                pagenum = serializer.validated_data.get('pagenum', 1)

                alarms = Alarm.objects.filter(group=self.get_group())

                feedback['data'] = {
                    'code': 200,
                    'message': u'Alarm list info',
                    'item_count': len(alarms),
                    'info': []
                }
                if is_paginate:
                    per_page = self.get_per_page()
                    paginator = Paginator(alarms, per_page)

                    try:
                        current_page_query = paginator.page(pagenum)
                    except PageNotAnInteger:
                        current_page_query = paginator.page(1)
                    except EmptyPage:
                        current_page_query = paginator.page(paginator.num_pages)

                    alarms = list(current_page_query)

                    feedback['data']['page_num'] = current_page_query.number
                    feedback['data']['page_count'] = paginator.num_pages

                for record in alarms:
                    feedback['data']['info'].append(record.represent())

            else:
                feedback['data'] = ErrorCode.parameter_invalid('alarm_list',
                                                               reason=serializer.format_errors())

        except Exception as e:
            natrix_exception.natrix_traceback()
            feedback['data'] = ErrorCode.sp_code_bug(e)

        return JsonResponse(data=feedback)


class MonitorListAPI(natrix_views.LoginAPIView):

    def get(self, request):
        feedback = {
            'permission': True
        }
        try:
            protocol_type = request.GET.get('protocol_type')
            if protocol_type is None:
                feedback['data'] = ErrorCode.parameter_missing('protocol_type')
                raise natrix_exception.ParameterMissingException(parameter='protocol_type')
            monitor_list = []
            for monitor in alarm_conf.MONITOR_TYPE.values():
                protocols = monitor.get('protocol', [])
                if protocol_type in protocols:
                    monitor_list.append({
                        'name': monitor.get('name'),
                        'value': monitor.get('name'),
                        'threshold_desc': '单位：{}'.format(monitor.get('unit')),
                        'is_condition': monitor.get('is_condition'),
                        'is_agg': monitor.get('is_agg'),
                        'agg_types': monitor.get('agg_types')

                    })

            feedback['data'] = {
                'code': 200,
                'message': u'monitor items list!',
                'info': monitor_list
            }
        except natrix_exception.NatrixBaseException as e:
            logger.info(e.get_log())
        except Exception as e:
            natrix_exception.natrix_traceback()
            feedback['data'] = ErrorCode.sp_code_bug(e)

        return JsonResponse(data=feedback)

