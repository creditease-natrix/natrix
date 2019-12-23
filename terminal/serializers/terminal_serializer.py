# -*- coding: utf-8 -*-
"""

"""
from __future__ import unicode_literals
import logging
import copy
import re
from collections import OrderedDict

from rest_framework import serializers
from django.core.cache import cache
from django.db.models import Q
from django.db import transaction
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from natrix.common import exception as natrix_exception
from natrix.common.natrix_views.serializers import NatrixSerializer, NatrixQuerySerializer
from utils.elasticsearch import NatrixESClient
from terminal.models import Organization, TerminalDevice, Address, Terminal, RegisterOrganization
from terminal.configurations import terminal_conf

logger = logging.getLogger(__name__)
device_status_choice =list(map(terminal_conf.choice_generator, terminal_conf.DEVICE_STATUS.values()))

device_operation_choice = copy.deepcopy(device_status_choice)
device_operation_choice.append(('delete', u'删除'))
device_operation_choice.append(('private', u'私有'))
device_operation_choice.append(('public', u'共享'))

terminal_operation_choice = list(map(terminal_conf.choice_generator, terminal_conf.TERMINAL_STATUS.values()))
terminal_operation_choice.append(('delete', u'删除'))


class DeviceBaiscSerializer(NatrixSerializer):
    """

    """
    sn = serializers.CharField(max_length=64)
    hostname = serializers.CharField(max_length=64, allow_blank=True, required=False)
    type = serializers.CharField(max_length=128, allow_blank=True, required=False)
    os_type = serializers.CharField(max_length=64, allow_blank=True, required=False)
    os_version = serializers.CharField(max_length=128, allow_blank=True, required=False)
    client_version = serializers.CharField(max_length=16, allow_blank=True, required=False)
    status = serializers.ChoiceField(choices=device_status_choice, required=False)

    detect_orgs = serializers.ListField(child=serializers.IntegerField(min_value=1),
                                        allow_empty=True, required=False)
    reg_orgs = serializers.ListSerializer(child=serializers.IntegerField(min_value=1),
                                          allow_empty=True)

    comment = serializers.CharField(max_length=512, allow_blank=True, required=False)
    update_time = serializers.DateTimeField(allow_null=True, required=False)

    device_alert = serializers.BooleanField(default=True)
    terminal_alert = serializers.BooleanField(default=False)

    def validate_sn(self, value):
        """Validate SN and generate instance.

        :param value:
        :return:
        """
        try:
            self.instance = TerminalDevice.objects.get(sn=value)
        except TerminalDevice.DoesNotExist:
            raise serializers.ValidationError('The device is not exist for sn({})'.format(value))
        return value

    def validate_reg_orgs(self, value):
        """Validate reg_orgs.

        The conditions, includes:
         - All organization ids is exist in DB
         - There are not repeat id
         - All organization's regions are consistent.

        :param value:
        :return:
        """
        orgs_query = list(Organization.objects.filter(id__in=value))

        if len(orgs_query) != len(value):
            raise serializers.ValidationError(
                'There are some inavailable organization id(repeat or non-existent)!')

        consistent_region = None
        for org in orgs_query:
            if org.region is None:
                continue
            if consistent_region is None:
                consistent_region = org.region
            elif consistent_region != org.region:
                raise serializers.ValidationError(
                    'The register organizations with more than one organizations')

        # generate register organizations
        self.reg_organizations = orgs_query
        self.reg_region = consistent_region

        return value

    def to_representation(self, instance):
        if not isinstance(instance, TerminalDevice):
            raise natrix_exception.ParameterInvalidException(parameter='instance')

        try:
            ret = OrderedDict()
            terminals = instance.terminal_set.all()
            total = 0
            active = 0
            alive = 0
            for t in terminals:
                total += 1
                if t.is_valid():
                    active += 1
                if t.is_alive():
                    alive += 1

            ret['sn'] = instance.sn
            ret['hostname'] = instance.hostname
            ret['type'] = instance.product
            ret['os_type'] = instance.os_type
            ret['os_version'] = '[{}]-[{}]'.format(instance.os_major_version,
                                                   instance.os_minor_version)
            ret['client_version'] = instance.natrixclient_version
            ret['status'] = instance.status
            ret['scope'] = instance.get_scope()
            ret['update_time'] = instance.last_online_time
            ret['comment'] = instance.comment
            ret['device_alert'] = instance.device_alert
            ret['terminal_alert'] = instance.terminal_alert
            register = instance.register
            ret['reg_orgs'] = list(map(lambda item: {'id': item.id,
                                                'name': item.name,
                                                'desc': item.get_full_name()},
                                  register.organizations.all() if register else []))
            segments = list(map(lambda t: t.get_segment(), instance.terminal_set.all()))
            ret['segments'] = [s for s in segments if s]

            ret['terminal_total'] = total
            ret['terminal_active'] = active
            ret['terminal_alive'] = alive

            return ret

        except Exception as e:
            logger.error('Serializer Terminal Device ERROR: {}'.format(e))
            raise natrix_exception.ClassInsideException(message=u'{}'.format(e))

    def update(self, instance, validated_data):
        try:
            with transaction.atomic():
                instance.device_alert = validated_data.get('device_alert', self.instance.device_alert)
                instance.terminal_alert = validated_data.get('terminal_alert', self.instance.terminal_alert)

                if not instance.register:
                    instance.register = RegisterOrganization.objects.create()

                if self.reg_region:
                    if instance.register.address:
                        instance.register.address.region = self.reg_region
                        instance.register.address.save()
                    else:
                        instance.register.address = Address.objects.create(region=self.reg_region)

                instance.register.organizations.clear()
                for item in self.reg_organizations:
                    instance.register.organizations.add(item)
                instance.register.save()

                instance.save()

                return instance
        except Exception as e:
            logger.error('Update terminal deivce error, {}'.format(e))


