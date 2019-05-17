# -*- coding: utf-8 -*-
"""

"""

from __future__ import unicode_literals, absolute_import
import time
import json

from celery import shared_task, task
from celery.utils import log

from django_redis import get_redis_connection
from django.contrib.auth.models import  User

from natrix.common.natrix_celery.tasks import NatrixUniqueTask
from natrix.common import exception as natrix_exception
from natrix.common.mqservice import MQService
from natrix.common.notify import send_email
from natrix.common.utils.time_processor import TimeProcessor
from terminal.models import TerminalDevice
from terminal.serializers.alive_serializer import AdvanceInfoSerializer, BasicInfoSerializer
from terminal.configurations.terminal_conf import TERMINAL_INDEX, TERMINAL_BASIC, TERMINAL_ADVANCE

from terminal.backends import store, keep_alive

logger = log.get_task_logger(__name__)
conn = get_redis_connection('default')


# set terminal basic info expire time in cache
# this will affect temrinal device status transition that from posting to active
basic_cache_expire_time = 120

# Terminal timeout
TERMINAL_TIMEOUT = 120


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
            'networks': basic_info.get('networks', {}).values(),
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


@shared_task(base=NatrixUniqueTask, bind=True)
def terminal_basic_guard(self, queue_name='keep_alive_basic'):
    """Terminal keep alive process.

    Used to maintain terminal status info, include device status, system info and interfaces info.
    It consumes basic_info which comes from natrix_keep_alive_basic queue in MQ service.

    :return:
    """

    def basic_data_process(ch, method, properties, body):
        basic_info_process.delay(body)
        ch.basic_ack(delivery_tag=method.delivery_tag)

    try:
        tasks_list = self.online_tasks()
        tasks_number = len(tasks_list)
        logger.info('Online task({name}) number : {number}'.format(name=self.name, number=tasks_number))
        channel = MQService.get_channel(queue_name)
        channel.basic_consume(consumer_callback=basic_data_process,
                              queue=queue_name)
        channel.start_consuming()

    except Exception as e:
        natrix_exception.natrix_traceback()
        logger.error('Task ({name}) raise exception {exception}'.format(name=self.name, exception=e))
    finally:
        logger.info('Task End!-{}'.format(self.name))


@shared_task(bind=True)
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
            'networks': networks.values(),
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


@shared_task(base=NatrixUniqueTask, bind=True)
def terminal_advance_guard(self, queue_name='keep_alive_advance'):
    """

    :return:
    """

    def advance_data_process(ch, method, properties, body):
        logger.info(body)
        advance_info_process.delay(body)
        ch.basic_ack(delivery_tag=method.delivery_tag)

    try:
        tasks_list = self.online_tasks()
        tasks_number = len(tasks_list)
        logger.info('Online task({name}) number : {number}'.format(name=self.name, number=tasks_number))
        channel = MQService.get_channel(queue_name)
        channel.basic_consume(consumer_callback=advance_data_process,
                              queue=queue_name)
        channel.start_consuming()
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
    store_data = {'receive_time': info.get('timestamp') * 1000,
                  'heartbeat': info.get('heartbeat') * 1000}

    store_data.update(info.get('hardware'))
    store_data.update(info.get('system'))
    store_data['networks'] = info.get('networks').values()

    store.save(TERMINAL_INDEX, TERMINAL_BASIC,store_data)


