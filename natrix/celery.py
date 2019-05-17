# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals
import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", 'natrix.settings')

app = Celery('natrix')
app.config_from_object('django.conf:settings')
app.conf.update(
    broker_transport_options = {
        "max_retries": 3, "interval_start": 0, "interval_step": 0.2, "interval_max": 0.5
    },
    worker_hijack_root_logger=False
)
# app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)
app.autodiscover_tasks()


@app.task(bind=True)
def debug_task(self):
    print('Request: {0!r}'.format(self.request))
