# -*- coding: utf-8 -*-

from __future__ import unicode_literals, absolute_import

from infrastructure.api.exports.messenger import NotifyAPI


def send_email(destinations, application, title, body, level='critical', description='Alert', supplement=''):
    """Email sending API


    :param destinations: A list of emails.
    :param application:
    :param title:
    :param body: string, a section of html.
    :param description: string, describe this action.
    :param supplement: string( optional ), a section of html.
    :return:
    """
    # TODO: optimize coding

    try:
        NotifyAPI.add_email(destinations, application, title, level,
                            description=description,
                            content={'body': body,
                                     'supplement': supplement})
        return True
    except Exception as e:
        print 'send email : {}'.format(e)
        return False
