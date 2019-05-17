# -*- coding: utf-8 -*-
""" RBAC-related interface

Natrix permission control depends RBAC application.

NOTE:
    If user isn't login, request.user is a instance of AnonymousUser in django.contrib.auth,
    and rbac.middleware set request.user_rbac as None.

"""
from __future__ import unicode_literals




def get_per_page(request):
    """
    :param user: User instance
    :return:
    """
    if hasattr(request, 'user_rbac'):
        user_rbac = request.user_rbac
        if user_rbac is not None:
            user = user_rbac.user
            if hasattr(user, 'userinfo'):
                return user.userinfo.per_page if user.userinfo else 10

    return 10


class UserAPI(object):

    @staticmethod
    def is_login(request):
        """ 连接是否登录

        :param request:
        :return:
        """
        if hasattr(request, 'user_rbac'):
            if request.user_rbac is not None:
                return True
        return False


    @staticmethod
    def get_per_page(request):
        """ 获取用户设置的页信息

        :param request:
        :return:
        """
        if hasattr(request, 'user_rbac'):
            user_rbac = request.user_rbac
            if user_rbac is not None:
                user = user_rbac.user
                if hasattr(user, 'userinfo'):
                    return user.userinfo.per_page if user.userinfo else 10

        return 10