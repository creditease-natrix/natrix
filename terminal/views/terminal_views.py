# -*- coding: utf-8 -*-
"""

"""

from __future__ import unicode_literals
import logging
import json

from django.http.response import JsonResponse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from rest_framework import status as http_status
from rest_framework.response import Response

from natrix.common.natrix_views.views import NatrixAPIView, NonAuthenticatedAPIView, LoginAPIView, RoleBasedAPIView
from natrix.common import exception as natrix_exception
from natrix.common.mqservice import MQService
from natrix.common.errorcode import ErrorCode

from terminal.models import TerminalDevice, Terminal
from terminal.serializers import alive_serializer, terminal_serializer
logger = logging.getLogger(__name__)


class TerminalAPI(LoginAPIView):
    """监测点相关接口

    """

    def get(self, request):
        feedback = {
            'permission': True
        }
        try:
            terminal_id = request.GET.get("id")

            if terminal_id is None:
                feedback['data'] = ErrorCode.parameter_missing('id')
                raise natrix_exception.ParameterMissingException(parameter='id')

            try:
                terminal = Terminal.objects.get(id=terminal_id)
            except TerminalDevice.DoesNotExist:
                feedback['data'] = ErrorCode.parameter_invalid(parameter='id',
                                                               reason=u'数据库中不存在响应数据')
                raise natrix_exception.ParameterInvalidException(parameter='id')

            terminal_info = {
                "mac": terminal.mac,
                "type": terminal.type,
                "localip": terminal.localip,
                "publicip": terminal.publicip,
                "netmask": terminal.netmask,
                "gateway": terminal.gateway,
                "status": terminal.status,
            }
            feedback["data"] = {
                "code": 200,
                "message": u"监测点详情查询成功!",
                "info": terminal_info
            }

        except natrix_exception.NatrixBaseException as e:
            logger.info(e.get_log())

        return JsonResponse(data=feedback)


class DeviceBasicPostAPI(NonAuthenticatedAPIView):
    """ Basic Info Post View

    Receive the basic info which is posted by terminal device.

    """

    def post(self, request, format=None):
        try:
            post_data = request.data

            serializer = alive_serializer.BasicInfoSerializer(data=post_data)
            if serializer.is_valid():
                networks = serializer.validated_data.get('networks')
                format_networks = {}
                for item in networks:
                    format_networks[item.get('name')] = item
                serializer.validated_data['networks'] = format_networks
                MQService.publish_message('natrix_keep_alive_basic',
                                          data=json.dumps(serializer.validated_data))
                return Response(status=http_status.HTTP_200_OK,
                                data={'message': u'Data is received!'})

            else:
                return Response(status=http_status.HTTP_400_BAD_REQUEST,
                                data={'errors': serializer.errors})
        except Exception as e:
            logger.error(u'Device Basic POST ERROR: {}'.format(e))
            return Response(status=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
                            data={'error': str(e)})


class DeviceAdvancePostAPI(NonAuthenticatedAPIView):
    """ Advance Info Post View

    Receive the advance info which is posted by terminal device.

    """

    def post(self, request, format=None):
        try:
            post_data = request.data
            serializer = alive_serializer.AdvanceInfoSerializer(data=post_data)
            if serializer.is_valid():
                networks = serializer.validated_data.get('networks')
                format_networks = {}
                for item in networks:
                    format_networks[item.get('name')] = item
                serializer.validated_data['networks'] = format_networks
                MQService.publish_message('natrix_keep_alive_advance',
                                          data=json.dumps(serializer.validated_data))
                return Response(status=http_status.HTTP_200_OK,
                                data={'message': u'Data is received!'})

            else:
                return Response(status=http_status.HTTP_400_BAD_REQUEST,
                                data={'errors': serializer.errors})
        except Exception as e:
            logger.error(u'Device Advance POST ERROR: {}'.format(e))
            return Response(status=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
                            data={'error': str(e)})


