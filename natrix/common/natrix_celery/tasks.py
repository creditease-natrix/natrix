# -*- coding: utf-8 -*-

from __future__ import unicode_literals, absolute_import

from celery.utils.log import get_task_logger
from celery import Task

logger = get_task_logger(__name__)


class NatrixBaseTask(Task):
    """

    """

    def is_valid(self):
        return True



    def online_tasks(self):
        info = self.app.control.inspect().active()
        current_task = []
        if info:
            for node, worker_list in info.items():
                for task_info in worker_list:
                    if task_info['name'] == self.name:
                        current_task.append(task_info)

        return current_task


class NatrixUniqueTask(NatrixBaseTask):

    natrix_apply_async_count = 0

    # def __init__(self, *args, **kwargs):
    #     super(NatrixUniqueTask, self).__init__(*args, **kwargs)
    #
    #
    # def is_permit_apply(self):
    #     """Check task if could be applied
    #
    #     Check condition:
    #     - runtime task
    #     - apply task
    #
    #     :return:
    #     """
    #     current_task = self.online_tasks()
    #     if len(current_task) > 1:
    #         error = 'Task({name}) is an unique task, but there are more than one in runtime({task_list})'.format(
    #             name=self.name,
    #             task_list=' '.join(map(lambda t: t['id'], current_task))
    #         )
    #         logger.error(error)
    #         raise natrix_exception.CeleryException(error)
    #     elif len(current_task) == 1:
    #         error = 'Task({name}) is an unique task, but there is one task at runtime status: ({task_id})'.format(
    #             name=self.name,
    #             task_id=map(lambda t: t['id'], current_task)
    #         )
    #         logger.info(error)
    #         raise natrix_exception.CeleryException(error)
    #
    #     # TODO: lock
    #     if self.natrix_apply_async_count > 0:
    #         error = 'Task({name}) is an unique task, but there are more than one '.format(
    #             name=self.name,
    #         )
    #         logger.info(error)
    #         raise natrix_exception.CeleryException(error)
    #
    #     logger.info('This unique task({name}) can be run!'.format(name=self.name))

    # def apply_async(self, args=None, kwargs=None, task_id=None, producer=None,
    #                 link=None, link_error=None, shadow=None, **options):
    #     self.is_permit_apply()
    #     self.natrix_apply_async_count += 1
    #     super(NatrixUniqueTask, self).apply_async(args=None, kwargs=None, task_id=None, producer=None,
    #                 link=None, link_error=None, shadow=None, **options)
    #
    # def on_failure(self, exc, task_id, args, kwargs, einfo):
    #     logger.info('Task Failure!{} {}'.format(exc, einfo))
    #     super(NatrixUniqueTask, self).on_failure(exc, task_id, args, kwargs, einfo)
