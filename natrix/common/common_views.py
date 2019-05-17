# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import logging
import types

from django.utils import six
from django.views.generic import View, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http.response import JsonResponse

from rest_framework.views import APIView

logger = logging.getLogger(__name__)


class BaseView(View):
    """
    The basic view for all views in eagle project.
    This view is a django view, and doesn't define anything.
    """
    pass


class BaseTemplateView(TemplateView, BaseView):
    """
    This view is a django template-view.
    If your view will display something in brower, you must inherit this view.
    """

    def get_context_data(self, *args, **kwargs):
        context = super(BaseTemplateView,
                        self).get_context_data(*args, **kwargs)
        return context


class BaseRBACView(LoginRequiredMixin, BaseTemplateView):
    """
    In this view, we add permission control about RBAC.
    This view inherit LoginRequireMixin, so it requires login-user.
    """
    permission_role = []

    def get_context_data(self, *args, **kwargs):
        context = super(BaseRBACView,
                        self).get_context_data(*args, **kwargs)
        context['per_page'] = self.get_per_page()
        return context

    def has_permission(self):
        if self.is_permit(self.permission_role):
            return True
        else:
            return False

    def is_permit(self, role=[]):
        """根据role判断权限，如果role为[]表示允许"""
        request = self.request
        if request:
            user_rbac = request.user_rbac
            if not user_rbac:
                logger.error("User doesn't associate with RBAC")
                return False
            if not isinstance(role, list):
                return False

            if len(role) == 0:
                return True

            if user_rbac.has_roles(role):
                return True
            else:
                return False
        else:
            logger.error("There isn't request in Rbac-view")
            return False

    def get_user(self):
        """获取当前用户"""
        user_rbac = self.request.user_rbac
        if user_rbac:
            return user_rbac.user
        else:
            return None

    def get_groups(self):
        """获取该用户所有的组列表"""
        user_rbac = self.request.user_rbac
        groups = user_rbac.groups() if user_rbac else []
        return map(lambda x: x[0], groups)

    def get_group(self):
        """获取用户当前组"""
        user_rbac = self.request.user_rbac
        group = user_rbac.get_group() if user_rbac else None
        return group

    def get_colleague(self):
        """获取同事列表"""
        user_rbac = self.request.user_rbac
        users = user_rbac.get_colleague() if user_rbac else []
        return users

    def get_per_page(self):
        """获取表格行数配置信息"""
        user_rbac = self.request.user_rbac
        if user_rbac:
            base_module = __import__('rbac.models', globals(), locals(), 'UserInfo' )
            module = getattr(base_module, 'UserInfo')
            if not hasattr(user_rbac.user, 'userinfo'):
                module.objects.create(user=user_rbac.user)

            userinfo = user_rbac.user.userinfo
            if userinfo:
                return userinfo.per_page
        return 10


# natrix exception handler used by NatrixAPIView. copy rest_framework.views.exception_handler
def natrix_exception_handler(exc, context):
    """

    :param exc:
    :param context:
    :return:
    """
    logger.info('Exception Happened: {}'.format(exc))
    return JsonResponse(data={
        'permission': False
    })


class NatrixAPIView(APIView):
    """Natrix APIView

    Rewrite APIView exception_handler. In REST-framework, it returned 404-response when an
    exception is throwed. We rewrite get_exception_handler method, it will return permission-deny
    (permission=False) for any exceptions.

    """

    def get_exception_handler(self):
        return natrix_exception_handler



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



if __name__ == '__main__':
    import doctest
    doctest.testmod()