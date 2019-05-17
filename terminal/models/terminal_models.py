# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging

from django.utils import timezone
from django.db import models, transaction

from natrix.common.utils import network
from natrix.common import exception as natrix_exception

from terminal.configurations.terminal_conf import NETWORK_TYPE_INFO, DEVICE_STATUS, TERMINAL_STATUS
from .address_models import Address
from .organization_models import Organization, HistorySave


logger = logging.getLogger(__name__)

choice_generator = lambda x : (x['name'], x['verbose_name'])

terminal_type_choice = map(choice_generator, NETWORK_TYPE_INFO.values())
terminal_status_choice = map(choice_generator, TERMINAL_STATUS.values())
device_status_choice = map(choice_generator, DEVICE_STATUS.values())


status_order = {
    'active': 0,
    'posting': 10,
    'maintain': 20
}

class PostOperator(HistorySave):
    """Terminal Post Operator.


    """
    name = models.CharField(verbose_name=u'运营商', max_length=64)

    def __unicode__(self):
        return u'{}'.format(self.name)


class RegisterOrganization(HistorySave):
    """Register Organization

    User can register a terminal device with some organizations, the address is optional.


    """
    organizations = models.ManyToManyField(Organization, verbose_name=u'组织',
                                          help_text=u'手动注册的职场')
    address = models.ForeignKey(Address, verbose_name=u'地址', on_delete=models.CASCADE, null=True)
    comment = models.TextField(verbose_name=u'备注', blank=True)

    def __unicode__(self):
        return u'{}-{}'.format(self.pk, self.address)

    def get_region(self):
        if self.address is not None:
            return self.address.region

        return self.organizations.region


