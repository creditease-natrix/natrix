# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import logging

from django_auth_ldap.backend import LDAPBackend
from django.contrib.auth.models import Group, User

from rbac.models import Role, Assign, GroupRole, UserInfo


logger = logging.getLogger(__name__)


class NatrixBackend(LDAPBackend):

    def get_or_create_user(self, username, ldap_user):
        result = super(NatrixBackend, self).get_or_create_user(username, ldap_user)
        # 用户首次登录，result[1]为True,需要为用户创建对应用户名的group并赋予相应的权限
        if result[1]:
            group = create_group(username)
            if group:
                init_rbac(result[0], group)
            else:
                logger.info("Exist the group named (%s), so can't map a group." % username)
        return result


def create_group(username):
    """
    根据用户名创建对应的用户组
    :param username:
    :return:
    """
    if username:
        groups = Group.objects.filter(name=username)
        if len(groups) > 0:
            return None
        group = Group.objects.create(name=username)
        return group
    else:
        return None


def init_rbac(user, group):
    """
    初始化首次登录的用户
    :param user:
    :param group:
    :return:
    """
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

