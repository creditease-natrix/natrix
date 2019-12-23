# -*- coding: utf-8 -*-
"""

"""

from __future__ import unicode_literals

import logging

from django.db import transaction
from django.http.response import JsonResponse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from natrix.common.natrix_views import views as natrix_views
from natrix.common import exception as natrix_exception
from natrix.common.errorcode import ErrorCode

from benchmark.serializers import task_serializer, analyse_serializer
from benchmark.models import Task, FollowedTask

logger = logging.getLogger(__name__)


class TimedTask(natrix_views.RoleBasedAPIView):

    natrix_roles = ['task_role', 'admin_role']

    def get(self, request):
        feedback = {
            'permission': True
        }
        try:
            get_data = request.GET
            serializer = task_serializer.TimedTaskInfoSerializer(data=get_data,
                                                                 user=self.get_user(),
                                                                 group=self.get_group())
            if serializer.is_valid():
                feedback['data'] = {
                    'code': 200,
                    'message': u'Timed task info!',
                    'data': serializer.representation()
                }
            else:
                logger.info('Timed task search with invalid parameters: {}'.format(serializer.format_errors()))
                feedback['data'] = ErrorCode.parameter_invalid('Timed_task_info',
                                                               reason=serializer.format_errors())
        except natrix_exception.NatrixBaseException as e:
            feedback['data'] = ErrorCode.sp_code_bug('Get task info has a bug: {}'.format(e.get_log()))
            logger.error(e.get_log())
        except Exception as e:
            natrix_exception.natrix_traceback()
            feedback['data'] = ErrorCode.sp_db_fault(e)

        return JsonResponse(data=feedback)

    def post(self, request, format=None):
        # create a new timed task
        feedback = {
            'permission': True
        }

        if not self.has_permission(self.natrix_roles):
            feedback['data'] = ErrorCode.permission_deny('You dont have permission')
            return JsonResponse(data=feedback)

        try:
            post_data = request.data
            serializer = task_serializer.TimedTaskSerializer(data=post_data,
                                                             user=self.get_user(),
                                                             group=self.get_group())
            if serializer.is_valid():
                serializer.save()
                feedback['data'] = {
                    'code': 200,
                    'message': 'Timed task creation successfully!',
                }
            else:
                logger.info('Timed task parameters is not available: {}'.format(serializer.format_errors()))
                feedback['data'] = ErrorCode.parameter_invalid('Timed_task_creation',
                                                               reason=serializer.format_errors())
        except natrix_exception.NatrixBaseException as e:
            feedback['data'] = ErrorCode.sp_code_bug('Create instant has a bug: {}'.format(e.get_log()))
            logger.error(e.get_log())
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

            task_id = request_data.get('id')
            try:
                task = Task.objects.get(id=task_id, group=self.get_group())
                serializer = task_serializer.TimedTaskSerializer(
                    data=request_data, instance=task, user=self.get_user(), group=self.get_group())
                if serializer.is_valid():
                    serializer.save()
                    feedback['data'] = {
                        'code': 200,
                        'message': "Timed task modify succesfully!"
                    }
                else:
                    feedback['data'] = ErrorCode.parameter_invalid(
                        'Timed task edit', reason=serializer.format_errors())
            except Task.DoesNotExist:
                feedback['data'] = ErrorCode.parameter_invalid('id', reason=u'Task is not exist')
        except natrix_exception.NatrixBaseException as e:
            feedback['data'] = ErrorCode.sp_code_bug('Create instant has a bug: {}'.format(e.get_log()))
            logger.error(e.get_log())
        except Exception as e:
            natrix_exception.natrix_traceback()
            feedback['data'] = ErrorCode.sp_db_fault(e)

        return JsonResponse(data=feedback)

    def delete(self, request):
        feedback = {
            'permission': True
        }

        if not self.has_permission(self.natrix_roles):
            feedback['data'] = ErrorCode.permission_deny('You dont have permission')
            return JsonResponse(data=feedback)

        try:
            task_id = request.GET.get('task_id')

            if not task_id:
                feedback['data'] = ErrorCode.parameter_missing('task_id')
                raise natrix_exception.ParameterMissingException(parameter='task_id')
            try:
                with transaction.atomic():
                    task = Task.objects.get(id=task_id, group=self.get_group())
                    task.schedule.delete()
                    task.delete()
                    feedback['data'] = {
                        'code': 200,
                        'message': 'Task delete successfully!'
                    }
            except Task.DoesNotExist:
                feedback['data'] = ErrorCode.parameter_invalid(
                    'task_id', reason='The task({}) is not exist!'.format(task_id))

        except natrix_exception.NatrixBaseException as e:
            logger.info(e.get_log())
        except Exception as e:
            natrix_exception.natrix_traceback()
            feedback['data'] = ErrorCode.sp_code_bug(e)

        return JsonResponse(data=feedback)


