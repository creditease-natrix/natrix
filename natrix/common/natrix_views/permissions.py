# -*- coding: utf-8 -*-
"""

"""
from __future__ import unicode_literals
import logging

from django.contrib.auth.models import Group, AnonymousUser
from rest_framework import permissions

logger = logging.getLogger(__name__)


class AdminPermission(permissions.IsAuthenticated):
    """Administrator Permission

    Only admin_group users have permission. In Natrix, admin_group is default system admin group.

    """

    def has_permission(self, request, view):
        if hasattr(request, 'user_rbac'):
            user_rbac = request.user_rbac
            if user_rbac is None:
                return False
            group = user_rbac.get_group()
            if group is None or not isinstance(group, Group):
                return False
            if group.name == 'admin_group':
                return True
            else:
                return False
        else:
            return False


class LoginPermission(permissions.IsAuthenticated):
    """Login Permission.

    The request must with a login user. In Natrix, login user means that the request with user_rbac
    attribute and the user_rbac has a group.

    """

    def has_permission(self, request, view):
        if hasattr(request, 'user_rbac'):
            user_rbac = request.user_rbac
            if user_rbac is None or isinstance(user_rbac, AnonymousUser):
                return False

            group = user_rbac.get_group()
            if group is None or not isinstance(group, Group):
                logger.error('Login user ({}) without group!'.format(user_rbac.user))
                return False
            else:
                return True
        else:
            return False


class NonPermission(permissions.IsAuthenticated):
    """

    """

    def has_permission(self, request, view):
        return True