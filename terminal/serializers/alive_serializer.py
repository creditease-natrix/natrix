# -*- coding: utf-8 -*-

from __future__ import unicode_literals, absolute_import

import logging
import IPy
from collections import OrderedDict

from django.db import transaction
from django.core.cache import cache
from rest_framework import serializers

from natrix.common import exception as natrix_exception

from terminal.models import TerminalDevice, Terminal
from terminal.models import Organization
from terminal.models import terminal_type_choice

logger = logging.getLogger(__name__)


class NatrixClientSerializer(serializers.Serializer):
    """All Info:  natrix client

    """
    natrixclient_version = serializers.CharField(max_length=16)
    # natrixclient_crontab_version = serializers.CharField(max_length=16,
    #                                                      allow_null=True,
    #                                                      allow_blank=True)
    # natrixclient_dashboard_version = serializers.CharField(max_length=16,
    #                                                        allow_null=True,
    #                                                        allow_blank=True)


class BasicHardwareSerializer(serializers.Serializer):
    """Basic Info: hardware

    """
    sn = serializers.CharField(max_length=64)
    hostname = serializers.CharField(max_length=64, allow_blank=True, allow_null=True)
    cpu_percent = serializers.FloatField(min_value=0, allow_null=True)
    memory_percent = serializers.FloatField(min_value=0)
    disk_percent = serializers.FloatField(min_value=0)


class LocationSerializer(serializers.Serializer):
    """Networks item: location_info

    """
    country = serializers.CharField()
    region = serializers.CharField()
    province = serializers.CharField()
    city = serializers.CharField()
    isp = serializers.CharField()


class InterfaceSerializer(serializers.Serializer):
    """All Info: networks

    """
    type = serializers.ChoiceField(choices=terminal_type_choice)
    name = serializers.CharField(max_length=64)
    macaddress = serializers.CharField(max_length=64, allow_null=True)
    local_ip = serializers.IPAddressField(allow_null=True)
    local_location = LocationSerializer(required=False, allow_null=True)
    netmask = serializers.IPAddressField(allow_null=True)
    broadcast = serializers.IPAddressField(allow_null=True)
    gateway = serializers.IPAddressField(allow_null=True)
    is_default = serializers.NullBooleanField(default=False)
    public_ip = serializers.IPAddressField(allow_null=True)

    public_location = LocationSerializer(required=False, allow_null=True)

    access_intranet = serializers.BooleanField(default=False)
    access_corporate = serializers.BooleanField(default=False)
    access_internet = serializers.BooleanField(default=False)

    def to_representation(self, instance):
        if not isinstance(instance, Terminal):
           raise natrix_exception.ParameterInvalidException(parameter='instance')
        try:
            ret = OrderedDict()
            ret['type'] = instance.type
            ret['name'] = instance.name
            ret['macaddress'] = instance.mac
            ret['localip'] = instance.localip
            ret['netmask'] = instance.netmask
            ret['broadcast'] = instance.broadcast
            ret['gateway'] = instance.gateway
            ret['is_default'] = instance.is_default
            ret['publicip'] = instance.publicip
            ret['status'] = instance.status
            ret['is_active'] = instance.is_active
            ret['access_intranet'] = instance.access_intranet
            ret['access_corporate'] = instance.access_corporate
            ret['access_internet'] = instance.access_internet
            ret['location_info'] = {
                'country': instance.country,
                'region': instance.region,
                'province': instance.province,
                'city': instance.city,
                'isp': instance.isp,
            }

            return ret
        except Exception as e:
            logger.error('Serializer Interface info ERROR: {}'.format(e))
            raise natrix_exception.ClassInsideException(message=u'{}'.format(e))


class OperatingSerializer(serializers.Serializer):
    """Advance Info: operating system

    """
    type = serializers.CharField()
    series = serializers.CharField()
    name = serializers.CharField()
    codename = serializers.CharField()
    major_version = serializers.CharField()
    minor_version = serializers.CharField()
    kernel_version = serializers.CharField()
    architecture = serializers.CharField()
    platform = serializers.CharField()
    python_version = serializers.CharField()
    desktop_version = serializers.CharField()
    selenium_version = serializers.CharField()
    chrome_version = serializers.CharField()
    chrome_webdriver_path = serializers.CharField(allow_null=True, allow_blank=True)
    chrome_webdriver_version = serializers.CharField()
    firefox_version = serializers.CharField()
    firefox_webdriver_path = serializers.CharField(allow_null=True, allow_blank=True)
    firefox_webdriver_version = serializers.CharField()


