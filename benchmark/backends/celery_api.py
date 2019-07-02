# -*- coding: utf-8 -*-
"""

"""
from __future__ import unicode_literals
import json

from django_celery_beat.models import IntervalSchedule, PeriodicTask, PeriodicTasks

def add_beat_schedule(frequency, task):

    interval_schedule, interval_created = IntervalSchedule.objects.get_or_create(
        every=frequency,
        period=IntervalSchedule.SECONDS
    )
    celery_task = PeriodicTask.objects.get_or_create(
        interval=interval_schedule,
        name='{}-schedule-(seconds)'.format(frequency),
        task=task,
        kwargs=json.dumps({'frequency': frequency}),
        one_off=False
    )

    return celery_task

