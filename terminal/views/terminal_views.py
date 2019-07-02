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

from natrix.common.natrix_views.views import NatrixAPIView, NonAuthenticatedAPIView
from natrix.common import exception as natrix_exception
from natrix.common.mqservice import MQService
from natrix.common.errorcode import ErrorCode

from terminal.views.organization_views import OrganizationPermission
from terminal.models import TerminalDevice, Terminal
from terminal.serializers import alive_serializer, terminal_serializer
logger = logging.getLogger(__name__)


class TerminalAPI(NatrixAPIView):
    """监测点相关接口

    """
    permission_classes = (OrganizationPermission,)
    authentication_classes = []

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

        except natrix_exception.BaseException as e:
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


class TerminalOverviewAPI(NonAuthenticatedAPIView):
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

            serializer = terminal_serializer.OverviewQuerySerializer(data=get_data)
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

        except natrix_exception.BaseException as e:
            logger.info(e.get_log())


        return JsonResponse(data=feedback)


class DeviceListAPI(NonAuthenticatedAPIView):
    """Device List API

    Offer post method.

    """

    def post(self, request, format=None):
        feedback = {
            'permission': True
        }
        try:
            post_data = request.data
            serializer = terminal_serializer.DeviceListQuerySerializer(data=post_data)
            if serializer.is_valid():
                terminal_devices = serializer.query_result()
                is_paginate = post_data.get('is_paginate', False)
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
                    feedback['data'] = {
                        'code': 200,
                        'message': u'终端设备列表信息',
                        'page_num': current_page_query.number,
                        'page_count': paginator.num_pages,
                        'info': []
                    }
                else:
                    feedback['data'] = {
                        'code': 200,
                        'message': u'全部终端设备信息',
                        'info': []
                    }

                for td in terminal_devices:
                    device_serializer = terminal_serializer.DeviceBaiscSerializer(instance=td)
                    feedback['data']['info'].append(device_serializer.data)
            else:
                feedback['data'] = ErrorCode.parameter_invalid(
                    'device_search', reason=serializer.format_errors()
                )
                raise natrix_exception.ParameterInvalidException(parameter='device_search')
        except natrix_exception.BaseException as e:
            logger.info(e.get_log())

        return JsonResponse(data=feedback)


class DeviceOperationAPI(NonAuthenticatedAPIView):
    """ Device Status API


    """

    def put(self, request, format=None):
        feedback = {
            'permission': True
        }
        try:
            post_data = request.data
            serializer = terminal_serializer.DeviceOperationSerializer(data=post_data)
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

        except natrix_exception.BaseException as e:
            logger.info(e.get_log())

        return JsonResponse(data=feedback)


