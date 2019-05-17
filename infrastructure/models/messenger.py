# -*- coding: utf-8 -*-
"""

"""
from __future__ import unicode_literals

from django.db import models
from django.utils import timezone

from infrastructure.configurations import messenger as configuration

# Create your models here.

choice_method = lambda x: (x.get('name'), x.get('verbose_name'))


# 通知方式
TYPE_CHOICE = map(choice_method, configuration.NOTIFY_TYPE.values())
LEVEL_CHOICE = map(choice_method, configuration.NOTIFY_LEVEL.values())

class NotifyRecord(models.Model):
    notify_type = models.CharField(verbose_name=u'通知方式', choices=TYPE_CHOICE, max_length=16)
    level = models.CharField(verbose_name=u'信息类型',
                             choices=LEVEL_CHOICE,
                             default='critical',
                             max_length=16)
    description = models.CharField(verbose_name=u'通知描述', max_length=64)
    application = models.CharField(verbose_name=u'应用名称', max_length=16)
    destinations = models.TextField(verbose_name=u'通知目标（JSON)')
    title = models.CharField(verbose_name=u'主题', max_length=64)
    content = models.TextField(verbose_name=u'通知内容(JSON)')

    generate_time = models.DateTimeField(verbose_name=u'产生时间（用于通知）', null=True)

    create_time = models.DateTimeField(verbose_name=u'创建时间', default=timezone.now)

    def __unicode__(self):
        return '{}-{}'.format(self.notify_type, self.destinations)



