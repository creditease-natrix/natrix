# -*- coding: utf-8 -*-
"""

"""
from __future__ import unicode_literals
import logging

from collections import OrderedDict

from django.db import transaction
from django.db.models import Q

from rest_framework import serializers

from natrix.common.utils.network import IPAddress
from natrix.common import exception as natrix_exception
from natrix.common.natrix_views import serializers as natrix_serializers

from terminal.configurations import organization_conf
from terminal.models import Address, Network, Contact, Broadband, Export, Region, Operator, Organization
from terminal.models import OrganizationAddress, OrganizationContact, OrganizationNetwork, OrganizationBroadBand
from terminal.models import SEGMENT_TYPES, IDENTITY_TYPE, BROADBAND, EXPORT_TYPE, EXPORT_DEVICE_TYPE
from terminal.models import HistorySave

logger = logging.getLogger(__name__)


class OrgPKSerializer(serializers.Serializer):
    """
    """
    id = serializers.IntegerField(min_value=1, required=True)
    
    def is_valid(self, model):
        if not issubclass(model, HistorySave):
            raise natrix_exception.ClassInsideException(message=u'OrgPKSerializer parameter error!')

        flag = super(OrgPKSerializer, self).is_valid()
        if not flag:
            return flag
        try:
            self.instance = model.objects.get(id=self.validated_data.get('id'))
        except model.DoesNotExist:
            self._errors['id'] = u'不能检索到相应数据！'
            flag = False

        return flag

    def get_db(self):
        return self.instance

    def create(self, validated_data):
        raise NotImplementedError()

    def update(self, instance, validated_data):
        raise NotImplementedError()


class AddressSerializer(natrix_serializers.NatrixSerializer):
    """Address Serializer (terminal.models.Address)

    Address has two primary keys, region (province and city) and address.
    So when add (create) a Address record, we will search before.


    """
    id = serializers.IntegerField(read_only=True)
    address = serializers.CharField(max_length=500, required=True)
    postcode = serializers.CharField(max_length=500, allow_blank=True)

    # create a Region instance
    province = serializers.CharField(required=True, max_length=20)
    city = serializers.CharField(required=True, max_length=20)

    comment = serializers.CharField(required=False, max_length=1000, default='',
                                    allow_blank=True, allow_null=True)

    def is_valid(self, raise_exception=False):
        flag = super(AddressSerializer, self).is_valid()
        if not flag:
            return flag

        try:

            region = Region.objects.get(Q(province=self.initial_data.get('province', None)) &
                                        Q(city=self.initial_data.get('city', None)))
            self._validated_data['region'] = region
            return True
        except Region.DoesNotExist:
            self._errors['province&city'] = [u'''The region is not exist.
            Please contact Natrix administrators!
            ''']
        except Region.MultipleObjectsReturned:
            self._errors['province&city'] = [u'''There are more than one resion records.
            Please contact Natrix administrators!
            ''']

        return False

    def create(self, validated_data):
        """

        :param validated_data:
        :return:
        """
        address = validated_data.get('address')
        postcode = validated_data.get('postcode')
        region = validated_data.get('region')

        try:
            address = Address.objects.get(Q(address=address) & Q(region=region))
            if address.postcode != postcode:
                address.postcode = postcode
                address.save()
        except Address.DoesNotExist:
            address = Address.objects.create(address=address,
                                             postcode=postcode,
                                             region=region)
        return address

    def update(self, instance, validated_data):
        instance.postcode = validated_data.get('postcode', instance.postcode)
        instance.save(self.user, self.group)
        return instance


