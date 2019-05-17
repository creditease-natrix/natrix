# -*- coding: utf-8 -*-
"""设备信息迁移脚本

将原raspi.models.PiInfo迁移到terminal.models.terminal.Terminal/TerminalDevice

NOTE:
    该迁移目前将丢失：位置和ISP信息（country, area, region, city, county, isp），
                    状态信息（ping_status, access_internet, access_corporate, access_intranet）

"""

from __future__ import unicode_literals

from django.db import transaction

from raspi.models import PiInfo

from terminal.models import Terminal, TerminalDevice
from terminal.models import Organization


terminal_converse = {
    'mac': 'macaddress',
    'localip': 'localip',
    'netmask': 'netmask',
    'gateway': 'gateway',
    'publicip': 'publicip',
    'status': 'status'
}

terminal_device_converse = {
    'hostname': 'hostname',
    'cpu': 'cpu',
    'cpu_usage': 'cpu_usage',
    'memory': 'memory',
    'memory_usage': 'memory_usage',
    'disk': 'disk',
    'disk_usage': 'disk_usage',
    'boot_time': 'boot_time',
    'hardware_version': 'hardware_version',
    'system': 'system',
    'version_name': 'version_name',
    'version_number': 'version_number',
    'kernel_version': 'kernel_version',
    'arch_version': 'arch_version',
    'python_version': 'python_version',
    'django_version': 'django_version',
    'piclient_version': 'piclient_version',
    'piclient_version_code': 'piclient_version_code',
    'purchase_time': 'purchase_time',
    'first_online_time': 'firstonlinetime',
    'last_online_time': 'lastonlinetime',
    'comment': 'comment'
}

piinfos = PiInfo.objects.all()
orgs = Organization.objects.filter(level=5)
orgs_dict = {}

for org in orgs:
    names = []
    level = 4
    temp = org
    while level > 0:
        names.insert(0, temp.name)
        temp = temp.parent
        level -= 1
    orgs_dict['<->'.join(names)] = org

try:
    for pi in piinfos:
        with transaction.atomic():
            # 增加监测点
            terminal_data = {}
            for k,v in terminal_converse.items():
                terminal_data[k] = getattr(pi, v)
            terminal_data['network_type'] = 'wired'

            try:
                terminal = Terminal.objects.get(mac=pi.macaddress)
                if terminal.localip != pi.localip or terminal.gateway != pi.gateway:
                    print u'存在冲突数据{}'.format(pi.macaddress)
                    raise  Exception(u'存在冲突数据'.format(pi.macaddress))

            except Terminal.DoesNotExist:
                terminal = Terminal.objects.create(**terminal_data)
            except Terminal.MultipleObjectsReturned:
                print u'存在多个监测点{}'.format(pi.macaddress)
                raise Exception(u'存在多个监测点{}'.format(pi.macaddress))

            # 增加检测设备
            terminal_device_data = {}
            for k,v in terminal_device_converse.items():
                terminal_device_data[k] = getattr(pi, v)

            hostname = pi.hostname
            try:
                device = TerminalDevice.objects.get(hostname=hostname)
                print '设备已存在暂时不进行创建'
            except TerminalDevice.DoesNotExist:
                workplace = pi.workplace
                regworkplace = pi.regworkplace

                if workplace:
                    wpname = '{}<->{}<->{}<->{}'.format(workplace.level1,
                                                        workplace.level2,
                                                        workplace.level4,
                                                        workplace.level5)
                else:
                    wpname = None

                if regworkplace:
                    regwpname = '{}<->{}<->{}<->{}'.format(regworkplace.level1,
                                                           regworkplace.level2,
                                                           regworkplace.level4,
                                                           regworkplace.level5)
                else:
                    regwpname = None

                terminal_device_data['organization'] = orgs_dict.get(wpname, None)
                terminal_device_data['reg_organization'] = orgs_dict.get(regwpname, None)
                terminal_device_data['uuid'] = hostname
                terminal_device = TerminalDevice.objects.create(**terminal_device_data)

                terminal.terminal_device = terminal_device
                terminal.save()

        print 'complete terminal create …………'

except Exception as e:
    print e.message



