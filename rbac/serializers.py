# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import logging

from django.contrib.auth import authenticate
from django.contrib.auth.models import User, Group
from rest_framework import serializers

from natrix.common.natrix_views import serializers as natrix_serializers
from natrix.common import exception as natrix_exceptions

from rbac.backends import user_registry

logger = logging.getLogger(__name__)


class RBACLoginSerializer(natrix_serializers.NatrixSerializer):
    username = serializers.CharField(max_length=150, required=True)
    password = serializers.CharField(max_length=150, required=True)


    def is_valid(self):
        flag = super(RBACLoginSerializer, self).is_valid()
        if not flag:
            return flag

        user = authenticate(username=self._validated_data.get('username'),
                            password=self._validated_data.get('password'))

        if user is not None:
            pass
        else:
            self._errors['authentication'] = ['Username or password error']
            flag = False

        return flag



class UserRegisterSerializer(natrix_serializers.NatrixSerializer):
    username = serializers.EmailField(max_length=150, required=True)
    password = serializers.CharField(max_length=16, min_length=6, required=True)
    verify_password = serializers.CharField(max_length=150, required=True)

    def validate_username(self, value):
        try:
            User.objects.get(username=value)
            raise serializers.ValidationError('The User({}) is exist!'.format(value))
        except User.DoesNotExist:
            pass

        try:
            Group.objects.get(name=value)
            raise serializers.ValidationError('The Group({}) is exist!'.format(value))
        except Group.DoesNotExist:
            pass

        return value

    def is_valid(self):
        flag = super(UserRegisterSerializer, self).is_valid()

        if not flag:
            return flag

        password = self._validated_data.get('password')
        verify_password = self._validated_data.get('verify_password')

        if password != verify_password:
            self._errors['password'] = ['passwords are unmatch']
            return False

        return flag

    def create(self, validated_data):
        username = validated_data.get('username')
        password = validated_data.get('password')
        user = user_registry(username, password)

        return user




