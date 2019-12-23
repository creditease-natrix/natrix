# -*- coding: utf-8 -*-
"""

"""
import logging
import ssl
import paho.mqtt.client as mqtt

from natrix.common.config import natrix_config as config


mqtt_logger = logging.getLogger(__name__)

# Read the configuration from natrix.ini
CONFIG_TOPIC = 'MQTT'
host = config.get_value(CONFIG_TOPIC, 'host')
port = int(config.get_value(CONFIG_TOPIC, 'port'))
username = config.get_value(CONFIG_TOPIC, 'username')
password = config.get_value(CONFIG_TOPIC, 'password')
ssl_used = config.get_value(CONFIG_TOPIC, 'ssl')


class NatrixMQTTClient(mqtt.Client):

    def __init__(self, *args, **kwargs):
        super(NatrixMQTTClient, self).__init__(*args, **kwargs)
        self.username_pw_set(username, password=password)

        if ssl_used.upper() == 'TRUE':
            ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
            self.tls_set_context(ssl_context)

    def connect(self, keepalive=60):
        return super(NatrixMQTTClient, self).connect(host=host, port=port, keepalive=keepalive)

    def is_connected(self):
        if self._sock:
            return True
        else:
            return False


def natrix_mqttclient(client_id):
    """Generate a natrix mqtt client.

    This function encapsulates all configurations about natrix mqtt client.

    Include:
    - client_id
      The unique id about mqtt connection.
    - username & password
      Username is device serial number which used to identify who am I;


    :return:
    """

    client = NatrixMQTTClient(client_id)
    return client


def publish_result_analyse(res, logger=None, service=None):
    if logger is None:
        logger = mqtt_logger

    if res.is_published():
        logger.info("Publish({}) successfully!".format(service))
    else:
        if res.rc == mqtt.MQTT_ERR_NO_CONN:
            logger.error("Publish({}) MQTT_ERR_NO_CONN".format(service))
        elif res.rc == mqtt.MQTT_ERR_SUCCESS:
            logger.info("Publish({}) MQTT_ERR_SUCCESS".format(service))
        elif res.rc == mqtt.MQTT_ERR_QUEUE_SIZE:
            logger.error("Publish({}) MQTT_ERR_QUEUE_SIZE".format(service))
        else:
            logger.error("Publish({}) operation with an unkown error".format(service))