class TerminalOverviewAPI(LoginAPIView):
    """

    """

    def get(self, request):
        feedback = {
            'permission': True
        }
        try:
            get_data = {
                'type': request.GET.get('type'),
                'filter': request.GET.getlist('filter'),
                'show_level': request.GET.get('show_level')
            }

            serializer = terminal_serializer.OverviewQuerySerializer(data=get_data,
                                                                     group=self.get_group())
            if serializer.is_valid():
                rest_data = serializer.query_result()
                feedback['data'] = {
                    'code': 200,
                    'message': u'终端设备分布',
                    'info': rest_data
                }
            else:
                feedback['data'] = ErrorCode.parameter_invalid(
                    parameter='Overview get parameter', reason=serializer.format_errors()
                )
                raise natrix_exception.ParameterInvalidException(parameter=serializer.format_errors())

        except natrix_exception.NatrixBaseException as e:
            logger.info(e.get_log())


        return JsonResponse(data=feedback)


class DeviceListAPI(LoginAPIView):
    """Device List API

    Offer post method.

    """

    def post(self, request, format=None):
        feedback = {
            'permission': True
        }
        try:
            post_data = request.data
            serializer = terminal_serializer.DeviceListQuerySerializer(data=post_data,
                                                                       group=self.get_group())
            if serializer.is_valid():
                terminal_devices = serializer.query_result()
                is_paginate = post_data.get('is_paginate', False)
                feedback['data'] = {
                    'code': 200,
                    'message': u'Terminal device list!',
                    'item_count': len(terminal_devices),
                    'info': []
                }

                if is_paginate:
                    per_page = self.get_per_page()
                    pagenum = post_data.get('pagenum', 1)

                    paginator = Paginator(terminal_devices, per_page)
                    try:
                        current_page_query = paginator.page(pagenum)
                    except PageNotAnInteger:
                        current_page_query = paginator.page(1)
                    except EmptyPage:
                        current_page_query = paginator.page(paginator.num_pages)
                    terminal_devices = current_page_query
                    feedback['data']['page_num'] = current_page_query.number
                    feedback['data']['page_count'] = paginator.num_pages

                for td in terminal_devices:
                    device_serializer = terminal_serializer.DeviceBaiscSerializer(instance=td)
                    feedback['data']['info'].append(device_serializer.data)
            else:
                feedback['data'] = ErrorCode.parameter_invalid(
                    'device_search', reason=serializer.format_errors()
                )
                raise natrix_exception.ParameterInvalidException(parameter='device_search')
        except natrix_exception.NatrixBaseException as e:
            logger.info(e.get_log())

        return JsonResponse(data=feedback)


class DeviceOperationAPI(RoleBasedAPIView):
    """ Device Status API


    """
    natrix_roles = ['admin_role']

    def put(self, request, format=None):
        feedback = {
            'permission': True
        }

        if not self.has_permission(self.natrix_roles):
            feedback['data'] = ErrorCode.permission_deny('You dont have permission')
            return JsonResponse(data=feedback)

        try:
            post_data = request.data
            serializer = terminal_serializer.DeviceOperationSerializer(data=post_data,
                                                                       group=self.get_group())
            if serializer.is_valid():
                serializer.action()

                feedback['data'] = {
                    'code': 200,
                    'message': u'终端设备状态修改成功'
                }
            else:
                feedback['data'] = ErrorCode.parameter_invalid(
                    'terminal_device', reason=serializer.format_errors())
                raise natrix_exception.ParameterInvalidException(parameter='terminal_device')

        except natrix_exception.NatrixBaseException as e:
            logger.info(e.get_log())

        return JsonResponse(data=feedback)


