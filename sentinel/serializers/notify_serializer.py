# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import logging, time

from rest_framework import serializers
from django.contrib.auth.models import User, Group
from django.db import transaction

from natrix.common.natrix_views.serializers import NatrixSerializer
from natrix.common import exception as natrix_exception
from sentinel.models import Alarm, Notification
from sentinel.models.alarm_models import NOTIFICATION_CHOICE
from sentinel.backends.deepmonitor import DeepMonitorNotificationManagement


logger = logging.getLogger(__name__)


choice_filter = lambda x: (x.get('name'), x.get('verbose_name'))


class NotifySerializer(NatrixSerializer):
    alarm_id = serializers.IntegerField(help_text=u'告警ID', required=False)
    description = serializers.CharField(max_length=255, help_text=u'通知描述', allow_blank=True)
    notify_type = serializers.ChoiceField(choices=NOTIFICATION_CHOICE, help_text=u'通知类型')

    users = serializers.ListField()
    is_recovery = serializers.BooleanField(help_text=u'是否恢复通知')
    frequency = serializers.IntegerField(help_text=u'频率（分钟）')
    start_time = serializers.TimeField(help_text=u'工作开始时间')
    end_time = serializers.TimeField(help_text=u'工作结束时间')

    def validate_alarm_id(self, value):
        try:
            alarm = Alarm.objects.get(pk=value, group=self.group)
            self.alarm = alarm
        except Alarm.DoesNotExist:
            raise serializers.ValidationError('The alarm({}) is not exist!'.format(value))

        return value

    def validate_users(self, value):
        #TODO: Validate users
        user_list = User.objects.filter(pk__in=value)
        if len(user_list) != len(value):
            raise serializers.ValidationError('There are non-exist user!')
        self.user_list = user_list

        return value

    def is_valid(self):
        flag = super(NotifySerializer, self).is_valid()

        if not hasattr(self, 'instance'):
            if not hasattr(self, 'alarm'):
                self._errors['alarm_id'] = ['"alarm_id" is required!']
                return False

        if not flag:
            return flag
        start_time = time.strptime(self.initial_data.get('start_time'), '%H:%M')
        end_time = time.strptime(self.initial_data.get('end_time'), '%H:%M')

        if end_time < start_time:
            self._errors['work_time'] = ['end_time must more than start_time']
            return False

        return flag

    def create(self, validated_data):
        description = validated_data.get('description')
        notify_type = validated_data.get('notify_type')
        is_recovery = validated_data.get('is_recovery')
        frequency = validated_data.get('frequency') * 60
        start_time = validated_data.get('start_time')
        end_time = validated_data.get('end_time')

        notify = Notification.objects.create(alarm=self.alarm,
                                             description=description,
                                             notify_type = notify_type,
                                             is_recovery=is_recovery,
                                             frequency=frequency,
                                             start_time=start_time,
                                             end_time=end_time,
                                             owner=self.user,
                                             group=self.group)
        for u in self.user_list:
            notify.users.add(u)

        notify_backend = DeepMonitorNotificationManagement(notify)
        deepmonitor_uuid, deepmonitor_operation = notify_backend.add()

        notify.deepmonitor_uuid = deepmonitor_uuid
        notify.deepmonitor_operation = deepmonitor_operation
        notify.save()

        return notify

    def update(self, instance, validate_data):
        description = validate_data.get('description')

        with transaction.atomic():
            instance.description = description if description else instance.description
            instance.notify_type = validate_data.get('notify_type')
            instance.is_recovery = validate_data.get('is_recovery')
            instance.frequency = validate_data.get('frequency') * 60
            instance.start_time = validate_data.get('start_time')
            instance.end_time = validate_data.get('end_time')

            instance.users.clear()
            for u in self.user_list:
                instance.users.add(u)

            notify_backend = DeepMonitorNotificationManagement(instance)
            notify_backend.modify()

            instance.save()

        return instance


class NotifySearchSerializer(NatrixSerializer):

    alarm_id = serializers.IntegerField()
    notify_id = serializers.IntegerField()

    def validate_alarm_id(self, value):
        try:
            alarm = Alarm.objects.get(pk=value)
            self.alarm = alarm
        except Alarm.DoesNotExist:
            raise serializers.ValidationError('The alarm({}) is not exist!'.format(value))

        return value

    def validate_notify_id(self, value):
        try:
            notification = Notification.objects.get(pk=value)
            self.notification = notification
        except Notification.DoesNotExist:
            raise serializers.ValidationError('The notification({}) is not exist!'.format(value))

        return value

    def is_valid(self, raise_exception=False):
        flag = super(NotifySearchSerializer, self).is_valid()
        if not flag:
            return flag

        if self.notification.alarm != self.alarm:
            self._errors['notify_id'] = ['notify_id and alarm_id is not matched!']
            return False

        return flag

    def presentation(self):
        assert hasattr(self, '_errors'), (
            'You must call `.isvalid()` before calling `.process()`'
        )

        assert not self.errors, (
            'You can not call `.process()` on a serializer with invalid data.'
        )

        notify = self.notification.represent()
        notify['frequency'] /= 60

        return notify


class NotificationListSerializer(NatrixSerializer):
    alarm_id = serializers.IntegerField()
    is_paginate = serializers.NullBooleanField(required=True)
    pagenum = serializers.IntegerField(min_value=1, required=False)

    def validate_alarm_id(self, value):
        if not isinstance(self.group, Group):
            raise natrix_exception.ClassInsideException(
                u'The user must join a group when query unfollowed task!')
        try:
            alarm = Alarm.objects.get(pk=value, group=self.group)
            self.alarm = alarm
        except Alarm.DoesNotExist as e:
            raise serializers.ValidationError('The alarm({}) is not exist!'.format(value))

        return value


class NotificationOperationSerializer(NatrixSerializer):
    notify_id = serializers.IntegerField(help_text=u'通知ID')
    operation = serializers.ChoiceField(choices=(('on', u'开启'), ('off', u'关闭')),
                                        help_text=u'操作')

    def validate_notify_id(self, value):
        try:
            notification = Notification.objects.get(pk=value, group=self.group)
            self.instance = notification
        except Notification.DoesNotExist as e:
            raise serializers.ValidationError('The notification({}) is not exist!'.format(value))

        return value

    def process(self):
        assert hasattr(self, '_errors'), (
            'You must call `.isvalid()` before calling `.process()`'
        )

        assert not self.errors, (
            'You can not call `.process()` on a serializer with invalid data.'
        )

        operation = self.validated_data.get('operation')

        notify_backend = DeepMonitorNotificationManagement(self.instance)
        notify_backend.switch()

        if operation == 'on':
            self.instance.status = True
        elif operation == 'off':
            self.instance.status = False

        self.instance.save()




