# -*- coding: utf-8 -*-
from django.conf.urls import url

from rbac import views

urlpatterns = [

    # provide for dashboard
    url(r'^get/userinfo$', views.get_userinfo, name='get_user'),
    url(r'^api/change_group$', views.change_group, name='api_change_group'),
    url(r'^api/getmenu$', views.layout_menu, name='front_menu'),
    url(r'^api/get/colleagues$', views.get_colleagues, name='api_colleagues'),

    url(r'^login/v1$', views.front_login, name='front_login'),
    url(r'^logout/v1$', views.front_logout, name='front_logout'),
    url(r'^user/register/v1$', views.front_register, name='front_register'),

]
