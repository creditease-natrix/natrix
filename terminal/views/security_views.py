# -*- coding: utf-8 -*-
"""

"""

from django.http.response import JsonResponse, HttpResponse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from natrix.common.natrix_views import views as natrix_views
from natrix.common import exception as natrix_exception
from natrix.common.natrixlog import NatrixLogging
from natrix.common.errorcode import ErrorCode

from terminal.serializers.security_serializer import LicenseQuerySerializer
from terminal.models.security_models import AccessLicense, GroupLicenseACL
from terminal.models.terminal_models import TerminalDevice


logger = NatrixLogging(__name__)


class LicenseListAPI(natrix_views.LoginAPIView):

    def get(self, request):
        feedback = {
            'permission': True
        }
        try:
            request_data = request.GET

            serializer = LicenseQuerySerializer(group=self.get_group(), data=request_data)

            if not serializer.is_valid():
                feedback['data'] = ErrorCode.parameter_invalid('License list',
                                                               reason=serializer.format_errors())

                return JsonResponse(data=feedback)

            is_paginate = serializer.validated_data.get('is_paginate')
            pagenum = serializer.validated_data.get('pagenum', 1)
            licenses_list = serializer.query_result()
            feedback['data'] = {
                'code': 200,
                'message': u'Terminal device list!',
                'item_count': len(licenses_list),
                'info': []
            }
            if is_paginate:
                per_page = self.get_per_page()
                paginator = Paginator(licenses_list, per_page)
                try:
                    current_page_query = paginator.page(pagenum)
                except PageNotAnInteger:
                    current_page_query = paginator.page(1)
                except EmptyPage:
                    current_page_query = paginator.page(paginator.num_pages)

                licenses_list = current_page_query
                feedback['data']['page_num'] = current_page_query.number
                feedback['data']['page_count'] = paginator.num_pages


            for record in licenses_list:
                feedback['data']['info'].append({
                    'key': record.license_key,
                    'status': record.get_status(),
                    'device_id': record.get_device_id(),
                    'bind_time': record.get_bind_time()
                })

        except natrix_exception.NatrixBaseException as e:
            natrix_exception.natrix_traceback()
            feedback['data'] = ErrorCode.sp_code_bug(e.get_log())
        except Exception as e:
            natrix_exception.natrix_traceback()
            feedback['data'] = ErrorCode.sp_code_bug(e)

        return JsonResponse(data=feedback)


class LicenseApplyAPI(natrix_views.RoleBasedAPIView):
    natrix_roles = ['admin_role']

    def get(self, request):
        feedback = {
            'permission': True
        }
        if not self.has_permission(self.natrix_roles):
            feedback['data'] = ErrorCode.permission_deny('You dont have permission')
            return JsonResponse(data=feedback)

        try:
            count = request.GET.get('count')

            try:
                count = int(count)
                remaining_count = GroupLicenseACL.get_remaining_number(self.get_group())

                if count > remaining_count:
                    feedback['data'] = ErrorCode.parameter_invalid(
                            'count', reason='You only have {} licenses to apply!'.format(remaining_count))
                    raise natrix_exception.ParameterInvalidException(parameter='count')

                license_count = AccessLicense.license_generator(self.get_group(), count=count)
                feedback['data'] = {
                    'code': 200,
                    'message': 'Create {} licenses!'.format(license_count)
                }
            except ValueError:
                feedback['data'] = ErrorCode.parameter_invalid('count', reason='Count must be a integer')

        except natrix_exception.NatrixBaseException as e:
            logger.info(e.get_log())
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
            license_key = request.GET.get('license_key')
            if license_key is None:
                feedback['data'] = ErrorCode.parameter_missing('license_key')
                raise natrix_exception.ParameterMissingException(parameter='license_key')

            res, message = AccessLicense.license_remove(license_key, self.get_group())
            if res:
                feedback['data'] = {
                    'code': 200,
                    'message': 'License delete successfully!'
                }
            else:
                feedback['data'] = ErrorCode.parameter_invalid('license_key', reason=message)

        except natrix_exception.NatrixBaseException as e:
            logger.info(e.get_log())
        except Exception as e:
            natrix_exception.natrix_traceback()
            feedback['data'] = ErrorCode.sp_code_bug(e)

        return JsonResponse(data=feedback)


@natrix_views.natrix_api_view(http_method_names=['GET'])
def mq_user_auth(request):
    """RabbitMQ user authentication

    Used by RabbitMQ management UI and device access.

    :param request:
    :return:
    """

    data = request.GET
    client_id = data.get('client_id')
    username = data.get('username')
    password = data.get('password')
    logger.info(f'<{username}> auth <{client_id}> connection')
    if username == 'mqtt-test':
        return HttpResponse('allow')

    if client_id:
        res = AccessLicense.to_bind_device(client_id, username)

        if res:
            return HttpResponse('allow')
        else:
            return HttpResponse('deny')

    return HttpResponse("allow management")


# rabbitmq vhost auth
@natrix_views.natrix_api_view(http_method_names=['GET'])
def mq_vhost_auth(request):

    data = request.GET

    return HttpResponse('allow')


# rabbitmq resource auth
@natrix_views.natrix_api_view(http_method_names=['GET'])
def mq_resource_auth(request):

    data = request.GET

    return HttpResponse('allow')


@natrix_views.natrix_api_view(http_method_names=['GET'])
def mq_topic_auth(request):

    data = request.GET

    routing_key = data.get('routing_key')
    client_id = data.get('variable_map.client_id')
    username = data.get('username')

    if username == 'mqtt-test':
        return HttpResponse('allow')

    if routing_key.startswith('natrix.basic'):
        try:
            TerminalDevice.objects.get(sn = username)
            AccessLicense.objects.get(license_key = client_id)
        except TerminalDevice.DoesNotExist:
            return HttpResponse('deny')
        except AccessLicense.DoesNotExist:
            return HttpResponse('deny')

    return HttpResponse('allow')