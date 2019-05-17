# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging

from django.db import models

from terminal.configurations import organization_conf
from .common_models import HistorySave
from .address_models import Region, Address

logger = logging.getLogger(__name__)


choice_extract = lambda item: (item.get('name'), item.get('verbose_name'))

SEGMENT_TYPES = map(choice_extract, organization_conf.SEGMENT_TYPES_INFO.values())

NETWORK_TYPE = map(choice_extract, organization_conf.NETWORK_TYPE_INFO.values())

IDENTITY_TYPE = map(choice_extract, organization_conf.IDENTITY_TYPE_INFO.values())

BROADBAND = map(choice_extract, organization_conf.BROADBAND_INFO.values())

OPERATOR = map(choice_extract, organization_conf.OPERATOR_DICT.values())

EXPORT_TYPE = map(choice_extract, organization_conf.EXPORT_TYPE_INFO.values())

EXPORT_DEVICE_TYPE = map(choice_extract, organization_conf.EXPORT_DEVICE_TYPE_INFO.values())


class Contact(HistorySave):
    """组织（职场）联系人

    """
    name = models.CharField("联系人", max_length=50, null=False)
    telephone = models.CharField("联系人电话", max_length=50, null=True)
    email = models.EmailField("联系人移动邮箱", max_length=50, null=False)
    wechat = models.CharField("微信", max_length=50, null=True)
    comment = models.TextField("备注", max_length=1000, null=True)

    def __unicode__(self):
        return self.name


class Network(HistorySave):
    """组织（职场）网络信息

    """
    segment = models.CharField("职场网段", max_length=50, unique=True)
    gateway = models.GenericIPAddressField("职场网关", null=True)
    segment_type = models.CharField("网段类型", choices=SEGMENT_TYPES, default='mix', max_length=20)
    comment = models.TextField("备注", max_length=1000, null=True)

    @staticmethod
    def filter_networks(ip, netmask, gateway=None):
        pass


    def __unicode__(self):
        return self.segment


class Operator(HistorySave):
    """运营商

    """
    name = models.CharField(u'运营商名称', choices=OPERATOR, max_length=20)

    def verbose_name(self):
        for choice in OPERATOR:
            if choice[0] == self.name:
                return choice[1]
        return ''

    def __unicode__(self):
        return self.name


class Broadband(HistorySave):
    """组织（职场）宽带信息

    """
    name = models.CharField("宽带名称", max_length=20)
    operator = models.ForeignKey(Operator, on_delete=models.CASCADE)
    access_type = models.CharField("宽带接入类型", choices=BROADBAND, max_length=50)
    speed = models.IntegerField("速度", null=False)
    start_time = models.DateField("租期开始日期", null=True)
    end_time = models.DateField("租期结束日期", null=True)
    staff_contact = models.CharField("公司内部宽带负责人", max_length=20, null=True)
    staff_contact_email = models.CharField("公司内部宽带负责人邮箱", max_length=50, null=True)
    staff_contact_telephone = models.CharField("公司内部宽带负责人电话", max_length=50, null=True)
    isp_contact = models.CharField("运营商负责人", max_length=20, null=True)
    isp_contact_email = models.CharField("运营商负责人邮箱", max_length=50, null=True)
    isp_contact_telephone = models.CharField("运营商负责人电话", max_length=50, null=True)
    comment = models.CharField("备注", max_length=1000, null=True)

    def __unicode__(self):
        return self.name


class Export(HistorySave):
    """组织（职场）出口信息

    """
    type = models.CharField("出口类型", choices=EXPORT_TYPE, max_length=16)
    ip = models.GenericIPAddressField(protocol='ipv4')
    device = models.CharField("出口设备", max_length=100, choices=EXPORT_DEVICE_TYPE)
    comment = models.CharField("备注", max_length=1000, null=True)
    # 第一版原型定义时确定
    # organization = models.ForeignKey(Organization, on_delete=models.CASCADE)

    def __unicode__(self):
        return '{}-{}'.format(self.type, self.ip)