class TerminalDevice(HistorySave):
    """监测设备

    """
    sn = models.CharField(verbose_name=u'设备序列号', max_length=128, primary_key=True)
    hostname = models.CharField(verbose_name=u'主机名', max_length=64, null=True)
    product = models.CharField(verbose_name=u'产品', max_length=128, null=True)
    boot_time = models.FloatField(verbose_name=u'运行时间', default=0)

    # cpu info
    cpu_model = models.CharField(verbose_name=u'CPU型号', max_length=128, null=True)
    cpu_core = models.IntegerField(verbose_name=u'CPU核数', default=0)
    cpu_percent = models.FloatField(verbose_name=u'CPU使用率（%）', default=0)

    # memory info
    memory_total = models.BigIntegerField(verbose_name=u'内存大小（Byte）', default=0)
    memory_used = models.BigIntegerField(verbose_name=u'内存使用量（Byte）', default=0)
    memory_percent = models.FloatField(verbose_name=u'内存使用率（%）', default=0)
    memory_frequency = models.FloatField(verbose_name=u'内存主频', null=True)

    # disk info
    disk_percent = models.FloatField(verbose_name=u'磁盘使用率（%）', default=0)

    # status info
    status = models.CharField(verbose_name=u'状态', choices=device_status_choice,
                              max_length=16, default='active')
    is_active = models.BooleanField(verbose_name=u'是否活跃', default=False)
    device_alert = models.BooleanField(verbose_name=u'是否对设备告警', default=True)
    terminal_alert = models.BooleanField(verbose_name=u'是否对终端告警', default=False)

    # # related terminals
    # terminals = models.ManyToManyField(Terminal, verbose_name=u'关联监测点')

    # system
    os_type = models.CharField(verbose_name=u'操作系统类型', max_length=64, null=True)
    os_series = models.CharField(verbose_name=u'操作系统系列', max_length=64, null=True)
    os_name = models.CharField(verbose_name=u'操作系统名称', max_length=64, null=True)
    os_codename = models.CharField(verbose_name=u'操作系统发行代号', max_length=64, null=True)
    os_major_version = models.CharField(verbose_name=u'操作系统主版本', max_length=64, null=True)
    os_minor_version = models.CharField(verbose_name=u'操作系统次版本', max_length=64, null=True)
    os_kernel_version = models.CharField(verbose_name=u'操作系统内核版本', max_length=64, null=True)
    os_architecture = models.CharField(verbose_name=u'操作系统架构信息', max_length=64, null=True)
    os_platform = models.CharField(verbose_name=u'综合平台信息', max_length=128, null=True)

    python_version = models.CharField(verbose_name=u'Python版本', max_length=128, null=True)
    desktop_version = models.CharField(verbose_name=u'桌面版本', max_length=128, null=True)

    selenium_version = models.CharField(verbose_name=u'selenium版本', max_length=128, null=True)
    chrome_version = models.CharField(verbose_name=u'Chrome版本', max_length=128, null=True)
    chrome_webdriver_path = models.CharField(verbose_name=u'Chrome驱动路径', max_length=256, null=True)
    chrome_webdriver_version = models.CharField(verbose_name=u'Chrome驱动版本', max_length=128, null=True)
    firefox_version = models.CharField(verbose_name=u'Firefox版本', max_length=128, null=True)
    firefox_webdriver_path = models.CharField(verbose_name=u'Firefox驱动路径', max_length=256, null=True)
    firefox_webdriver_version = models.CharField(verbose_name=u'Firefox驱动版本', max_length=128, null=True)

    natrixclient_version = models.CharField(verbose_name=u'Natrix客户端版本', max_length=128, null=True)

    organizations = models.ManyToManyField(Organization, verbose_name=u'检测组织',
                                          related_name="auto_organization", blank=True,
                                           help_text=u'通过网络信息监测到的职场')
    register = models.ForeignKey(RegisterOrganization,
                                 verbose_name=u'职场注册',
                                 null=True,
                                 on_delete=models.SET_NULL,
                                 help_text=u'职场注册信息')

    comment = models.TextField("备注", default=u'')

    first_online_time = models.DateTimeField("上线时间", auto_now_add=True, editable=True)
    last_online_time = models.DateTimeField("更新时间", auto_now=True)

    def get_orgname_list(self):
        """终端设备关联的组织信息

        :return:
        """
        orgs = self.register.organizations.all()
        reg_org_list = []
        for org in orgs:
            reg_org_list.append(org.get_fullname_list())

        return reg_org_list

    def get_org_list(self):
        if self.register is None:
            return []

        reg_org_list = []
        orgs = self.register.organizations.all()
        for org in orgs:
            reg_org_list.append(org.get_org_relation())

        return reg_org_list

    def get_region(self):
        """Get terminal device region info.

        :return:
        """
        if self.register is None or self.register.address is None:
            return None, None


        region = self.register.address.region

        if region is None:
            return None, None
        else:
            return region.province, region.city

    def is_register(self):
        """

        :return:
        """
        if self.register and self.register.organizations.count() > 0:
            return True
        else:
            return False

    def status_change(self, status):
        if status in ('active', 'maintain'):
            terminal_status = status
        elif status in ('posting'):
            terminal_status = 'active'
        else:
            logger.error('Configure terminal deivce status with an error status ({})'.format(status))
            raise natrix_exception.ClassInsideException(
                message='models.TerminalDevice.status_change with an error parameter(status={})'.format(status))
        with transaction.atomic():
            self.status = status
            terminals = self.terminal_set.all()
            for terminal in terminals:
                terminal.status = terminal_status
                terminal.save()
            self.save()

    def dead_change(self):
        with transaction.atomic():
            self.is_active = False
            self.save()
            terminals = self.terminal_set.all()
            for t in terminals:
                t.is_active = False
                t.save()

    def is_available(self):
        if self.is_active and self.status == 'active':
            return True
        else:
            return False

    def get_available_terminals(self):
        """Get all available terminals of this device.

        :return:
        """
        return Terminal.objects.filter(dev=self, is_active=True, status='active')

    @staticmethod
    def get_available_devices():
        """

        :return:
        """
        return TerminalDevice.objects.filter(is_active=True, status='active')

    @staticmethod
    def status_cmp(pre, next):
        """

        :param pre:
        :param next:
        :return:
        """
        return status_order.get(pre.status, 100) - status_order.get(next.status, 100)

    @staticmethod
    def online_time_cmp(pre, next):
        if pre.last_online_time > next.last_online_time:
            return 1
        else:
            return -1

    def get_terminals(self):
        terminals = self.terminal_set.all()
        return list(terminals)

    def __unicode__(self):
        return u'{}-{}'.format(self.hostname, self.sn)

    class Meta:
        ordering = ['-first_online_time']


