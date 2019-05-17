# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import logging
import sys
import threading

from django.apps import AppConfig
from natrix.common import exception as natrix_exception

logger = logging.getLogger('natrix_boot.terminal')


class TerminalConfig(AppConfig):
    name = 'terminal'

    def __init__(self, *args, **kwargs):
        self._lock = threading.Lock()
        super(TerminalConfig, self).__init__(*args, **kwargs)

    def ready(self):
        """Terminal application initial process.
        :return:
        """
        if 'manage.py' in sys.argv:
            return
        logger.info('Terminal Application initialize process ..........')
        from natrix.common import natrix_celery
        from terminal.tasks import terminal_alive_master
        try:
            alive_masters = natrix_celery.get_interval_task(terminal_alive_master.name)
            if len(alive_masters) == 0:
                logger.info('Configure terminal application [alive master]')
                natrix_celery.create_periodic_task('Terminal Alive Master',
                                                   terminal_alive_master.name,
                                                   frequency=1)
            elif len(alive_masters) == 1:
                logger.info('Terminal application [alive master] has been configured!')
            else:
                logger.error('Terminal applciation [alive master] with an error configuration: '
                             'with ({}) alive master'.format(len(alive_masters)))

        except natrix_exception.BaseException as e:
            logger.error('Terminal application initialize error: {}'.format(e.get_log()))

