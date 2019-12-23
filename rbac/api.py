# -*- coding: utf-8 -*-
import logging

from django.db import transaction
from django.contrib.auth.models import Group, User
from django.conf import settings

from rbac.models import Role, Assign, GroupRole, UserInfo


logger = logging.getLogger(__name__)


def init_userinfo(user):
    try:
        UserInfo.objects.get(user=user)
    except UserInfo.DoesNotExist:
        UserInfo.objects.create(user=user)


def create_group(group_name):
    """
    :param username:
    :return:
    """
    # TODO: If a new user create group and the group name is exist will build the relation.
    # So, the next step of rbac will add group managment policy.
    if group_name:
        group, exist = Group.objects.get_or_create(name=group_name)
        return group
    else:
        return None


def init_rbac(user, group):
    """Initialize The RBAC relationship

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

        GroupRole.objects.get_or_create(group=group, role=admin_role)
        GroupRole.objects.get_or_create(group=group, role=task_role)
        GroupRole.objects.get_or_create(group=group, role=alert_role)
        GroupRole.objects.get_or_create(group=group, role=read_role)

        Assign.objects.get_or_create(user=user, group=group, role=admin_role)
        Assign.objects.get_or_create(user=user, group=group, role=task_role)
        Assign.objects.get_or_create(user=user, group=group, role=alert_role)
        Assign.objects.get_or_create(user=user, group=group, role=read_role)

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


def get_group_member(group):
    """Get all members in the group.

    :param group:
    :return:
    """

    members = set()

    assigns = Assign.objects.filter(group=group)

    for record in assigns:
        members.add(record.user)

    return list(members)


def get_group_administrator(group):
    """Get all administrators in the group.

    :param group:
    :return:
    """
    administritors = set()

    assigns = Assign.objects.filter(group=group, role__name='admin_role')

    for record in assigns:
        administritors.add(record.user)

    return list(administritors)


def init_admin_configuration():
    """Init django superuser

    :return:
    """
    admin_username = settings.ADMIN_USERNAME
    admin_password = settings.ADMIN_PASSWORD
    admin_email = settings.ADMIN_EMAIL
    admin_group = settings.ADMIN_GROUP

    try:
        with transaction.atomic():
            try:
                User.objects.get(username=admin_username)
                logger.info('Admin user is initialized!')
            except User.DoesNotExist:
                user= User.objects.create_superuser(username=admin_username,
                                                    password=admin_password,
                                                    email=admin_email)
                init_userinfo(user)
                group = create_group(admin_group)

                init_rbac(user, group)
    except Exception as e:
        logger.error(f'Initialize administrator with error: {e}')