class DeviceOperationSerializer(NatrixSerializer):
    sn = serializers.CharField(max_length=64)
    operation = serializers.ChoiceField(choices=device_operation_choice)

    def is_valid(self, raise_exception=False):
        flag = super(DeviceOperationSerializer, self).is_valid(raise_exception=False)
        if not flag:
            return flag
        sn = self.initial_data.get('sn')
        try:
            terminal_device = TerminalDevice.objects.get(sn=sn, group=self.group)
            self.instance = terminal_device
        except TerminalDevice.DoesNotExist as e:
            self._errors['sn'] = ['Can not search the device with {}'.format(sn)]
            flag = False

        return flag

    def action(self, **kwargs):
        operation = self.validated_data.get('operation')
        if operation == 'delete':
            self.instance.delete()
            return None
        elif operation in ('active', 'maintain'):
            self.instance.status_change(operation)
        elif operation in ('public', 'private'):
            self.instance.scope_change(operation)

        return self.instance


class TerminalOperationSerializer(NatrixSerializer):
    """

    """
    mac = serializers.CharField(max_length=12)
    operation = serializers.ChoiceField(choices=terminal_operation_choice)

    def is_valid(self, raise_exception=False):
        flag = super(TerminalOperationSerializer, self).is_valid(raise_exception=False)
        if not flag:
            return flag
        mac = self.initial_data.get('mac')
        try:
            terminal = Terminal.objects.get(mac=mac, dev__group=self.group)
            self.instance = terminal
        except Terminal.DoesNotExist as e:
            self._errors['mac'] = ['Can not search the terminal with {}'.format(mac)]
            flag = False

        return flag

    def action(self, **kwargs):
        operation = self.validated_data.get('operation')
        if operation == 'delete':
            self.instance.delete()
            return None
        else:
            self.instance.status = operation
            self.instance.save()
            return self.instance


