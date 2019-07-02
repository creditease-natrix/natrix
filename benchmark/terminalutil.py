# -*- coding: utf-8 -*-
"""

"""
from __future__ import unicode_literals
import logging

from terminal.api.exports import terminalapi

logger = logging.getLogger(__name__)


# TODO: test
def terminal_policy(switch, conditions=None):
    """

    :param switch:
    :param conditions:
    :return:
    """
    terminals = []
    if not switch:
        alive_terminals = terminalapi.TerminalAPI.get_alive_terminals()
        # terminals is a list, witch item with ip and mac
        terminals = [t.address_info() for t in alive_terminals]
    else:
        if conditions['terminal_select']:
            for item in conditions['terminals']:
                try:
                    terminal = terminalapi.TerminalInfo(pk=item)
                    terminals.append(terminal.address_info())
                except Exception as e:
                    logger.error('The temrinal ({}) is not exist!'.format(item))
        else:
            filter_terminals = terminalapi.TerminalAPI.filter_available_terminals(
                type=conditions['filter_type'],
                filter_condition=conditions['filter_condition']
            )
            for item in filter_terminals:
                terminals.append(item.address_info())

    return terminals
