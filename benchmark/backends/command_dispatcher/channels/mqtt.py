# -*- coding: utf-8 -*-
"""
"""
import json, time

from natrix.common.natrixlog import NatrixLogging
from natrix.common import exception as natrix_exceptions
from utils.natrixmqtt import natrix_mqttclient, publish_result_analyse

from .base import DispachClient

logger = NatrixLogging(__name__)


client_id = 'command_dispacher_{}'


class MQTTDispachClient(DispachClient):
    """

    """

    def __init__(self):
        super(MQTTDispachClient, self).__init__()

    def __enter__(self):
        client = natrix_mqttclient(client_id.format(time.time()))
        self.client = client
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        print('end of connection')
        self.client.disconnect()

    def command_dispach(self, mac, command_info):
        if not self.client.is_connected():
            self.client.connect()
        logger.info('MQTT dispatch command | {} | {} | {}'.format(
            mac, command_info.get('uuid'), command_info.get('generate_timestamp')))
        topic_str = 'natrix/benchmark/{}'.format(mac)
        res = self.client.publish(topic=topic_str,
                                  payload=json.dumps(command_info),
                                  qos=2,
                                  retain=False)

        publish_result_analyse(res, logger=logger, service='Benchmark command dispach')

    def response_subscribe(self, topic='natrix/response', celery_task=None):

        def process_response(client, userdata, message):
            try:
                response_data = json.loads(str(message.payload, encoding='utf-8'))
                logger.info(response_data)
                celery_task.delay(response_data)
            except Exception as e:
                natrix_exceptions.natrix_traceback()
                logger.error('Process testing response with error: {}'.format(e))

        def on_connect(client, userdta, flags, rc):
            print('subscribe ....')
            client.subscribe(topic, qos=1)
            client.message_callback_add(topic, process_response)

        self.client.on_connect = on_connect
        self.client.connect(keepalive=10)

        self.client.loop_forever()
