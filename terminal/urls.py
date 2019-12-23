# -*- coding: utf-8 -*-
from django.conf.urls import url

from terminal.views import organization_views, region_views, terminal_views, common_views, security_views


urlpatterns = [
    url(r'^common/provinces/v1', region_views.get_provinces, name='get_provinces'),
    url(r'^common/cities/v1', region_views.get_cities, name='get_cities'),
    url(r'^common/terminals/list/v1', common_views.TerminalListAPI.as_view(), name='common_terminal_list'),
    url(r'^common/terminals/count/v1', common_views.TerminalCountAPI.as_view(), name='common_terminal_count'),

    url(r'^post/basic/v1$', terminal_views.DeviceBasicPostAPI.as_view(), name='basic_post'),
    url(r'^post/advance/v1$', terminal_views.DeviceAdvancePostAPI.as_view(), name='advance_post'),

    url(r'^device/overview/v1', terminal_views.TerminalOverviewAPI.as_view(), name='device_overview'),
    url(r'^device/list/v1', terminal_views.DeviceListAPI.as_view(), name='device_list'),
    url(r'^device/operation/v1', terminal_views.DeviceOperationAPI.as_view(), name='device_operation'),
    url(r'^device/basic/v1', terminal_views.DeviceBasicAPI.as_view(), name='device_basic'),
    url(r'^device/hardware/v1', terminal_views.DeviceHardwareAPI.as_view(), name='device_hardware'),
    url(r'^device/os/v1', terminal_views.DeviceOSAPI.as_view(), name='device_os'),
    url(r'^device/postinfo/v1', terminal_views.TerminalPostAPI.as_view(), name='device_post'),

    url(r'^terminal/operation/v1', terminal_views.TerminalOperationAPI.as_view(), name='terminal_operation'),
    url(r'^terminal/list/v1', terminal_views.TerminalListAPI.as_view(), name='terminal_list'),

    url(r'^organization/v1', organization_views.OrganizationAPI.as_view(), name='organization'),
    url(r'^organization/summary/v1', organization_views.OrganizationSummaryAPI.as_view(), name='organization_summary'),
    url(r'^organization/list/v1', organization_views.OrganizationList.as_view(), name='organization_list'),
    url(r'^organization/children/v1', organization_views.OrganizationAPI.get_children, name='get_children'),
    url(r'^organization/get_full_path/v1', organization_views.OrganizationAPI.get_full_path, name='get_full_path'),
    # url(r'^organization/terminal/v1', terminal_views.TerminalAPI.as_view(), name='terminal_detail'),
    url(r'^organization/address/v1', organization_views.AddressAPI.as_view(), name='address_api'),
    url(r'^organization/contact/v1', organization_views.ContactAPI.as_view(), name='contact_api'),


    # security url
    url(r'^licenses/list/v1', security_views.LicenseListAPI.as_view(), name='license_list'),
    url(r'^licenses/apply/v1', security_views.LicenseApplyAPI.as_view(), name='licese_apply'),

    url(r'^conn/user', security_views.mq_user_auth, name='mq_user_auth'),
    url(r'^conn/vhost', security_views.mq_vhost_auth, name='mq_vhost_auth'),
    url(r'^conn/resource', security_views.mq_resource_auth, name='mq_resource_auth'),
    url(r'^conn/topic', security_views.mq_topic_auth, name='mq_topic_auth'),

]