def get_region_dist(group=None):
    """Calculate terminal (not device) distribution in region.

    The terminal device filter condition:
    - must register
    - device.status must be active

    :return:
    """
    if group:
        cache_key = 'terminal_device_region_distribution_{}'.format(group.name)
    else:
        cache_key = 'terminal_device_region_distribution_{}'.format('all')

    dist_data = cache.get(cache_key)

    if dist_data:
        return dist_data

    dist_data = {}
    if group:
        devices = TerminalDevice.objects.filter(group=group)
    else:
        devices = TerminalDevice.objects.all()

    total = 0
    alive = 0
    unalive = 0
    unregister = 0
    devices_set = set()

    for d_i in devices:
        devices_set.add(d_i.sn)
        total += 1

        if not d_i.is_register():
            unregister += 1

        province, city = d_i.get_region()
        if province is None:
            province = u'unkown'
        if city is None:
            city = u'unkown'

        if dist_data.get(province, None) is None:
            dist_data[province] = {
                'name': province,
                'total': 0,
                'alive': 0,
                'unalive': 0,
                'devices': set(),
                'desc': province,
                'identification': {
                    'type': 'region',
                    'value': '[{}]-[all]'.format(province)
                },
                'children': {}
            }
        dist_data[province]['total'] += 1
        dist_data[province]['devices'].add(d_i.sn)

        if dist_data[province]['children'].get(city, None) is None:
            dist_data[province]['children'][city] = {
                'name': city,
                'total': 0,
                'alive': 0,
                'unalive': 0,
                'devices': set(),
                'desc': city,
                'identification': {
                    'type': 'region',
                    'value': u'[{}]-[{}]'.format(province, city)
                }
            }

        dist_data[province]['children'][city]['total'] += 1
        dist_data[province]['children'][city]['devices'].add(d_i.sn)

        if d_i.is_available():
            dist_data[province]['alive'] += 1
            dist_data[province]['children'][city]['alive'] += 1
            alive += 1

        else:
            dist_data[province]['unalive'] += 1
            dist_data[province]['children'][city]['unalive'] += 1
            unalive += 1

    rest_data = {
        'name': 'all',
        'total': total,
        'alive': alive,
        'unalive': unalive,
        'devices': devices_set,
        'identification': {
            'type': 'region',
            'value': '[all]-[all]'
        },
        'children': dist_data
    }


    cache.set(cache_key, rest_data, 300)

    return rest_data


def get_organization_dist(group=None):
    """Calculate terminal distribution in organization

    :return:
    """
    if group:
        cache_key = 'terminal_device_org_distribution_{}'.format(group.name)
    else:
        cache_key = 'terminal_device_org_distribution_{}'.format('all')

    dist_data = cache.get(cache_key)
    if dist_data:
        return dist_data

    dist_data = {}

    if group:
        devices = TerminalDevice.objects.filter(group=group)
    else:
        devices = TerminalDevice.objects.all()

    # Initialize organization dict
    if group:
        orgs = Organization.objects.filter(Q(pk=1) | Q(group=group)).order_by('level')
    else:
        orgs = Organization.objects.all().order_by('level')

    for org in orgs:
        dist_data[org.id] = {
            'name': org.name,
            'desc': org.name,
            'level': org.level,
            'total': 0,
            'alive': 0,
            'unalive': 0,
            'devices': set(),
            'identification': {
                'type': 'organization',
                'value': org.id
            },
            'parent': None,
            'children': []
        }
        if org.parent is not None:
            if dist_data.get(org.parent.id, None) is None:
                logger.error('There is an organization with an exist parent: {}->{}'.format(org.parent.id, org.id))
            else:
                dist_data[org.parent.id]['children'].append(org.id)
                dist_data[org.id]['parent'] = org.parent.id

    for d_i in devices:
        dev_orgs = d_i.register.organizations.all() if d_i.register else []

        for org in dev_orgs:
            temp_id = org.id
            is_alive = d_i.is_available()

            while temp_id is not None:

                if temp_id in dist_data:
                    if d_i.sn in dist_data[temp_id]['devices']:
                        break
                    else:
                        dist_data[temp_id]['total'] += 1
                        if is_alive:
                            dist_data[temp_id]['alive'] += 1
                        else:
                            dist_data[temp_id]['unalive'] += 1
                        dist_data[temp_id]['devices'].add(d_i.sn)

                    parent_id = dist_data[temp_id].get('parent', None)
                    if parent_id:
                        if dist_data[parent_id]['level'] >= dist_data[temp_id]['level']:
                            logger.error('There is loop in organization: {}->{}'.format(parent_id, temp_id))
                            break
                    else:
                        break
                    temp_id = parent_id

                else:
                    logger.error('There is an register organiztion is '
                                 'not exist: {}-{}'.format(d_i.sn, org.id))
                    break

    cache.set(cache_key, dist_data, 300)

    return dist_data