class NetworkSerializer(natrix_serializers.NatrixSerializer):
    id = serializers.IntegerField(read_only=True)
    segment = serializers.CharField(required=True, max_length=50)
    segment_type = serializers.ChoiceField(required=True, choices=SEGMENT_TYPES)
    gateway = serializers.IPAddressField(max_length=50, allow_blank=True)
    comment = serializers.CharField(max_length=1000, allow_blank=True)

    def is_valid(self, raise_exception=False):
        flag = super(NetworkSerializer, self).is_valid()
        if not flag:
            return flag

        try:
            segment = IPAddress(self.initial_data.get('segment'))
            if self.initial_data.get('gateway') not in segment:
                self._errors['gateway'] = u'网关与网段不匹配！'
                flag = False
        except ValueError as e:
            logger.info(e.message)
            self._errors['segment'] = u'无效的网段信息！'
            flag = False
        return flag

    def create(self, validated_data):
        try:
            network = Network.objects.get(segment=validated_data.get('segment'))
        except Network.DoesNotExist:
            network = Network.objects.create(**validated_data)

        return network

    def update(self, instance, validated_data):
        instance.segment_type = validated_data.get('segment_type', instance.segment_type)
        instance.gateway = validated_data.get('gateway', instance.gateway)
        instance.comment = validated_data.get('comment', instance.comment)
        instance.save(self.user, self.group)

        return instance


class ContactSerializer(natrix_serializers.NatrixSerializer):
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(required=True, max_length=50)
    telephone = serializers.CharField(max_length=50, allow_blank=True)
    email = serializers.EmailField(required=True, max_length=50)
    wechat = serializers.CharField(max_length=50, allow_blank=True)
    identity = serializers.ChoiceField(required=True, choices=IDENTITY_TYPE)

    def create(self, validated_data):
        try:
            contact = Contact.objects.get(email=validated_data.get('email'))
        except Contact.DoesNotExist:
            contact = Contact.objects.create(name=validated_data.get('name'),
                                             telephone=validated_data.get('telephone'),
                                             email=validated_data.get('email'),
                                             wechat=validated_data.get('wechat'))

        return contact

    def update(self, instance, validated_data):
        instance.name = validated_data.get('name', instance.name)
        instance.telephone = validated_data.get('telephone', instance.telephone)
        instance.wechat = validated_data.get('webchat', instance.wechat)

        instance.save(self.user, self.group)

        return instance


class BroadbandSerializer(natrix_serializers.NatrixSerializer):
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(required=True, max_length=20)
    operator = serializers.CharField(required=True, max_length=20)
    access_type = serializers.ChoiceField(choices=BROADBAND, required=True)
    speed = serializers.IntegerField(required=True)
    isp_contact = serializers.CharField(max_length=20, allow_blank=True)
    isp_contact_telephone = serializers.CharField(max_length=50, allow_blank=True)
    isp_contact_email = serializers.CharField(max_length=50, allow_blank=True)
    staff_contact = serializers.CharField(max_length=20, allow_blank=True)
    staff_contact_telephone = serializers.CharField(max_length=50, allow_blank=True)
    staff_contact_email = serializers.CharField(max_length=50, allow_blank=True)
    start_time = serializers.DateField(allow_null=True, required=False)
    end_time = serializers.DateField(allow_null=True, required=False)
    comment = serializers.CharField(max_length=1000, allow_blank=True)

    def is_valid(self, raise_exception=False):
        flag = super(BroadbandSerializer, self).is_valid()
        if not flag:
            return flag
        operator = Operator.objects.filter(name=self.initial_data.get('operator'))
        if operator.count() == 1:
            self._validated_data['operator'] = operator[0]
        else:
            self._errors['operator'] = [u'无效的运营商信息，请与管理员联系！']
            flag = False

        return flag

    def create(self, validated_data):
        try:
            broadband = Broadband.objects.get(
                Q(name=validated_data.get('name')) &
                Q(operator=validated_data.get('operator')) &
                Q(speed=validated_data.get('speed')) &
                Q(start_time=validated_data.get('start_time')) &
                Q(end_time=validated_data.get('end_time')) &
                Q(staff_contact=validated_data.get('staff_contact')) &
                Q(isp_contact=validated_data.get('isp_contact'))
            )
        except Broadband.DoesNotExist:
            broadband = Broadband.objects.create(**validated_data)

        return broadband

    def update(self, instance, validated_data):
        """Change fields beyond primary keys, because these fields can't be changed

        :param instance:
        :param validated_data:
        :return:
        """
        instance.access_type = validated_data.get('access_type', instance.access_type)
        instance.isp_contact_telephone = validated_data.get('isp_contact_telephone',
                                                            instance.isp_contact_telephone)
        instance.isp_contact_email = validated_data.get('isp_contact_email',
                                                        instance.isp_contact_email)
        instance.staff_contact_telephone = validated_data.get('staff_contact_telephone',
                                                              instance.staff_contact_telephone)
        instance.staff_contact_email = validated_data.get('staff_contact_email',
                                                          instance.staff_contact_email)
        instance.comment = validated_data.get('comment', instance.comment)

        instance.save(self.user, self.group)

        return instance


