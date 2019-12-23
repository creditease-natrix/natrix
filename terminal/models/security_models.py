# -*- coding: utf-8 -*-
"""

"""

import logging, random

from auditlog.registry import auditlog
from django.utils import timezone
from django.db import models, transaction
from django.contrib.auth.models import  Group

from natrix.common.utils.time_processor import time_timestamp
from natrix.common import exception as natrix_exception
from .common_models import HistorySave
from .terminal_models import TerminalDevice

logger = logging.getLogger(__name__)


def get_letter_set():
    letter_set = []
    for i in range(65, 91):
        letter_set.append(chr(i))
    for i in range(97, 123):
        letter_set.append(chr(i))
    for i in range(48, 58):
        letter_set.append(chr(i))
    return letter_set


letter_set = get_letter_set()


def license_key_generator(length=16):
    letter_length = len(letter_set)
    license_str = []
    # first character must be a letter
    license_str.append(letter_set[random.randint(0, 52-1)])
    while length > 0:
        random_index = random.randint(0, letter_length-1)
        license_str.append(letter_set[random_index])
        length -= 1
    return ''.join(license_str)


class AccessLicense(HistorySave):
    """

    """

    license_key = models.CharField(verbose_name='证书Key', max_length=64, primary_key=True)

    bind_device = models.ForeignKey(TerminalDevice, on_delete=models.SET_NULL, null=True,
                                    verbose_name='绑定设备')
    online = models.BooleanField(verbose_name='是否在线', default=False)

    group = models.ForeignKey(Group, verbose_name='隶属组', on_delete=models.CASCADE)

    create_time = models.DateTimeField(verbose_name='创建时间', default=timezone.now)
    update_time = models.DateTimeField(verbose_name='更新时间', auto_now=True)

    def get_status(self):
        if self.bind_device is None:
            return 'unbinding'
        else:
            return 'binding'

    def get_device_id(self):
        if self.bind_device:
            return self.bind_device.sn
        else:
            return None

    def get_bind_time(self):
        if self.bind_device is None:
            return None

        bind_record = BindingHistory.objects.filter(access_license=self, bind_device=self.bind_device).first()

        return time_timestamp(bind_record.bind_time)

    @staticmethod
    def to_bind_device(license_key, sn):
        try:
            with transaction.atomic():
                try:
                    license_instance = AccessLicense.objects.get(license_key=license_key)
                except AccessLicense.DoesNotExist:
                    license_instance = None

                try:
                    device_instance = TerminalDevice.objects.get(sn=sn)
                except TerminalDevice.DoesNotExist:
                    logger.debug('Add a new devices')
                    device_instance = TerminalDevice.objects.create(sn=sn, group=license_instance.group)

                if license_instance is None or device_instance is None:
                    logger.info('To binding device with errro: license({}) or '
                                'device({}) is not exist'.format(license_instance, device_instance))
                    raise natrix_exception.NatrixBaseException()

                if device_instance.group is None or device_instance.group != license_instance.group:
                    logger.debug('Set the device group ({})'.format(license_instance.group))
                    device_instance.group = license_instance.group
                    device_instance.clean_group_related_fields()

                    device_instance.save()

                # The binding-policy
                if license_instance.bind_device is None:
                    logger.debug('The license({}) is available which bind_device is None'.format(license_instance.license_key))
                    AccessLicense.unbinding_device(device_instance)

                    license_instance.bind_device = device_instance
                    license_instance.online = True
                    BindingHistory.objects.create(
                        access_license = license_instance,
                        bind_device = device_instance,
                        device_key = device_instance.sn
                    )
                    license_instance.save()

                else:
                    # reconnected
                    if license_instance.bind_device == device_instance:
                        license_instance.online = True
                        license_instance.save()
                    else:
                        logger.error('A device({}) want to bind a license({}) which is '
                                    'related with othe device'.format(sn, license_key))
                        raise natrix_exception.NatrixBaseException()
        except natrix_exception.NatrixBaseException as e:
            logger.error('bind device with natrix exception: {}'.format(e))
            return False
        except Exception as e:
            natrix_exception.natrix_traceback()
            logger.error('bind device with exception: {}'.format(e))
            return False

        return True

    @staticmethod
    def unbinding_device(device):
        """clean the license - device related

        :param device:
        :return:
        """
        related_license = AccessLicense.objects.filter(bind_device=device)
        for rl in related_license:
            rl.bind_device = None
            rl.save()

    @staticmethod
    def can_binding(license_key):
        try:
            license_instance = AccessLicense.objects.get(license_key=license_key)

        except AccessLicense.DoesNotExist:
            license_instance = None

        return license_instance

    @staticmethod
    def license_generator(group, count=1):
        instance_count = 0
        try:
            while count > 0:
                license_key = license_key_generator(length=16)
                try:
                    AccessLicense.objects.get(license_key=license_key)
                except AccessLicense.DoesNotExist:
                    AccessLicense.objects.create(license_key=license_key, group=group)
                    count -= 1
                    instance_count += 1
        except Exception as e:
            natrix_exception.natrix_traceback()
            logger.error(e)

        return instance_count

    @staticmethod
    def license_remove(license_key, group):
        """Delete the license

        :param license_key:
        :param group:
        :return:
        """

        with transaction.atomic():
            try:
                license_instance = AccessLicense.objects.get(license_key=license_key, group=group)
                if license_instance.bind_device:
                    license_instance.bind_device.delete()
                license_instance.delete()
                return True, 'Remove successfully'
            except AccessLicense.DoesNotExist:
                return False, 'Cant query the license.'


    class Meta:
        ordering = ['bind_device','update_time']


class BindingHistory(models.Model):

    access_license = models.ForeignKey(AccessLicense, on_delete=models.CASCADE)
    bind_device = models.ForeignKey(TerminalDevice, on_delete=models.SET_NULL, null=True,
                                    verbose_name='绑定设备')
    device_key = models.CharField(verbose_name='设备标识（用户设备注销）', max_length=128)

    bind_time = models.DateTimeField(verbose_name='创建时间', default=timezone.now)

    def __str__(self):
        return '{}-{}'.format(self.access_license, self.device_key)


class GroupLicenseACL(models.Model):
    group = models.ForeignKey(Group, verbose_name='控制组', on_delete=models.CASCADE)
    max_count = models.IntegerField(verbose_name='最大数量', default=10)

    @staticmethod
    def get_remaining_number(group):
        try:
            acl = GroupLicenseACL.objects.get(group=group)

            exist_acl_count = AccessLicense.objects.filter(group=group).count()
            remaining_acl_count = acl.max_count - exist_acl_count

            if remaining_acl_count < 0:
                logger.error('The current license count({}) is more than max count({}) for {}'.format(
                    exist_acl_count, acl.max_count, group))

                return 0
            return remaining_acl_count

        except GroupLicenseACL.DoesNotExist:
            acl = GroupLicenseACL.objects.create(group=group)
            return acl.max_count



    def __str__(self):
        return '{}-{}'.format(self.group, self.max_count)


auditlog.register(AccessLicense)
auditlog.register(BindingHistory)