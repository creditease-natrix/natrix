# -*- coding: utf-8 -*-
""" Benchmark cleaner cleans the Timeout Command, which include consume timeout and response timeout

"""
import json
from celery import task, shared_task
from celery.utils import log

from natrix.common import exception as natrix_exception, mqservice
from natrix.common.config import natrix_config as config
from benchmark.backends.command_dispatcher import (
    processor, get_process_client, response_expired_process)


__all__ = [
    'command_dead_processor',
    'command_clean_processor',
    'command_dead_task'
]
logger = log.get_task_logger(__name__)

CONFIG_TOPIC = 'BENCHMARK'

command_timeout = int(config.get_value(CONFIG_TOPIC, 'command_clean_time'))


@task(bind=True)
def command_dead_task(self, data):
    try:
        command_processor = processor.CommandExpiredProcessor(data)
        command_processor.process()
    except natrix_exception.NatrixBaseException as e:
        logger.error('Process dead message ERROR: {}'.format(e.get_log()))
    except Exception as e:
        logger.error('Get an expected Exception: {}'.format(e))


# TODO: remove mqservice
@task(bind=True)
def command_dead_processor(self):
    """Process Dead Command

    :return:
    """
    def dead_data_process(ch, method, properties, body):
        command_data = json.loads(body)
        try:
            command_dead_task.delay(command_data)
            # ack receive message
            ch.basic_ack(delivery_tag=method.delivery_tag)

        except natrix_exception.NatrixBaseException as e:
            logger.error('Process dead message ERROR: {}'.format(e.get_log()))

    with mqservice.MQService.get_purge_channel() as channel:
        try:
            process_client = get_process_client(channel, 'dead')
            process_client.consume(dead_data_process)

        except Exception as e:
            logger.error(u'{}'.format(e))
        finally:
            logger.info('Task End! - {}'.format(self.name))


@task(bind=True)
def command_clean_processor(self):
    """

    :return:
    """
    logger.info('Start to clean unresponse command')
    try:
        response_expired_process(freshness=command_timeout)
    except Exception as e:
        # TODO:
        logger.error(u'{}'.format(e))
