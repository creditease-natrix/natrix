# -*- coding: utf-8 -*-
"""组织信息迁移脚本

将原raspi.models.WorkPlace中定义的workplace迁移到terminal.model.Organization中
NOTE:
    增加一个一级的宜信公司组织，其他所有的组织结构放在该组织下；
    确定线上是否存在（二版）职场管理数据。

"""
from __future__ import unicode_literals
import logging

from django.db import transaction

from raspi.models import WorkPlace

from terminal.models import Organization
from terminal.models import Region, Address, OrganizationAddress
from terminal.models import Network, OrganizationNetwork
from terminal.models import Contact, OrganizationContact

logger = logging.getLogger(__name__)


with transaction.atomic():
    preroot = Organization.objects.get(id=1)

    # 获取当前根组织
    try:
        root = Organization.objects.get(level=1, name=u'宜信公司')
    except Organization.DoesNotExist:
        root = Organization.objects.create(
            name= u'宜信公司',
            level=1,
            parent=preroot,
            comment=u'宜信公司'
        )

    workplaces = WorkPlace.objects.all()

try:
    for wp in workplaces:
        orgnames = []
        orgnames.append(wp.level1)
        orgnames.append(wp.level2)
        orgnames.append(wp.level4)
        orgnames.append(wp.level5)

        # 区域信息：未在未配置省市信息的职场
        province = wp.province if wp.province else u'未知'
        city = wp.city if wp.city else u'未知'
        address = wp.address

        # 网络管理信息
        segment = wp.worknet
        gateway = wp.worknetgateway

        # 联系人信息
        name = wp.contact
        telephone = wp.contact_mobi
        email = wp.contact_email

        # 根组织
        currorg = root

        with transaction.atomic():
            # 标识组织是最新创建，还是已存在
            flag = None
            # 创建组织
            for orgname in orgnames:
                try:
                    currorg = currorg.get_children().get(name=orgname)
                    flag = False
                except Organization.DoesNotExist:
                    currorg = Organization.objects.create(
                        name = orgname,
                        level = currorg.level + 1,
                        parent = currorg,
                        comment = u'同步Raspi数据'
                    )
                    flag = True
                except Organization.MultipleObjectsReturned:
                    print u'在同一组织内，存在同名的组织： {}'.format(orgname)
                    raise Exception()
            if flag:
                print 'Organization({}) is exist! '.format(' | '.join(orgnames))

            # 新添加的组织
            if True:
                # migrate address info from raspi
                regions = Region.objects.filter(province__contains=province).filter(city__contains=city)
                if regions.count() == 0:
                    print '发现未知区域({})： {}-{}'.format(orgnames, province, city)
                    raise Exception('区域规则异常')
                elif regions.count() > 1:
                    print u'区域迁移规则异常({})： {}-{}'.format(orgnames, province, city)

                    raise  Exception('区域规则异常')

                try:
                    address_obj = Address.objects.get(region=regions[0], address=address)
                except Address.DoesNotExist:
                    address_obj = Address.objects.create(
                        region=regions[0],
                        address=address
                    )
                except Address.MultipleObjectsReturned:
                    print u'存在多个地址数据{}'.format(address)
                    raise Exception('存在多个地址数据')
                try:
                    OrganizationAddress.objects.get(address=address_obj,organization=currorg)
                except OrganizationAddress.DoesNotExist:
                    OrganizationAddress.objects.create(address=address_obj,
                                                       organization=currorg,
                                                       comment=u'同步Raspi数据')
                # migrate network info from raspi
                if segment:
                    try:
                        # TODO: 校验网段数据的正确性
                        network_obj = Network.objects.get(segment=segment)
                        if network_obj.gateway != gateway:
                            print u'导入过程中存在不一致的网段配置信息：（{}-源数据备注）-（{}-导入网关）'.format(
                                network_obj.comment,
                                gateway
                            )
                    except Network.DoesNotExist:
                        network_obj = Network.objects.create(
                            segment=segment,
                            gateway=gateway,
                            segment_type='wired',
                            comment=u'同步Raspi数据'
                        )
                    except Network.MultipleObjectsReturned:
                        print u'存在多个网段{}'.format(segment)
                        raise Exception('存在多个网段')
                    try:
                        OrganizationNetwork.objects.get(network=network_obj,
                                                        organization=currorg)
                    except OrganizationNetwork.DoesNotExist:
                        OrganizationNetwork.objects.create(network=network_obj,
                                                           organization=currorg)

                if email:
                    try:
                        contact_obj = Contact.objects.get(email=email)

                    except Contact.DoesNotExist:
                        contact_obj = Contact.objects.create(
                            name=name,
                            telephone=telephone,
                            email=email,
                            comment=u'同步Raspi数据'
                        )
                    except Contact.MultipleObjectsReturned:
                        print u'存在多个联系人：{}'.format(email)
                        raise Exception('存在多个联系人信息')
                    try:
                        OrganizationContact.objects.get(
                            contact=contact_obj,
                            organization=currorg,
                            identity='user'
                        )
                    except OrganizationContact.DoesNotExist:
                        OrganizationContact.objects.create(
                            contact=contact_obj,
                            organization=currorg,
                            identity='user'
                        )
                else:
                    print u'无联系人信息: {} | {} | {}'.format(orgnames, email, name)

except Exception as e:
    print e.message
    print 'an exception happen'









