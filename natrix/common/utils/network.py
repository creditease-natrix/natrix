# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import IPy

class IPAddress(IPy.IP):

    def is_segment(self):
        if self._prefixlen != -1:
            return True
        else:
            return False

    def is_host(self):
        if self._prefixlen == -1:
            return True
        else:
            return False


class NetAddress(object):
    """Network Address

    """

    def __init__(self, ipaddr, netmask):
        """
        May raise ValueError exception.

        :param ipaddr:
        :param netmask:
        """
        self.ipaddr = IPy.IP(ipaddr)
        self.netaddr = self.ipaddr.make_net(netmask)

    def strNormal(self):
        return self.netaddr.strNormal()




