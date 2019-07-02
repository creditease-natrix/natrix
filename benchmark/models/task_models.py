# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import logging, time, json
import uuid

from django.db import models, transaction
from django.utils import timezone
from django.contrib.auth.models import User, Group

from natrix.common import exception as natrix_exception
import benchmark.configurations.task_conf as CONF
from benchmark.terminalutil import terminal_policy

logger = logging.getLogger(__name__)

choice_filter = lambda x: (x.get('name'), x.get('verbose_name'))

PROTOCOL_CHOICES = map(choice_filter, CONF.PROTOCOL_INFO.values())


class Command(models.Model):

    id = models.UUIDField(verbose_name=u'COMMAND ID',
                          primary_key=True,
                          default=uuid.uuid4,
                          editable=False)

    protocol_type = models.CharField(verbose_name=u'协议类型', choices=PROTOCOL_CHOICES,
                                     max_length=16, editable=False, null=False)
    protocol_parameters = models.TextField(verbose_name=u'协议配置(JSON)', editable=False, default='{}')

    destination = models.CharField(verbose_name=u'目的URI', max_length=255,
                                   editable=False, null=False)

    create_time = models.DateTimeField(verbose_name=u'创建时间', default=timezone.now, editable=False)

    @staticmethod
    def command_generator(protocol_type, protocol_parameters, destination, method=None):

        protocol_parameters_str = json.dumps(protocol_parameters)

        try:
            command = Command.objects.get(protocol_type=protocol_type,
                                          protocol_parameters=protocol_parameters_str,
                                          destination=destination)
        except Command.DoesNotExist:
            command = Command.objects.create(protocol_type=protocol_type,
                                             protocol_parameters=protocol_parameters_str,
                                             destination=destination)

        return command

    def terminal_command_representation(self):
        try:
            command_parameters = json.loads(self.protocol_parameters)

            command_info = {
                'command_uuid': str(self.id),
                'command_protocol': self.protocol_type,
                'command_destination': self.destination,
                'command_parameters': command_parameters
            }
            return command_info
        except Exception as e:
            natrix_exception.natrix_traceback()
            logger.error('Get command representation(terminal) with error: {}'.format(e))
            raise natrix_exception.ClassInsideException(message='Can not get available command info')

    class Meta:
        ordering = ['-create_time']

    def __unicode__(self):
        return u'({})-{}'.format(self.id, self.destination)


class Schedule(models.Model):
    """

    """

    status = models.BooleanField(verbose_name=u'是否开启', default=True)
    frequency = models.IntegerField(verbose_name=u'监控频率(s)')
    effective_time = models.DateTimeField(verbose_name=u'生效时间', null=True)
    expiry_time = models.DateTimeField(verbose_name=u'失效时间', null=True)

    def is_alive(self):
        if not self.status:
            return False

        if self.expiry_time > timezone.now():
            return True
        else:
            return False

    def __unicode__(self):
        return u'{}-{}'.format(self.status, self.frequency)


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

    destination = models.CharField(verbose_name=u'目的URI', max_length=255,
                                   editable=False, null=False)
    terminal_switch = models.BooleanField(verbose_name=u'终端配置开关', default=False)
    protocol_switch = models.BooleanField(verbose_name=u'协议配置开关', default=False)

    terminal_condition = models.TextField(verbose_name=u'终端过滤条件', default=u'{}')
    protocol_type = models.CharField(verbose_name=u'协议类型', choices=PROTOCOL_CHOICES,
                                     max_length=16, editable=False, null=False)
    method = models.CharField(verbose_name=u'协议方法', max_length=64, null=True)
    protocol_condition = models.TextField(verbose_name=u'协议配置', default=u'{}')

    terminal_count = models.IntegerField(verbose_name=u'终端数量', default=0)
    terminals = models.TextField(verbose_name=u'终端列表', default=u'[]')

    command = models.ForeignKey(Command, verbose_name=u'相关指令', on_delete=models.CASCADE)
    schedule = models.ForeignKey(Schedule, verbose_name=u'调度配置',
                                 on_delete=models.CASCADE, null=True)


    result_snapshot = models.TextField(verbose_name=u'结果快照', null=True, blank=True)

    owner = models.ForeignKey(User, verbose_name=u'创建用户', null=True, related_name='owner')
    group = models.ForeignKey(Group, verbose_name=u'关联组', null=True, related_name='group')
    access_ip = models.GenericIPAddressField(verbose_name=u'访问IP', null=True)
    create_time = models.DateTimeField(verbose_name=u'创建时间', default=timezone.now,
                                       editable=False)
    update_time = models.DateTimeField(verbose_name=u'更新时间', default=timezone.now)

    def turn_on(self):
        with transaction.atomic():
            self.status = True
            self.schedule.status = True
            self.schedule.save()
            self.save()

    def turn_off(self):
        with transaction.atomic():
            self.status = False
            self.schedule.status = False
            self.schedule.save()
            self.save()

    def status_represent(self):
        if self.status:
            if self.schedule.is_alive():
                return 'running'
            else:
                return 'expired'
        else:
            return 'stoped'

    def table_represent(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'scope': self.scope,
            'protocol_type': self.protocol_type,
            'destination': self.destination,
            'frequency': self.schedule.frequency / 60 if self.schedule else 0,
            'status': self.status_represent(),
            'create_time': (time.mktime(self.create_time.timetuple()) - time.timezone) * 1000,
            'effective_time': (time.mktime(self.schedule.effective_time.timetuple()) - time.timezone) * 1000
        }

    def get_terminals(self):
        try:
            condition = json.loads(self.terminal_condition)
            terminals = terminal_policy(self.terminal_switch, conditions=condition)

        except Exception as e:
            natrix_exception.natrix_traceback()
            logger.error('Get terminals info with errro: {}'.format(e))
            terminals = []

        return terminals

    def task_command_represent(self):
        command_data = {
            'command': self.command.terminal_command_representation(),
            'task_tag': {
                'task_id': str(self.id),
                'task_generate_time': time.time()
            },
            'terminals': self.get_terminals()
        }

        return command_data

    def __unicode__(self):
        return '({})-{}'.format(self.id, self.time_type)

    class Meta:
        ordering = ['-create_time', '-update_time']


class FollowedTask(models.Model):
    task = models.ForeignKey(Task, verbose_name=u'关联任务', null=False,
                             on_delete=models.CASCADE)
    user = models.ForeignKey(User, verbose_name=u'创建用户', null=False,
                             on_delete=models.CASCADE)
    group = models.ForeignKey(Group, verbose_name=u'关联组', null=False,
                              on_delete=models.CASCADE)

    def __unicode__(self):
        return '{}-{}'.format(self.task, self.group)







