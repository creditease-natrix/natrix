# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin

from infrastructure.models.messenger import NotifyRecord

# Register your models here.
@admin.register(NotifyRecord)
class NotifyRecordAdmin(admin.ModelAdmin):
    list_display = ('notify_type', 'title', 'application', 'description', 'create_time')
    list_filter = ('application', 'notify_type')