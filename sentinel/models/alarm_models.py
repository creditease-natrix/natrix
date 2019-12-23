# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import logging, time

from django.utils import timezone
from django.db import models
from django.contrib.auth.models import User, Group

from benchmark.models import Task

from sentinel.configurations import alarm_conf, notify_conf

logger = logging.getLogger(__name__)

choice_filter = lambda x: (x.get('name'), x.get('verbose_name'))
time2stamp = lambda x: (time.mktime(x.timetuple()) - time.timezone) * 1000

MONITOR_CHOICE = list(map(choice_filter, alarm_conf.MONITOR_TYPE.values()))
OPERATION_CHOICE = list(map(choice_filter, alarm_conf.OPERATION_INFO.values()))
AGGREGATION_CHOICE = list(map(choice_filter, alarm_conf.AGGREGATION_INFO.values()))
NOTIFICATION_CHOICE = list(map(choice_filter, notify_conf.NOTIFICATION_TYPE.values()))


class Alarm(models.Model):
    name = models.CharField(verbose_name=u'告警名称', max_length=64, null=False)
    description = models.TextField(verbose_name=u'告警描述', default=u'')
    task = models.ForeignKey(Task, verbose_name=u'关联定时测任务', on_delete=models.CASCADE)

    monitor_type = models.CharField(verbose_name=u'监控指标项', max_length=64,
                                    choices=MONITOR_CHOICE)
    operation = models.CharField(verbose_name=u'判断操作', max_length=16,
                                 choices=OPERATION_CHOICE, null=True)
    threshold = models.FloatField(verbose_name=u'阈值', null=True)
    aggregation_type = models.CharField(verbose_name=u'聚合类型', max_length=64,
                                        choices=AGGREGATION_CHOICE, null=True)
    agg_condition =models.FloatField(verbose_name=u'聚合条件', null=True)

    status = models.BooleanField(verbose_name=u'开关', default=True)

    deepmonitor_uuid = models.UUIDField(verbose_name='Deepmonitor ID')

    owner = models.ForeignKey(User, verbose_name=u'创建用户', null=True, on_delete=models.CASCADE)
    group = models.ForeignKey(Group, verbose_name=u'关联组', null=True, on_delete=models.CASCADE)

    create_time = models.DateTimeField(verbose_name=u'创建时间', default=timezone.now,
                                       editable=False)
    update_time = models.DateTimeField(verbose_name=u'更新时间', default=timezone.now)

    def alarm_status(self):

        if self.status:
            return 'on'
        else:
            return 'off'

    def represent(self):
        return {
            'id': self.pk,
            'name': self.name,
            'description': self.description,
            'task_id': self.task.id,
            'task_name': self.task.name,
            'protocol': self.task.protocol_type,
            'task_description': self.task.description,
            'monitor_type': self.monitor_type,
            'operation': self.operation,
            'threshold': self.threshold,
            'aggregation_type': self.aggregation_type,
            'aggregation_condition': self.agg_condition,
            'status': self.status,
            'alarm_status': self.alarm_status(),
            'create_time': time2stamp(self.create_time)
        }

    def __unicode__(self):
        return '{}-{}'.format(self.name, self.group)

    class Meta:
        ordering = ['-create_time']


class Notification(models.Model):

    alarm = models.ForeignKey(Alarm, verbose_name=u'关联告警', on_delete=models.CASCADE)
    description = models.TextField(verbose_name=u'通知描述', default=u'')
    users = models.ManyToManyField(User, verbose_name=u'通知用户')
    notify_type = models.CharField(verbose_name=u'通知类型', max_length=16,
                                   choices=NOTIFICATION_CHOICE)
    is_recovery = models.BooleanField(verbose_name=u'恢复通知开关', default=True)
    frequency = models.IntegerField(verbose_name=u'通知频率（秒）')

    status = models.BooleanField(verbose_name=u'通知开关', default=True)

    start_time = models.TimeField(verbose_name=u'开始工作时间')
    end_time = models.TimeField(verbose_name=u'结束工作时间')

    deepmonitor_uuid = models.UUIDField(verbose_name='Deepmonitor ID', null=True)
    deepmonitor_operation = models.UUIDField(verbose_name='Deepmonitor Notify Operation ID', null=True)

    owner = models.ForeignKey(User, verbose_name=u'创建用户', null=True,
                              related_name='alarm_owner', on_delete=models.CASCADE)
    group = models.ForeignKey(Group, verbose_name=u'关联组', null=True, on_delete=models.CASCADE)

    create_time = models.DateTimeField(verbose_name=u'创建时间', default=timezone.now,
                                       editable=False)
    update_time = models.DateTimeField(verbose_name=u'更新时间', default=timezone.now)

    def users_represent(self):
        return [ {'user_id': u.id, 'user_name': u.username} for u in self.users.all()]

    def represent(self):
        return {
            'id': self.pk,
            'description': self.description,
            'status': self.status,
            'users': self.users_represent(),
            'notify_type': self.notify_type,
            'is_recovery': self.is_recovery,
            'frequency': self.frequency,
            'start_time': self.start_time.strftime('%H:%M'),
            'end_time': self.end_time.strftime('%H:%M'),
            'create_time': time2stamp(self.create_time)
        }


    def __unicode__(self):
        return '{}-{}'.format(self.notify_type, self.group)


