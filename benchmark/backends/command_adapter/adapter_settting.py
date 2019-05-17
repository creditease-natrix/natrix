# -*- coding: utf-8 -*-
"""
"""

from __future__ import unicode_literals
import logging

from natrix.common import exception as natrix_exceptions

logger = logging.getLogger(__name__)


EXCHANGE_REQUEST_TEMPLATE = 'natrix_request_{tag}'
EXCHANGE_COMMAND_DEAD = 'natrix_command_dlx'
EXCHANGE_RESPONSE = 'natrix_command_response'

QUEUE_RESPONSE = 'natrix_dial_response'
QUEUE_DEAD = 'natrix_command_dead'

ROUTE_RESPONSE = 'command_response'
ROUTE_DEAD = 'dead_command'


class AdapterMQSetting(object):
    """定义Adapter中关于MQ的定义

    """
    @staticmethod
    def init_request_queue(channel, tag):
        """初始化请求队列相关的信息

        :param channel:
        :return:
        """
        try:
            exchange_name = EXCHANGE_REQUEST_TEMPLATE.format(tag=tag)

            channel.exchange_declare(exchange=exchange_name, exchange_type='direct')
            channel.queue_declare(queue=exchange_name,
                                  durable=True,
                                  arguments={
                                      'x-message-ttl': 120000,
                                      'x-dead-letter-exchange': EXCHANGE_COMMAND_DEAD,
                                      'x-dead-letter-routing-key': 'dead_command'
                                  })
            channel.queue_bind(exchange=exchange_name,
                               queue=exchange_name,
                               routing_key='command')

        except Exception as e:
            logger.error(e)
            raise natrix_exceptions.ClassInsideException(message=str(e))

    @staticmethod
    def init_dead_queue(channel):
        """初始化'超时未消费'command队列相关配置

        :param channel:
        :return:
        """
        try:
            exchange_name = EXCHANGE_COMMAND_DEAD
            queue_name = QUEUE_DEAD
            routing_key = ROUTE_DEAD

            channel.exchange_declare(exchange=exchange_name, exchange_type='direct')
            channel.queue_declare(queue=queue_name,
                                  durable=True)
            channel.queue_bind(exchange=exchange_name,
                               queue=queue_name,
                               routing_key=routing_key)

        except Exception as e:
            logger.error(e)
            raise natrix_exceptions.ClassInsideException(message=str(e))

    @staticmethod
    def init_response_queue(channel):
        """初始化'超时未响应'command队列相关配置

        :return:
        """
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
            channel.queue_declare(queue=queue_name, durable=True)
        except Exception as e:
            logger.error(e)
            raise natrix_exceptions.ClassInsideException(message=str(e))