class OverviewQuerySerializer(NatrixQuerySerializer):
    """Over view request data

    """
    type = serializers.ChoiceField(choices=(('region', u'区域'), ('organization', u'组织')))
    filter = serializers.ListSerializer(child=serializers.CharField(max_length=64))
    show_level = serializers.IntegerField(allow_null=True)

    def is_valid(self, raise_exception=False):
        flag = super(OverviewQuerySerializer, self).is_valid(raise_exception=False)
        if not flag:
            return flag

        type_value = self.initial_data.get('type')
        filter_value = self.initial_data.get('filter')
        if type_value == 'region':
            if len(filter_value) != 2:
                self._errors['filter'] = ['The region filter list must contain 2 items']
                flag = False
        else:
            for item in filter_value:
                if not item.isdigit():
                    self.errors['filter'] = ['The items in organization filter list must be integer']
                    flag = False
                    break

        return flag

    def query(self, validated_data):
        """

        :param validated_data:
        :return:
        """
        type_value = validated_data.get('type')
        filter_value = validated_data.get('filter')
        show_level = 3 if validated_data.get('show_level') is None else validated_data.get('show_level')

        if type_value == 'region':
            query_rest = self.region_query(filter_value, show_level=show_level)
        else:
            query_rest = self.organization_query(filter_value, show_level=show_level)

        return query_rest

    def _format_region_tree(self, root, deep):
        """Transform children to list.

        :return:
        """
        if root is None:
            return
        root.pop('devices')
        if root.get('children', None) is None:
            return

        if deep > 1:
            children = root['children']
            root['children'] = list(children.values())
            for item in root['children']:
                self._format_region_tree(item, deep-1)
        else:
            root['children'] = None

    def region_query(self, filter_value, show_level=3):
        """Region Query.

        Calculating terminal devices distribution in region is a complex action,
        because a terminal device has many register organizations and an organization
        has many addresses.
        So we store the result in redis and set expiry_time(5 minutes).

        :param filter_value:
        :param show_level:
        :return:
        """

        region_distribution = get_region_dist(self.group)

        filter_len = len(filter_value)
        if filter_len == 0:
            province = 'all'
            city = 'all'
        elif filter_len == 1:
            province = filter_value[0]
            city = 'all'
        else:
            province = filter_value[0]
            city = filter_value[1]

        if province in ['all', None]:
            filter_data = region_distribution
        elif region_distribution['children'].get(province, None) is not None:
            if city in ['all', None]:
                filter_data = region_distribution['children'][province]
            elif region_distribution['children'][province].get('children', {}).get(city, None) is not None:
                filter_data = region_distribution['children'][province]['children'][city]
            else:
                filter_data = None
        else:
            filter_data = None

        if filter_data is None:
            return {}
        else:
            self._format_region_tree(filter_data, deep=show_level)

            return filter_data

    def _format_org_tree(self, root, data, deep):
        if root not in data:
            return None

        if deep <= 0:
            return None

        node = copy.copy(data[root])
        node.pop('devices')
        children = node.get('children', None)
        node['children'] = []
        if children:
            for child in children:
                branch = self._format_org_tree(child, data, deep-1)
                if branch:
                    node['children'].append(branch)
        return node

    def organization_query(self, filter_value, show_level=3):
        """

        :param filter_value:
        :param show_level:
        :return:
        """

        org_distribution = get_organization_dist(self.group)

        filter_len = len(filter_value)
        if filter_len == 0:
            root = 1
        else:
            root = int(filter_value[-1])

        rest_data = self._format_org_tree(root, org_distribution, show_level)
        return rest_data


