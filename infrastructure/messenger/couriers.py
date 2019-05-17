# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import logging
import time
import json
from jinja2 import Template
import requests

from django.core.mail import send_mail

from natrix.common import exception as natrix_exceptions

from infrastructure.configurations import messenger as conf
from .templates import HTML_TEMPLATE

logger = logging.getLogger(__name__)

class Notify(object):
    """The base class.

    """

    def __init__(self, to=[]):
        if self.valid_to(to):
            self.to = to
        else:
            raise natrix_exceptions.ClassInsideException(
                        message=u'Create Notify class with an error parameter')

    def valid_to(self, to):
        """ Check whether the parameter(to) is available.

        :return: boolean
        """
        if isinstance(to, (list, tuple)):
            return True
        else:
            return False

    def set_destination(self, to):
        if isinstance(to, (list, tuple)) and to:
            self.to = to
        else:
            raise natrix_exceptions.ClassInsideException(
                message=u'Create Notify class with an error parameter : to'
            )

    def notify(self, message):
        """send message

        :param message:
        :return:
        """
        if not (self.valid_to(self.to) and self.to):
            raise natrix_exceptions.ClassInsideException(
                message=u'You must have a valid paremeter(to) before calling `.notify()`'
            )

    def record(self):
        """ To record the notification in database.

        :return:
        """
        pass


class EmailNotify(Notify):
    """Email Notify Class.

    """

    def valid_message(self, message):
        """Check whether message is available.

        :param message:
        :return:
        """
        if isinstance(message, dict):
            if message.get('title', None) is None or message.get('time', None) is None \
                    or message.get('body', None) is None:
                return False
            return True
        else:
            return False

    def notify(self, message):
        """
        :param message: dict, must includes title, time and body; supplement is optional
        :return:
        """
        super(EmailNotify, self).notify(message)

        try:
            if not self.valid_message(message):
                raise natrix_exceptions.ParameterException(parameter='title, time and body')
            title = message.get('title', '')
            time = message.get('time', '')
            body = message.get('body', '')
            supplement = message.get('supplement', '')

            html_template = Template(HTML_TEMPLATE)
            html_message = html_template.render(title=title,
                                                time=time,
                                                body=body,
                                                supplement=supplement)


            resp = send_mail(subject=title,
                             message='',
                             from_email=conf.DEFAULT_FROM_EMAIL,
                             recipient_list=self.to,
                             fail_silently=False,
                             html_message=html_message)
            logger.info(resp)

        except natrix_exceptions.ParameterException as e:
            raise natrix_exceptions.BaseException(err=e.get_log())
        except Exception as e:
            raise natrix_exceptions.BaseException('Error(send email): {}'.format(e))


class SmsNotify(Notify):

    def valid_message(self, message):
        content = message.get('body', None)
        if isinstance(content, basestring) and len(content) < 50:
            return True

        return False

    def notify(self, message):
        try:
            if not self.valid_message(message):
                raise natrix_exceptions.ParameterException(parameter='')
            for t in self.to:
                payload = {
                    'version': '3.0',
                    'batchId': time.time(),
                    'orgNo': conf.SMS_ORGNO,
                    'typeNo': conf.SMS_TYPENO,
                    'mobile': t,
                    'keywords': json.dumps({
                        'custName': message.get('body')
                    })
                }
                response = requests.post(conf.SMS_URL, data=payload)

                response.raise_for_status()

        except natrix_exceptions.ParameterException as e:
            raise natrix_exceptions.BaseException(err=e.get_log())
        except requests.RequestException as e:
            raise natrix_exceptions.BaseException(err='Error post')
        except Exception as e:
            raise natrix_exceptions.BaseException(err=str(e))


def get_notify_instance(type, to =[]):
    if type == 'email':
        return EmailNotify(to=to)
    elif type == 'sms':
        return SmsNotify(to=to)
    else:
        raise natrix_exceptions.ParameterInvalidException(parameter='notify type')
    

