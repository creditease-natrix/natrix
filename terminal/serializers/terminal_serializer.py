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
from terminal.models import Organization, TerminalDevice, Address, Terminal, RegisterOrganization
from terminal.configurations import terminal_conf
from terminal.backends import store

logger = logging.getLogger(__name__)
device_status_choice = map(terminal_conf.choice_generator, terminal_conf.DEVICE_STATUS.values())

device_operation_choice = copy.deepcopy(device_status_choice)
device_operation_choice.append(('delete', u'删除'))

terminal_operation_choice = map(terminal_conf.choice_generator, terminal_conf.TERMINAL_STATUS.values())
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
            ret['update_time'] = instance.last_online_time
            ret['comment'] = instance.comment
            ret['device_alert'] = instance.device_alert
            ret['terminal_alert'] = instance.terminal_alert
            register = instance.register
            ret['reg_orgs'] = map(lambda item: {'id': item.id,
                                                'name': item.name,
                                                'desc': item.get_full_name()},
                                  register.organizations.all() if register else [])
            ret['detect_orgs'] = map(lambda item: {'id': item.id,
                                                   'name': item.name,
                                                   'desc': item.get_full_name()},
                                     instance.organizations.all())
            segments = map(lambda t: t.get_segment(), instance.terminal_set.all())
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
            terminal_device = TerminalDevice.objects.get(sn=sn)
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
        else:
            self.instance.status_change(operation)

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
            terminal = Terminal.objects.get(mac=mac)
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


def calculate_region_dist():
    """Calculate terminal (not device) distribution in region.

    The terminal device filter condition:
    - must register
    - device.status must be active

    :return:
    """

    dist_data = {}
    terminals = Terminal.objects.all()
    total = 0
    alive = 0
    unalive = 0
    unregister = 0
    terminal_set = set()

    for t in terminals:
        if not t.is_valid():
            continue
        total += 1

        if not t.dev.is_register():
            unregister += 1
        terminal_set.add(t.mac)

        province, city = t.dev.get_region()
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
                'terminals': set(),
                'desc': province,
                'identification': {
                    'type': 'region',
                    'value': '[{}]-[all]'.format(province)
                },
                'children': {}
            }

        dist_data[province]['total'] += 1
        dist_data[province]['terminals'].add(t.mac)

        if t.is_alive():
            dist_data[province]['alive'] += 1
            alive += 1
        else:
            dist_data[province]['unalive'] += 1
            unalive += 1

        if dist_data[province]['children'].get(city, None) is None:
            dist_data[province]['children'][city] = {
                'name': city,
                'total': 0,
                'alive': 0,
                'unalive': 0,
                'terminals': set(),
                'desc': city,
                'identification': {
                    'type': 'region',
                    'value': u'[{}]-[{}]'.format(province, city)
                }
            }

        dist_data[province]['children'][city]['total'] += 1
        dist_data[province]['children'][city]['terminals'].add(t.mac)
        if t.is_alive():
            dist_data[province]['children'][city]['alive'] += 1
        else:
            dist_data[province]['children'][city]['unalive'] += 1

    rest_data = {
        'name': 'all',
        'total': total,
        'alive': alive,
        'unalive': unalive,
        'terminals': terminal_set,
        'identification': {
            'type': 'region',
            'value': '[all]-[all]'
        },
        'children': dist_data
    }
    return rest_data


