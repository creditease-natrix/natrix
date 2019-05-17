# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from celery import shared_task, task
from celery.utils import log

from .messenger.tasks import messenger_guard


logger = log.get_logger(__name__)

@shared_task(bind=True)
def infrastructure_service_master(self):
    """

    :param self:
    :return:
    """

    info = self.app.control.inspect().active()
    task_info = dict()
    if info:
        for node, worker_list in info.items():
            for worker_info in worker_list:
                task_name = worker_info['name']
                if task_name not in task_info:
                    task_info[task_name] = 1
                task_info[task_name] += 1

    messenger_guard_count = task_info.get(messenger_guard.name, 0)

    if messenger_guard_count == 0:
        messenger_guard.apply_async()
    elif messenger_guard_count == 1:
        logger.info('There is one messenger_guard is alive')
    else:
        logger.info('There is more than one messenger_guard are alive.{}'.format(messenger_guard_count))




