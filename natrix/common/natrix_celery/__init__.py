# -*- coding: utf-8 -*-
"""

"""
from __future__ import unicode_literals
import json
import logging

from django_celery_beat.models import PeriodicTask

from natrix.common import exception as natrix_exception

from .celery_beat import PeriodicTaskController, PeriodicTaskSerializer

logger = logging.getLogger(__name__)


def create_periodic_task(name, task, expires=None, args=None, kwargs=None,
                         frequency=None,
                         crontab_minute=None, crontab_hour=None, crontab_day_of_week=None,
                         crontab_day_of_month=None, crontab_month_of_year=None):
    """

    :return:
    """
    task_data = {
        'name': name,
        'task': task,
        'expires': expires,
    }
    if frequency is not None:
        task_data['interval'] = {
            'every': frequency,
            'period': 'minutes'
        }
    crontab = {}
    if crontab_minute is not None:
        crontab['minute'] = crontab_minute
    if crontab_hour is not None:
        crontab['hour'] = crontab_hour
    if crontab_day_of_week is not None:
        crontab['day_of_week'] = crontab_day_of_week
    if crontab_day_of_month is not None:
        crontab['day_of_month'] = crontab_day_of_month
    if crontab_month_of_year is not None:
        crontab['month_of_year'] = crontab_month_of_year

    if len(crontab) != 0:
        task_data['crontab'] = crontab

    if args is not None:
        if isinstance(args, list):
            task_data['args'] = json.dumps(args)
        else:
            raise natrix_exception.ClassInsideException(message=u'periodic task args is not list')

    if kwargs is not None:
        if isinstance(kwargs, dict):
            task_data['kwargs'] = json.dumps(kwargs)
        else:
            raise natrix_exception.ClassInsideException(message=u'periodic task kwargs is not dict')

    serializer = PeriodicTaskSerializer(data=task_data)
    if serializer.is_valid():
        serializer.save()
    else:
        raise natrix_exception.ClassInsideException(message=serializer.errors)



def get_crontab_task(task, crontab_minute=None, crontab_hour=None, crontab_day_of_week=None,
                     crontab_day_of_month=None, crontab_month_of_year=None):
    kwargs = {}

    if crontab_minute is not None:
        kwargs['crontab_minute'] = crontab_minute

    if crontab_hour is not None:
        kwargs['crontab_hour'] = crontab_hour

    if crontab_day_of_week is not None:
        kwargs['crontab_day_of_week'] = crontab_day_of_week

    if crontab_day_of_month is not None:
        kwargs['crontab_day_of_month'] = crontab_day_of_month

    if crontab_month_of_year is not None:
        kwargs['crontab_month_of_year'] = crontab_month_of_year

    tasks = PeriodicTaskController.get_crontab_tasks(task, **kwargs)

    return tasks


def get_interval_task(task, interval=None):
    tasks = PeriodicTaskController.get_interval_tasks(task, interval=interval)
    return tasks


def update_periodic_task(name, task, expires=None, args=None, kwargs=None,
                         frequency=None,
                         crontab_minute=None, crontab_hour=None, crontab_day_of_week=None,
                         crontab_day_of_month=None, crontab_month_of_year=None,
                         crontab_cancel=False, ):
    pass


def delete_periodic_task(pk):
    """删除指定periodic task

    :param pk: the primary key
    :return:
    """
    try:
        task_instance = PeriodicTask.objects.get(pk=pk)
        task_instance.delete()
    except PeriodicTask.DoesNotExist:
        logger.info('The periodic_task is not exist! {}'.format(pk))

