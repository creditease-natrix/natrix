# -*- coding: utf-8 -*-
import uuid

from auditlog.registry import auditlog
from django.db import models, transaction
from django.contrib.auth.models import Group
from django.contrib.auth.models import User
from django.contrib.auth.models import Permission

# Create your models here.

class Role(models.Model):
    name = models.CharField(max_length=100,
                            unique=True,
                            verbose_name=u"角色名")
    desc = models.CharField(max_length=100,
                            unique=True,
                            verbose_name=u"角色描述")
    permissions = models.ManyToManyField(Permission)

    def __unicode__(self):
        return self.name


class Assign(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    role = models.ForeignKey(Role, on_delete=models.CASCADE)
    group = models.ForeignKey(Group, on_delete=models.CASCADE)

    def __unicode__(self):
        return '{}_with_{}_in_{}'.format(self.user,
                                         self.role,
                                         self.group)

    class Meta:
        unique_together = ("user", "role", "group")


class UserRBAC(object):
    user = None
    group = None

    def __init__(self, user):
        if not isinstance(user, User):
            raise TypeError
        self.user = user
        if hasattr(user, 'userinfo') and user.userinfo and user.userinfo.last_login_group:
            self.group = user.userinfo.last_login_group

    def groups(self):
        assigns = Assign.objects.filter(user=self.user).all()

        group_dict = dict()
        for a in assigns:
            if a.group not in group_dict:
                group_dict[a.group] = list()
                group_dict[a.group].append(a.role)
            else:
                group_dict[a.group].append(a.role)

        return [(k, v) for k, v in group_dict.items()]

    def assign(self, role, group):
        if not isinstance(role, Role):
            raise TypeError

        if not isinstance(group, Group):
            raise TypeError

        assign = Assign()
        assign.user = self.user
        assign.role = role
        assign.group = group
        assign.save()

        return True

    def get_groups(self):
        assigns = Assign.objects.filter(user=self.user).all().order_by('group')
        return set([a.group for a in assigns])

    def get_roles(self, group=None):
        # current roles
        if group is None:
            if self.group is None:
                return []
            group = self.group

        if not isinstance(group, Group):
            raise TypeError

        groups = self.groups()
        for g, rs in groups:
            if group.pk == g.pk:
                return rs

        return []

    def has_role(self, role, group=None):
        roles = self.get_roles(group)

        if isinstance(role, str):
            # special role, just in the group
            if role == 'in':
                return len(roles) == 0

            role = Role.objects.filter(name=role).first()
            if role is None:
                return False

        if not isinstance(role, Role):
            raise TypeError

        return role.pk in [r.pk for r in roles]

    def has_roles(self, role_list, group=None):

        roles = self.get_roles(group)
        if isinstance(role_list, list):
            for r in role_list:
                role = Role.objects.filter(name=r).first()
                if role is None:
                    return False
                if not isinstance(role, Role):
                    raise TypeError
                if role.pk in [r.pk for r in roles]:
                    return True

        return False

    def is_admin(self):
        """判断用户是否为组管理员"""
        return self.has_role(str("admin_role"))

    def is_supergroup(self):
        """判断在管理组中"""
        if self.group and self.group.name=='admin_group':
            return True
        return False

    def is_task(self):
        """判断用户是否为任务管理员管理员"""
        return self.has_role(str("task_role"))

    def change_group(self, group):
        if not isinstance(group, Group):
            raise TypeError

        self.group = group

    def get_group(self):
        return self.group

    def get_colleague(self):
        """获取所在组所有成员"""
        group = self.get_group()
        if group is None:
            return []
        user_ids = Assign.objects.filter(group=group).values('user_id')
        users = User.objects.filter(id__in=user_ids).order_by('username')
        return users


class GroupRole(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    role = models.ForeignKey(Role, on_delete=models.CASCADE)

    def __unicode__(self):
        return '{}_with_{}'.format(self.group, self.role)

    class Meta:
        unique_together = ("group", "role")


class UserInfo(models.Model):
    uuid = models.UUIDField(verbose_name=u'User ID(outside)',
                            primary_key=True,
                            default=uuid.uuid4,
                            editable=False)
    user = models.OneToOneField(User,
                                verbose_name=u'关联用户',
                                on_delete=models.CASCADE)
    phone = models.CharField(verbose_name=u'电话',
                             max_length=32,
                             null=True)
    per_page = models.IntegerField(verbose_name=u'页大小',
                                   default=10)

    last_login_group = models.ForeignKey(Group,
                                         verbose_name=u'上次登录组',
                                         null=True,
                                         on_delete=models.CASCADE)


class GroupInfo(models.Model):
    group = models.OneToOneField(Group,
                                 verbose_name='关联组',
                                 on_delete=models.CASCADE)

    desc = models.TextField(verbose_name='描述', null=True)



# auditlog.register(Role)
# auditlog.register(Assign)
