# -*- coding: utf-8 -*-
"""

"""
from __future__ import unicode_literals

from django.db.models import Q

from natrix.common import exception as natrix_exceptions

from terminal.serializers import common_serializer
from terminal.models import Terminal

# 有效的端版本
TERMINAL_VALID_VERSION = 0.35


class TerminalInfo(object):
    """Terminal Object (export)


    """

    def __init__(self, pk=None, instant=None):
        if not (instant is None):
            if isinstance(instant, Terminal):
                self.instant = instant
                return
            else:
                raise natrix_exceptions.ParameterInvalidException(parameter='instant')

        if pk:
            try:
                self.instant = Terminal.objects.get(mac=pk)
            except Terminal.DoesNotExist:
                raise natrix_exceptions.ParameterInvalidException(parameter='pk')
        else:
            raise natrix_exceptions.ParameterMissingException(parameter='pk or instant')

    def info(self):
        """get a terminal information

        Terminal Info:
         - pk, terminal mac address (the terminal primary key)
         - type, terminal type, network type, include wire, wireless, mobile
         - ip, an accessible ip address in local network
         - organizations, a list of organizations witch registry in terminal device

        :return: dict
        """
        terminal_data = {
            'pk': self.instant.mac,
            'type': self.instant.type,
            'ip': self.instant.localip,
            'organizations': (
                [{'id': org.id,
                  'fullname': '<->'.join(org.get_full_name())
                  } for org in self.instant.dev.register.organizations]
                if self.instant.dev.register else []
            )
        }
        return terminal_data

    def address_info(self):
        info = {
            'mac': self.instant.mac,
            'ip': self.instant.localip
        }
        return info


class TerminalAPI(object):
    """客户端接口代码

    """

    def __init__(self):
        pass

    @staticmethod
    def get_alive_terminals():
        """

        Alive Terminal: The terminal is active and alive, and the related terminal device is active
        and alive.

        :return: a list of TerminalInfo instant.
        """
        terminals = Terminal.objects.filter(Q(is_active=True) &
                                            Q(status='active') &
                                            Q(dev__is_active=True) &
                                            Q(dev__status='active'))

        return [TerminalInfo(instant=t) for t in terminals]

    @staticmethod
    def get_terminal_register_info(mac):
        """Get terminal register info

        :param mac:
        :return:
        """
        try:
            terminal = Terminal.objects.get(mac=mac)
            register = terminal.dev.register if terminal.dev else None

            if register is None:
                return None

            address = register.address
            organizations = register.organizations.all()
            register_info = {
                'organizations': [],
                'region': None,
                'isp': terminal.isp
            }

            region = address.region if address.region else None
            if region is None:
                register_info['region'] = None
            else:
                register_info['region'] = {
                    'province': region.province,
                    'city': region.city
                }

            for org in organizations:
                register_info['organizations'].append({
                    'id': org.id,
                    'name': org.get_full_name()
                })
            return register_info

        except Terminal.DoesNotExist:
            return None

    @staticmethod
    def filter_available_terminals(type, filter_condition):
        filter_data = {
            'type': type,
            'is_classify': False,
            'filter_condition': filter_condition
        }

        serializer = common_serializer.TerminalFilterSerializer(data=filter_data)

        if serializer.is_valid():
            terminals = serializer.query_result()[0].get('terminals', [])
            return [TerminalInfo(pk=t['value']) for t in terminals]
        else:
            raise natrix_exceptions.ClassInsideException(
                message='Filter available terminals: {}'.format(serializer.format_errors()))


def get_terminalinfo(pk):
    """Get a terminal info instant

    :param pk:
    :return:
    """
    return TerminalInfo(pk=pk)







