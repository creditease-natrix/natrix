# -*- coding: utf-8 -*-
"""In this module, we define some common views for natrix development.

"""
from __future__ import unicode_literals
import sys
import logging
import types
import traceback

from django.utils import six
from django.http.response import JsonResponse
from django.contrib.auth.models import AnonymousUser
from rest_framework import exceptions as rest_exceptions
from rest_framework.views import APIView

from natrix.common.errorcode import ErrorCode

from .authentication import NonAuthentication
from .permissions import LoginPermission

logger = logging.getLogger(__name__)


def natrix_exception_handler(exc, context):
    """Natrix exception_handler

    natrix exception handler used by NatrixAPIView. copy rest_framework.views.exception_handler

    :param exc:
    :param context:
    :return:
    """
    logger.info('Exception Happened: {}'.format(exc))

    if isinstance(exc, rest_exceptions.MethodNotAllowed):
        data = {
            'permission': True,
            'data': ErrorCode.permission_deny(
                message=u'HTTP方法访问权限问题：{}'.format(exc.detail))
        }
    else:
        data = {
            'permission': False
        }

    # Output the exception traceback
    ex, val, tb = sys.exc_info()
    traceback.print_exception(ex, val, tb)

    return JsonResponse(data=data)


class NatrixAPIView(APIView):
    """Natrix APIView (Basic Class)

    Rewrite APIView exception_handler. In REST-framework, it returned 404-response when an
    exception is throwed. We rewrite get_exception_handler method, it will return permission-deny
    (permission=False) for any exceptions.

    """

    def get_exception_handler(self):
        return natrix_exception_handler

    def get_per_page(self):
        """get

        :param request:
        :return:
        """

        user = self.get_user()
        if user is None or isinstance(user, AnonymousUser):
            return 10

        if hasattr(user, 'userinfo'):
            return user.userinfo.per_page if user.userinfo else 10
        else:
            return 10

    def get_user(self):
        """get request user

        :return:
        """
        request = self.request
        if not hasattr(request, 'user_rbac'):
            return AnonymousUser()
        user_rbac = request.user_rbac
        if user_rbac is None:
            return AnonymousUser()

        return user_rbac.user

    def get_group(self):
        """获取用户当前组"""
        user_rbac = self.request.user_rbac
        group = user_rbac.get_group() if user_rbac else None
        return group


class NonAuthenticatedAPIView(NatrixAPIView):
    """The view that doesn't need authentication.

    """
    authentication_classes = (NonAuthentication, )


class LoginAPIView(NatrixAPIView):
    """

    """
    authentication_classes = (NonAuthentication, )
    permission_classes = (LoginPermission, )

# copy django.decortors.api_view
def natrix_api_view(http_method_names=None, exclude_from_schema=False):
    """
    Decorator that converts a function-based view into an APIView subclass.
    Takes a list of allowed methods for the view as an argument.
    """
    http_method_names = ['GET'] if (http_method_names is None) else http_method_names

    def decorator(func):

        WrappedAPIView = type(
            six.PY3 and 'WrappedAPIView' or b'WrappedAPIView',
            (NatrixAPIView,),
            {'__doc__': func.__doc__}
        )

        # Note, the above allows us to set the docstring.
        # It is the equivalent of:
        #
        #     class WrappedAPIView(APIView):
        #         pass
        #     WrappedAPIView.__doc__ = func.doc    <--- Not possible to do this

        # api_view applied without (method_names)
        assert not(isinstance(http_method_names, types.FunctionType)), \
            '@api_view missing list of allowed HTTP methods'

        # api_view applied with eg. string instead of list of strings
        assert isinstance(http_method_names, (list, tuple)), \
            '@api_view expected a list of strings, received %s' % type(http_method_names).__name__

        allowed_methods = set(http_method_names) | set(('options',))
        WrappedAPIView.http_method_names = [method.lower() for method in allowed_methods]

        def handler(self, *args, **kwargs):
            return func(*args, **kwargs)

        for method in http_method_names:
            setattr(WrappedAPIView, method.lower(), handler)

        WrappedAPIView.__name__ = func.__name__
        WrappedAPIView.__module__ = func.__module__

        WrappedAPIView.renderer_classes = getattr(func, 'renderer_classes',
                                                  APIView.renderer_classes)

        WrappedAPIView.parser_classes = getattr(func, 'parser_classes',
                                                APIView.parser_classes)

        WrappedAPIView.authentication_classes = getattr(func, 'authentication_classes',
                                                        APIView.authentication_classes)

        WrappedAPIView.throttle_classes = getattr(func, 'throttle_classes',
                                                  APIView.throttle_classes)

        WrappedAPIView.permission_classes = getattr(func, 'permission_classes',
                                                    APIView.permission_classes)

        WrappedAPIView.exclude_from_schema = exclude_from_schema
        return WrappedAPIView.as_view()
    return decorator

