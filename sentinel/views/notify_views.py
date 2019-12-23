# -*- coding: utf-8 -*-
"""

"""
import logging

from django.http.response import JsonResponse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from natrix.common.natrix_views import views as natrix_views
from natrix.common.natrix_views import permissions as natrix_permissions
from natrix.common import exception as natrix_exception
from natrix.common.errorcode import ErrorCode

from sentinel.models import Notification
from sentinel.serializers import notify_serializer
from sentinel.backends.deepmonitor import DeepMonitorNotificationManagement

logger = logging.getLogger(__name__)


class NotificationAPI(natrix_views.NatrixAPIView):
    permission_classes = (natrix_permissions.LoginPermission,)
    authentication_classes = []

    def get(self, request):
        feedback = {
            'permission': True
        }
        try:
            request_data = request.GET
            serializer = notify_serializer.NotifySearchSerializer(data=request_data,
                                                                  user=self.get_user(),
                                                                  group=self.get_group())
            if serializer.is_valid():
                feedback['data'] = {
                    'code': 200,
                    'message': u'Notification information!',
                    'info': serializer.presentation()
                }
            else:
                feedback['data'] = ErrorCode.parameter_invalid('Notification search',
                                                               reason=serializer.format_errors())
        except Exception as e:
            natrix_exception.natrix_traceback()
            feedback['data'] = ErrorCode.sp_code_bug(e)

        return JsonResponse(data=feedback)

    def post(self, request, format=None):
        feedback = {
            'permission': True
        }
        try:
            request_data = request.data
            serializer = notify_serializer.NotifySerializer(data=request_data,
                                                            user=self.get_user(),
                                                            group=self.get_group())
            if serializer.is_valid():
                serializer.save()
                feedback['data'] = {
                    'code': 200,
                    'message': u'Notification create successfully!'
                }
            else:
                feedback['data'] = ErrorCode.parameter_invalid(
                        'notify_creation', reason=serializer.format_errors())

        except Exception as e:
            natrix_exception.natrix_traceback()
            feedback['data'] = ErrorCode.sp_code_bug(e)

        return JsonResponse(data=feedback)

    def put(self, request, format=None):
        feedback = {
            'permission': True
        }

        try:
            request_data = request.data
            notify_id = request_data.get('notify_id')
            if notify_id is None:
                feedback['data'] = ErrorCode.parameter_missing('notify_id')
                raise  natrix_exception.ParameterMissingException(parameter='notify_id')

            try:
                notification = Notification.objects.get(pk=notify_id, group=self.get_group())
            except Notification.DoesNotExist as e:
                feedback['data'] = ErrorCode.parameter_invalid(
                    'notify_id', reason=u'Notification({}) is not exist!'.format(notify_id))
                raise natrix_exception.ParameterInvalidException(parameter='notify_id')

            serializer = notify_serializer.NotifySerializer(data=request_data,
                                                            instance=notification,
                                                            user=self.get_user(),
                                                            group=self.get_group())

            if serializer.is_valid():
                serializer.save()
                feedback['data'] = {
                    'code': 200,
                    'message': u'Notification edit successfully!'
                }
            else:
                feedback['data'] = ErrorCode.parameter_invalid('Notification Edition',
                                                               serializer.format_errors())

        except natrix_exception.NatrixBaseException as e:
            logger.info('Modify notification with error: {}'.format(e.get_log()))
        except Exception as e:
            natrix_exception.natrix_traceback()
            feedback['data'] = ErrorCode.sp_code_bug(e)

        return JsonResponse(data=feedback)

    def delete(self, request):
        feedback = {
            'permission': True
        }
        try:
            notify_id = request.GET.get('notify_id')
            if not notify_id:
                feedback['data'] = ErrorCode.parameter_missing('notify_id')
                raise natrix_exception.ParameterMissingException(parameter='notify_id')
            try:
                notification = Notification.objects.get(pk = notify_id, group=self.get_group())
                notify_backend = DeepMonitorNotificationManagement(notification)
                result, message = notify_backend.delete()
                if result:
                    notification.delete()
                    feedback['data'] = {
                        'code': 200,
                        'message': 'Notification delete successfully!'
                    }
                else:
                    feedback['data'] = ErrorCode.sp_code_bug(f'Delete notification from abstreaming failed: {message}')

            except Notification.DoesNotExist as e:
                feedback['data'] = ErrorCode.parameter_invalid(
                    'notify_id', reason='The notification({}) is not exist!'.format(notify_id)
                )
        except natrix_exception.NatrixBaseException as e:
            logger.info(e.get_log())
        except Exception as e:
            natrix_exception.natrix_traceback()
            feedback['data'] = ErrorCode.sp_code_bug(e)

        return JsonResponse(data=feedback)


class NotificationOperationAPI(natrix_views.NatrixAPIView):
    permission_classes = (natrix_permissions.LoginPermission,)
    authentication_classes = []

    def put(self, request, format=None):
        feedback = {
            'permission': True
        }
        try:
            request_data = request.data
            serializer = notify_serializer.NotificationOperationSerializer(
                    data=request_data, user=self.get_user(), group=self.get_group())

            if serializer.is_valid():
                serializer.process()
                feedback['data'] = {
                    'code': 200,
                    'message': 'Operate successfully!'
                }
            else:
                logger.info('Operation with error : {}'.format(serializer.format_errors()))
                feedback['data'] = ErrorCode.parameter_invalid('notification_operation',
                                                               reason=serializer.format_errors())

        except Exception as e:
            natrix_exception.natrix_traceback()
            feedback['data'] = ErrorCode.sp_code_bug(e)

        return JsonResponse(data=feedback)


class NotificationListAPI(natrix_views.NatrixAPIView):
    permission_classes = (natrix_permissions.LoginPermission,)
    authentication_classes = []

    def get(self, request):
        feedback = {
            'permission': True
        }
        try:
            request_data = request.GET

            serializer = notify_serializer.NotificationListSerializer(data=request_data,
                                                                      user=self.get_user(),
                                                                      group=self.get_group())
            if not serializer.is_valid():
                feedback['data'] = ErrorCode.parameter_invalid('notification_list',
                                                               reason=serializer.format_errors())
                raise natrix_exception.ParameterInvalidException(parameter='notification_list')


            is_paginate = serializer.validated_data.get('is_paginate')
            pagenum = serializer.validated_data.get('pagenum', 1)

            notifications = serializer.alarm.notification_set.all()
            feedback['data'] = {
                'code': 200,
                'message': u'Notification list info',
                'item_count': len(notifications),
                'info': []
            }

            if is_paginate:
                per_page = self.get_per_page()
                paginator = Paginator(notifications, per_page)

                try:
                    current_page_query = paginator.page(pagenum)
                except PageNotAnInteger:
                    current_page_query = paginator.page(1)
                except EmptyPage:
                    current_page_query = paginator.page(paginator.num_pages)
                notifications = list(current_page_query)

                feedback['data']['page_num'] = current_page_query.number
                feedback['data']['page_count'] = paginator.num_pages

            for n in notifications:
                feedback['data']['info'].append(n.represent())

        except natrix_exception.NatrixBaseException as e:
            logger.info(e.get_log())
        except Exception as e:
            natrix_exception.natrix_traceback()
            feedback['data'] = ErrorCode.sp_code_bug(e)

        return JsonResponse(data=feedback)



