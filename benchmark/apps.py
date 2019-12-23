# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import logging
import sys

from django.apps import AppConfig

from natrix.common import exception as natrix_exception

logger = logging.getLogger('natrix_boot.terminal')

class BenchmarkConfig(AppConfig):
    name = 'benchmark'

    def ready(self):
        if 'manage.py' in sys.argv:
            return

        logger.info('Benchmark application initialize ......')
        from natrix.common import natrix_celery
        from benchmark.tasks import command_adapter_guardian
        try:
            command_adapter_guardian_list = natrix_celery.get_interval_task(command_adapter_guardian.name)

            if len(command_adapter_guardian_list) == 0:
                logger.info('Configure benchmark application (command adapter guardian)')
                natrix_celery.create_periodic_task('Command Adapter Guardian',
                                                   command_adapter_guardian.name,
                                                   frequency=1)
            elif len(command_adapter_guardian_list) > 1:
                logger.error('There are more than one (command adapter guardian), you had better to delete.')

        except natrix_exception.NatrixBaseException as e:
            logger.error('Benchmark application initialize error: {}'.format(e.get_log()))


