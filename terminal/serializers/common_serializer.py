# -*- coding: utf-8 -*-
"""

"""
from __future__ import unicode_literals, absolute_import

import logging

from rest_framework import serializers
from django.db.models import Q

from natrix.common.natrix_views.serializers import NatrixQuerySerializer
from terminal.models import Region, TerminalDevice, Organization

logger = logging.getLogger(__name__)

class TerminalFilterSerializer(NatrixQuerySerializer):
    """Get alive terminal list.

    """
    group_own = serializers.BooleanField(help_text='Limitation of terminal owner', default=False)
    type = serializers.ChoiceField(choices=(('region', u'区域'), ('organization', u'组织')))
    is_classify = serializers.BooleanField(required=False, default=False)
    filter_condition = serializers.ListField(child=serializers.CharField())

    def query(self, validated_data, **kwargs):
        group_own = validated_data.get('group_own')
        type_value = validated_data.get('type')
        is_classify = validated_data.get('is_classify')
        filter_condition = validated_data.get('filter_condition')

        if type_value == 'region':
            query_rest = self.region_query(filter_condition, group_own)
        elif type_value == 'organization':
            query_rest = self.organization_query(filter_condition)
        else:
            query_rest = []

        if not is_classify:
            res = [
                {
                    'name': 'default',
                    'terminals': list(map(lambda t: {'name': t.mac, 'value': t.mac}, query_rest))
                }
            ]
        else:
            if type_value == 'region':
                res = self.region_classify(filter_condition, query_rest)
            else:
                res = self.organization_classify(filter_condition, query_rest)

        return res

    def region_query(self, filter_condition, group_own=False):
        filter_len = len(filter_condition)
        if filter_len > 0:
            provinces = [filter_condition[0]]
        else:
            provinces = ['all']

        if filter_len > 1:
            cities = [filter_condition[1]]
        else:
            cities = ['all']

        regions = Region.query_region(provinces, cities)
        if group_own:
            terminal_devices = TerminalDevice.get_group_available_devices(group=self.group)
        else:
            terminal_devices = TerminalDevice.get_available_devices(group=self.group)

        terminal_devices = terminal_devices.filter(Q(register__address__region__in=regions))

        terminals = []
        for td in terminal_devices:
            terminals.extend(td.get_available_terminals())

        return set(terminals)

    def region_classify(self, filter_condition, terminals):
        filter_len = len(filter_condition)
        if filter_len == 0 or filter_condition[0] == 'all':
            aggregation = 'province'
        else:
            aggregation = 'city'
        classify_dict = {}
        for t in terminals:
            key = self.get_region_key(t, aggregation)
            if key not in classify_dict:
                classify_dict[key] = {
                    'name': key,
                    'terminals': []
                }
            classify_dict[key]['terminals'].append({
                'name': t.mac,
                'value': t.mac
            })

        return classify_dict.values()

    def get_region_key(self, terminal, aggregation):
        register = terminal.dev.register
        if register is None:
            return 'unkown'

        address = register.address
        if address is None:
            return 'unkown'

        region = address.region
        if region is None:
            return 'unkown'

        key = getattr(region, aggregation)
        if key:
            return key
        else:
            return 'unkown'

    def organization_classify(self, filter_condition, terminals):

        filter_len = len(filter_condition)
        if filter_len < 2:
            root = 1
        else:
            root = filter_condition[-2]

        try:
            org = Organization.objects.get(pk=root)

            classify_dict = {}
            for t in terminals:
                if not t.dev:
                    continue
                org_list = t.dev.get_org_list()


                for relation_list in org_list:
                    relation_len = len(relation_list)
                    try:
                        index = relation_list.index(org)
                    except ValueError:
                        index = -1

                    if index == -1:
                        continue

                    if index + 1 == relation_len:
                        if 'default' not in classify_dict:
                            classify_dict['default'] = {
                                'name': 'default',
                                'terminals': [],
                                'terminals_set': set()
                            }
                        if t.mac not in classify_dict['default']['terminals_set']:
                            classify_dict['default']['terminals'].append({
                                'name': t.mac,
                                'value': t.mac
                            })
                            classify_dict['default']['terminals_set'].add(t.mac)
                        continue

                    row_org = relation_list[index + 1]

                    if row_org.pk not in classify_dict:
                        classify_dict[row_org.pk] = {
                            'name': row_org.name,
                            'terminals': [],
                            'terminals_set': set()
                        }

                    if t.mac not in classify_dict[row_org.pk]['terminals_set']:
                        classify_dict[row_org.pk]['terminals'].append({
                            'name': t.mac,
                            'value': t.mac
                        })
                        classify_dict[row_org.pk]['terminals_set'].add(t.mac)

            classify_list = list(map(lambda x: {'name': x['name'], 'terminals': x['terminals']},
                                classify_dict.values()))

            return classify_list

        except Organization.DoesNotExist:
            return []

    def organization_query(self, filter_condition):

        filter_len = len(filter_condition)
        if filter_len < 2:
            root = 1
        else:
            root = filter_condition[-2]

        try:
            terminals = []
            curr_org = Organization.objects.get(pk=root)

            # get all descendants of curr_org
            orgs = curr_org.get_all_tree_nodes()

            registers = []
            for org in orgs:
                registers.extend(org.registerorganization_set.all())

            for register in registers:
                tds = register.terminaldevice_set.all()
                for td in tds:
                    if td.is_available():
                        terminals.extend(td.get_available_terminals())

            return set(terminals)
        except Organization.DoesNotExist:
            logger.error('The organization({}) is not exist!'.format(root))
            return []

    def query_terminals(self):
        group_own = self.validated_data.get('group_own')
        type_value = self.validated_data.get('type')
        filter_condition = self.validated_data.get('filter_condition')

        if type_value == 'region':
            query_rest = self.region_query(filter_condition, group_own)
        elif type_value == 'organization':
            query_rest = self.organization_query(filter_condition)
        else:
            query_rest = []

        return query_rest


