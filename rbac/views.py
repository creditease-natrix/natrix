# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging
import json

from django.contrib.auth import authenticate, login, logout
from django.views.generic import View
from django.http import JsonResponse
from django.contrib.auth.models import User, Group
from django.views.decorators.csrf import csrf_exempt


from natrix.common.errorcode import ErrorCode
from natrix.common import exception as natrix_exceptions
from natrix.common.natrix_views.views import NatrixAPIView

from rbac.serializers import UserRegisterSerializer
from rbac import api
from .menu import get_menu

import rbac

logger = logging.getLogger(__name__)

# Create your views here.

@csrf_exempt
def front_login(request):
    """
    RBAC login API

    :param request:
    :return:
    """
    feedback = {
        'permission': True
    }
    if not (request.method == 'POST'):
        feedback['data'] = ErrorCode.permission_deny('{}(method) is not offerd'.format(request.method))
        return JsonResponse(data=feedback)

    data = json.loads(request.body if request.body else '{}')

    username = data.get('username', None)
    password = data.get('password', None)

    try:
        if username is None:
            feedback['data'] = ErrorCode.parameter_missing(parameter='username')
            raise natrix_exceptions.ParameterMissingException(parameter='username')
        if password is None:
            feedback['data'] = ErrorCode.parameter_missing(parameter='password')
            raise natrix_exceptions.ParameterMissingException(parameter='password')

        user = authenticate(username=username, password=password)

        if user is not None:
            login(request, user)
            feedback['data'] = {'message': u'Login successfully!',
                                'sessionid': request.session.session_key,
                                'username': username,
                                'code': 200
                                }
        else:
            feedback['data'] = ErrorCode.unauthenticated()

    except natrix_exceptions.BaseException as e:
        logger.info(e.get_log())

    return JsonResponse(data=feedback)


@csrf_exempt
def front_logout(request):
    """
    RBAC logout API

    :param request:
    :return:
    """
    feedback = {
        'permission': True
    }
    if not (request.method == 'GET'):
        feedback['data'] = ErrorCode.permission_deny('{}(method) is not offerd'.format(request.method))
        return JsonResponse(data=feedback)

    result = logout(request)
    feedback['data'] = {
        'code': 200,
        'message': u'Logout successfully！'
    }

    return JsonResponse(data=feedback)


@csrf_exempt
def front_register(request):
    """
    RBAC register API

    :param request:
    :return:
    """
    feedback = {
        'permission': True
    }
    if not (request.method == 'POST'):
        feedback['data'] = ErrorCode.permission_deny('{}(method) is not offerd'.format(request.method))
        return JsonResponse(data=feedback)

    data = json.loads(request.body if request.body else '{}')

    try:
        serializer = UserRegisterSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            feedback['data'] = {
                'code': 200,
                'message': 'Registry successfully!'
            }
        else:
            feedback['data']= ErrorCode.parameter_invalid('authentication parametters',
                                                          reason=serializer.format_errors())
            raise natrix_exceptions.ParameterInvalidException(parameter=serializer.format_errors())

    except natrix_exceptions.ClassInsideException as e:
        logger.info(e.get_log())
    except natrix_exceptions.BaseException as e:
        logger.info(e.get_log())

    return JsonResponse(data=feedback)



def get_userinfo(request):
    feedback = {
        'permission': True
    }
    userinfo = {}
    if hasattr(request, 'user_rbac'):
        user_rbac = request.user_rbac
        if user_rbac:
            groups = map(lambda x: x[0], user_rbac.groups())

            feedback['data'] = {
                'code': 200,
                'user': user_rbac.user.username,
                'curr_group': user_rbac.get_group().name if user_rbac.get_group() else None,
                'groups': map(lambda g: {'id': g.id, 'name': g.name}, groups)
            }
        else:
            feedback['data'] = {
                'code': 400,
                'message': u'用户未登录'
            }

    return JsonResponse(data=feedback)


def get_colleagues(request):
    feedback = {
        'permission': True
    }
    if hasattr(request, 'user'):
        colleagues = request.user_rbac.get_colleague()
        feedback['data'] = {
            'code': 200,
            'message': u'同组用户信息列表',
            'colleagures': map(lambda c: {'id': c.id,
                                          'name': c.username,
                                          'email': c.email if c.email else '',
                                          'phone': '' if c.userinfo.phone is None or c.userinfo.phone=='None' else c.userinfo.phone
                                          },
                               colleagues)
        }

    else:
        feedback['data'] = {
            'code': 400,
            'message': u'用户未登录'
        }

    return JsonResponse(data=feedback)


@csrf_exempt
def change_group(request):
    # data = request.POST
    data = json.loads(request.body if request.body else '{}')


    group_id = data.get('id', None)
    try:
        if group_id is None:
            logger.error(u'dashboard切换组逻辑，未传递组信息！')
            raise RequestParamError
        group = Group.objects.get(id=group_id)

        rbac.change_rbac_group(request, group)
        api.update_last_login(request.user, group)


        return get_userinfo(request)
    except RequestParamError:
        return get_userinfo(request)
    except Group.DoesNotExist:
        logger.error(u'要切换的组不存在！')
        return get_userinfo(request)


def layout_menu(request):
    menu = get_menu(request)
    return JsonResponse(data={
        'menuinfo': menu
    })




class ExistDataException(Exception):
    pass

# 请求参数错误
class RequestParamError(Exception):
    pass




