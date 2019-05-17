# -*- coding: utf-8 -*-
"""

"""

from __future__ import unicode_literals

import logging, json
import uuid

from django.http.response import JsonResponse
from django.utils import timezone

from natrix.common.common_views import NatrixAPIView
from natrix.common import exception as natrix_exception
from natrix.common.errorcode import ErrorCode

from benchmark.models import Task
from benchmark.serializers import task_serializer
from benchmark.backends import command_adapter

logger = logging.getLogger(__name__)

class InstantTask(NatrixAPIView):
    """Instant Task Info API

    mehtod:
    - GET
        get instant task information
    - POST
        create instant task

    """

    permission_classes = ()
    authentication_classes = []

    def get(self, request):
        """GET method

        Get an instant task information.

        :param request:
        :return:
        """
        feedback = {
            'permission': True
        }
        try:
            task_id = request.GET.get('task_id', None)
            if task_id is None:
                feedback['data'] = ErrorCode.parameter_missing('task_id')
                raise natrix_exception.ParameterMissingException(parameter='task_id')
            try:
                uuid.UUID(hex=task_id)
                task = Task.objects.get(id=task_id, time_type='instant')
                serializer = task_serializer.InstantTaskSerializer(instance=task)
                feedback['data'] = {
                        'code': 200,
                        'message': u'Instant Task Info!',
                        'info': serializer.data
                }
            except ValueError:
                feedback['data'] = ErrorCode.parameter_invalid('task_id', reason=u'must be a UUID')
                raise natrix_exception.ParameterInvalidException(parameter='task_id')
            except Task.DoesNotExist:
                feedback['data'] = ErrorCode.parameter_invalid(
                    'task_id', reason=u'Can not retrieve Instant Task: {}'.format(task_id))
                raise natrix_exception.ParameterInvalidException(parameter='task_id')
            except natrix_exception.BaseException as e:
                logger.error(e.get_log())
                feedback['data'] = ErrorCode.sp_code_bug('Serializer error: {}'.format(e.get_log()))
            except Exception as e:
                logger.error(e)
                feedback['data'] = ErrorCode.sp_code_bug('Unknow error: {}'.format(e))

        except natrix_exception.BaseException as e:
            logger.info(e.get_log())

        return JsonResponse(data=feedback)

    def post(self, request, format=None):
        """Create an instant task

        :param request:
        :param format:
        :return:
        """
        feedback = {
            'permission': True
        }
        try:
            post_data = request.data
            serializer = task_serializer.InstantTaskSerializer(data=post_data)
            if serializer.is_valid():
                task = serializer.save()
                feedback['data'] = {
                        'code': 200,
                        'message': 'Instant task creation successfully!',
                        'info': {
                            'task_id': task.pk
                        }
                }
            else:
                logger.info('Instant task parameters is not available: {}'.format(serializer.format_errors()))
                feedback['data'] = ErrorCode.parameter_invalid('instant_task_creation',
                                                               reason=serializer.format_errors())
        except natrix_exception.BaseException as e:
            feedback['data'] = ErrorCode.sp_code_bug('Create instant has a bug: {}'.format(e.get_log()))
            logger.error(e.get_log())
        except Exception as e:
            natrix_exception.natrix_traceback()
            feedback['data'] = ErrorCode.sp_db_fault(str(e))

        return JsonResponse(data=feedback)


