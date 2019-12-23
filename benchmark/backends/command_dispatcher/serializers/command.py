# -*- coding: utf-8 -*-
"""

"""

from __future__ import unicode_literals
import logging

from rest_framework import serializers as rest_serializers

from natrix.common.natrix_views import serializers as natrix_serializers
from benchmark.configurations import task_conf

logger = logging.getLogger(__name__)
choice_filter = lambda x: (x.get('name'), x.get('verbose_name'))

class TerminalCommand(natrix_serializers.NatrixSerializer):
    """Terminal Format Command.


    """

    uuid = rest_serializers.UUIDField()
    protocol = rest_serializers.ChoiceField(choices=list(map(choice_filter,
                                                             task_conf.PROTOCOL_INFO.values())))
    destination = natrix_serializers.SchemeURLField()
    parameters = rest_serializers.DictField()

    generate_timestamp = rest_serializers.FloatField(min_value=0)
    terminal = rest_serializers.CharField(max_length=12)