def calculate_organization_dist():
    """Calculate terminal distribution in organization

    :return:
    """
    dist_data = {}
    terminals = Terminal.objects.all()
    # Initialize organization dict
    orgs = Organization.objects.all().order_by('level')
    for org in orgs:
        dist_data[org.id] = {
            'name': org.name,
            'desc': org.name,
            'level': org.level,
            'total': 0,
            'alive': 0,
            'unalive': 0,
            'terminals': set(),
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

    for t in terminals:
        if not t.is_valid():
            continue

        dev_orgs = t.dev.register.organizations.all() if t.dev.register else []
        # TODO: consider unregiste temrinal

        for org in dev_orgs:
            temp = org.id
            is_alive = t.is_alive()

            while temp is not None:

                if temp in dist_data:
                    if t.mac in dist_data[temp]['terminals']:
                        break
                    else:
                        dist_data[temp]['total'] += 1
                        if is_alive:
                            dist_data[temp]['alive'] += 1
                        else:
                            dist_data[temp]['unalive'] += 1
                        dist_data[temp]['terminals'].add(t.mac)

                    parent_id = dist_data[temp].get('parent', None)
                    if parent_id:
                        if dist_data[parent_id]['level'] >= dist_data[temp]['level']:
                            logger.error('There is loop in organization: {}->{}'.format(parent_id, temp))
                            break
                    else:
                        break
                    temp = parent_id
                else:
                    logger.error('There is an register organiztion is not exist: {}-{}'.format(t.mac, org.id))
                    break

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
        root.pop('terminals')
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
        region_distribution = cache.get('terminal_device_region_distribution')

        if region_distribution is None:
            region_distribution = calculate_region_dist()
            cache.set('terminal_device_region_distribution', region_distribution, 60)

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
        node.pop('terminals')
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
        org_distribution = cache.get('terminal_device_org_distribution')

        if org_distribution is None:
            org_distribution = calculate_organization_dist()
            cache.set('terminal_device_org_distribution', org_distribution, 60)

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

            region_distribution = cache.get('terminal_device_region_distribution')

            if region_distribution is None:
                region_distribution = calculate_region_dist()
                cache.set('terminal_device_region_distribution', region_distribution, 300)

            if province in ['all']:
                terminals = region_distribution.get('terminals', {})
            elif province in region_distribution['children']:
                if city in ['all', None]:
                    terminals = region_distribution['children'][province].get('terminals', [])
                elif city in region_distribution['children'][province]['children']:
                    terminals = region_distribution['children'][province]['children'].get(city, {}).get('terminals', [])
                else:
                    terminals = []
            else:
                terminals = []

        else:
            organization_id = validated_data.get('organization_id')

            org_distribution = cache.get('terminal_device_org_distribution')

            if org_distribution is None:
                org_distribution = calculate_organization_dist()
                cache.set('terminal_device_org_distribution', org_distribution, 300)

            if organization_id in org_distribution:
                terminals = org_distribution[organization_id]['terminals']
            else:
                terminals = []

        terminal_list = Terminal.objects.filter(mac__in=list(terminals))
        terminal_devices = list(set(map(lambda x: x.dev, terminal_list)))

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
            identification_serializer = IdentificationSerializer(data=identification)
            if identification_serializer.is_valid():
                terminal_devices = identification_serializer.query_result()
            else:
                flag = False
                self._errors['identification'] = identification_serializer.errors
                return flag
        elif search:
            terminals = Terminal.objects.filter(Q(mac__contains=search) | Q(localip__contains=search))
            terminal_devices = set(list(TerminalDevice.objects.filter(natrixclient_version=search)))
            for t in terminals:
                td = t.dev
                terminal_devices.add(td)
        else:
            terminal_devices = TerminalDevice.objects.all()

        if status != 'all':
            terminal_devices = filter(lambda dev: dev.status == status, terminal_devices)

        self._validated_data['terminal_devices'] = list(terminal_devices)

        return flag

    def query(self, validated_data):

        def dev_cmp(pre, next):
            # sort devices: status, online_time

            flag = TerminalDevice.status_cmp(pre, next)
            if flag != 0:
                return flag

            return TerminalDevice.online_time_cmp(pre, next)

        terminal_devices = self.validated_data.get('terminal_devices')
        res_list = sorted(terminal_devices, cmp=dev_cmp)

        return res_list


class DeviceExceptionListQuerySerializer(NatrixQuerySerializer):
    """

    """
    inactive = serializers.NullBooleanField(required=False)
    unregister = serializers.NullBooleanField(required=False)
    unmatch = serializers.NullBooleanField(required=False)
    search = serializers.CharField(max_length=64, allow_blank=True, required=False)
    is_paginate = serializers.NullBooleanField(required=True)
    pagenum = serializers.IntegerField(min_value=1, required=False)

    def is_valid(self, raise_exception=False):
        flag = super(DeviceExceptionListQuerySerializer, self).is_valid()

        logger.debug('initial data : {}'.format(self.initial_data))

        return flag

    def query(self, validated_data):
        """
        Exceptional devices includes:
         - maintain, posting or inactive devices
         - without register or without registry organizations
         -
        :param validated_data:
        :return:
        """
        inactive = validated_data.get('inactive', False)
        unregister = validated_data.get('unregister', False)
        unmatch = validated_data.get('unmatch', False)
        search = validated_data.get('search', '')

        # device status is not active
        inactive_devices = set(TerminalDevice.objects.filter(is_active=False))

        # unregister device
        unregister_devices = TerminalDevice.objects.filter(Q(register=None) | Q(register__organizations=None))
        logger.info(unregister_devices)

        # organization unmatch device
        unmatch_devices = set()
        register_devices = TerminalDevice.objects.exclude(Q(register=None))
        for dev in register_devices:
            reg_orgs = set(dev.register.organizations.all())
            detect_orgs = set(dev.organizations.all())
            if reg_orgs.isdisjoint(detect_orgs):
                unmatch_devices.add(dev)
        set_list = []

        if inactive:
            set_list.append(inactive_devices)
        if unregister:
            set_list.append(unregister_devices)
        if unmatch:
            set_list.append(unmatch_devices)

        # union set
        filter_devices = reduce(lambda x, y: set(x).union(set(y)), set_list) if set_list else set()

        if search:
            search_set = set()
            version_search = set(TerminalDevice.objects.filter(Q(natrixclient_version__contains=search)))
            search_set.update(version_search)
            terminals = Terminal.objects.filter(Q(mac__contains=search) | Q(localip__contains=search))
            network_search = map(lambda t: t.dev, terminals)
            search_set.update(network_search)

            filter_devices = filter_devices.intersection(search_set)

        return sorted(filter_devices, key=lambda x: x.sn)


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
            device = TerminalDevice.objects.get(sn=value)
        except TerminalDevice.DoesNotExist:
            raise serializers.ValidationError('The device is not exist for sn({})'.format(value))
        return value

    def query(self, validated_data, **kwargs):

        sn = self.validated_data.get('sn')
        is_paginate = self.validated_data.get('is_paginate')
        pagenum = self.validated_data.get('pagenum')

        def format_data(data_list):
            # TODO: process es data
            return map(lambda d: {
                'send_time': d.get('_source', {}).get('heartbeat'),
                'receive_time': d.get('_source', {}).get('receive_time', 0),
                'type': 'basic' if d.get('_type') == 'terminal_basic' else 'advance'
            }, data_list)

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
            'size': 100,
            'sort': {
                'heartbeat': {
                    'order': 'desc'
                }
            }
        }

        post_list = store.pull(terminal_conf.TERMINAL_INDEX, condition)

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


terminal_list_status_choice = map(terminal_conf.choice_generator, terminal_conf.TERMINAL_STATUS.values())
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

        def terminal_cmp(pre, next):
            flag = Terminal.status_cmp(pre, next)
            if flag != 0:
                return flag

            # is_active==True first
            flag = Terminal.active_cmp(pre, next)
            if flag != 0:
                return flag

            flag = Terminal.update_time_cmp(pre, next)

            return flag


        terminals = Terminal.objects.filter(*filter_condition).order_by('dev__sn')
        res_list = sorted(terminals, cmp=terminal_cmp)

        return res_list