class AdvanceSystemSerializer(serializers.Serializer):
    """Advance Info: system

    """
    operating = OperatingSerializer()
    natrixclient = NatrixClientSerializer()

    def to_representation(self, instance):
        """

        :param instance:
        :return:
        """
        if not isinstance(instance, TerminalDevice):
            logger.error('Serializer Hardware ERROR: {}'.format('instance is not a terminal device'))
            raise natrix_exception.ParameterInvalidException(parameter='instance')

        try:
            ret = OrderedDict()
            ret['os'] = u'[{}]-[{}]'.format(instance.os_type, instance.os_series)
            ret['os_name'] = instance.os_name
            ret['os_version'] = u'[{}]-[{}]'.format(instance.os_major_version, instance.os_minor_version)
            ret['os_kernel_version'] = instance.os_kernel_version
            ret['arch_info'] = instance.os_architecture
            ret['platform'] = instance.os_platform
            ret['python_version'] = instance.python_version
            ret['natrix_version'] = instance.natrixclient_version
            ret['chrome_version'] = instance.chrome_version
            ret['chrome_webdriver_version'] = instance.chrome_webdriver_version
            ret['firefox_version'] = instance.firefox_version
            ret['firefox_webdriver_version'] = instance.firefox_webdriver_version

            return ret
        except Exception as e:
            logger.error('Serializer OS info ERROR: {}'.format(e))
            raise natrix_exception.ClassInsideException(message='{}'.format(e))


class CpuInfoSerializer(serializers.Serializer):
    """CPU Info

    """
    cpu_model = serializers.CharField(allow_null=True, required=False)
    cpu_core = serializers.IntegerField(allow_null=True, required=False)
    cpu_percent = serializers.FloatField(allow_null=True, required=False)


class MemoryInfoSerializer(serializers.Serializer):
    """Memory Info

    """
    memory_total = serializers.IntegerField()
    memory_used = serializers.IntegerField()
    memory_percent = serializers.FloatField()

    memory_frequency = serializers.FloatField(required=False, allow_null=True)


class DiskInfoSerializer(serializers.Serializer):
    """Disk Info

    """
    disk_percent = serializers.FloatField()


class AdavnceHardwareSerializer(serializers.Serializer):
    """Advance Info: hardware

    """
    sn = serializers.CharField()
    hostname = serializers.CharField()
    product = serializers.CharField(allow_null=True)
    boot_time = serializers.IntegerField(min_value=0, help_text=u'启动时间（s)')
    cpu_info = CpuInfoSerializer()
    memory_info = MemoryInfoSerializer()
    disk_info = DiskInfoSerializer()

    def to_representation(self, instance):
        """

        :param instance:
        :return:
        """
        if not isinstance(instance, TerminalDevice):
            logger.error('Serializer Hardware ERROR: {}'.format('instance is not a terminal device'))
            raise natrix_exception.ParameterInvalidException(parameter='instance')
        try:
            ret = OrderedDict()
            ret['sn'] = instance.sn
            ret['hostname'] = instance.hostname
            ret['product'] = instance.product
            ret['boot_time'] = instance.boot_time
            ret['cpu_info'] = {
                'cpu_model': instance.cpu_model,
                'cpu_core': instance.cpu_core,
                'cpu_percent': instance.cpu_percent,
            }
            ret['memory_info'] = {
                'memory_total': instance.memory_total,
                'memory_used': instance.memory_used,
                'memory_percent': instance.memory_percent,
                'memory_frequency': instance.memory_frequency,
            }
            ret['disk_info'] = {
                'disk_percent': instance.disk_percent
            }

            return ret
        except Exception as e:
            logger.error('Serializer Hardware info ERROR: {}'.format(e))
            raise natrix_exception.ClassInsideException(message='{}'.format(e))


class BasicInfoSerializer(serializers.Serializer):
    """Basic Info

    """

    system = NatrixClientSerializer()
    hardware = BasicHardwareSerializer()
    networks = InterfaceSerializer(many=True)
    heartbeat = serializers.FloatField(min_value=0)

    def create(self, validated_data):
        """Update or create terminal-device and terminal info.

        :param validated_data:
        :return:
        """
        sn = validated_data.get('hardware').get('sn')
        natrixclient = validated_data.get('system')
        hardware = validated_data.get('hardware')
        networks = validated_data.get('networks')

        heartbeat = validated_data.get('heartbeat')

        try:
            with transaction.atomic():
                try:
                    terminal_device = TerminalDevice.objects.get(sn=sn)
                except TerminalDevice.DoesNotExist:
                    logger.info('The terminal device (SN): {} isnt exist'.format(sn))
                    raise natrix_exception.NatrixBaseException(err='The device is not exist')

                terminal_device.natrixclient_version = natrixclient.get('natrixclient_version')
                terminal_device.natrixclient_crontab_version = natrixclient.get('natrixclient_crontab_version')
                terminal_device.natrixclient_dashboard_version = natrixclient.get('natrixclient_dashboard_version')

                terminal_device.hostname = hardware.get('hostname')
                terminal_device.cpu_percent = hardware.get('cpu_percent')
                terminal_device.memory_percent = hardware.get('memory_percent')
                terminal_device.disk_percent = hardware.get('disk_percent')

                terminal_device.is_active = True
                terminal_device.save()

                update_networks(terminal_device, networks)

                terminal_device.save()

                return terminal_device
        except Exception as e:
            logger.error('Basic keep alive TRANSACTION exception {}'.format(e))
            raise natrix_exception.DatabaseTransactionException(model='Terminal related',
                                                                business='Basic Keep Alive')


