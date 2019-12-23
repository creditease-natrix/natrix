# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import logging
import json
import pika

from django.utils import timezone
from natrix.common.mqservice import MQService
from infrastructure.configurations import messenger as conf

logger = logging.getLogger(__name__)

class NotifyAPI(object):

    @staticmethod
    def add_email(destinations, application, title, level, generate_time=None,
                  description='Email notification!', content={}):

        # TODO: 参数校验，包括内容
        if generate_time is None:
            generate_time = timezone.now()

        channel = MQService.get_channel(conf.queue_name, durable=True)

        generate_time = generate_time.astimezone(timezone.get_current_timezone())
        logger.info('call add email : {}'.format(generate_time))

        alert_data = {
            'type': 'email',
            'level': level,
            'destinations': destinations,
            'time': generate_time.isoformat(),
            'application': application,
            'title': title,
            'description': description,
            'content': content
        }
        logger.info('publish a message in natrix_notification_queue: {}'.format(json.dumps(alert_data)))
        channel.basic_publish(exchange='',
                              routing_key=conf.queue_name,
                              body=json.dumps(alert_data),
                              properties=pika.BasicProperties(delivery_mode=2))


    @staticmethod
    def add_sms(destinations, application, title, level, generate_time=timezone.now(),
                description='Email notification!', body=''):

        # TODO: 考虑迁移到rabbitmq
        connection = pika.BlockingConnection(pika.ConnectionParameters(host=conf.BROKER_SERVER))
        channel = connection.channel()
        # TODO: rabbitmq queue声明方式，考虑？
        channel.queue_declare(queue=conf.queue_name, durable=True)

        generate_time = generate_time.astimezone(timezone.get_current_timezone())

        alert_data = {
            'type': 'sms',
            'level': level,
            'destinations': destinations,
            'time': generate_time.isoformat(),
            'application': application,
            'title': title,
            'description': description,
            'content': {
                'body': body
            }
        }
        channel.basic_publish(exchange='',
                              routing_key=conf.queue_name,
                              body=json.dumps(alert_data),
                              properties=pika.BasicProperties(delivery_mode=2))

        connection.close()

