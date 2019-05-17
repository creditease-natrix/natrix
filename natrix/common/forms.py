# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django import forms
from django.forms.widgets import TextInput
from django.core import validators

class EagleCharField(forms.CharField):
    def __init__(self, max_length=None, min_length=None, strip=True, empty_value='',
                 readonly=False, *args, **kwargs):
        super(EagleCharField, self).__init__(max_length=max_length,
                                             min_length=min_length,
                                             strip=strip,
                                             empty_value=empty_value,
                                             *args,
                                             **kwargs)
        if not ('class' in self.widget.attrs):
            self.widget.attrs['class'] = 'form-control'
        else:
            self.widget.attrs['class'] += 'form-control'

        if readonly:
            self.widget.attrs["readonly"] = True


class EagleTextarea(forms.CharField):
    def __init__(self, max_length=None, min_length=None, strip=True, empty_value='',
                 readonly=False, *args, **kwargs):
        kwargs.setdefault('widget', forms.Textarea(attrs={'rows':5}))

        super(EagleTextarea, self).__init__(max_length=max_length,
                                             min_length=min_length,
                                             strip=strip,
                                             empty_value=empty_value,
                                             *args,
                                             **kwargs)
        if not ('class' in self.widget.attrs):
            self.widget.attrs['class'] = 'form-control'
        else:
            self.widget.attrs['class'] += 'form-control'

        if readonly:
            self.widget.attrs["readonly"] = True


# 目前显示异常
class EagleChoiceField(forms.ChoiceField):
    def __init__(self, choices=(), required=True, widget=None, label=None,
                 initial=None, help_text='', *args, **kwargs):
        super(EagleChoiceField, self).__init__(choices=choices,
                                               required=required,
                                               widget=widget,
                                               label=label,
                                               initial=initial,
                                               help_text=help_text,
                                               *args,
                                               **kwargs)
        if not ('class' in self.widget.attrs):
            self.widget.attrs['class'] = 'form-control'
        else:
            self.widget.attrs['class'] += 'form-control'



class EagleIntegerField(forms.IntegerField):
    def __init__(self, max_value=None, min_value=None, *args, **kwargs):
        super(EagleIntegerField, self).__init__(max_value=max_value,
                                                min_value=min_value,
                                                *args,
                                                **kwargs)
        if not ('class' in self.widget.attrs):
            self.widget.attrs['class'] = 'form-control'
        else:
            self.widget.attrs['class'] += 'form-control'


class EagleFloatField(forms.FloatField):
    def __init__(self, max_value=None, min_value=None, *args, **kwargs):
        super(EagleFloatField, self).__init__(max_value=max_value,
                                                min_value=min_value,
                                                *args,
                                                **kwargs)
        if not ('class' in self.widget.attrs):
            self.widget.attrs['class'] = 'form-control'
        else:
            self.widget.attrs['class'] += ' form-control'


class EagleBooleanField(forms.BooleanField):
    def __init__(self, *args, **kwargs):
        super(EagleBooleanField, self).__init__(*args,
                                                **kwargs)



class EagleURLField(forms.URLField):
    widget = TextInput
    default_validators = [validators.URLValidator(schemes=['http', 'https', ''])]
    def __init__(self, max_length=None, readonly=False, *args, **kwargs):
        super(EagleURLField, self).__init__(max_length=128,
                                            min_length=5,
                                            *args,
                                            **kwargs)
        if not ('class' in self.widget.attrs):
            self.widget.attrs['class'] = 'form-control'
        else:
            self.widget.attrs['class'] += 'form-control'

        if readonly:
            self.widget.attrs["readonly"] = True


class EagleMultipleChoiceField(forms.MultipleChoiceField):
    def __init__(self, *args, **kwargs):
        super(EagleMultipleChoiceField, self).__init__(*args,
                                            **kwargs)
        if not ('class' in self.widget.attrs):
            self.widget.attrs['class'] = 'form-control'
        else:
            self.widget.attrs['class'] += ' form-control'