class ExportSerializer(natrix_serializers.NatrixSerializer):
    id = serializers.IntegerField(read_only=True)
    type = serializers.ChoiceField(required=True, choices=EXPORT_TYPE)
    ip = serializers.IPAddressField(required=True)
    device = serializers.ChoiceField(required=True, choices=EXPORT_DEVICE_TYPE)
    comment = serializers.CharField(max_length=1000, allow_blank=True)

    def create(self, validated_data):
        try:
            # exportinfo = Export.objects.get(
            #     Q(device=validated_data.get('device')) &
            #     Q(type=validated_data.get('type')) &
            #     Q(ip=validated_data.get('ip'))
            # )
            exportinfo = Export.objects.get(
                device=validated_data.get('device'),
                type=validated_data.get('type'),
                ip=validated_data.get('ip')
            )
        except Export.DoesNotExist:
            exportinfo = Export.objects.create(**validated_data)
        except Export.MultipleObjectsReturned:
            exportinfos = Export.objects.filter(
                Q(device=validated_data.get('device')) &
                Q(type=validated_data.get('type')) &
                Q(ip=validated_data.get('ip'))
            )
            exportinfo = exportinfos.first()

        return exportinfo

    def update(self, instance, validated_data):
        """

        :param instance:
        :param validated_data:
        :return:
        """
        instance.comment = validated_data.get('comment', instance.comment)

        instance.save(self.user, self.group)
        return instance


