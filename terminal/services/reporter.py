# -*- coding: utf-8 -*-

"""

"""
import json
import time
from celery import shared_task, task
from celery.utils import log
from django_redis import get_redis_connection

from natrix.common import exception as natrix_exception
from utils.elasticsearch import NatrixESClient
from utils.natrixmqtt import natrix_mqttclient

from terminal.backends import keep_alive
from terminal.serializers.alive_serializer import AdvanceInfoSerializer, BasicInfoSerializer
from terminal.configurations.terminal_conf import TERMINAL_BASIC, TERMINAL_ADVANCE

logger = log.get_task_logger(__name__)
conn = get_redis_connection('default')


# set terminal basic info expire time in cache
# this will affect terminal device status transition that from posting to active
basic_cache_expire_time = 120


def update_alive_info(sn, networks):
    keep_alive.AliveStateAPI.update_state(sn)

    for info in networks:
        mac = info.get('macaddress')
        access_intranet = info.get('access_intranet')
        access_corporate = info.get('access_corporate')
        access_internet = info.get('access_internet')

        if access_intranet or access_corporate or access_internet:
            keep_alive.AliveStateAPI.update_state(mac, state=True)
        else:
            keep_alive.AliveStateAPI.update_state(mac, state=False)


@task
def basic_info_process(body):
    """The task: process basic terminal info.

    Basic terminal info must be stored in redis as a string type, the key format is terminal-{sn} and
    the value is a json string. When one terminal first post (there is not record for it) or some info
    changed (system info and networks info)，must create or update mysql.

    :param body:
    :return:
    """
    try:
        basic_info = json.loads(body)

        terminal_info = {
            'system': basic_info.get('system', None),
            'hardware': basic_info.get('hardware', None),
            'networks': list(basic_info.get('networks', {}).values()),
            'heartbeat': basic_info.get('heartbeat', None)
        }

        serializer = BasicInfoSerializer(data=terminal_info)

        if serializer.is_valid():
            sn = serializer.validated_data.get('hardware').get('sn')

            # update alive state machine
            update_alive_info(sn, serializer.validated_data.get('networks'))

            redis_key = 'terminal-{}'.format(sn)
            cache_info = conn.get(redis_key)
            if cache_info is None:
                serializer.save()
            else:
                old_info = json.loads(cache_info)
                if not (old_info.get('system', None) == basic_info.get('system') and
                                old_info.get('networks', None) == basic_info.get('networks')):
                    logger.info(u'Terminal device({}) is changed or cache-data is expired!'.format(sn))
                    serializer.save()
                else:
                    logger.debug('Terminal info is not changed!')

            # Update Terminal info in redis, and add timestamp key.
            basic_info['timestamp'] = time.time()
            conn.set(redis_key, json.dumps(basic_info), basic_cache_expire_time)

            # TODO: move to infrastructrue
            store_basic_info(basic_info)
        else:
            logger.error('Basic Guard Error: {}. Drop it.'.format(serializer.errors))
    except ValueError as e:
        natrix_exception.natrix_traceback()
        logger.error('Basic info is not json format: {}'.format(body))
    except Exception as e:
        natrix_exception.natrix_traceback()
        logger.error('Occur an exception: {}'.format(e))


@task(bind=True)
def terminal_basic_guard(self):
    """Terminal keep alive process.

    Used to maintain terminal status info, include device status, system info and interfaces info.
    It consumes basic_info which comes from natrix_keep_alive_basic queue in MQ service.

    :return:
    """

    def data_processor(client, userdata, message):
        logger.info('Process basic message {}'.format(message.topic))
        device_info = str(message.payload, encoding="utf-8")
        print(device_info)
        basic_info_process.delay(device_info)

    def on_message(client, userdata, message):
        logger.info('Baisc receive unexpected message: {}'.format(message))

    def on_connect(client, userdata, flags, rc):
        logger.info('Terminal Basic Guard has connected broker!')
        broker_client.subscribe('natrix/basic/#', qos=0)
        client.message_callback_add('natrix/basic/#', data_processor)

    try:
        broker_client = natrix_mqttclient('device_basic_info')

        broker_client.on_connect = on_connect
        broker_client.on_message = on_message

        broker_client.connect(keepalive=30)
        broker_client.loop_forever()

    except Exception as e:
        natrix_exception.natrix_traceback()
        logger.error('Task ({name}) raise exception {exception}'.format(name=self.name, exception=e))
    finally:
        logger.info('Task End!-{}'.format(self.name))


