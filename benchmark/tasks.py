# -*- coding: utf-8 -*-
"""

"""
from celery import shared_task
from celery.utils import log

from natrix.common import natrix_celery, exception as natrix_exception

from benchmark.models import Task
from benchmark.backends.command_dispatcher import dispatch_command

from benchmark.services import *


logger = log.get_task_logger(__name__)

DEAD_PROCESSOR_COUNT = 1
RESPONSE_PROCESSOR_COUNT = 1


@shared_task(bind=True)
def command_adapter_guardian(self):
    """Command Adapter Guardian

    This task must ensure that DEAD_PROCESOR_COUNT command_dead_processor tasks and
    RESPONSE_PROCESSOR_COUNT command_response_processor tasks are alive(active).

    :return:
    """
    dead_processor_num = DEAD_PROCESSOR_COUNT
    response_processor_num = RESPONSE_PROCESSOR_COUNT

    info = self.app.control.inspect().active()

    if info:
        for node, worker_list in info.items():
            for task_info in worker_list:
                if task_info['name'] == command_dead_processor.name:
                    dead_processor_num -= 1
                elif task_info['name'] == command_response_processor.name:
                    response_processor_num -= 1

    if dead_processor_num < 0 or response_processor_num < 0:
        logger.error(u'The [command_dead_processor]({}) or [command_response_processor]({}) exceed.'.format(
            dead_processor_num, response_processor_num
        ))

    #
    logger.info('There are {alive}/{total} [command_dead_processor] alive.'.format(
        alive=DEAD_PROCESSOR_COUNT-dead_processor_num, total=DEAD_PROCESSOR_COUNT))
    for _ in range(dead_processor_num):
        command_dead_processor.apply_async()

    #
    logger.info('There are {alive}/{total} [command_response_processor] alive.'.format(
        alive=RESPONSE_PROCESSOR_COUNT - response_processor_num, total=RESPONSE_PROCESSOR_COUNT))
    for _ in range(response_processor_num):
        command_response_processor.apply_async()

    # check whether command_clean_processor exist
    try:
        alive_cleaner = natrix_celery.get_interval_task(command_clean_processor.name)
        if len(alive_cleaner) == 0:
            logger.info('Configure [command cleaner processor]')
            natrix_celery.create_periodic_task('Command Adapter [command cleaner]',
                                               command_clean_processor.name,
                                               frequency=1)

        elif len(alive_cleaner) > 1:
            logger.error('There are more than one [command cleaner processor] ')
    except natrix_exception.NatrixBaseException as e:
        logger.error('{}'.format(e.get_log()))


@shared_task(bind=True)
def timed_task_process(self, frequency=0):

    tasks = Task.objects.filter(time_type='timed', schedule__frequency=frequency)

    logger.info('Process {}-schedule task ({})'.format(frequency, len(tasks)))

    for task in tasks:
        if task.schedule.is_alive():
            logger.debug('Process {} task'.format(task.id))
            res = dispatch_command(task.task_command_represent())
            logger.debug('Dispatch timed-task result: {}'.format(res))
        else:
            logger.debug('Timed task{} is expired or turn-off'.format(str(task.id)))



