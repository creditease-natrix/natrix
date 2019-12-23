# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin

from .models.alarm_models import Alarm, Notification
# Register your models here.

@admin.register(Alarm)
class AlarmAdmin(admin.ModelAdmin):
    list_display = ('pk', 'name', 'monitor_type', 'task', 'status', 'group')
    list_filter = ('monitor_type', 'group')


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('pk', 'description', 'notify_type', 'group')
    list_filter = ('notify_type', 'group')