# -*- coding: utf-8 -*-
""" Benchmark receiver receive Dial Testing response

"""
from celery import task
from celery.utils import log

from natrix.common import exception as natrix_exception
from benchmark.backends.command_dispatcher import processor
from benchmark.backends.command_dispatcher.channels.mqtt import MQTTDispachClient

logger = log.get_task_logger(__name__)


__all__ = ['command_response_task', 'command_response_processor']


@task(bind=True)
def command_response_task(self, data):
    try:
        command_processor = processor.ResponseProcessor(data)
        command_processor.process()
    except natrix_exception.NatrixBaseException as e:
        natrix_exception.natrix_traceback()
        logger.error('Consume reponse data error: {}'.format(e.get_log()))
    except Exception as e:
        natrix_exception.natrix_traceback()
        logger.error('Get an expected Exception: {}'.format(e))


@task(bind=True)
def command_response_processor(self):
    """Process Terminal Response

    :return:
    """
    with MQTTDispachClient() as client:
        print('start process response: {}'.format(client))
        client.response_subscribe(celery_task=command_response_task)