class AdvanceInfoSerializer(serializers.Serializer):
    """Advance Info

    """
    system = AdvanceSystemSerializer()
    hardware = AdavnceHardwareSerializer()
    networks = InterfaceSerializer(many=True)
    heartbeat = serializers.FloatField(min_value=0)

    def create(self, validated_data):
        """Update or create terminal-device and terminal info.

        :param validated_data:
        :return:
        """
        sn = validated_data.get('hardware').get('sn', None)
        operating = validated_data.get('system').get('operating')
        natrixclient = validated_data.get('system').get('natrixclient')
        hardware = validated_data.get('hardware')
        networks = validated_data.get('networks')

        # TODO: check the post data is valid
        heartbeat = validated_data.get('heartbeat')
        try:
            with transaction.atomic():
                try:
                    terminal_device = TerminalDevice.objects.get(sn=sn)
                except TerminalDevice.DoesNotExist:
                    logger.info('The terminal device ({}) isnt exist'.format(sn))
                    raise natrix_exception.NatrixBaseException(err='The device is not exist')

                terminal_device.os_type = operating.get('type')
                terminal_device.os_series = operating.get('series')
                terminal_device.os_name = operating.get('name')
                terminal_device.os_codename = operating.get('codename')
                terminal_device.os_major_version = operating.get('major_version')
                terminal_device.os_minor_version = operating.get('minor_version')
                terminal_device.os_kernel_version = operating.get('kernel_version')
                terminal_device.os_architecture = operating.get('architecture')
                terminal_device.os_platform = operating.get('platform')
                terminal_device.python_version = operating.get('python_version')
                terminal_device.desktop_version = operating.get('desktop_version')
                terminal_device.selenium_version = operating.get('selenium_version')
                terminal_device.chrome_version = operating.get('chrome_version')
                terminal_device.chrome_webdriver_path = operating.get('chrome_webdriver_path')
                terminal_device.chrome_webdriver_version = operating.get('chrome_webdriver_version')
                terminal_device.firefox_version = operating.get('firefox_version')
                terminal_device.firefox_webdriver_path = operating.get('firefox_webdriver_path')
                terminal_device.firefox_webdriver_version = operating.get('firefox_webdriver_version')

                terminal_device.natrixclient_version = natrixclient.get('natrixclient_version')

                terminal_device.hostname = hardware.get('hostname')
                terminal_device.product = hardware.get('product')
                terminal_device.boot_time = hardware.get('boot_time')
                terminal_device.cpu_model = hardware.get('cpu_info').get('cpu_model')
                terminal_device.cpu_core = hardware.get('cpu_info').get('cpu_core')
                terminal_device.cpu_percent = hardware.get('cpu_info').get('cpu_percent')
                terminal_device.memory_total = hardware.get('memory_info').get('memory_total')
                terminal_device.memory_used = hardware.get('memory_info').get('memory_used')
                terminal_device.memory_percent = hardware.get('memory_info').get('memory_percent')
                terminal_device.memory_frequency = hardware.get('memory_info').get('memory_frequency')
                terminal_device.disk_percent = hardware.get('disk_info').get('disk_percent')

                terminal_device.save()

                update_networks(terminal_device, networks)

                terminal_device.save()


                return terminal_device
        except Exception as e:
            logger.error('Advance keep alive TRANSACTION exception {}'.format(e))
            raise natrix_exception.DatabaseTransactionException(model='Terminal related',
                                                                business='Advance Keep Alive')


def update_networks(device, networks):
    """Update Terminal Device networks info.

    The networks info relate with detective organizations.

    :return:
    """
    logger.info('update network!')
    if not isinstance(device, TerminalDevice):
        raise natrix_exception.ParameterException(parameter='device')

    if not isinstance(networks, list):
        raise natrix_exception.ParameterException(parameter='networks')

    for interface in networks:
        mac = interface.get('macaddress')

        try:
            terminal = Terminal.objects.get(mac=mac)
        except Terminal.DoesNotExist:
            terminal = Terminal.objects.create(mac=mac, status='active', dev=device)

        terminal.dev = device
        terminal.name = interface.get('name')
        terminal.type = interface.get('type')
        terminal.localip = interface.get('local_ip')
        terminal.netmask = interface.get('netmask')
        terminal.gateway = interface.get('gateway')
        terminal.publicip = interface.get('public_ip')
        terminal.is_default = interface.get('is_default')
        terminal.access_intranet = interface.get('access_intranet')
        terminal.access_corporate = interface.get('access_corporate')
        terminal.access_internet = interface.get('access_internet')


        if interface.get('access_intranet') or interface.get('access_corporate') or interface.get('access_internet'):
            terminal.is_active = True
        else:
            terminal.is_active = False

        terminal.save()



