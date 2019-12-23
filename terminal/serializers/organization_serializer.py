"""

"""

from collections import OrderedDict

from django.db import transaction
from django.db.models import Q

from rest_framework import serializers

from natrix.common import exception as natrix_exception
from natrix.common.natrix_views import serializers as natrix_serializers
from natrix.common.natrixlog import NatrixLogging

from terminal.configurations import organization_conf
from terminal.models import Address, Contact, Region, Organization
from terminal.models import OrganizationAddress, OrganizationContact
from terminal.models import IDENTITY_TYPE
from terminal.models import HistorySave

logger = NatrixLogging(__name__)


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


class OrganizationSerializer(natrix_serializers.NatrixSerializer):
    id = serializers.IntegerField(read_only=True)
    level = serializers.IntegerField(min_value=1, read_only=True, help_text=u'组织级别')

    name = serializers.CharField(max_length=50)
    parent = serializers.IntegerField(min_value=1, required=False)

    addresses = serializers.ListField(child=AddressSerializer(), required=False)
    contacts = serializers.ListField(child=ContactSerializer(), default=[])

    comment = serializers.CharField(max_length=1000, required=False,
                                    allow_null=True, allow_blank=True)

    def validate_id(self, value):
        try:
            instance = Organization.objects.get(id=value, group=self.group)
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
                    self._errors['name'] = ['There is the same organization name!']
                    return False
        else:
            if self.parent_org.get_children().filter(name=name).count() > 0:
                self._errors['name'] = ['There is the same organization name with same organization level!']
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
                group=self.group,
                region=self.address_region if hasattr(self, 'address_region') else None)
            if hasattr(self, 'address_serializers'):
                for serializer in self.address_serializers:
                    OrganizationAddress.objects.create(address=serializer.save(),
                                                       organization=instance,
                                                       comment=serializer.validated_data.get('comment'))

            if hasattr(self, 'contact_serializers'):
                for serializer, identity in self.contact_serializers:
                    OrganizationContact.objects.create(
                        contact=serializer.save(),
                        organization=instance,
                        identity=identity
                    )

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


            if hasattr(self, 'address_serializers'):
                for serializer in self.address_serializers:
                    OrganizationAddress.objects.create(address=serializer.save(),
                                                       organization=instance,
                                                       comment=serializer.validated_data.get('comment'))


            if hasattr(self, 'contact_serializers'):
                for serializer, identity in self.contact_serializers:
                    OrganizationContact.objects.create(
                        contact=serializer.save(),
                        organization=instance,
                        identity=identity
                    )

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
            ret['id'] = org_instance.pk
            ret['name'] = org_instance.name
            ret['full_name'] = org_instance.get_full_name()
            ret['addresses'] = list(map(lambda addr: addr.address_desc(), org_instance.get_addresses()))
            return ret

        except Exception as e:
            logger.error(e)
            raise natrix_exception.ClassInsideException(message='summary Organization error')