class IdentificationSerializer(NatrixQuerySerializer):

    type = serializers.ChoiceField(choices=(('region', u'区域'), ('organization', u'组织')))
    value = serializers.CharField(max_length=64)

    def is_valid(self, raise_exception=False):
        flag = super(IdentificationSerializer, self).is_valid(raise_exception=False)
        if not flag:
            return flag
        type = self.initial_data.get('type')
        value = self.initial_data.get('value')
        try:
            if type == 'region':
                m = re.search(r'^\[(\S+)\]-\[(\S+)\]', value)
                if m is None:
                    flag = False
                    self._errors['value'] = ['region value error: {}'.format(value)]
                else:
                    province = m.group(1)
                    city = m.group(2)

                    self._validated_data['province'] = province
                    self._validated_data['city'] = city
            else:
                self._validated_data['organization_id'] = int(value)
        except ValueError as e:
            self._errors['value'] = ['organization value must be an integer.{}'.format(value)]
            logger.info('{}'.format(e))
            flag = False
        except Exception as e:
            logger.error('{}'.format(e))
            flag = False

        return flag

    def query(self, validated_data):
        type = validated_data.get('type')
        if type == 'region':
            province = validated_data.get('province')
            city = validated_data.get('city')

            region_distribution = get_region_dist(self.group)

            if province in ['all']:
                devices_list = region_distribution.get('devices', [])
            elif province in region_distribution['children']:
                if city in ['all', None]:
                    devices_list = region_distribution['children'][province].get('devices', [])
                elif city in region_distribution['children'][province]['children']:
                    devices_list = region_distribution['children'][province]['children'].get(city, {}).get('devices', [])
                else:
                    devices_list = []
            else:
                devices_list = []

        else:
            organization_id = validated_data.get('organization_id')

            org_distribution = get_organization_dist(self.group)

            if organization_id in org_distribution:
                devices_list = org_distribution[organization_id]['devices']
            else:
                devices_list = []

        terminal_devices = TerminalDevice.objects.filter(sn__in=list(devices_list))

        return terminal_devices


device_status_query_choice = copy.deepcopy(device_status_choice)
device_status_query_choice.append(('all', 'all'))
class DeviceListQuerySerializer(NatrixQuerySerializer):
    search = serializers.CharField(max_length=64, allow_blank=True, required=False)
    status = serializers.ChoiceField(choices=device_status_query_choice, default='all')
    identification = IdentificationSerializer(required=False, allow_null=True)
    is_paginate = serializers.NullBooleanField()
    pagenum = serializers.IntegerField(min_value=1, required=False)

    def is_valid(self, raise_exception=False):
        flag = super(DeviceListQuerySerializer, self).is_valid()
        if flag is False:
            return flag

        identification = self.initial_data.get('identification')
        search = self.initial_data.get('search', '')
        status = self.initial_data.get('status', 'all')

        if identification is not None:
            identification_serializer = IdentificationSerializer(data=identification,
                                                                 group=self.group)
            if identification_serializer.is_valid():
                terminal_devices = identification_serializer.query_result()
            else:
                flag = False
                self._errors['identification'] = identification_serializer.errors
                return flag
        elif search:
            terminals = Terminal.objects.filter(Q(mac__contains=search) |
                                                Q(localip__contains=search)).filter(dev__group=self.group)
            terminal_devices = set(list(TerminalDevice.objects.filter(natrixclient_version=search,
                                                                      group=self.group)))
            for t in terminals:
                td = t.dev
                terminal_devices.add(td)
        else:
            terminal_devices = TerminalDevice.objects.filter(group=self.group)

        if status != 'all':
            terminal_devices = filter(lambda dev: dev.status == status, terminal_devices)

        self._validated_data['terminal_devices'] = list(terminal_devices)

        return flag

    def query(self, validated_data):

        device_cmp_key = lambda x: (x.get_status_intvalue(), x.first_online_time)

        terminal_devices = self.validated_data.get('terminal_devices')
        res_list = sorted(terminal_devices, key=device_cmp_key)

        return res_list


