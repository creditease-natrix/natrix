# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin

from .models import Command, Task, FollowedTask, Schedule

# Register your models here.

@admin.register(Command)
class CommandAdmin(admin.ModelAdmin):
    list_display = ('pk', 'protocol_type', 'destination', 'protocol_parameters', 'create_time')
    list_filter = ('protocol_type', )


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('pk', 'status', 'scope', 'time_type', 'command', 'create_time')
    list_filter = ('scope', 'time_type', 'purpose', 'protocol_type')


@admin.register(FollowedTask)
class FollowedTaskAdmin(admin.ModelAdmin):
    list_display = ('pk', 'task', 'user', 'group')
    list_filter = ('user', 'group')


@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin):
    list_display = ('pk', 'frequency', 'status', 'effective_time', 'expiry_time')
    list_filter = ('status',)
