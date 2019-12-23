# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import sys
import logging

from django.apps import AppConfig

logger = logging.getLogger('natrix_boot.terminal')


class RbacConfig(AppConfig):
    name = 'rbac'

    def ready(self):
        if 'runserver' not in sys.argv:
            return

        logger.info('Initialize RBAC application')
        from rbac.api import init_admin_configuration

        init_admin_configuration()



