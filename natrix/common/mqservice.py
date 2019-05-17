# -*- coding: utf-8 -*-
"""Natrix 系统的消息队列服务，采用RabbitMQ

"""

from __future__ import unicode_literals, absolute_import
import contextlib
try:
    import ConfigParser as configparser
except ImportError:
    import configparser
import logging
import os
import pika

from natrix import settings

logger = logging.getLogger(__name__)

# TODO: 该模块中的部分功能，考虑将来迁移infrastructure，对mq进行系统性管理。（待找到好的方式，兼容的封装、统计的队列管理等）
root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
config_file = root_dir + "/natrix.ini"
config = configparser.ConfigParser()
config.read(config_file)
BROKER_SERVER = config.get("RABBITMQ", "host")
BROKER_PORT = config.get("RABBITMQ", "port")
BROKER_USER = config.get("RABBITMQ", "username")
BROKER_PASSWORD = config.get("RABBITMQ", "password")
VIRTUAL_HOST = config.get("RABBITMQ", "vhost")


class MQService(object):

    @staticmethod
    def get_channel(queue_name, durable=True, timeout=None, dead_exchange='natrix_dlx',
                    dead_routing_key='dead'):
        kwargs = dict()
        if BROKER_SERVER:
            kwargs['host'] = BROKER_SERVER
        if BROKER_PORT:
            kwargs['port'] = int(BROKER_PORT)
        if BROKER_USER and BROKER_PASSWORD:
            credential = pika.PlainCredentials(BROKER_USER, BROKER_PASSWORD)
            kwargs['credentials'] = credential
        if VIRTUAL_HOST:
            kwargs['virtual_host'] = VIRTUAL_HOST

        parameters = pika.ConnectionParameters(**kwargs )

        connection = pika.BlockingConnection(parameters)
        channel = connection.channel()

        # 声明消息队列
        if timeout:
            channel.queue_declare(queue=queue_name,
                                  durable=durable,
                                  arguments={
                                      'x-dead-letter-exchange': dead_exchange,
                                      'x-message-ttl': timeout,
                                      'x-dead-letter-routing-key': dead_routing_key
                                  }
                                  )
        else:
            channel.queue_declare(queue=queue_name, durable=durable)

        channel.basic_qos(prefetch_count=1)

        return channel

    @staticmethod
    def publish_message(queue_name, data, host=BROKER_SERVER, durable=True):
        connection = pika.BlockingConnection(pika.ConnectionParameters(host=host))
        channel = connection.channel()

        # 声明消息队列
        channel.queue_declare(queue=queue_name, durable=durable)

        channel.basic_publish(exchange='',
                              routing_key=queue_name,
                              body=data,
                              properties=pika.BasicProperties(delivery_mode=2))
        connection.close()

    @staticmethod
    @contextlib.contextmanager
    def get_purge_channel():
        kwargs = dict()
        if BROKER_SERVER:
            kwargs = {'host': BROKER_SERVER}
        if BROKER_USER and BROKER_PASSWORD:
            credential = pika.PlainCredentials(BROKER_USER, BROKER_PASSWORD)
            kwargs['credentials'] = credential
        if VIRTUAL_HOST:
            kwargs['virtual_host'] = VIRTUAL_HOST

        parameters = pika.ConnectionParameters(**kwargs)

        connection = pika.BlockingConnection(parameters)
        channel = connection.channel()

        yield channel

        channel.close()
        connection.close()


if __name__ == '__main__':
    def consume_queue(ch, method, properties, body):
        print 'context : {}'.format(body)

    credential = pika.PlainCredentials('natrix', 'natrix')
    parameters = pika.ConnectionParameters(
        host='127.0.0.1',
        virtual_host='natrix',
        credentials=credential)

    connection = pika.BlockingConnection(parameters)
    channel = connection.channel()
    queue_name = 'keep_alive_basic'
    channel.queue_declare(queue=queue_name)

    channel.basic_consume(basic_consume=consume_queue,
                          queue=queue_name)

    channel.start_consuming()





