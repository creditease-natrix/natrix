# -*- coding: utf-8 -*-
import logging

from django.contrib.auth.models import Group, User

from rbac.models import Role, Assign, GroupRole, UserInfo

logger = logging.getLogger(__name__)

def create_group(group_name):
    """
    根据用户名创建对应的用户组
    :param username:
    :return:
    """
    if group_name:
        groups = Group.objects.filter(name=group_name)
        if len(groups) > 0:
            return None
        group = Group.objects.create(name=group_name)
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
        read_role, created = Role.objects.get_or_create(name="read_role", desc="只读角色")

        GroupRole.objects.create(group=group, role=admin_role)
        GroupRole.objects.create(group=group, role=task_role)
        GroupRole.objects.create(group=group, role=read_role)

        Assign.objects.create(user=user, group=group, role=admin_role)
        Assign.objects.create(user=user, group=group, role=task_role)
        Assign.objects.create(user=user, group=group, role=read_role)
        return True
    else:
        return False


def update_last_login(user, group):
    if isinstance(user, User) and isinstance(group, Group):
        if not hasattr(user, 'userinfo'):
            userinfo = UserInfo.objects.create(user=user,
                                               last_login_group=group)
        else:
            userinfo = user.userinfo
            userinfo.last_login_group = group
            userinfo.save()
    else:
        logger.error(u'保存登录信息失败！')

