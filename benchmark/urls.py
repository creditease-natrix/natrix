# -*- coding: utf-8 -*-
from django.conf.urls import url

from .views import instant_views

urlpatterns = [
    url(r'^instant/task/v1$', instant_views.InstantTask.as_view(), name='instanttask'),
    url(r'^instant/status/v1$', instant_views.InstantStatus.as_view(), name='instantstatus'),
    url(r'^instant/analyse/v1$', instant_views.InstantAnalyse.as_view(), name='instantanalyse')
]