# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import sys
import logging

from django.apps import AppConfig

from natrix.common import exception as natrix_exception

logger = logging.getLogger('natrix_boot.terminal')

class InfrastructureConfig(AppConfig):
    name = 'infrastructure'

    def ready(self):
        if 'manage.py' in sys.argv:
            return

        logger.info('Infrastructure Application initialize process .........')

        from natrix.common import natrix_celery
        from infrastructure.tasks import infrastructure_service_master
        try:
            alive_masters = natrix_celery.get_interval_task(infrastructure_service_master.name)
            if len(alive_masters) == 0:
                logger.info('Configure infrastructure application [alive master]')
                natrix_celery.create_periodic_task('Infrastructrue Alive Master',
                                                   infrastructure_service_master.name,
                                                   frequency=1)
            elif len(alive_masters) == 1:
                logger.info('Infrastructure application ')
            else:
                logger.error('Infrastructure applciation [alive master] with an error configuration: '
                             'with ({}) alive master'.format(len(alive_masters)))

        except natrix_exception.NatrixBaseException as e:
            logger.error('Infrastructure application initialize error: {}'.format(e.get_log()))



