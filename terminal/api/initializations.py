# -*- coding: utf-8 -*-

from terminal.models import Organization


def _init_organization():
    root_org, is_exist = Organization.objects.get_or_create(name='Natrix', pk=1)


def initialize():
    _init_organization()