class DeviceBasicAPI(RoleBasedAPIView):
    """

    """

    natrix_roles = ['admin_role']

    def get(self, request):
        feedback = {
            'permission': True
        }
        try:
            sn = request.GET.get('sn')
            if sn is None:
                feedback['data'] = ErrorCode.parameter_missing('sn')
                raise natrix_exception.ParameterMissingException(parameter='sn')
            try:
                device = TerminalDevice.objects.get(sn=sn)
            except TerminalDevice.DoesNotExist:
                feedback['data'] = ErrorCode.parameter_invalid(
                    parameter='sn', reason=u'The record is not exist')
                raise natrix_exception.ParameterInvalidException(parameter='sn')

            try:
                serializer = terminal_serializer.DeviceBaiscSerializer(instance=device)
                feedback['data'] = {
                    'code': 200,
                    'message': u'终端设备系统信息',
                    'info': serializer.data
                }
                return JsonResponse(data=feedback)
            except natrix_exception.NatrixBaseException as e:
                feedback['data'] = ErrorCode.sp_db_fault(aspect=u'Serializer error: {}'.format(e.get_log()))
                raise natrix_exception.ClassInsideException(message=u'Serializer error: {}'.format(e.get_log()))

        except natrix_exception.NatrixBaseException as e:
            logger.info(e.get_log())

        return JsonResponse(data=feedback)

    def put(self, request, format=None):
        feedback = {
            'permission': True
        }

        if not self.has_permission(self.natrix_roles):
            feedback['data'] = ErrorCode.permission_deny('You dont have permission')
            return JsonResponse(data=feedback)

        try:
            post_data = request.data
            serializer = terminal_serializer.DeviceBaiscSerializer(data=post_data)
            if serializer.is_valid():
                serializer.save()
                feedback['data'] = {
                    'code': 200,
                    'message': u'终端设备信息修改成功'
                }
            else:
                feedback['data'] = ErrorCode.parameter_invalid(
                    'terminal_device', reason=serializer.format_errors())
                raise natrix_exception.ParameterInvalidException(parameter='terminal_device')

        except natrix_exception.NatrixBaseException as e:
            logger.info(e.get_log())

        return JsonResponse(data=feedback)


class DeviceOSAPI(LoginAPIView):

    def get(self, request):
        feedback = {
            'permission': True
        }
        try:
            sn = request.GET.get('sn')
            if sn is None:
                feedback['data'] = ErrorCode.parameter_missing('sn')
                raise natrix_exception.ParameterMissingException(parameter='sn')
            try:
                device = TerminalDevice.objects.get(sn=sn)
                logger.debug('device info {}'.format(device))
            except TerminalDevice.DoesNotExist:
                feedback['data'] = ErrorCode.parameter_invalid(
                    parameter='sn', reason=u'The record is not exist')
                raise natrix_exception.ParameterInvalidException(parameter='sn')

            try:
                serializer = alive_serializer.AdvanceSystemSerializer(instance=device)
                feedback['data'] = {
                    'code': 200,
                    'message': u'终端设备系统信息',
                    'info': serializer.data
                }
                return JsonResponse(data=feedback)
            except natrix_exception.NatrixBaseException as e:
                feedback['data'] = ErrorCode.sp_db_fault(aspect=u'Terminal OS serializer error')
                raise natrix_exception.ClassInsideException(message=u'Terminal OS serializer error')

        except natrix_exception.NatrixBaseException as e:
            logger.info(e.get_log())

        return JsonResponse(data=feedback)


class DeviceHardwareAPI(LoginAPIView):
    """ Obtain Device hardware

    """

    def get(self, request):
        feedback = {
            'permission': True
        }
        try:
            sn = request.GET.get('sn')
            if sn is None:
                feedback['data'] = ErrorCode.parameter_missing('sn')
                raise natrix_exception.ParameterMissingException(parameter='sn')
            try:
                device = TerminalDevice.objects.get(sn=sn)
                logger.debug('device info {}'.format(device))
            except TerminalDevice.DoesNotExist:
                feedback['data'] = ErrorCode.parameter_invalid(
                    parameter='sn', reason=u'The record is not exist')
                raise natrix_exception.ParameterInvalidException(parameter='sn')

            try:
                serializer = alive_serializer.AdavnceHardwareSerializer(instance=device)
                feedback['data'] = {
                    'code': 200,
                    'message': u'终端设备硬件信息',
                    'info': serializer.data
                }
                return JsonResponse(data=feedback)
            except natrix_exception.NatrixBaseException as e:
                feedback['data'] = ErrorCode.sp_db_fault(aspect=u'Terminal Hardware serializer error')
                raise natrix_exception.ClassInsideException(message=u'Terminal Hardware serializer error')

        except natrix_exception.NatrixBaseException as e:
            logger.info(e.get_log())

        return JsonResponse(data=feedback)


