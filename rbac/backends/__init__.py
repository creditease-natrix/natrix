# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import logging

from django.contrib.auth.models import User, Group

from natrix.common import exception as natrix_exceptions
from rbac.models import Role, GroupRole, UserInfo, Assign

logger = logging.getLogger(__name__)

def init_rbac_user(user, group):
    if isinstance(user, User) and isinstance(group, Group):
        admin_role, created = Role.objects.get_or_create(name="admin_role", desc="组管理角色")
        task_role, created = Role.objects.get_or_create(name="task_role", desc="任务管理角色")
        alert_role, created = Role.objects.get_or_create(name="alert_role", desc="告警管理角色")
        read_role, created = Role.objects.get_or_create(name="read_role", desc="只读角色")

        GroupRole.objects.create(group=group, role=admin_role)
        GroupRole.objects.create(group=group, role=task_role)
        GroupRole.objects.create(group=group, role=alert_role)
        GroupRole.objects.create(group=group, role=read_role)

        Assign.objects.create(user=user, group=group, role=admin_role)
        Assign.objects.create(user=user, group=group, role=task_role)
        Assign.objects.create(user=user, group=group, role=alert_role)
        Assign.objects.create(user=user, group=group, role=read_role)

        user.email = user.username
        user.save()

        UserInfo.objects.create(user=user)
        return True
    else:
        return False


def user_registry(username, password):
    """Registry a new user

    :param username: an email address
    :param password:
    :return:
    """

    try:
        user = User.objects.create_user(username=username,
                                   email=username,
                                   password=password)

        try:
            Group.objects.get(name=username)
            raise natrix_exceptions.ClassInsideException('The group({}) is exist'.format(username))

        except Group.DoesNotExist:
            group = Group.objects.create(name=username)

        rest = init_rbac_user(user, group)

        if not rest:
            raise natrix_exceptions.ClassInsideException('Init RBAC with exception')

        return user

    except Exception as e:
        logger.error('There is an exception: {}'.format(e))
        raise natrix_exceptions.ClassInsideException(
            message='New user creatation with exception: {}'.format(e))





