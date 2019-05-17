# -*- coding: utf-8 -*-
"""

"""
from __future__ import unicode_literals
import logging

from rest_framework import serializers
from django.db import transaction
from django_celery_beat.models import IntervalSchedule, PeriodicTask, CrontabSchedule

logger = logging.getLogger(__name__)

class IntervalScheduleSerializer(serializers.ModelSerializer):

    def create(self, validated_data):
        """创建一个IntervalSchedule实例

        :param validated_data:
        :return:
        """
        try:
            interval_instance, _ = IntervalSchedule.objects.get_or_create(**validated_data)
        except IntervalSchedule.MultipleObjectsReturned:
            logger.info('There are more than one IntervalSchedule!{}'.format(validated_data))
            interval_instance = IntervalSchedule.objects.filter(**validated_data).first()

        return interval_instance

    class Meta:
        model = IntervalSchedule
        fields = ('every', 'period')


class CrontabScheduleSerializer(serializers.ModelSerializer):

    def create(self, validated_data):
        """

        :param validated_data:
        :return:
        """
        try:
            crontab_instance, _ = CrontabSchedule.objects.get_or_create(**validated_data)
        except CrontabSchedule.MultipleObjectsReturned:
            logger.info('There are more than one CrontabSchedule! {}'.format(validated_data))
            crontab_instance = CrontabSchedule.objects.filter(*validated_data).first()

        return crontab_instance

    class Meta:
        model = CrontabSchedule
        fields = ('minute', 'hour', 'day_of_week', 'day_of_month', 'month_of_year')


class PeriodicTaskSerializer(serializers.ModelSerializer):

    interval = IntervalScheduleSerializer(required=False, allow_null=True)
    crontab = CrontabScheduleSerializer(required=False, allow_null=True)

    def create(self, validated_data):
        with transaction.atomic():
            if 'interval' in validated_data:
                interval = validated_data.pop('interval')
                if interval is None:
                    interval_instance = None
                else:
                    interval_serializer = IntervalScheduleSerializer(data=interval)
                    if interval_serializer.is_valid():
                        interval_instance = interval_serializer.save()
                    else:
                        logger.info('T')
            else:
                interval_instance = None

            if 'crontab' in validated_data:
                crontab = validated_data.pop('crontab')
                if crontab is None:
                    crontab_instance = None
                else:
                    crontab_serializer = CrontabScheduleSerializer(data=crontab)
                    if crontab_serializer.is_valid():
                        crontab_instance = crontab_serializer.save()
                    else:
                        logger.info()
            else:
                crontab_instance = None

            if interval_instance is None and crontab_instance is None:
                logger.error(u'Creating a Task with out schedule, So it is a invalid Task.')

            instance = PeriodicTask.objects.create(interval=interval_instance,
                                                   crontab=crontab_instance,
                                                   **validated_data)
            return instance

    def update(self, instance, validated_data):

        with transaction.atomic():
            if 'interval' in validated_data:
                interval = validated_data.pop('interval')
                if interval is None:
                    instance.interval = None
                else:
                    interval_serializer = IntervalScheduleSerializer(data=interval)
                    if interval_serializer.is_valid():
                        interval_instance = interval_serializer.save()
                        instance.interval = interval_instance

            if 'crontab' in validated_data:
                crontab = validated_data.pop('crontab')
                if crontab is None:
                    instance.crontab = None
                else:
                    crontab_serializer = CrontabScheduleSerializer(data=crontab)
                    if crontab_serializer.is_valid():
                        instance.crontab = crontab_serializer.save()

            instance.name = validated_data.get('name', instance.name)
            instance.task = validated_data.get('task', instance.task)
            instance.args = validated_data.get('args', instance.args)
            instance.kwargs = validated_data.get('kwargs', instance.kwargs)
            instance.expires = validated_data.get('expires', instance.expires)

            instance.save()
            return instance

    class Meta:
        model = PeriodicTask
        fields = ('name', 'task', 'interval', 'crontab', 'args', 'kwargs', 'expires', )
        depth = 1


class PeriodicTaskController(object):

    @staticmethod
    def get_interval_tasks(task, interval=None):
        tasks = PeriodicTask.objects.filter(task=task)
        if interval is not None:
            tasks = tasks.filter(interval__every=interval, interval__period='minutes')

        return tasks

    @staticmethod
    def get_crontab_tasks(task, crontab_minute='*', crontab_hour='*',
                          crontab_day_of_week='*', crontab_day_of_month='*', crontab_month_of_year='*'):
        tasks = PeriodicTask.objects.filter(task=task)

        tasks = tasks.filter(crontab__minute=crontab_minute,
                             crontab__hour=crontab_hour,
                             crontab__day_of_week=crontab_day_of_week,
                             crontab__day_of_month=crontab_day_of_month,
                             crontab__month_of_year=crontab_month_of_year)
        return tasks






