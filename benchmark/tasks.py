# -*- coding: utf-8 -*-
"""

"""

from __future__ import unicode_literals, absolute_import
import json

from celery import shared_task, task
from celery.utils import log

from natrix.common import natrix_celery, exception as natrix_exception, mqservice
from benchmark.backends.command_adapter import adapter, adapter_settting

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
    except natrix_exception.BaseException as e:
        logger.error('{}'.format(e.get_log()))


@task(bind=True)
def command_dead_processor(self):
    """Porcess Dead Command


    :return:
    """
    def dead_data_process(ch, method, properties, body):
        command_data = json.loads(body)
        try:
            command_processor = adapter.CommandProcessor(stage='dead', command=command_data)
            command_processor.do()
        except natrix_exception.BaseException as e:
            logger.error('Process dead message ERROR: {}'.format(e.get_log()))
        finally:
            ch.basic_ack(delivery_tag=method.delivery_tag)

    with mqservice.MQService.get_purge_channel() as channel:
        try:
            # TODO:
            adapter_settting.AdapterMQSetting.init_dead_queue(channel)
            channel.basic_consume(consumer_callback=dead_data_process,
                                  queue=adapter_settting.QUEUE_DEAD)
            channel.start_consuming()

        except Exception as e:
            # TODO:
            logger.error(u'{}'.format(e))
        finally:
            logger.info('Task End! - {}'.format(self.name))


@task(bind=True)
def command_response_processor(self):
    """Process Terminal Response

    :return:
    """
    def response_data_process(ch, method, properties, body):
        try:
            command_data = json.loads(body)

            command_processor = adapter.CommandProcessor(stage='response', command=command_data)
            command_processor.do()
        except natrix_exception.BaseException:
            natrix_exception.natrix_traceback()
            logger.error('Consume reponse data error: {}'.format(command_data))
        finally:
            ch.basic_ack(delivery_tag=method.delivery_tag)

    with mqservice.MQService.get_purge_channel() as channel:
        try:
            adapter_settting.AdapterMQSetting.init_response_queue(channel)
            channel.basic_consume(consumer_callback=response_data_process,
                                  queue=adapter_settting.QUEUE_RESPONSE)
            channel.start_consuming()

        except Exception as e:
            natrix_exception.natrix_traceback()
            logger.error(u'{}'.format(e))
        finally:
            logger.info('Task End! - {}'.format(self.name))


@shared_task(bind=True)
def command_clean_processor(self):
    """

    :return:
    """
    try:
        adapter.CommandProcessor.process_unresponse()
    except Exception as e:
        # TODO:
        logger.error(u'{}'.format(e))



