# -*- coding: utf-8 -*-
"""

"""
from __future__ import unicode_literals, absolute_import

from benchmark.api.imports import terminal as terminal_api



class TerminalAPI(object):

    def __init__(self, mac):
        self.mac = mac
        self.register_info = terminal_api.get_terminal_info(mac)

        if self.register_info is None:
            self.register_orgs = []
            self.register_isp = ''
            self.register_region = None
        else:
            self.register_orgs = list(self.register_info.get('organizations', []))
            self.register_isp = self.register_info.get('isp', '')
            self.register_region = self.register_info.get('region', None)

    def get_register_orgs(self):
        return self.register_orgs

    def get_register_isp(self):
        return '' if self.register_isp is None else self.register_isp

    def get_org_ids(self):
        return map(lambda x: x['id'], self.register_orgs)

    def get_org_names(self):
        return map(lambda x: x['name'], self.register_orgs)

    def get_register_province(self):
        if self.register_region is None:
            return ''
        else:
            return self.register_region.get('province', '')

    def get_register_city(self):
        if self.register_region is None:
            return ''
        else:
            return self.register_region.get('city', '')