class DeviceBasicAPI(NonAuthenticatedAPIView):
    """

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
            except natrix_exception.BaseException as e:
                feedback['data'] = ErrorCode.sp_db_fault(aspect=u'Serializer error: {}'.format(e.get_log()))
                raise natrix_exception.ClassInsideException(message=u'Serializer error: {}'.format(e.get_log()))

        except natrix_exception.BaseException as e:
            logger.info(e.get_log())

        return JsonResponse(data=feedback)

    def put(self, request, format=None):
        feedback = {
            'permission': True
        }
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

        except natrix_exception.BaseException as e:
            logger.info(e.get_log())

        return JsonResponse(data=feedback)


class DeviceOSAPI(NonAuthenticatedAPIView):

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
            except natrix_exception.BaseException as e:
                feedback['data'] = ErrorCode.sp_db_fault(aspect=u'Terminal OS serializer error')
                raise natrix_exception.ClassInsideException(message=u'Terminal OS serializer error')

        except natrix_exception.BaseException as e:
            logger.info(e.get_log())

        return JsonResponse(data=feedback)


class DeviceHardwareAPI(NonAuthenticatedAPIView):
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
            except natrix_exception.BaseException as e:
                feedback['data'] = ErrorCode.sp_db_fault(aspect=u'Terminal Hardware serializer error')
                raise natrix_exception.ClassInsideException(message=u'Terminal Hardware serializer error')

        except natrix_exception.BaseException as e:
            logger.info(e.get_log())

        return JsonResponse(data=feedback)


class DeviceExceptionsAPI(NonAuthenticatedAPIView):

    def get(self, request):
        feedback = {
            'permission': True
        }
        try:
            get_data = request.GET
            serializer = terminal_serializer.DeviceExceptionListQuerySerializer(data=get_data)
            if serializer.is_valid():
                terminal_devices = serializer.query_result()
                is_paginate = get_data.get('is_paginate', False)
                if is_paginate:
                    per_page = self.get_per_page()
                    pagenum = get_data.get('pagenum', 1)

                    paginator = Paginator(terminal_devices, per_page)
                    try:
                        current_page_query = paginator.page(pagenum)
                    except PageNotAnInteger:
                        current_page_query = paginator.page(1)
                    except EmptyPage:
                        current_page_query = paginator.page(paginator.num_pages)
                    terminal_devices = current_page_query
                    feedback['data'] = {
                        'code': 200,
                        'message': u'异常终端设备列表信息',
                        'page_num': current_page_query.number,
                        'page_count': paginator.num_pages,
                        'info': []
                    }
                else:
                    feedback['data'] = {
                        'code': 200,
                        'message': u'全部异常终端设备信息',
                        'info': []
                    }
                for dev in terminal_devices:
                    feedback['data']['info'].append(
                        {
                            'sn': dev.sn,
                            'status': dev.status,
                            'reg_orgs': map(lambda item: {'id': item.id,
                                                          'name': item.name,
                                                          'desc': item.get_full_name()},
                                            dev.register.organizations.all() if dev.register else []),

                            'detect_orgs': map(lambda item: {'id': item.id,
                                                             'name': item.name,
                                                             'desc': item.get_full_name()},
                                               dev.organizations.all()),
                            'terminals': map(lambda  item: {'name': item.name,
                                                            'local_ip': item.localip,
                                                            'status': item.status,
                                                            'is_active': item.is_active},
                                             dev.terminal_set.all())
                        }
                    )

            else:
                feedback['data'] = ErrorCode.parameter_invalid(
                    'device_exception_search', reason=serializer.format_errors()
                )
                raise natrix_exception.ParameterInvalidException(parameter='device_exception_search')

        except natrix_exception.BaseException as e:
            logger.info(e.get_log())

        return JsonResponse(data=feedback)


class TerminalListAPI(NonAuthenticatedAPIView):
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
                    feedback['data'] = {
                        'code': 200,
                        'message': u'Terminal list info',
                        'page_num': current_page_query.number,
                        'page_count': paginator.num_pages,
                    }
                else:
                    feedback['data'] = {
                        'code': 200,
                        'message': u'Terminal list info',
                    }

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
        except natrix_exception.BaseException as e:
            logger.info(e.get_log())

        return JsonResponse(data=feedback)


class TerminalOperationAPI(NonAuthenticatedAPIView):
    """Terminal Operation API

    """
    def put(self, request, format=None):
        feedback = {
            'permission': True
        }
        try:
            put_data = request.data
            serializer = terminal_serializer.TerminalOperationSerializer(data=put_data)
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
        except natrix_exception.BaseException as e:
            logger.info(e.get_log())

        return JsonResponse(data=feedback)


class TerminalPostAPI(NonAuthenticatedAPIView):

    def get(self, request):
        feedback = {
            'permission': True
        }
        try:
            get_data = request.GET
            serializer = terminal_serializer.TerminalPostSerializer(data=get_data)
            if serializer.is_valid():
                per_page = self.get_per_page()
                data = serializer.query_result(per_page=per_page)
                feedback['data'] = {
                    'code': 200,
                    'message': u'Terminal post info list',
                }
                feedback['data'].update(data)
            else:
                feedback['data'] = ErrorCode.parameter_invalid(
                    'terminal_post_search', reason=serializer.format_errors()
                )
                raise natrix_exception.ParameterInvalidException(parameter='terminal_post_search')


        except natrix_exception.BaseException as e:
            logger.info(e.get_log())

        return JsonResponse(data=feedback)

    def post(self):
        pass



