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


@admin.register(Role, Assign, GroupRole, UserInfo)
class StandardAdmin(BaseAdmin):
    pass