class InstantStatus(NatrixAPIView):

    permission_classes = ()
    authentication_classes = []

    def get(self, request):
        """Get instant task status

        Used by front-end to determine whether a instant task is finished.
        If finished is true, front-end can't finish periodic retriving action.

        :param request:
        :return:
        """
        feedback = {
            'permission': True
        }

        try:
            task_id = request.GET.get('task_id', None)
            if task_id is None:
                feedback['data'] = ErrorCode.parameter_missing('task_id')
                raise natrix_exception.ParameterMissingException(parameter='task_id')
            try:
                uuid.UUID(hex=task_id)
            except ValueError:
                feedback['data'] = ErrorCode.parameter_invalid('task_id', reason=u'must be a UUID')
                raise natrix_exception.ParameterInvalidException(parameter='task_id')
            try:
                task = Task.objects.get(id=task_id, time_type='instant')
                # response_count = success + wrong
                res = command_adapter.get_command_data(task.command.id)
                success = len(res.get('success'))
                wrong = len(res.get('error'))
                response_count = success + wrong

                time_delta = timezone.now() - task.create_time

                if task.status and ( response_count == task.terminal_count or time_delta.seconds > 120):
                    task.status = False
                    task.result_snapshot = json.dumps(res)
                    task.save()

                feedback['data'] = {
                    'code': 200,
                    'message': 'Instant Task Status',
                    'info': {
                        'finished': not task.status,
                        'total': task.terminal_count,
                        'responses': response_count,
                        'success': success,
                        'wrong': wrong
                    }
                }

            except Task.DoesNotExist:
                feedback['data'] = ErrorCode.parameter_invalid(
                    'task_id', reason=u'Can not retrieve Instant Task: {}'.format(task_id))
                raise natrix_exception.ParameterInvalidException(parameter='task_id')

        except natrix_exception.BaseException as e:
            logger.error(e.get_log())

        return JsonResponse(data=feedback)

    def put(self, request, format=None):
        """To turn off an instant task.

        The instant task can only turn off. After turn off an instant task, we didn't receive
        terminal-response (the result terminal return).

        :param request:
        :param format:
        :return:
        """
        logger.info('run status put method: {}'.format(request))
        feedback = {
            'permission': True
        }
        try:
            task_id = request.data.get('task_id', None)
            if task_id is None:
                feedback['data'] = ErrorCode.parameter_missing('task_id')
                raise natrix_exception.ParameterMissingException(parameter='task_id')

            try:
                uuid.UUID(hex=task_id)
            except ValueError:
                feedback['data'] = ErrorCode.parameter_invalid('task_id', reason=u'must be a UUID')
                raise natrix_exception.ParameterInvalidException(parameter='task_id')
            try:

                task = Task.objects.get(id=task_id, time_type='instant')

                if task.status:
                    res = command_adapter.get_command_data(task.command.id)
                    task.status = False
                    task.result_snapshot = json.dumps(res)
                    task.save()
                    message = u'Turn off task successfully!'
                else:
                    message = u'The task is already turned off!'
                    res = json.loads(task.result_snapshot)

                success = len(res.get('success'))
                wrong = len(res.get('error'))
                response_count = success + wrong

                feedback['data'] = {
                    'code': 200,
                    'message': message,
                    'info': {
                        'finished': not task.status,
                        'total': task.terminal_count,
                        'responses': response_count,
                        'success': success,
                        'wrong': wrong
                    }
                }
            except Task.DoesNotExist:
                feedback['data'] = ErrorCode.parameter_invalid(
                    'task_id', reason=u'Can not retrieve Instant Task: {}'.format(task_id))
                raise natrix_exception.ParameterInvalidException(parameter='task_id')

        except natrix_exception.BaseException as e:
            logger.error(e.get_log())

        return JsonResponse(data=feedback)


class InstantAnalyse(NatrixAPIView):
    """

    """

    def get(self, request):
        feedback = {
            'permission': True
        }
        try:
            get_data = {
                'task_id': request.GET.get('task_id'),
                'view_point': request.GET.get('view_point'),
                'chart_name': request.GET.get('chart_name')
            }

            serializer = task_serializer.InstantTaskAnalyseSerializer(data=get_data)
            if serializer.is_valid():
                analyse_data = serializer.analyse()
                feedback['data'] = {
                    'code': 200,
                    'message': u'Instant task analyse data!',
                    'info': analyse_data
                }
            else:
                logger.info(serializer.errors)
                feedback['data'] = ErrorCode.parameter_invalid('task_analyse',
                                                               serializer.format_errors())
                raise natrix_exception.ParameterInvalidException(parameter='task_analyse')

        except natrix_exception.BaseException as e:
            logger.error(e.get_log())
        except Exception as e:
            natrix_exception.natrix_traceback()
            feedback['data'] = ErrorCode.sp_code_bug(e)

        return JsonResponse(data=feedback)