class Organization(HistorySave):
    """组织信息（源职场表）

    """
    name = models.CharField('组织名称', max_length=50)
    level = models.IntegerField('组织级别', default=0)
    parent = models.ForeignKey('self', verbose_name=u'父级组织', null=True)
    # TODO: restrict addresses region
    region = models.ForeignKey(Region, verbose_name=u'组织区域', null=True)
    addresses = models.ManyToManyField(Address, through='OrganizationAddress')
    contacts = models.ManyToManyField(Contact, through='OrganizationContact')
    networks = models.ManyToManyField(Network, through='OrganizationNetwork')
    broadbands = models.ManyToManyField(Broadband, through='OrganizationBroadBand')
    exports = models.ManyToManyField(Export, verbose_name=u'出口信息', blank=True)
    comment = models.TextField("备注", max_length=1000, null=True)

    '''
    得到自己的子组织
    '''
    def get_children(self):
        children = Organization.objects.filter(parent=self)
        return children

    def get_full_name(self):
        org_name = []
        curr_org = self
        while curr_org.level > 0:
            org_name.insert(0, curr_org.name)
            curr_org = curr_org.parent
        return ' | '.join(org_name)

    def get_fullname_list(self, top_level=1):
        org_name = []
        curr_org = self
        while curr_org.level >= top_level:
            org_name.append(curr_org.name)
            curr_org = curr_org.parent
        org_name.reverse()
        return org_name

    def get_org_relation(self):
        org_list = []

        curr_org = self
        while curr_org.parent:
            org_list.append(curr_org)
            curr_org = curr_org.parent
        org_list.append(curr_org)

        org_list.reverse()
        return org_list

    def get_all_tree_nodes(self):
        orgs = set([self])
        pre_orgs = set([self])
        while len(pre_orgs) > 0:
            children = Organization.objects.filter(parent__in=pre_orgs)
            orgs.update(children)
            pre_orgs = set(children)

        return orgs


    def parent_full_name(self):
        if self.parent:
            return self.parent.get_full_name()
        else:
            return u''


    class Meta:
        ordering = ['level', 'name']


    '''
    得到当前组织下所有的联系人
    '''
    def get_contacts(self):
        return self.contacts.all()

    '''
    得到当前组织下联系人数量
    '''
    def get_contacts_num(self):
        return len(self.contacts.all())

    '''
    获取当前组织下的所有宽带信息
    '''
    def get_broadbands(self):
        return self.broadbands.all()

    '''
    得到当前组织下所有的网络信息
    '''
    def get_networks(self):
        return self.networks.all()

    '''
    得到当前组织下网络信息数量
    '''
    def get_networks_num(self):
        return len(self.networks.all())

    '''
    得到当前组织下所有的地址信息
    '''
    def get_addresses(self):
        return self.addresses.all()

    def get_region(self):
        """Get organization region info.


        :return:
        """
        pass

    '''
    获取当前组织下的所有出口信息
    '''
    def get_exports(self):
        exports = Export.objects.filter(organization=self)
        return exports

    def to_python(self):
        pass

    def __unicode__(self):
        return self.name


class OrganizationContact(HistorySave):
    """组织与组织联系人关联表

    """
    contact = models.ForeignKey(Contact, on_delete=models.CASCADE)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    # user-普通用户, admin-管理员
    identity = models.CharField("人员职能", choices=IDENTITY_TYPE, max_length=50, default="user")

    def __unicode__(self):
        return '{}-{}-{}'.format(self.organization, self.identity, self.contact)


class OrganizationNetwork(HistorySave):
    """组织与网络信息关联表

    """
    network = models.ForeignKey(Network, on_delete=models.CASCADE)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)

    def __unicode__(self):
        return '{}-{}'.format(self.network, self.organization)


class OrganizationAddress(HistorySave):
    """组织与地址关联表

    """
    address = models.ForeignKey(Address, on_delete=models.CASCADE)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    comment = models.TextField(verbose_name=u'备注', default=u'', null=True)

    def __unicode__(self):
        return '{}-{}'.format(self.organization, self.address)


class OrganizationBroadBand(HistorySave):
    """组织与宽带信息关联表

    """
    broadband = models.ForeignKey(Broadband, on_delete=models.CASCADE)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)

    def __unicode__(self):
        return '{}-{}'.format(self.broadband, self.organization)