# -*- coding: utf-8 -*-
"""

"""
from celery import task
from celery.utils import log
from django.contrib.auth.models import  User

from natrix.common import exception as natrix_exception
from natrix.common.utils.time_processor import TimeProcessor
from natrix.common.notify import send_email

from rbac.api import get_group_administrator
from terminal.models import TerminalDevice
from terminal.backends import keep_alive as keep_terminal_alive

logger = log.get_task_logger(__name__)


# Terminal timeout
TERMINAL_TIMEOUT = 60
# The frequency of terminal outline, terminal_guardian runs every 1 minute.
ALERT_FREQUENCY = 10


@task(bind=True)
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
            terminals = td.get_active_terminals()
            dev_state = keep_terminal_alive.AliveStateAPI.keep_alive(sn, timeout=TERMINAL_TIMEOUT)

            if td.is_active != dev_state.get_curr_state():
                td.is_active = dev_state.get_curr_state()
                td.save()

            terminals_state = []
            for t in terminals:
                t_state = keep_terminal_alive.AliveStateAPI.keep_alive(t.mac, timeout=TERMINAL_TIMEOUT)
                terminals_state.append(t_state)

                if t.is_active != t_state.get_curr_state():
                    t.is_active = t_state.get_curr_state()
                    t.save()

            # contain the object type and state info
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
        except natrix_exception.NatrixBaseException as e:
            logger.error('{}'.format(e.get_log()))


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
        if state.get_alert_times() % ALERT_FREQUENCY == 0:
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
                org_info = '{name}  ({address})'.format(
                        name=org.get_full_name(), address=org.get_addresses_info())
                locations.append(item_template.format(info=org_info))
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
            return u'<font color="red">失联</font>', u'终端设备在{}时刻停止信息上报！'.format(
                TimeProcessor.timestamp_presentation(time_info))
        elif type == 'recovery':
            return u'<font color="green">恢复</font>', u'终端设备在{}时刻开始上报信息，告警解除！'.format(
                TimeProcessor.timestamp_presentation(time_info))
        elif type == 'dead':
            return u'<font color="red">失联</font>', u'终端设备持续{}时间，未上报信息！'.format(
                TimeProcessor.second_presentation(time_info))
        else:
            return u'<font color="green">正常</font>', '终端设备连接正常'

    def get_issues(issues, alert_police=lambda x: False):
        """Get the alert info which is represented as a table.

        :param issues:
        :param alert_police:
        :return:
        """
        item_template = u'''
            <tr>
                <td align="center">{tag}</td>
                <td align="center">{type}</td>
                <td align="center">{alert_type}</td>
                <td align="center">{alert_desc}</td>
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

    if dev.status == 'maintain':
        return

    issues = get_issues(alert_info, notify_police)
    if issues:
        alert_emails = get_alert_emails(dev.group)

        logger.info('There is an alert : {}, {}'.format(issues, alert_emails))

        send_email(destinations=alert_emails,
                   application=u'terminal',
                   title=u'Natrix终端维护通知',
                   body=EMAIL_BODY_TEMPLATE.format(
                       issues=issues,
                       location=get_location(dev)
                   ),
                   description=u'终端设备维护信息', )


def get_alert_emails(group):
    group_members = get_group_administrator(group)
    emails = set()
    try:
        for u in group_members:
            emails.add(u.email)
    except User.DoesNotExist:
        logger.error('There is not admin user!')

    return list(emails)


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


