# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import logging, json

from celery import shared_task, task

from natrix.common.mqservice import MQService
from natrix.common import exception as natrix_exceptions

from infrastructure.models.messenger import NotifyRecord
from infrastructure.messenger import couriers
from infrastructure.configurations import messenger as conf

logger = logging.getLogger(__name__)


@shared_task(bind=True)
def messenger_guard(self, queue_name=conf.queue_name):

    def messenger_data_process(ch, method, properties, body):
        messenger_processor.delay(body)
        ch.basic_ack(delivery_tag=method.delivery_tag)

    try:
        channel = MQService.get_channel(queue_name, durable=True)
        channel.basic_consume(consumer_callback=messenger_data_process,
                              queue=queue_name)
        channel.start_consuming()
    except Exception as e:
        natrix_exceptions.natrix_traceback()
        logger.error('Task ({name}) raise exception {exception}'.format(name=self.name, exception=e))
    finally:
        logger.info('Task End!-{}'.format(self.name))


@task
def messenger_processor(body):
    logger.info('send a message: {}'.format(body))
    message = json.loads(body)

    type = message.get('type', None)
    level = message.get('level', 'critical')

    application = message.get('application', '')
    description = message.get('description', '')
    destinations = message.get('destinations', [])
    title = message.get('title', '')
    generate_time = message.get('time', None)
    content = message.get('content', {})

    email_message = {
        'title': title,
        'time': generate_time,
        'body': content.get('body', ''),
        'supplement': content.get('supplement', '')
    }
    try:
        notify = couriers.get_notify_instance(type, destinations)
        notify.notify(message=email_message)

        NotifyRecord.objects.create(notify_type=type,
                                    level=level,
                                    description=description,
                                    application=application,
                                    destinations=json.dumps(destinations),
                                    title=title,
                                    content=json.dumps(content),
                                    generate_time=generate_time)
    except natrix_exceptions.NatrixBaseException as e:
        logger.error('There is an exception happend: {}'.format(e.get_log()))
    except Exception as e:
        logger.error('Natrix messenger-engine: uncatched {}'.format(e))





