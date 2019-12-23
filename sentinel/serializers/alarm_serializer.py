# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import logging

from rest_framework import serializers

from natrix.common.natrix_views.serializers import NatrixSerializer

from benchmark.models import Task

from sentinel.configurations import alarm_conf
from sentinel.models import Alarm
from sentinel.models.alarm_models import MONITOR_CHOICE, OPERATION_CHOICE, AGGREGATION_CHOICE
from sentinel.backends.deepmonitor import DeepMonitorAlarmManagement

logger = logging.getLogger(__name__)

class AlarmSerializer(NatrixSerializer):

    alarm_id = serializers.IntegerField(read_only=True, help_text=u'告警ID')
    name = serializers.CharField(max_length=64, help_text=u'告警名称', required=False, default='')
    description = serializers.CharField(max_length=255, help_text=u'告警描述')
    task_id = serializers.UUIDField(help_text=u'任务ID')
    monitor_type = serializers.ChoiceField(choices=MONITOR_CHOICE, help_text=u'指标项')
    operation = serializers.ChoiceField(choices=OPERATION_CHOICE,
                                        help_text=u'判断操作',
                                        required=False,
                                        allow_null=True)
    threshold = serializers.FloatField(help_text=u'阈值',
                                       required=False,
                                       allow_null=True)
    aggregation_type = serializers.ChoiceField(choices=AGGREGATION_CHOICE,
                                               help_text=u'聚合方式',
                                               required=False,
                                               allow_null=True)
    aggregation_condition = serializers.FloatField(help_text=u'聚合条件',
                                                   allow_null=True,
                                                   required=False)

    def validate_task_id(self, value):
        # TODO: validate if this task is your owned task or followed task
        try:
            task = Task.objects.get(id=value)
            self.task = task

            return value
        except Task.DoesNotExist:
            raise serializers.ValidationError('The task({}) is not exist!'.format(value))

    def is_valid(self, raise_exception=False):
        flag = super(AlarmSerializer, self).is_valid()

        if not flag:
            return flag

        if hasattr(self, 'instance') and self.instance:
            if self.instance.task != self.task:
                self._errors['task_id'] = ['Task can not be changed in edit api']
                return False

        protocol_type = self.task.get_protocol_type()
        monitor_type = self.initial_data.get('monitor_type')
        if protocol_type not in alarm_conf.MONITOR_TYPE.get(monitor_type, {}).get('protocol', []):
            self._errors['monitor_type'] = ['{} task without {} monitor!'.format(protocol_type, monitor_type)]
            return False

        # TODO: validate aggregation configuration
        return flag

    def create(self, validated_data):
        name = validated_data.get('name')
        description = validated_data.get('description')
        monitor_type = validated_data.get('monitor_type')
        operation = validated_data.get('operation')
        threshold = validated_data.get('threshold')
        aggregation_type = validated_data.get('aggregation_type')
        aggregation_condition = validated_data.get('aggregation_condition')
        aggregation_condition = aggregation_condition if aggregation_condition is not None else 0

        alarm = Alarm(name=name, description=description, task=self.task,
                                     monitor_type=monitor_type, operation=operation,
                                     threshold=threshold, aggregation_type=aggregation_type,
                                     agg_condition=aggregation_condition,
                                     owner=self.user, group=self.group)

        alarm_backend = DeepMonitorAlarmManagement(alarm)
        backend_id = alarm_backend.add()
        alarm.deepmonitor_uuid = backend_id

        alarm.save()

        return alarm

    def update(self, instance, validated_data):
        description = validated_data.get('description')
        instance.name = validated_data.get('name')
        instance.description = instance.description if description is None else description
        instance.monitor_type = validated_data.get('monitor_type')
        instance.operation = validated_data.get('operation')
        instance.threshold = validated_data.get('threshold')
        instance.aggregation_type = validated_data.get('aggregation_type')
        instance.agg_condition = validated_data.get('aggregation_condition')

        alarm_backend = DeepMonitorAlarmManagement(instance)
        alarm_backend.modify()

        instance.save()

        return instance


class AlarmOperationSerializer(NatrixSerializer):

    alarm_id = serializers.IntegerField(help_text=u'告警ID')
    operation = serializers.ChoiceField(choices=(('on', u'开启'), ('off', u'关闭')),
                                        help_text=u'操作')

    def validate_alarm_id(self, value):
        try:
            alarm = Alarm.objects.get(pk=value, group=self.group)
            self.instance = alarm
        except Alarm.DoesNotExist as e:
            raise serializers.ValidationError('The alarm({}) is not exist!'.format(value))

        return value

    def process(self):
        assert hasattr(self, '_errors'), (
            'You must call `.isvalid()` before calling `.process()`'
        )

        assert not self.errors, (
            'You can not call `.process()` on a serializer with invalid data.'
        )

        operation = self.validated_data.get('operation')

        alarm_backend = DeepMonitorAlarmManagement(self.instance)
        res, desc = alarm_backend.switch()
        if res:
            if operation == 'on':
                self.instance.status = True
            elif operation == 'off':
                self.instance.status = False
            self.instance.save()
        else:
            ...


class AlarmListSerializer(NatrixSerializer):
    is_paginate = serializers.NullBooleanField(required=True)
    pagenum = serializers.IntegerField(min_value=1, required=False)
