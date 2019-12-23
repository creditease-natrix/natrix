# -*- coding: utf-8 -*-
"""
"""

import logging
from django.conf import settings


log_level = logging.getLevelName(settings.LOG_LEVEL.upper())


class NatrixLogging(object):

    def __init__(self, name):
        self.logger = logging.getLogger(name=name)

    def debug(self, *args, **kwargs):
        if log_level <= logging.DEBUG:
            self.logger.debug(*args, **kwargs)

    def info(self, *args, **kwargs):
        if log_level <= logging.INFO:
            self.logger.info(*args, **kwargs)

    def error(self, *args, **kwargs):
        if log_level <= logging.ERROR:
            self.logger.error(*args, **kwargs)

