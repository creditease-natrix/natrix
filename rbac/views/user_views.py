# -*- coding: utf-8 -*-
"""

"""
import logging, json

from django.http.response import JsonResponse
from django.contrib.auth.models import User, Group
from django.contrib.auth import authenticate, login, logout
from django.views.decorators.csrf import csrf_exempt

from natrix.common.natrix_views import views as natrix_views
from natrix.common.natrix_views import permissions as natrix_permissions
from natrix.common import exception as natrix_exception
from natrix.common.errorcode import ErrorCode

from rbac.models import UserInfo
from rbac.serializers import UserRegisterSerializer
from rbac import change_rbac_group, api
from rbac.menu import get_menu


logger = logging.getLogger(__name__)


class UserAPI(natrix_views.NatrixAPIView):
    permission_classes = (natrix_permissions.LoginPermission,)
    authentication_classes = []

    def get(self, request):
        feedback = {
            'permission': True
        }
        try:
            request_data = request.GET
            username = request_data.get('username', None)
            curr_user = self.get_user()
            if username is None:
                user = curr_user
            else:
                user = User.objects.get(username=username)
            userinfo = {
                'username': user.username,
                'email': user.email,
                'phone': None,
                'per_page': None,
                'groups': [],
                'roles': []
            }
            if user.username == curr_user.username:
                rbac_user = request.user_rbac
                if hasattr(user, 'userinfo'):
                    userinfo['phone'] = user.userinfo.phone
                    userinfo['per_page'] = user.userinfo.per_page

                groups = rbac_user.get_groups()
                userinfo['groups'] = [g.name for g in groups]
                userinfo['roles'] = [r.name for r in rbac_user.get_roles()]
            feedback['data'] = {
                'code': 200,
                'message': 'User information',
                'info': userinfo
            }
        except User.DoesNotExist as e:
            natrix_exception.natrix_traceback()
            feedback['data'] = ErrorCode.sp_code_bug(e)
        except User.MultipleObjectsReturned as e:
            natrix_exception.natrix_traceback()
            feedback['data'] = ErrorCode.sp_code_bug(e)
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
            email = request_data.get('email', None)
            phone = request_data.get('phone', None)
            per_page = request_data.get('per_page', None)

            user = self.get_user()
            if email is not None:
                user.email = email
                user.save()

            if hasattr(user, 'userinfo'):
                userinfo = user.userinfo
            else:
                userinfo = UserInfo.objects.create(user=user)

            if phone is not None:
                userinfo.phone = phone

            if per_page is not None:
                userinfo.per_page = per_page

            userinfo.save()
            feedback['data'] = {
                'code': 200,
                'message': 'User information change succeffully!'
            }
            return JsonResponse(data=feedback)

        except Exception as e:
            natrix_exception.natrix_traceback()
            feedback['data'] = ErrorCode.sp_code_bug(e)

        return JsonResponse(data=feedback)


@natrix_views.natrix_api_view(http_method_names=['POST'])
def login_authentication(request):
    """RBAC login API

    :param request:
    :return:
    """
    feedback = {
        'permission': True
    }

    data = request.data

    username = data.get('username', None)
    password = data.get('password', None)

    try:
        if username is None:
            feedback['data'] = ErrorCode.parameter_missing(parameter='username')
            raise natrix_exception.ParameterMissingException(parameter='username')
        if password is None:
            feedback['data'] = ErrorCode.parameter_missing(parameter='password')
            raise natrix_exception.ParameterMissingException(parameter='password')

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

    except natrix_exception.NatrixBaseException as e:
        logger.info(e.get_log())

    return JsonResponse(data=feedback)


@natrix_views.natrix_api_view(http_method_names=['GET'])
def logout_api(request):
    """RBAC logout API

        :param request:
        :return:
    """
    feedback = {
        'permission': True
    }

    # TODO: add judgement
    result = logout(request)
    feedback['data'] = {
        'code': 200,
        'message': u'Logout successfully！'
    }

    return JsonResponse(data=feedback)


@natrix_views.natrix_api_view(http_method_names=['POST'])
def user_register(request):
    """RBAC register API

    :param request:
    :return:
    """
    feedback = {
        'permission': True
    }
    data = request.data
    try:
        serializer = UserRegisterSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            feedback['data'] = {
                'code': 200,
                'message': 'Registry successfully!'
            }
        else:
            feedback['data'] = ErrorCode.parameter_invalid('authentication parametters',
                                                           reason=serializer.format_errors())
            raise natrix_exception.ParameterInvalidException(parameter=serializer.format_errors())

    except natrix_exception.ClassInsideException as e:
        logger.info(e.get_log())
    except natrix_exception.NatrixBaseException as e:
        logger.info(e.get_log())

    return JsonResponse(data=feedback)


def userinfo_api(request):
    feedback = {
        'permission': True
    }
    if hasattr(request, 'user_rbac'):
        user_rbac = request.user_rbac
        if user_rbac:
            groups = map(lambda x: x[0], user_rbac.groups())

            feedback['data'] = {
                'code': 200,
                'user': user_rbac.user.username,
                'curr_group': user_rbac.get_group().name if user_rbac.get_group() else None,
                'groups': list(map(lambda g: {'id': g.id, 'name': g.name}, groups))
            }
        else:
            feedback['data'] = {
                'code': 400,
                'message': 'You do not login!'
            }

    return JsonResponse(data=feedback)


@csrf_exempt
def change_group_api(request):
    data = json.loads(request.body if request.body else '{}')

    group_id = data.get('id', None)
    try:
        if group_id is None:
            logger.error(u'dashboard切换组逻辑，未传递组信息！')
            raise natrix_exception.ParameterMissingException('group_id')
        group_id = int(group_id)

        group = Group.objects.get(id=group_id)

        change_rbac_group(request, group)
        api.update_last_login(request.user, group)

        return userinfo_api(request)
    except natrix_exception.NatrixBaseException as e:
        return userinfo_api(request)
    except Group.DoesNotExist:
        logger.error(u'要切换的组不存在！')
        return userinfo_api(request)
    except Exception as e:
        natrix_exception.natrix_traceback()
        return userinfo_api(request)


@natrix_views.natrix_api_view(http_method_names=['GET'])
def user_colleagues_api(request):
    feedback = {
        'permission': True
    }
    if hasattr(request, 'user'):
        colleagues = request.user_rbac.get_colleague()

        feedback['data'] = {
            'code': 200,
            'message': u'同组用户信息列表',
            'colleagures': list(map(
                    lambda c: {'id': c.id,
                               'name': c.username,
                               'email': c.email if c.email else '',
                               'phone': '' if not hasattr(c, 'userinfo') or c.userinfo.phone is None or c.userinfo.phone=='None' else c.userinfo.phone
                               },
                    colleagues))
        }

    else:
        feedback['data'] = {
            'code': 400,
            'message': 'You do not login'
        }

    return JsonResponse(data=feedback)


@natrix_views.natrix_api_view(http_method_names=['GET'])
def layout_menu_api(request):
    menu = get_menu(request)
    return JsonResponse(data={
        'menuinfo': menu
    })