class TerminalListAPI(LoginAPIView):
    """Obtain termina

    """

    def post(self, request):
        feedback = {
            'permission': True
        }
        try:
            post_data = request.data
            serializer = terminal_serializer.TerminalListQuerySerializer(data=post_data)
            if serializer.is_valid():
                terminals = serializer.query_result()

                is_paginate = serializer.data.get('is_paginate')

                feedback['data'] = {
                    'code': 200,
                    'message': u'Terminal list info',
                    'item_count': len(terminals)
                }

                if is_paginate:
                    pagenum = serializer.data.get('pagenum', 1)
                    per_page = self.get_per_page()
                    paginator = Paginator(terminals, per_page)

                    try:
                        current_page_query = paginator.page(pagenum)
                    except PageNotAnInteger:
                        current_page_query = paginator.page(1)
                    except EmptyPage:
                        current_page_query = paginator.page(paginator.num_pages)

                    terminals = current_page_query
                    feedback['data']['page_num'] = current_page_query.number
                    feedback['data']['page_count'] = paginator.num_pages

                terminal_list = []
                for record in terminals:
                    serializer = alive_serializer.InterfaceSerializer(instance=record)
                    terminal_list.append(serializer.data)

                feedback['data']['info'] = terminal_list

            else:
                feedback['data'] = ErrorCode.parameter_invalid(
                    'terminal_list', reason=serializer.format_errors()
                )
                raise natrix_exception.ParameterInvalidException(parameter='terminal_list')
        except natrix_exception.NatrixBaseException as e:
            logger.info(e.get_log())

        return JsonResponse(data=feedback)


class TerminalOperationAPI(RoleBasedAPIView):
    """Terminal Operation API

    """

    natrix_roles = ['admin_role']

    def put(self, request, format=None):
        feedback = {
            'permission': True
        }

        if not self.has_permission(self.natrix_roles):
            feedback['data'] = ErrorCode.permission_deny('You dont have permission')
            return JsonResponse(data=feedback)

        try:
            put_data = request.data
            serializer = terminal_serializer.TerminalOperationSerializer(data=put_data,
                                                                         group=self.get_group())
            if serializer.is_valid():
                serializer.action()
                feedback['data'] = {
                    'code': 200,
                    'message': u'终端监测点状态修改成功'
                }
            else:
                feedback['data'] = ErrorCode.parameter_invalid(
                    'terminal', reason=serializer.format_errors()
                )
                raise natrix_exception.ParameterInvalidException(parameter='terminal')
        except natrix_exception.NatrixBaseException as e:
            logger.info(e.get_log())

        return JsonResponse(data=feedback)


class TerminalPostAPI(LoginAPIView):
    """Get a terminal post records.

    To search at most 100 records of terminal posted, include basic and advanced terminal information

    """

    def get(self, request):
        feedback = {
            'permission': True
        }
        try:
            get_data = request.GET
            serializer = terminal_serializer.TerminalPostSerializer(data=get_data)
            if serializer.is_valid():
                per_page = self.get_per_page()
                try:
                    data = serializer.query_result(per_page=per_page)
                    feedback['data'] = {
                        'code': 200,
                        'message': u'Terminal post info list',
                    }
                    feedback['data'].update(data)
                except Exception as e:
                    natrix_exception.natrix_traceback()
                    feedback['data'] = ErrorCode.sp_code_bug('Query terminal reported information with error!')
                    logger.error(e)
            else:
                feedback['data'] = ErrorCode.parameter_invalid(
                    'terminal_post_search', reason=serializer.format_errors()
                )
                raise natrix_exception.ParameterInvalidException(parameter='terminal_post_search')

        except natrix_exception.NatrixBaseException as e:
            logger.info(e.get_log())

        return JsonResponse(data=feedback)

