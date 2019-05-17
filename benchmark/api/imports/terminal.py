# -*- coding: utf-8 -*-
"""

"""

from __future__ import unicode_literals, absolute_import

from terminal.api.exports import terminalapi


def get_terminal_info(mac):
    terminal_info = terminalapi.TerminalAPI.get_terminal_register_info(mac)

    return terminal_info

