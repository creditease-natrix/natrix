# -*- coding: utf-8 -*-

from django.conf.urls import url

from .views import alarm_views, notify_views

urlpatterns = [
    url('^monitor/list/v1$', alarm_views.MonitorListAPI.as_view(), name='monitor_list'),
    url('^alarm/v1$', alarm_views.AlarmAPI.as_view(), name='alarm'),
    url('^alarm/list/v1$', alarm_views.AlarmListAPI.as_view(), name='alarm_list'),
    url('^alarm/operation/v1$', alarm_views.AlarmOperationAPI.as_view(), name='alarm_operation'),

    url('^alarm/notify/v1$', notify_views.NotificationAPI.as_view(), name='notify'),
    url('^alarm/notify/list/v1$', notify_views.NotificationListAPI.as_view(), name='notify_list'),
    url('^alarm/notify/operation/v1$',
        notify_views.NotificationOperationAPI.as_view(),
        name='notify_operation'),

]