class TerminalPostSerializer(NatrixQuerySerializer):
    sn = serializers.CharField(max_length=64)
    is_paginate = serializers.BooleanField(required=True)
    pagenum = serializers.IntegerField(required=False)

    def validate_sn(self, value):
        """Validate SN

        :param value:
        :return:
        """
        try:
            TerminalDevice.objects.get(sn=value)
        except TerminalDevice.DoesNotExist:
            raise serializers.ValidationError('The device is not exist for sn({})'.format(value))
        return value

    def query(self, validated_data, **kwargs):

        sn = self.validated_data.get('sn')
        is_paginate = self.validated_data.get('is_paginate')
        pagenum = self.validated_data.get('pagenum')

        def format_data(data_list):
            # TODO: process es data
            return list(map(lambda d: {
                'send_time': d.get('_source', {}).get('heartbeat'),
                'receive_time': d.get('_source', {}).get('receive_time', 0),
                'type': 'basic' if d.get('_type') == 'terminal_basic' else 'advance'
            }, data_list))

        condition = {
            'query': {
                'bool': {
                    'must': [
                        {
                            'terms': {
                                '_type': [terminal_conf.TERMINAL_ADVANCE, terminal_conf.TERMINAL_BASIC]
                            },
                        },
                        {
                            'match': {
                                'sn': sn
                            }
                        }
                    ]
                }
            },
            # TODO: maybe move to user configuration
            'size': 100,
            'sort': {
                'receive_time': {
                    'order': 'desc'
                }
            }
        }

        natrix_es_client = NatrixESClient(app='terminal')
        post_list = natrix_es_client.pull(condition)

        data = {}
        if is_paginate:
            per_page = kwargs.get('per_page', 10)
            paginator = Paginator(post_list, per_page)
            try:
                current_page_query = paginator.page(pagenum)
            except PageNotAnInteger:
                current_page_query = paginator.page(1)
            except EmptyPage:
                current_page_query = paginator.page(paginator.num_pages)

            data['page_num'] = current_page_query.number
            data['page_count'] = paginator.num_pages
            data['info'] = format_data(current_page_query)
        else:
            data['info'] = format_data(post_list)

        return data


terminal_list_status_choice = list(map(terminal_conf.choice_generator, terminal_conf.TERMINAL_STATUS.values()))
terminal_list_status_choice.append(('all', 'all'))
terminal_is_active_choice = (('all', 'all'), ('yes', u'是'), ('no', u'否'))
class TerminalListQuerySerializer(NatrixQuerySerializer):
    search = serializers.CharField(max_length=64, allow_blank=True, required=False)
    sn = serializers.CharField(max_length=64, required=False)
    status = serializers.ChoiceField(choices=terminal_list_status_choice, default='all')
    is_active = serializers.ChoiceField(choices=terminal_is_active_choice, default='all')
    is_paginate = serializers.BooleanField()
    pagenum = serializers.IntegerField(min_value=1,required=False)

    def query(self, validated_data, **kwargs):
        search = validated_data.get('search')
        sn = validated_data.get('sn')
        status = validated_data.get('status')
        is_active = validated_data.get('is_active')

        filter_condition = []
        if search:
            filter_condition.append(Q(mac__contains=search) | Q(localip__contains=search))

        if status != 'all':
            filter_condition.append(Q(status=status))

        if is_active == 'no':
            filter_condition.append(Q(is_active=False))
        elif is_active == 'yes':
            filter_condition.append(Q(is_active=True))

        if sn:
            filter_condition.append((Q(dev__sn=sn)))

        def sorted_metrics(item):
            return not item.is_active, item.digital_status(), item.update_time

        terminals = Terminal.objects.filter(*filter_condition).order_by('dev__sn')
        res_list = sorted(terminals, key=sorted_metrics)

        return res_list


