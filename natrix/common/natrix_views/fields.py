# -*- coding: utf-8 -*-
"""

"""
from django.core.validators import URLValidator
from django.utils.translation import ugettext_lazy as _
from django.utils.encoding import force_text

from rest_framework import fields as rest_fields


class NatrixURLValidator(URLValidator):

    def __call__(self, value):
        value = force_text(value)
        if '://' not in value:
            value = 'http://{}'.format(value)
        super(NatrixURLValidator, self).__call__(value)


class SchemeURLField(rest_fields.CharField):
    default_error_messages = {
        'invalid': _('Enter a valid URL.')
    }

    def __init__(self, schemes=None, **kwargs):
        super(SchemeURLField, self).__init__(**kwargs)
        validator = NatrixURLValidator(schemes=schemes, message=self.error_messages['invalid'])
        self.validators.append(validator)


class NullFloatField(rest_fields.FloatField):
    NULL_VALUES = {'n', 'N', 'null', 'Null', 'NULL', '', None}

    def __init__(self, default=None, **kwargs):
        super(NullFloatField, self).__init__(**kwargs)
        self._default = default

    def to_internal_value(self, data):
        if data in self.NULL_VALUES:
            return float(self._default)
        else:
            return super(NullFloatField, self).to_internal_value(data)

    def get_value(self, dictionary):
        value = super(NullFloatField, self).get_value(dictionary)

        if value in self.NULL_VALUES:
            return self._default
        return value


