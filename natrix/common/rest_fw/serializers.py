# -*- coding: utf-8 -*-
"""

"""
from __future__ import unicode_literals
from django.db.models import Model
from rest_framework import serializers

from natrix.common import exception as natrix_exception


class NatrixSerializer(serializers.Serializer):
    """

    """
    def __init__(self, user=None, group=None, **kwargs):
        super(NatrixSerializer, self).__init__(**kwargs)

        # TODO: 可能需要进行参数判断
        self.user = user
        self.group = group


class IDSerializer(serializers.Serializer):
    """
    """
    id = serializers.IntegerField(min_value=1, required=True)

    def __init__(self, model=None):
        super(IDSerializer, self).__init__()
        self.model = model

    def is_valid(self, model):
        if not issubclass(model, Model):
            raise natrix_exception.ClassInsideException(message=u'IDSerializer parameter error!')

        flag = super(IDSerializer, self).is_valid()
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

