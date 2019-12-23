# -*- coding: utf-8 -*-
"""

"""
import logging

from django.db import models
from django.contrib.auth.models import Group

from terminal.configurations import organization_conf
from .common_models import HistorySave
from .address_models import Region, Address

logger = logging.getLogger(__name__)


choice_extract = lambda item: (item.get('name'), item.get('verbose_name'))

SEGMENT_TYPES = list(map(choice_extract, organization_conf.SEGMENT_TYPES_INFO.values()))

NETWORK_TYPE = list(map(choice_extract, organization_conf.NETWORK_TYPE_INFO.values()))

IDENTITY_TYPE = list(map(choice_extract, organization_conf.IDENTITY_TYPE_INFO.values()))

OPERATOR = list(map(choice_extract, organization_conf.OPERATOR_DICT.values()))


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

    def __str__(self):
        return '{}({})'.format(self.name, self.pk)


class Organization(HistorySave):
    """组织信息（源职场表）

    """
    name = models.CharField('组织名称', max_length=50)
    level = models.IntegerField('组织级别', default=0)
    parent = models.ForeignKey('self', verbose_name=u'父级组织', null=True, on_delete=models.CASCADE)
    # TODO: restrict addresses region
    region = models.ForeignKey(Region, verbose_name=u'组织区域', null=True, on_delete=models.SET_NULL)
    addresses = models.ManyToManyField(Address, through='OrganizationAddress')
    contacts = models.ManyToManyField(Contact, through='OrganizationContact')
    comment = models.TextField("备注", max_length=1000, null=True)

    group = models.ForeignKey(Group, on_delete=models.CASCADE, null=True)

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

    def get_contacts(self):
        return self.contacts.all()

    def get_contacts_num(self):
        return len(self.contacts.all())

    def get_addresses(self):
        return self.addresses.all()

    def get_addresses_info(self):
        addresses = self.addresses.all()
        return [addr.address_desc() for addr in addresses]

    def get_region(self):
        """Get organization region info.


        :return:
        """
        pass

    def to_python(self):
        pass

    class Meta:
        ordering = ['level', 'name']

    def __unicode__(self):
        return self.name

    def __str__(self):
        return '{}({})'.format(self.name, self.pk)


class OrganizationContact(HistorySave):
    """组织与组织联系人关联表

    """
    contact = models.ForeignKey(Contact, on_delete=models.CASCADE)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    # user-普通用户, admin-管理员
    identity = models.CharField("人员职能", choices=IDENTITY_TYPE, max_length=50, default="user")

    def __unicode__(self):
        return '{}-{}-{}'.format(self.organization, self.identity, self.contact)


class OrganizationAddress(HistorySave):
    """组织与地址关联表

    """
    address = models.ForeignKey(Address, on_delete=models.CASCADE)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    comment = models.TextField(verbose_name=u'备注', default=u'', null=True)

    def __unicode__(self):
        return '{}-{}'.format(self.organization, self.address)