class Terminal(HistorySave):
    """监测点信息

    """

    mac = models.CharField(verbose_name=u'监测点MAC地址', unique=True, max_length=32)
    dev = models.ForeignKey(TerminalDevice, verbose_name=u'关联设备',
                            on_delete=models.CASCADE, null=True)

    name = models.CharField(verbose_name=u'名称', max_length=32)
    type = models.CharField(verbose_name=u'监测点上网方式', choices=terminal_type_choice,
                            max_length=16, default='wired')
    localip = models.CharField(verbose_name=u'网卡IP', max_length=50, null=True)
    netmask = models.CharField(verbose_name=u'子网掩码', max_length=50, null=True)
    gateway = models.CharField(verbose_name=u'默认网关', max_length=50, null=True)
    publicip = models.CharField(verbose_name=u'公网IP', max_length=50, null=True)
    broadcast = models.CharField(verbose_name=u'广播地址', max_length=50, null=True)

    country = models.CharField(verbose_name=u'国家', max_length=64, null=True)
    region = models.CharField(verbose_name=u'地区', max_length=64, null=True)
    province = models.CharField(verbose_name=u'省份', max_length=64, null=True)
    city = models.CharField(verbose_name=u'城市', max_length=64, null=True)
    isp = models.CharField(verbose_name=u'运营商', max_length=64, null=True)

    is_default = models.BooleanField(verbose_name=u'默认检测点', default=False)
    access_intranet = models.BooleanField(verbose_name=u'内网访问能力', default=False)
    access_corporate = models.BooleanField(verbose_name=u'企业网访问能力', default=False)
    access_internet = models.BooleanField(verbose_name=u'互联网访问能力', default=False)

    status = models.CharField(verbose_name=u'状态', choices=terminal_status_choice,
                              max_length=16, null=True)
    is_active = models.BooleanField(verbose_name=u'是否活跃', default=False)

    operator = models.ForeignKey(PostOperator, verbose_name=u'运营商', null=True)

    create_time = models.DateTimeField("创建时间", default=timezone.now)
    update_time = models.DateTimeField("更新时间", auto_now=True)


    def is_valid(self):
        """

        :return:
        """
        if self.status == 'active' and isinstance(self.dev, TerminalDevice):
            return True
        else:
            return False

    def is_alive(self):
        if self.status == 'active' and self.is_active:
            return True
        else:
            return False

    def get_segment(self):
        """Get terminal segment.

        A terminal equals an interface of device.

        :return:
        """
        if not (self.localip and self.netmask):
            return None
        try:
            ip_obj = network.IPAddress(self.localip)
            return str(ip_obj.make_net(self.netmask))
        except ValueError as e:
            logger.error(e)
            return None
        except Exception as e:
            logger.error(e)
            return None

        return None

    @staticmethod
    def status_cmp(pre, next):
        """

        :param pre:
        :param next:
        :return:
        """
        return status_order.get(pre.status, 100) - status_order.get(next.status, 100)

    @staticmethod
    def update_time_cmp(pre, next):
        if pre.update_time > next.update_time:
            return 1
        else:
            return -1
    @staticmethod
    def active_cmp(pre, next):

        return next.is_active - pre.is_active

    def __unicode__(self):
        return u'{}-{}-{}'.format(self.mac, self.localip, self.status)

    class Meta:
        ordering = ['-create_time']








