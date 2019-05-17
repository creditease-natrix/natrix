# -*- coding: utf-8 -*-
from django.conf.urls import url

from rbac import views

urlpatterns = [
    url(r'^change_group/(?P<id>[0-9\-]+)$',
        views.ChangeGroupView.as_view(),
        name='rbac_change_group'),
    url(r'^portal/change_group/(?P<id>[0-9\-]+)$',
        views.PortalChangeGroupView.as_view(),
        name='rbac_portal_change_group'),
    url(r'^portal_change_group/(?P<id>[0-9\-]+)/(?P<url>[\w\W]+)$',
        views.PortalChangeGroupView.as_view(),
        name='portal_change_group'),

    url(r'^user/manage/$', views.UserManageView.as_view(), name="user_manage"),
    url(r'^user/add/$', views.UserAddView.as_view(), name="user_add"),
    url(r'^user/edit/(?P<userid>\d+)/$', views.UserEditView.as_view(), name="user_edit"),

    url(r'^group/add/$', views.GroupAddView.as_view(), name="group_add"),
    url(r'^group/del/(?P<userid>\d+)/$', views.user_del, name="user_del"),

    url(r'^userinfo$', views.UserView.as_view(),
        name='userinfo'),


    # provide for dashboard
    url(r'^get/userinfo$', views.get_userinfo, name='get_user'),
    url(r'^api/change_group$', views.change_group, name='api_change_group'),
    url(r'^api/getmenu$', views.layout_menu, name='front_menu'),
    url(r'^api/get/colleagues$', views.get_colleagues, name='api_colleagues'),

    url(r'^login$', views.front_login, name='front_login'),
    url(r'^logout$', views.front_logout, name='front_logout'),

]