class TimedTaskList(natrix_views.LoginAPIView):

    def get(self, request):
        feedback = {
            'permission': True
        }
        try:
            get_data = request.GET

            serializer = task_serializer.TableSearchSerializer(data=get_data)
            if serializer.is_valid():
                is_paginate = serializer.validated_data.get('is_paginate')
                search = serializer.validated_data.get('search', '')
                pagenum = serializer.validated_data.get('pagenum', 1)

                tasks = []
                group_tasks = Task.objects.filter(group=self.get_group(),
                                                  purpose='benchmark',
                                                  time_type='timed',
                                                  name__contains=search)
                for t in group_tasks:
                    record = t.table_represent()
                    record['operations'] = ['analyse',
                                            'edit',
                                            'off' if t.status else 'on',
                                            'delete',
                                            'alert']
                    tasks.append(record)


                follow_tasks = FollowedTask.objects.filter(group=self.get_group(),
                                                           task__name__contains=search)

                for t in follow_tasks:
                    record = t.task.table_represent()
                    record['operations'] = ['analyse',
                                            'unfollowed',
                                            'alert']
                    tasks.append(record)
                feedback['data'] = {
                    'code': 200,
                    'message': u'Terminal list info',
                    'item_count': len(tasks),
                }

                if is_paginate:
                    per_page = self.get_per_page()
                    paginator = Paginator(tasks, per_page)

                    try:
                        current_page_query = paginator.page(pagenum)
                    except PageNotAnInteger:
                        current_page_query = paginator.page(1)
                    except EmptyPage:
                        current_page_query = paginator.page(paginator.num_pages)

                    tasks = list(current_page_query)
                    feedback['data']['page_num'] = current_page_query.number
                    feedback['data']['page_count'] = paginator.num_pages


                feedback['data']['info'] = tasks
            else:
                logger.info('Timed task search parameters is not available: {}'.format(
                    serializer.format_errors()))
                feedback['data'] = ErrorCode.parameter_invalid('timed_task_search',
                                                               reason=serializer.format_errors())

        except natrix_exception.NatrixBaseException as e:
            feedback['data'] = ErrorCode.sp_code_bug('Get time task list with bug: {}'.format(e.get_log()))
            logger.error(e.get_log())
        except Exception as e:
            natrix_exception.natrix_traceback()
            feedback['data'] = ErrorCode.sp_code_bug(e)

        return JsonResponse(data=feedback)


class UnfollowedTaskList(natrix_views.LoginAPIView):

    def get(self, request):
        feedback = {
            'permission': True
        }
        try:
            get_data = request.GET
            serializer = task_serializer.UnfollowedTaskSerializer(data=get_data,
                                                                  user=self.get_user(),
                                                                  group=self.get_group())

            if serializer.is_valid():
                task_list = serializer.query_result()
                feedback['data'] = {
                    'code': 200,
                    'message': 'Unfollowed task list!',
                    'info': task_list
                }
            else:
                logger.info('Unfollowed task search parameters is not available: {}'.format(
                    serializer.format_errors()))
                feedback['data'] = ErrorCode.parameter_invalid('timed_task_search',
                                                               reason=serializer.format_errors())

        except natrix_exception.ClassInsideException as e:
            feedback['data'] = ErrorCode.sp_code_bug('Query unfollowed tasks: {}'.format(e.get_log()))
            logger.error(e.get_log())
        except Exception as e:
            natrix_exception.natrix_traceback()
            feedback['data'] = ErrorCode.sp_code_bug(e)

        return JsonResponse(data=feedback)


