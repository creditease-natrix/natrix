# -*- coding: utf-8 -*-
"""

"""
from __future__ import unicode_literals
import logging, json
import pika

from natrix.common import exception as natrix_exception
from .base import DispachClient


logger = logging.getLogger(__name__)


EXCHANGE_REQUEST_TEMPLATE = 'natrix_request_{tag}'
EXCHANGE_COMMAND_DEAD = 'natrix_command_dlx'
EXCHANGE_RESPONSE = 'natrix_command_response'

QUEUE_RESPONSE = 'natrix_dial_response'
QUEUE_DEAD = 'natrix_command_dead'

ROUTE_RESPONSE = 'command_response'
ROUTE_DEAD = 'dead_command'


class RabbitMQChannel(object):
    """

    """

    def __init__(self, channel, type):
        self.type = type
        self.channel = channel

        if type == 'request':
            pass
        elif type == 'dead':
            self.init_dead_queue_channel()
        elif type == 'response':
            self.init_response_queue()
        else:
            pass

    def init_request_queue(self, tag):
        try:
            exchange_name = EXCHANGE_REQUEST_TEMPLATE.format(tag=tag)

            self.channel.exchange_declare(exchange=exchange_name, exchange_type='direct')
            self.channel.queue_declare(queue=exchange_name,
                                       durable=True,
                                       arguments={
                                          'x-message-ttl': 120000,
                                          'x-dead-letter-exchange': EXCHANGE_COMMAND_DEAD,
                                          'x-dead-letter-routing-key': 'dead_command'
                                      })
            self.channel.queue_bind(exchange=exchange_name,
                                    queue=exchange_name,
                                    routing_key='command')

        except Exception as e:
            natrix_exception.natrix_traceback()
            raise natrix_exception.ClassInsideException(message=str(e))

    def init_dead_queue_channel(self):
        try:
            exchange_name = EXCHANGE_COMMAND_DEAD
            queue_name = QUEUE_DEAD
            routing_key = ROUTE_DEAD

            self.channel.exchange_declare(exchange=exchange_name, exchange_type='direct')
            self.channel.queue_declare(queue=queue_name,
                                  durable=True)
            self.channel.queue_bind(exchange=exchange_name,
                               queue=queue_name,
                               routing_key=routing_key)

        except Exception as e:
            natrix_exception.natrix_traceback()
            raise natrix_exception.ClassInsideException(message=str(e))

    def consume(self, callback):
        if self.type == 'dead':
            queue_name = QUEUE_DEAD
        elif self.type == 'response':
            queue_name = QUEUE_RESPONSE

        self.channel.basic_consume(
            consumer_callback=callback, queue=queue_name)
        self.channel.start_consuming()

    def init_response_queue(self):
        try:
            exchange_name = EXCHANGE_RESPONSE
            queue_name = QUEUE_RESPONSE
            routing_key = ROUTE_RESPONSE

            # channel.exchange_declare(exchange=exchange_name, exchange_type='direct')
            # channel.queue_declare(queue=queue_name,
            #                       durable=True)
            # channel.queue_bind(exchange=exchange_name,
            #                    queue=queue_name,
            #                    routing_key=routing_key)
            self.channel.queue_declare(queue=queue_name, durable=True)

        except Exception as e:
            natrix_exception.natrix_traceback()
            raise natrix_exception.ClassInsideException(message=str(e))

    def publish_request(self, data, terminal):
        try:
            self.init_request_queue(terminal)
            exchange_name = EXCHANGE_REQUEST_TEMPLATE.format(tag=terminal)

            res = self.channel.basic_publish(exchange=exchange_name,
                                        routing_key='command',
                                        body=json.dumps(data),
                                        properties=pika.BasicProperties(delivery_mode=2))

            logger.debug('Publish a command({}) reqeust: {}'.format(terminal, res))

        except Exception as e:
            natrix_exception.natrix_traceback()
            logger.error('Command publish: terminal({}), error({})'.format(terminal, e))


class RabbitMQClient(DispachClient):

    def command_dispach(self, mac, command_info):
        ...

        # try:
        #     with mqservice.MQService.get_purge_channel() as channel:
        #         terminal_channel = RabbitMQChannel(channel=channel, type='request')
        #         data['terminal'] = terminal
        #         terminal_channel.publish_request(data=data, terminal=terminal)
        # except Exception as e:
        #     natrix_exception.natrix_traceback()
        #     logger.error('Dispatch command with error: {}'.format(e))






