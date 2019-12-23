# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin

# Register your models here.

from rbac.models import Assign
from rbac.models import Role
from rbac.models import GroupRole
from rbac.models import UserInfo

# Register your models here.
class BaseAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'pk')


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('pk', 'name', 'desc')


@admin.register(GroupRole)
class GroupRoleAdmin(admin.ModelAdmin):
    list_display = ('pk', 'group', 'role')


@admin.register(Assign)
class AssignAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'group')


@admin.register(UserInfo)
class UserInfoAdmin(admin.ModelAdmin):
    list_display = ('pk', 'user', 'per_page', 'last_login_group')