@task
def advance_info_process(body):
    """The task: process advanced terminal info.

    Advanced terminal info only be stored in mysql。

    :param body:
    :return:
    """
    try:
        advance_info = json.loads(body)

        networks = advance_info.get('networks', {})

        terminal_info = {
            'system': advance_info.get('system'),
            'hardware': advance_info.get('hardware'),
            'networks': list(networks.values()),
            'heartbeat': advance_info.get('heartbeat')
        }

        serializer = AdvanceInfoSerializer(data=terminal_info)
        if serializer.is_valid():
            sn = serializer.validated_data.get('hardware').get('sn')

            # update alive state machine
            update_alive_info(sn, serializer.validated_data.get('networks'))

            serializer.save()

            # store info in es
            advance_info['timestamp'] = time.time()
            store_advance_info(advance_info)
        else:
            logger.error('Advance Guard Error: {}'.format(serializer.errors))

    except ValueError as e:
        natrix_exception.natrix_traceback()
        logger.error('Advance info is not json format: {}'.format(body))
    except Exception as e:
        natrix_exception.natrix_traceback()
        logger.error('Occur an exception: {}'.format(e))


@shared_task(bind=True)
def terminal_advance_guard(self):
    """

    :return:
    """

    def data_processor(client, userdata, message):
        logger.info('Process advanced message {}'.format(message.topic))
        device_info = str(message.payload, encoding="utf-8")
        advance_info_process.delay(device_info)

    def on_message(client, userdata, message):
        logger.info('Advanced receive unexpected message: {}'.format(message))

    def on_connect(client, userdata, flags, rc):
        broker_client.subscribe('natrix/advanced/#', qos=0)
        client.message_callback_add('natrix/advanced/#', data_processor)

    try:
        broker_client = natrix_mqttclient('device_advanced_info')

        broker_client.on_connect = on_connect
        broker_client.on_message = on_message

        broker_client.connect(keepalive=30)
        broker_client.loop_forever()

    except Exception as e:
        natrix_exception.natrix_traceback()
        logger.error('Task ({name}) raise exception {exception}'.format(name=self.name, exception=e))
    finally:
        logger.info('Task End!-{}'.format(self.name))


def store_basic_info(info):
    """Format data and store it to ES

    :param info:
    :return:
    """
    store_data = {'receive_time': int(info.get('timestamp') * 1000),
                  'heartbeat': info.get('heartbeat') * 1000}

    store_data.update(info.get('hardware'))
    store_data.update(info.get('system'))
    store_data['networks'] = list(info.get('networks').values())

    natrix_es_client = NatrixESClient(app='terminal')
    natrix_es_client.push(TERMINAL_BASIC,store_data)


def store_advance_info(info):
    """

    :param info:
    :return:
    """
    store_data = {'receive_time': int(info.get('timestamp') * 1000),
                  'heartbeat': info.get('heartbeat') * 1000}
    system_info = info.get('system')
    hardware_info = info.get('hardware')

    def update_data(dest, source):
        if not isinstance(source, dict):
            return

        for key, value in source.items():
            if isinstance(value, dict):
                update_data(dest, value)
            else:
                if key in dest:
                    logger.error('key({}) is repeat in advance data'.format(key))
                else:
                    dest[key] = value

    update_data(store_data, system_info)
    update_data(store_data, hardware_info)

    store_data['networks'] = list(info.get('networks').values())

    natrix_es_client = NatrixESClient(app='terminal')
    natrix_es_client.push(TERMINAL_ADVANCE, store_data)


@task(bind=True)
def terminal_alive_master(self):
    """Terminal Alive Master Task

    This task maintain must ensure two tasks is in running, they are:
        terminal_consumer_1: used to consume basic_info of terminal device post
        terminal_consumer_2: used to consume advance_info of terminal device post

    :param self:
    :return:
    """

    basic_guard_count = 0
    advance_guard_count = 0
    info = self.app.control.inspect().active()
    if info:
        for node, worker_list in info.items():
            for task_info in worker_list:
                if task_info['name'] == terminal_basic_guard.name:
                    basic_guard_count += 1
                if task_info['name'] == terminal_advance_guard.name:
                    advance_guard_count += 1

    if basic_guard_count == 0:
        terminal_basic_guard.apply_async()
    elif basic_guard_count == 1:
        logger.info('terminal_basic_guard task is alive')
    else:
        logger.error('There is more than one terminal_basic_guard is alive.(count={})'.format(basic_guard_count))

    if advance_guard_count == 0:
        terminal_advance_guard.apply_async()
    elif advance_guard_count == 1:
        logger.info('terminal_advance_guard task is alive.')
    else:
        logger.error('There is more than one terminal_advance_guard is alive.(count={})'.format(advance_guard_count))