class OrganizationSerializer(natrix_serializers.NatrixSerializer):
    id = serializers.IntegerField(read_only=True)
    level = serializers.IntegerField(min_value=1, read_only=True, help_text=u'组织级别')

    name = serializers.CharField(max_length=50)
    parent = serializers.IntegerField(min_value=1, required=False)

    addresses = serializers.ListField(child=AddressSerializer(), required=False)
    contacts = serializers.ListField(child=ContactSerializer(), default=[])
    networks = serializers.ListField(child=NetworkSerializer(), required=False)
    broadbands = serializers.ListField(child=BroadbandSerializer(), required=False)
    exports = serializers.ListField(child=ExportSerializer(), required=False)

    comment = serializers.CharField(max_length=1000, required=False,
                                    allow_null=True, allow_blank=True)

    def validate_id(self, value):
        try:
            instance = Organization.objects.get(id=value)
            self.instance = instance
        except Organization.DoesNotExist:
            raise serializers.ValidationError('The organization({}) is not exist'.format(value))

        return value

    def validate_parent(self, value):
        try:
            parent_org = Organization.objects.get(id=value)
            if int(parent_org.level) + 1 > organization_conf.MAX_LEVEL:
                raise serializers.ValidationError('There new organization level exceed the max level!')
            self.parent_org = parent_org
        except Organization.DoesNotExist:
            raise serializers.ValidationError('The parent({}) organization is not exist'.format(value))

        return value

    def validate_addresses(self, values):
        """The addresses must with the same region.

        :param values:
        :return:
        """

        address_serializers = []
        for value in values:
            serializer = AddressSerializer(self.user, self.group, data=value)
            if serializer.is_valid():
                address_serializers.append(serializer)
            else:
                logger.error('Create address error: {}'.format(serializer.format_errors()))
                raise serializers.ValidationError(
                            'Address is error: {}'.format(serializer.format_errors()))
        region_set = set()
        for addr in address_serializers:
            region_set.add(addr.validated_data.get('region'))

        # Generate address_region
        if len(region_set) > 1:
                raise serializers.ValidationError(
                    'The addresses with more than one regions'
                )
        elif len(region_set) == 1:
            self.address_region = region_set.pop()
        else:
            self.address_region = None

        # Generate address list
        self.address_serializers = address_serializers

        return values

    def validate_networks(self, values):
        """
        Create network_list
        :param values:
        :return:
        """
        network_serializers = []
        for value in values:
            serializer = NetworkSerializer(self.user, self.group, data=value)

            if serializer.is_valid():
                network_serializers.append(serializer)
            else:
                logger.error('Create network error: {}'.format(serializer.format_errors()))
                raise serializers.ValidationError(
                    'Network is error: {}'.format(serializer.format_errors())
                )

        self.network_serializers = network_serializers

        return values

    def validate_contacts(self, values):
        """
        Create contact_list.

        :param values:
        :return:
        """

        contact_serializers = []
        for value in values:
            serializer = ContactSerializer(self.user, self.group, data=value)

            if serializer.is_valid():
                contact_serializers.append((serializer,
                                            serializer.validated_data.get('identity')))
            else:
                logger.error('Create contact error: {}'.format(serializer.format_errors()))
                raise serializers.ValidationError(
                    'Contact is error: {}'.format(serializer.format_errors())
                )

        self.contact_serializers = contact_serializers

        return values

    def validate_broadbands(self, values):
        """
        Create broadband_list.
        :param values:
        :return:
        """
        broadband_serializers = []
        for value in values:
            serializer = BroadbandSerializer(self.user, self.group, data=value)

            if serializer.is_valid():
                broadband_serializers.append(serializer)
            else:
                logger.error('Create broadband error: {}'.format(serializer.format_errors()))
                raise serializers.ValidationError(
                    'Broadband is error: {}'.format(serializer.format_errors())
                )
        self.broadband_serializers = broadband_serializers

        return values

    def validate_exports(self, values):
        """
        Create export_list.
        :param values:
        :return:
        """
        export_serializers = []
        for value in values:
            serializer = ExportSerializer(self.user, self.group, data=value)

            if serializer.is_valid():
                export_serializers.append(serializer)
            else:
                logger.error('Create export error: {}'.format(serializer.format_errors()))
                raise serializers.ValidationError(
                    'Export is error: {}'.format(serializer.format_errors())
                )
        self.export_serializers = export_serializers

        return values

    def is_valid(self, raise_exception=False):
        flag = super(OrganizationSerializer, self).is_valid()
        if not flag:
            return flag

        # validate organization name
        name = self.initial_data.get('name', None)
        if self.initial_data.get('id', None):
            org_id = self.initial_data['id']
            name = self.initial_data['name']
            try:
                instance = Organization.objects.get(id=org_id)
                self.instance = instance
            except Organization.DoesNotExist:
                self._errors['id'] = ['The organization({}) is not exist'.format(org_id)]
                return False

        if hasattr(self, 'instance') and isinstance(self.instance, Organization):
            if self.instance.name != name:
                if self.instance.parent.get_children().filter(name=name).count() > 0:
                    self._errors['name'] = ['There is the same name organization!']
                    return False
        else:
            if self.parent_org.get_children().filter(name=name).count() > 0:
                self._errors['name'] = ['There is the same name organization!']
                return False

        return  flag

    def create(self, validated_data):
        name = validated_data.get('name')
        comment = validated_data.get('comment')

        with transaction.atomic():
            instance = Organization.objects.create(
                name=name,
                parent=self.parent_org,
                level=self.parent_org.level + 1,
                comment=comment,
                region=self.address_region if hasattr(self, 'address_region') else None)
            if hasattr(self, 'address_serializers'):
                for serializer in self.address_serializers:
                    OrganizationAddress.objects.create(address=serializer.save(),
                                                       organization=instance,
                                                       comment=serializer.validated_data.get('comment'))

            if hasattr(self, 'network_serializers'):
                for serializer in self.network_serializers:
                    OrganizationNetwork.objects.create(network=serializer.save(),
                                                       organization=instance)

            if hasattr(self, 'contact_serializers'):
                for serializer, identity in self.contact_serializers:
                    OrganizationContact.objects.create(
                        contact=serializer.save(),
                        organization=instance,
                        identity=identity
                    )

            if hasattr(self, 'broadband_serializers'):
                for serializer in self.broadband_serializers:
                    OrganizationBroadBand.objects.create(
                        broadband=serializer.save(),
                        organization=instance
                    )

            if hasattr(self, 'export_serializers'):
                for serializer in self.export_serializers:
                    instance.exports.add(serializer.save())

            instance.save()
            return instance

    def update(self, instance, validated_data):
        name = validated_data.get('name')
        comment = validated_data.get('comment')

        with transaction.atomic():
            instance.name = name
            instance.comment = comment

            if hasattr(self, 'address_region'):
                instance.region = self.address_region
            else:
                instance.region = None

            for relate_item in instance.organizationaddress_set.all():
                relate_item.delete(self.user, self.group)
            for relate_item in instance.organizationcontact_set.all():
                relate_item.delete(self.user, self.group)
            for relate_item in instance.organizationnetwork_set.all():
                relate_item.delete(self.user, self.group)
            for relate_item in instance.organizationbroadband_set.all():
                relate_item.delete(self.user, self.group)
            for relate_item in list(instance.exports.all()):
                instance.exports.remove(relate_item)


            if hasattr(self, 'address_serializers'):
                for serializer in self.address_serializers:
                    OrganizationAddress.objects.create(address=serializer.save(),
                                                       organization=instance,
                                                       comment=serializer.validated_data.get('comment'))

            if hasattr(self, 'network_serializers'):
                for serializer in self.network_serializers:
                    OrganizationNetwork.objects.create(network=serializer.save(),
                                                       organization=instance)

            if hasattr(self, 'contact_serializers'):
                for serializer, identity in self.contact_serializers:
                    OrganizationContact.objects.create(
                        contact=serializer.save(),
                        organization=instance,
                        identity=identity
                    )

            if hasattr(self, 'broadband_serializers'):
                for serializer in self.broadband_serializers:
                    OrganizationBroadBand.objects.create(
                        broadband=serializer.save(),
                        organization=instance
                    )

            if hasattr(self, 'export_serializers'):
                for serializer in self.export_serializers:
                    instance.exports.add(serializer.save())

            instance.save()

        return instance

    def to_representation(self, instance):

        if not isinstance(instance, Organization):
            raise natrix_exception.ParameterInvalidException(parameter='instance')

        ret = OrderedDict()
        # TODO:
        return ret

    def summary_presentation(self, instance=None):
        """Summary info about organization

        :param instance: an instance of organization
        :return:
        """

        org_instance = None
        if not (instance is None):
            org_instance = instance
        elif hasattr(self, 'instance'):
            org_instance = self.instance

        if not isinstance(org_instance, Organization):
            raise natrix_exception.ParameterInvalidException(parameter='instance')

        try:
            ret = OrderedDict()
            ret['id'] = org_instance.id
            ret['name'] = org_instance.name
            ret['full_name'] = org_instance.get_full_name()
            ret['addresses'] = map(lambda addr: str(addr), org_instance.get_addresses())
            ret['networks'] = map(lambda n: str(n), org_instance.get_networks())
            return ret

        except Exception as e:
            logger.error(e)
            raise natrix_exception.ClassInsideException(message='summary Organization error')

