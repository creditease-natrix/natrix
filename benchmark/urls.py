# -*- coding: utf-8 -*-
from django.conf.urls import url

from .views import instant_views, timed_views

urlpatterns = [
    # Instant task urls
    url(r'^instant/task/v1$', instant_views.InstantTask.as_view(), name='instanttask'),
    url(r'^instant/status/v1$', instant_views.InstantStatus.as_view(), name='instantstatus'),
    url(r'^instant/analyse/v1$', instant_views.InstantAnalyse.as_view(), name='instantanalyse'),

    # Timed task urls
    url(r'^timed/task/v1$', timed_views.TimedTask.as_view(), name='timedTask'),
    url(r'^timed/task/list/v1$', timed_views.TimedTaskList.as_view(), name='timedTaskList'),
    url(r'^timed/unfollowedTask/list/v1$', timed_views.UnfollowedTaskList.as_view(), name='unfollowedList'),
    url(r'^timed/operation/v1$', timed_views.TimedTaskOperation.as_view(), name='timedTaskOperation'),

    url(r'^timed/task/select/v1$', timed_views.TimedTaskSelect.as_view(), name='timedTaskSelect'),
    url(r'^timed/analyse/v1$', timed_views.TimedTaskAnalyse.as_view(), name='timedTaskAnalyse'),

]