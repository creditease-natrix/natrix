"""

"""
from django.db.models import Q
from django.contrib.auth.models import Group
from rest_framework import serializers

from natrix.common.natrixlog import NatrixLogging
from natrix.common.natrix_views.serializers import NatrixSerializer, NatrixQuerySerializer
from natrix.common import exception as natrix_exception

from terminal.models.security_models import AccessLicense

logger = NatrixLogging(__name__)


class LicenseQuerySerializer(NatrixQuerySerializer):

    status = serializers.ChoiceField(choices=(('all', '全部'), ('used', '已使用'), ('available', '可用')),
                                     default='all')
    is_paginate = serializers.NullBooleanField()
    pagenum = serializers.IntegerField(min_value=1, required=False)

    def __init__(self, group, **kwargs):
        if not isinstance(group, Group):
            logger.error('Validate license-list paramaters must with group')
            raise natrix_exception.ParameterInvalidException()

        super(LicenseQuerySerializer, self).__init__(group=group, **kwargs)



    def query(self, validated_data, **kwargs):
        status = validated_data.get('status')

        licenses = AccessLicense.objects.filter(group=self.group)

        if status == 'used':
            licenses = licenses.filter(~ Q(bind_device=None))
            # licenses = licenses.filter(bind_device__not=None)
        elif status == 'available':
            licenses = licenses.filter(bind_device=None)

        return licenses







