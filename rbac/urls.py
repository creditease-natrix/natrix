# -*- coding: utf-8 -*-
"""

"""
from django.conf.urls import url

from rbac.views import user_views, group_views, backend_views

urlpatterns = [

    # provide for dashboard
    url(r'^get/userinfo$', user_views.userinfo_api, name='userinfo_api'),
    url(r'^api/change_group$', user_views.change_group_api, name='group_change_api'),
    url(r'^api/getmenu$', user_views.layout_menu_api, name='user_menu_api'),

    url(r'^login/v1$', user_views.login_authentication, name='login_api'),
    url(r'^logout/v1$', user_views.logout_api, name='logout_api'),
    url(r'^user/register/v1$', user_views.user_register, name='user_register'),

    url(r'^api/colleagues/v1$', user_views.user_colleagues_api, name='colleagues_api'),

    url(r'^user/v1$', user_views.UserAPI.as_view(), name='user_api'),
    url(r'^group/v1$', group_views.GroupAPI.as_view(), name='group_api'),
    url(r'^group/user/v1$', group_views.GroupUserAPI.as_view(), name='group_user_api'),
    url(r'^group/user/list/v1$', group_views.GroupUserList.as_view(), name='group_list_api'),

    url(r'^user/contacts/v1$', backend_views.abstreming_notify_api, name='user_contact_api'),

]
