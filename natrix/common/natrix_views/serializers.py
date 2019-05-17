# -*- coding: utf-8 -*-
"""

"""
from __future__ import unicode_literals
import logging

from django.db.models import Model
from rest_framework import serializers

from natrix.common import exception as natrix_exception

from .fields import (SchemeURLField, NullFloatField)

logger = logging.getLogger(__name__)

class NatrixSerializer(serializers.Serializer):
    """

    Provice formate error information.

    """
    def __init__(self, user=None, group=None, **kwargs):
        super(NatrixSerializer, self).__init__(**kwargs)

        # TODO: 可能需要进行参数判断
        self.user = user
        self.group = group

    def format_errors(self):
        if self._errors:
            errors_list = map(lambda (key, values): u'{}: {}'.format(key, ';'.join(values)),
                              self._errors.items())
            return '\n'.join(errors_list)
        else:
            return ''


class IDSerializer(NatrixSerializer):
    """
    """
    id = serializers.IntegerField(min_value=1, required=True)

    def __init__(self, model=None, **kwargs):
        super(IDSerializer, self).__init__(**kwargs)
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


class NatrixQuerySerializer(NatrixSerializer):
    """Natrix Query Serializer

    This type of serializer doesn't require to provide create and update methods.

    """

    def query(self, validated_data, **kwargs):
        """

        :return:
        """
        raise NotImplementedError('`query()` must be implemented.')

    def query_result(self, **kwargs):
        """Used to get query result.

        In the end of this funtion, will call query() function to get result data, so user must
        implement query() function. The result data will as the data part of api response.

        :return:
        """
        assert hasattr(self, '_errors'), (
            'You must call `.isvalid()` before calling `.query_result()`'
        )

        assert not self.errors, (
            'You can not call `.query_result()` on a serializer with invalid data.'
        )

        validated_data = dict(
            list(self.validated_data.items()) +
            list(kwargs.items())
        )

        return self.query(validated_data, **kwargs)