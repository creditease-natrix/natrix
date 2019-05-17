# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import logging
import uuid

from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User, Group
import benchmark.configurations.task_conf as CONF

logger = logging.getLogger(__name__)

choice_filter = lambda x: (x.get('name'), x.get('verbose_name'))


PROTOCOL_CHOICES = map(choice_filter, CONF.PROTOCOL_INFO.values())


class Command(models.Model):

    id = models.UUIDField(verbose_name=u'COMMAND ID',
                          primary_key=True,
                          default=uuid.uuid4,
                          editable=False)
    type = models.CharField(verbose_name=u'类型', max_length=16,
                            choices=(('instant', u'即时测'), ('timing', u'定时测')))

    method = models.CharField(verbose_name=u'协议方法', max_length=64, null=True)

    protocol_type = models.CharField(verbose_name=u'协议类型', choices=PROTOCOL_CHOICES,
                                     max_length=16, editable=False, null=False)
    protocol_conf = models.TextField(verbose_name=u'协议配置(JSON)', editable=False, default='{}')

    destination = models.CharField(verbose_name=u'目的URI', max_length=255,
                                   editable=False, null=False)

    create_time = models.DateTimeField(verbose_name=u'创建时间', default=timezone.now, editable=False)

    def __unicode__(self):
        return u'({})-{}'.format(self.id, self.destination)



class Schedule(models.Model):

    create_time = models.DateTimeField(verbose_name=u'创建时间', default=timezone.now, editable=False)


SCOPE_CHOICES = map(choice_filter, CONF.TASK_SCOPE.values())
TIME_CHOICES = map(choice_filter, CONF.TASK_TIME_TYPE.values())
PURPOSE_CHOICES = map(choice_filter, CONF.TASK_PURPOSE.values())

class Task(models.Model):

    id = models.UUIDField(verbose_name=u'任务ID',
                          primary_key=True,
                          default=uuid.uuid4,
                          editable=False)
    name = models.CharField(verbose_name=u'任务名称', max_length=64, null=False)
    description = models.TextField(verbose_name=u'任务描述',default=u'')

    status = models.BooleanField(verbose_name=u'任务状态', default=True,
                                 max_length=16, null=False)
    scope = models.CharField(verbose_name=u'任务范围', choices=SCOPE_CHOICES,
                             default='private', max_length=16)
    time_type = models.CharField(verbose_name=u'任务类型', choices=TIME_CHOICES,
                                 max_length=16)
    purpose = models.CharField(verbose_name=u'用途', choices=PURPOSE_CHOICES,
                               default=u'benchmark', max_length=16)

    terminal_condition = models.TextField(verbose_name=u'过滤条件', default=u'{}')

    # TODO: 考虑是否要增加
    terminal_count = models.IntegerField(verbose_name=u'终端数量', default=0)
    terminals = models.TextField(verbose_name=u'终端列表', default=u'[]')

    command = models.ForeignKey(Command, verbose_name=u'相关指令', on_delete=models.CASCADE)
    schedule = models.ForeignKey(Schedule, verbose_name=u'调度配置',
                                 on_delete=models.CASCADE, null=True)
    effective_time = models.DateTimeField(verbose_name=u'生效时间', null=True)
    expiry_time = models.DateTimeField(verbose_name=u'失效时间', null=True)

    result_snapshot = models.TextField(verbose_name=u'结果快照', null=True, blank=True)

    owner = models.ForeignKey(User, verbose_name=u'创建用户', null=True, related_name='owner')
    group = models.ForeignKey(Group, verbose_name=u'关联组', null=True, related_name='group')
    access_ip = models.GenericIPAddressField(verbose_name=u'访问IP', null=True)
    create_time = models.DateTimeField(verbose_name=u'创建时间', default=timezone.now,
                                       editable=False)
    update_time = models.DateTimeField(verbose_name=u'更新时间', default=timezone.now)


    def __unicode__(self):
        return '({})-{}'.format(self.id, self.time_type)

    class Meta:
        ordering = ['-create_time', '-update_time']



class FollowedTask(models.Model):
    task = models.ForeignKey(Task, verbose_name=u'关联任务', null=False)
    user = models.ForeignKey(User, verbose_name=u'创建用户', null=False)
    group = models.ForeignKey(Group, verbose_name=u'关联组', null=False)

    def __unicode__(self):
        return '{}-{}'.format(self.task, self.group)







