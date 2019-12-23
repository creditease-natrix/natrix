# -*- coding: utf-8 -*-
"""

"""

from rest_framework import serializers

from natrix.common.natrixlog import NatrixLogging
from natrix.common.natrix_views.serializers import NatrixSerializer


logger = NatrixLogging(__name__)


class AccessControlSerializer(NatrixSerializer):

    username = serializers.CharField(max_length=64)
    password = serializers.CharField(max_length=64)

    client_id = serializers.CharField(max_length=64)