class TimedTaskOperation(natrix_views.RoleBasedAPIView):

    natrix_roles = ['task_role', 'admin_role']

    def put(self, request, format=None):
        feedback = {
            'permission': True
        }

        if not self.has_permission(self.natrix_roles):
            feedback['data'] = ErrorCode.permission_deny('You dont have permission')
            return JsonResponse(data=feedback)

        try:
            put_data = request.data
            serializer = task_serializer.TimedTaskOperationSerializer(
                data=put_data, user=self.get_user(), group=self.get_group())

            if serializer.is_valid():
                serializer.process()
                feedback['data'] = {
                    'code': 200,
                    'message': 'Operate successfully!'
                }
            else:
                raise natrix_exception.ParameterInvalidException(parameter=serializer.format_errors())
        except natrix_exception.NatrixBaseException as e:
            feedback['data'] = ErrorCode.permission_deny('Operation Task: {}'.format(e.get_log()))
            logger.error(e.get_log())
        except Exception as e:
            natrix_exception.natrix_traceback()
            feedback['data'] = ErrorCode.sp_code_bug(e)

        return JsonResponse(data=feedback)


class TimedTaskSelect(natrix_views.LoginAPIView):

    def get(self, request):
        feedback = {
            'permission': True
        }
        try:
            request_data = request.GET
            serializer = task_serializer.TimedTaskSelectSerializer(data=request_data,
                                                                   user=self.get_user(),
                                                                   group=self.get_group())
            if serializer.is_valid():
                task_list = serializer.query_result()
                feedback['data'] = {
                    'code': 200,
                    'message': u'Timed task select list',
                    'info': task_list
                }
            else:
                logger.info('The parameters in query task select list interface is not available: {}'.format(
                    serializer.format_errors()
                ))
                feedback['data'] = ErrorCode.parameter_invalid('timed_task_select',
                                                               reason=serializer.format_errors())

        except natrix_exception.ClassInsideException as e:
            logger.error(e.get_log())
            feedback['data'] = ErrorCode.sp_code_bug('Query timed tasks select: {}'.format(e.get_log()))
        except Exception as e:
            natrix_exception.natrix_traceback()
            feedback['data'] = ErrorCode.sp_code_bug(e)

        return JsonResponse(data=feedback)


class TimedTaskAnalyse(natrix_views.LoginAPIView):
    """

    """

    def get(self, request):
        feedback = {
            'permission': True
        }
        try:
            request_data = request.GET
            serializer = analyse_serializer.TimedTaskAnalyseSerializer(data=request_data,
                                                                       user=self.get_user(),
                                                                       group=self.get_group())
            if serializer.is_valid():
                analyse_data = serializer.analyse()
                feedback['data'] = {
                    'code': 200,
                    'message': u'Timed task analyse data!',
                    'info': analyse_data
                }
            else:
                logger.info('Timed task analyse with error: {}'.format(serializer.format_errors()))
                feedback['data'] = ErrorCode.parameter_invalid('timed task analyse',
                                                               serializer.format_errors())

        except natrix_exception.ClassInsideException as e:
            logger.error(e.get_log())
            feedback['data'] = ErrorCode.sp_code_bug('Timed task analyse: {}'.format(e.get_log()))
        except Exception as e:
            natrix_exception.natrix_traceback()
            feedback['data'] = ErrorCode.sp_code_bug(e)

        return JsonResponse(data=feedback)



