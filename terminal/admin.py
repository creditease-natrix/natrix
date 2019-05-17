# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin
from django.contrib.admin import ModelAdmin

from terminal.models import History, Region, Address, Contact, Organization
from terminal.models import Network, Broadband, Operator, Export

from terminal.models import OrganizationContact, OrganizationNetwork, \
    OrganizationAddress, OrganizationBroadBand

from terminal.models import Terminal, TerminalDevice, RegisterOrganization, PostOperator
# Register your models here.

@admin.register(History)
class HistoryAdmin(ModelAdmin):
    list_display = ['pk', 'model_name', 'pk_field', 'operator', 'operate_date']
    list_filter = ['model_name']


@admin.register(Region)
class RegionAdmin(ModelAdmin):
    list_display = ['citycode', 'province', 'city']
    list_filter = ['province']


@admin.register(Address)
class AddressAdmin(ModelAdmin):
    list_display = ['pk', 'region', 'address', 'postcode']


@admin.register(Contact)
class ContactAdmin(ModelAdmin):
    list_display = ['pk', 'name', 'telephone']


@admin.register(Network)
class NetworkAdmin(ModelAdmin):
    list_display = ['pk', 'segment', 'gateway', 'segment_type']


@admin.register(Operator)
class OperatorAdmin(ModelAdmin):
    list_display = ['pk', 'name']


@admin.register(Broadband)
class BroadbandAdmin(ModelAdmin):
    list_display = ['pk', 'name', 'operator', 'access_type', 'speed']
    list_filter = ['operator', 'access_type']


@admin.register(Organization)
class OrganizationAdmin(ModelAdmin):
    list_display = ['pk', 'name', 'parent', 'level']


@admin.register(Export)
class ExportAdmin(ModelAdmin):
    list_display = ['pk', 'type', 'ip', 'device']


# register relation table
admin.site.register(OrganizationContact)
admin.site.register(OrganizationNetwork)
admin.site.register(OrganizationAddress)
admin.site.register(OrganizationBroadBand)


@admin.register(TerminalDevice)
class TerminalDeviceAdmin(ModelAdmin):
    list_display = ['hostname', 'sn', 'product', 'comment', 'last_online_time']


@admin.register(Terminal)
class TerminalAdmin(ModelAdmin):
    list_display = ['mac', 'type', 'localip', 'status']

@admin.register(RegisterOrganization)
class RegisterOrgAdmin(ModelAdmin):
    list_display = ['pk', 'address', 'comment']


@admin.register(PostOperator)
class PostOperatorAdmin(ModelAdmin):
    list_display = ['id', 'name']