def store_advance_info(info):
    """

    :param info:
    :return:
    """
    store_data = {'receive_time': info.get('timestamp') * 1000,
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

    store_data['networks'] = info.get('networks').values()

    store.save(TERMINAL_INDEX, TERMINAL_ADVANCE, store_data)


@shared_task(bind=True)
def terminal_guardian(self):
    """Terminal device alive checking.

    Only take care of active terminal devices.

    Check all terminal-devices update time ( named last_online_time in terminal_device table)
    or the timestamp in redis per 3 minutes, if they are all 3 minutes ago send alert email
    to some user.

    :return:
    """

    terminal_devices = list(TerminalDevice.objects.all())

    for td in terminal_devices:
        try:
            # get all register
            sn = td.sn
            terminals = td.terminal_set.all()
            dev_state = keep_alive.AliveStateAPI.keep_alive(sn, timeout=TERMINAL_TIMEOUT)

            if td.is_active != dev_state.get_curr_state():
                td.is_active = dev_state.get_curr_state()
                td.save()

            terminals_state = []
            for t in terminals:
                t_state = keep_alive.AliveStateAPI.keep_alive(t.mac, timeout=TERMINAL_TIMEOUT)
                terminals_state.append(t_state)

                if t.is_active != t_state.get_curr_state():
                    t.is_active = t_state.get_curr_state()
                    t.save()

            alert_info = []

            if td.device_alert:
                alert_info.append([
                    'device',
                    dev_state
                ])

            if td.terminal_alert:
                for t_state in terminals_state:
                    alert_info.append([
                        'terminal',
                        t_state
                    ])

            terminal_alert(td, alert_info)

        except ValueError as e:
            logger.error('Parse terminal cache info error : {}'.format(e))
        except natrix_exception.BaseException as e:
            logger.error('{}'.format(e.get_log()))

def get_admin_email():
    try:
        user = User.objects.get(username='admin')
        email = user.email
    except User.DoesNotExist:
        logger.error('There is not admin user!')
        email = None

    return email if email else None

ALIVE_EMAIL_LIST = []

if get_admin_email():
    ALIVE_EMAIL_LIST.append(get_admin_email())


EMAIL_BODY_TEMPLATE = u'''
<p>尊敬的Natrix用户,系统检测到终端设备发生了如下问题：</p>
{issues}
<p>该终端设备位于：{location}</p>
<p>如果发现终端发生失联问题，请按下面的事项进行排查：</p>
    <p>1. 电源线接通正常；</p>
    <p>2. 网线接通正常。</p>
    <p>如果有其他问题，请发送邮件到natrixgroup@163.com</p>
    谢谢！
<p></p>
'''

def notify_police(state):
    """The police determine the condition of sending an alert email.

    :param times:
    :return:
    """
    event_type, event_info = state.get_event()

    if event_type == 'aliving':
        return False

    if event_type == 'dead-first':
        return True

    if event_type == 'recovery':
        return True

    if event_type == 'dead':
        if state.get_alert_times() % 10 == 0:
            return True
        else:
            return False

    return False


def terminal_alert(dev, alert_info):
    """

    :param terminal: a TerminalDevice instant.
    :parma fresh_time: fresh time, the unit is second.
    :return:
    """
    def get_location(dev):
        """Get the address of terminal device.

        :param dev:
        :return:
        """
        item_template = u'<li>{info}</li>'
        organizations = dev.register.organizations.all() if dev.register else []
        locations = []
        if organizations:
            for org in organizations:
                # TODO: organization address must be modified
                locations.append(item_template.format(
                    '{name}  {address}'.format(name=org.get_full_name(),
                                               address=org.get_addresses())
                ))
        else:
            locations.append(item_template.format(info=u'无注册职场，具体位置未知！'))

        return u'<ul>{}</ul>'.format(''.join(locations))

    def issue_representation(type, time_info):
        """

        :param type:
        :param time_info:
        :return:
        """
        if type == 'dead-first':
            return u'失联', u'终端设备在{}时刻停止信息上报！'.format(
                TimeProcessor.timestamp_presentation(time_info))
        elif type == 'recovery':
            return u'恢复', u'终端设备在{}时刻开始上报信息，告警解除！'.format(
                TimeProcessor.timestamp_presentation(time_info))
        elif type == 'dead':
            return u'失联', u'终端设备持续{}时间，未上报信息！'.format(
                TimeProcessor.second_presentation(time_info))
        else:
            return u'正常', '终端设备连接正常'

    def get_issues(issues, alert_police=lambda x: False):
        """Get the alert info which is represented as a table.

        :param issues:
        :param alert_police:
        :return:
        """
        item_template = u'''
            <tr>
                <td>{tag}</td>
                <td>{type}</td>
                <td>{alert_type}</td>
                <td>{alert_desc}</td>
            </tr>
        '''
        issue_list = []
        for type, issue in issues:
            if alert_police(issue):
                alert_type, alert_desc = issue_representation(*issue.get_event())
                issue_list.append(
                    item_template.format(
                        tag = issue.pk,
                        type = u'终端设备' if type == 'device' else u'终端',
                        alert_type=alert_type,
                        alert_desc=alert_desc
                    )
                )
        if issue_list:
            return u'''<table>
                    <tr>
                        <th>标识</th>
                        <th>类型</th>
                        <th>告警类型</th>
                        <th>告警描述</th>
                    </tr>
            {table_body}
            </table>'''.format(table_body = ''.join(issue_list))
        else:
            return None

    issues = get_issues(alert_info, notify_police)

    if issues:
        logger.info('There is an alert : {}'.format(issues))
        send_email(destinations=ALIVE_EMAIL_LIST,
                   application=u'terminal',
                   title=u'Natrix终端维护通知',
                   body=EMAIL_BODY_TEMPLATE.format(
                       issues=issues,
                       location=get_location(dev)
                   ),
                   description=u'终端设备维护信息', )


