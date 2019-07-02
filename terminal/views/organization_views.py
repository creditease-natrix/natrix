# -*- coding: utf-8 -*-
"""

"""
from __future__ import unicode_literals
import json
import logging

from django.contrib.auth.models import Group
from django.http import JsonResponse
from django.db.models import Q
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db import transaction

from rest_framework import permissions
from rest_framework.decorators import permission_classes as natrix_permission_classes

from natrix.common.errorcode import ErrorCode
from natrix.common.natrix_views.views import NatrixAPIView, natrix_api_view
from natrix.common.natrix_views.serializers import IDSerializer
from natrix.common import exception as natrix_exception

from terminal.models import Operator, Address
from terminal.models import Organization, Broadband, Contact, Network
from terminal.models import OrganizationContact, OrganizationAddress
from terminal.models import OrganizationNetwork, OrganizationBroadBand
from terminal.configurations import organization_conf as orgconf
# todo: 迁移
from terminal.serializers import organization_serializer

logger = logging.getLogger(__name__)

class OrganizationPermission(permissions.IsAuthenticated):
    """组织管理权限控制

    """
    def has_permission(self, request, view):
        if hasattr(request, 'user_rbac'):
            user_rbac = request.user_rbac
            if user_rbac is None:
                return False

            group = user_rbac.get_group()
            if group is None or not isinstance(group, Group):
                return False

            if group.name == 'admin_group':
                return True
        else:
            return False


class OrganizationAPI(NatrixAPIView):
    """组织部门管理API

    所有关于组织管理相关接口，如标准接口（增删改查）和额外接口（）

    """
    permission_classes = (OrganizationPermission, )
    authentication_classes = []

    def get_object(self):
        pass

    def get(self, request, format=None):
        feedback = {
            'permission': True
        }
        try:
            serializer = IDSerializer(data=request.GET)
            if serializer.is_valid(Organization):
                organization = serializer.get_db()
            else:
                feedback['data'] = ErrorCode.parameter_invalid(
                    'id', reason=json.dumps(serializer.errors, ensure_ascii=False))
                raise natrix_exception.ParameterInvalidException(parameter='id')

            # TODO: 用 REST-framework的方式取代
            org_info = {
                "id": organization.id,
                "name": organization.name,
                "parent": organization.parent_full_name(),
                "level": organization.level,
                "comment": organization.comment
            }

            addresses_info = []
            addresses = organization.get_addresses()
            for item in addresses:
                addr_info = {
                    'province': item.region.province,
                    'city': item.region.city,
                    'address': item.address,
                    'postcode': item.postcode
                }
                addresses_info.append(addr_info)

            contacts_info = []
            contacts = organization.organizationcontact_set.all()
            for item in contacts:
                contact_info = {
                    'name': item.contact.name,
                    'telephone': item.contact.telephone,
                    'email': item.contact.email,
                    'wechat': item.contact.wechat,
                    'identity': item.identity,
                    'identity_verbosename': orgconf.IDENTITY_TYPE_INFO.get(
                        item.identity, {}).get('verbose_name', '')

                }
                contacts_info.append(contact_info)

            networks_info = []
            networks = organization.get_networks()
            for item in networks:
                network_info = {
                    'segment': item.segment,
                    'gateway': item.gateway,
                    'segment_type': item.segment_type,
                    'segment_type_verbosename': orgconf.SEGMENT_TYPES_INFO.get(
                        item.segment_type, {}).get('verbose_name', ''),
                    'comment': item.comment
                }
                networks_info.append(network_info)

            broadbands_info = []
            broadbands = organization.get_broadbands()
            for item in broadbands:
                broadband_info = {
                    'id': item.id,
                    'name': item.name,
                    'operator': item.operator.name,
                    'operator_verbosename': orgconf.OPERATOR_DICT.get(item.operator.name, {}).get('verbose_name', ''),
                    'access_type': item.access_type,
                    'access_type_verbosename': orgconf.BROADBAND_INFO.get(
                        item.access_type, {}).get('verbose_name', ''),
                    'speed': item.speed,
                    'end_time': item.end_time,
                    'staff_contact': item.staff_contact,
                    'staff_contact_email': item.staff_contact_email,
                    'staff_contact_telephone': item.staff_contact_telephone,
                    'isp_contact': item.isp_contact,
                    'isp_contact_email': item.isp_contact_email,
                    'isp_contact_telephone': item.isp_contact_telephone,
                    'comment': item.comment
                }
                broadbands_info.append(broadband_info)

            exports_info = []
            exports = organization.get_exports()
            for item in exports:
                export_info = {
                    'device': item.device,
                    'device_verbosename': orgconf.EXPORT_DEVICE_TYPE_INFO.get(item.device).get('verbose_name', ''),
                    'type': item.type,
                    'type_verbosename': orgconf.EXPORT_TYPE_INFO.get(
                        item.type, {}).get('verbose_name',''),
                    'ip': item.ip,
                    'comment': item.comment
                }
                exports_info.append(export_info)

            devices_info = []
            register_list = organization.registerorganization_set.all()
            terminal_devices = set()
            for register in register_list:
                terminal_devices.update(register.terminaldevice_set.all())

            for item in terminal_devices:
                terminals_info = []
                terminals = item.terminal_set.all()
                for t in terminals:
                    terminal_info = {
                        "mac": t.mac,
                        "id": t.id
                    }
                    terminals_info.append(terminal_info)
                device_info = {
                    "sn": item.sn,
                    "type": item.product,
                    "piclient_version": item.natrixclient_version,
                    "last_online_time": item.last_online_time,
                    "terminals": terminals_info,
                    "comment": item.comment
                }
                devices_info.append(device_info)

            children_info = []
            children = organization.get_children()
            for item in children:
                child_info = {
                    "name": item.name,
                    "level": item.level,
                    "comment": item.comment
                }
                children_info.append(child_info)

            feedback['data'] = {
                "code": 200,
                "message": u"组织详情查询详细信息!",
                "info": {
                    "organization": org_info,
                    "addresses": addresses_info,
                    "contacts": contacts_info,
                    "broadbands": broadbands_info,
                    "networks": networks_info,
                    "exports": exports_info,
                    "devices": devices_info,
                    "children": children_info
                }
            }

        except natrix_exception.BaseException as e:
            logger.info(e.get_log())

        return JsonResponse(data=feedback)

    def post(self, request, format=None):
        feedback = {
            'permission': True
        }
        user = request.user_rbac.user
        group = request.user_rbac.group
        try:
            post_data = request.data
            serializer = organization_serializer.OrganizationSerializer(user=user, group=group, data=post_data)
            if serializer.is_valid():
                serializer.save()
            else:
                logger.error('Create organization error: {}'.format(serializer.format_errors()))
                feedback['data'] = ErrorCode.parameter_invalid('Organization Creation',
                                                               serializer.format_errors())
                raise natrix_exception.ParameterInvalidException(parameter='Organization Creation')

            feedback['data'] = {
                        'code': 200,
                        'message': u'职场添加成功！'
                    }
        except natrix_exception.BaseException as e:
            logger.info(e.get_log())
        except Exception as e:
            natrix_exception.natrix_traceback()
            logger.error('There is an uncatch expection: {}'.format(e))
            feedback['data'] = ErrorCode.sp_code_bug(str(e))

        return JsonResponse(data=feedback)

    def put(self, request, format=None):
        feedback = {
            'permission': True
        }
        try:
            user = request.user_rbac.user
            group = request.user_rbac.group

            post_data = request.data
            serializer = organization_serializer.OrganizationSerializer(
                user=user, group=group, data=post_data)

            if serializer.is_valid():
                instance = serializer.save()
                feedback['data'] = {
                    'code': 200,
                    'message': u'组织修改成功！'
                }
            else:
                logger.error('There are some errors: {}'.format(serializer.format_errors()))
                feedback['data'] = ErrorCode.parameter_invalid(
                    'organization change', serializer.format_errors())

        except natrix_exception.BaseException as e:
            logger.info(e.get_log())

        return JsonResponse(data=feedback)

    def delete(self, request, format=None):
        feedback = {
            'permission': True
        }
        try:
            user = request.user_rbac.user
            group = request.user_rbac.group

            post_data = request.GET
            serializer = IDSerializer(data=post_data)
            if serializer.is_valid(Organization):
                organization = serializer.get_db()
                if organization.id == 1:
                    feedback['data'] = ErrorCode.parameter_invalid('id', reason=u'删除组织结构不存在')
                    raise natrix_exception.ParameterInvalidException(parameter='id')
                elif organization.get_children().count() > 0:
                    feedback['data'] = ErrorCode.parameter_invalid('id', reason=u'该组织存在子组织，不能删除')
                    raise natrix_exception.ParameterInvalidException(parameter='id')
                else:
                    organization.delete(user, group)
                    feedback['data'] = {
                        'code': 200,
                        'message': u'组织删除成功!'
                    }
            else:
                feedback['data'] = ErrorCode.parameter_invalid(
                    'id', reason=json.dumps(serializer.errors, ensure_ascii=False))
                raise natrix_exception.ParameterInvalidException(parameter='id')
        except natrix_exception.ClassInsideException as e:
            logger.info(e.get_log())
            feedback['data'] = ErrorCode.sp_code_bug('IDSerializer error')
        except natrix_exception.BaseException as e:
            logger.info(e.get_log())

        return JsonResponse(data=feedback)

    @staticmethod
    @natrix_api_view(['GET'])
    @natrix_permission_classes((OrganizationPermission, ))
    def get_full_path(request):
        """获取组织链信息

        :param request:
        :return:
        """
        feedback = {
            'permission': True
        }
        try:
            serializer = IDSerializer(data=request.GET)
            if serializer.is_valid(Organization):
                organization = serializer.get_db()
            else:
                feedback['data'] = ErrorCode.parameter_invalid(
                    'id', reason=json.dumps(serializer.errors, ensure_ascii=False))
                raise natrix_exception.ParameterInvalidException(parameter='id')

            full_path_info = []
            while True:
                if organization.level > 0:
                    org_info = {
                        "id": organization.id,
                        "name": organization.name,
                        "level": organization.level
                    }
                    full_path_info.insert(0, org_info)
                    organization = organization.parent
                else:
                    break
            feedback['data'] = {
                "code": 200,
                "message": u"获取组织全链成功!",
                "info": full_path_info
            }

        except natrix_exception.BaseException as e:
            logger.info(e.get_log())

        return JsonResponse(data=feedback)

    @staticmethod
    @natrix_api_view(['GET'])
    @natrix_permission_classes(())
    def get_children(request):
        feedback = {
            'permission': True
        }
        try:
            data = {'id': request.GET.get('parent', None)}
            serializer = IDSerializer(data=data)
            if serializer.is_valid(Organization):
                organization = serializer.get_db()
            else:
                feedback['data'] = ErrorCode.parameter_invalid(
                    'id', reason=json.dumps(serializer.errors, ensure_ascii=False))
                raise natrix_exception.ParameterInvalidException(parameter='id')

            children_info = []
            for item in organization.get_children():
                child_info = dict()
                child_info['id'] = item.id
                child_info['name'] = item.name
                child_info['level'] = item.level
                child_info['comment'] = item.comment
                children_info.append(child_info)

            feedback['data'] = {
                'code': 200,
                'message': u'子组织列表信息',
                'info': children_info
            }

        except natrix_exception.BaseException as e:
            logger.info(e.get_log())

        return JsonResponse(data=feedback)


class OrganizationSummaryAPI(NatrixAPIView):
    permission_classes = (OrganizationPermission,)
    authentication_classes = []

    def get(self, request, format=None):
        feedback = {
            'permission': True
        }
        try:
            id = request.GET.get('id')
            try:
                org_instance = Organization.objects.get(id=id)
                serializer = organization_serializer.OrganizationSerializer(instance=org_instance)
                feedback['data'] = {
                    'code': 200,
                    'message': u'Terminal device summary info!',
                    'info': serializer.summary_presentation()
                }
            except Organization.DoesNotExist:
                feedback['data'] = ErrorCode.parameter_invalid('id', reason=u'Organization record is not exist！')
                raise natrix_exception.ParameterInvalidException(parameter='id')
            except natrix_exception.BaseException as e:
                feedback['data'] = ErrorCode.sp_code_bug(e.get_log())
                raise natrix_exception.ClassInsideException(message=e.get_log())
        except natrix_exception.BaseException as e:
            logger.info(e.get_log())

        return JsonResponse(data=feedback)



class OrganizationList(NatrixAPIView):
    """组织部门列表API

    """
    permission_classes = (OrganizationPermission,)
    authentication_classes = []

    def post(self, request):
        feedback = {
            'permission': True
        }
        try:
            post_data = request.data

            parent = post_data.get('parent', None)
            is_paginate = post_data.get('is_paginate', None)

            search = post_data.get('search', '')
            pagenum = post_data.get('pagenum', 1)

            if parent is None:
                feedback['data'] = ErrorCode.parameter_missing('parent')
                raise natrix_exception.ParameterMissingException(parameter='parent')

            if is_paginate is None:
                feedback['data'] = ErrorCode.parameter_missing('is_paginate')
                raise natrix_exception.ParameterMissingException(parameter='is_paginate')

            try:
                org_parent = Organization.objects.get(id=parent)
            except Organization.DoesNotExist:
                feedback['data'] = ErrorCode.parameter_invalid('parent',
                                                               reason=u'数据不存在！')
                raise natrix_exception.ParameterInvalidException(parameter='parent')

            origin_orgs = []
            parents = [org_parent]
            while len(parents) > 0:
                children = list(Organization.objects.filter(parent__in=parents))
                origin_orgs.extend(children)
                parents = children

            organizations = []
            if search:
                for orgitem in origin_orgs:
                    if search in orgitem.name:
                        organizations.append(orgitem)
                        continue
                    networks = orgitem.networks.all()
                    for net in networks:
                        if search in net.segment:
                            organizations.append(orgitem)
                            break
            else:
                organizations = origin_orgs

            data = {
                'code': 200,
                'message': u'职场信息列表'
            }
            if is_paginate:
                per_page = self.get_per_page()
                painator = Paginator(organizations, per_page)
                try:
                    organizations = painator.page(pagenum)
                except EmptyPage:
                    organizations = painator.page(1)
                except PageNotAnInteger:
                    organizations = painator.page(painator.num_pages)

                data['page_count'] = painator.num_pages
                data['page_num'] = organizations.number

            organizations_info = []

            for org in organizations:
                organizations_info.append({
                    'id': org.id,
                    'name': org.name,
                    'parent': org.parent_full_name(),
                    'level': org.level,
                    'children_num': len(org.get_children())
                })

            data['info'] = organizations_info
            feedback['data'] = data

        except natrix_exception.BaseException as e:
            logger.info(e.get_log())

        return JsonResponse(data=feedback)


class OperatorList(NatrixAPIView):
    """

    """
    permission_classes = (OrganizationPermission,)
    authentication_classes = []

    def get(self, request):
        feedback = {
            'permission': True
        }

        operators = Operator.objects.all()
        feedback['data'] = {
            'code': 200,
            'message': u'所有运营商列表信息',
            'info': map(lambda x: {'id': x.id,
                                   'name': x.name,
                                   'verbose_name': x.verbose_name()},
                        operators)
        }

        return JsonResponse(data=feedback)


class ExportDeviceTypeList(NatrixAPIView):
    """职场出口设备类型列表信息

    """
    permission_classes = (OrganizationPermission,)
    authentication_classes = []

    def get(self, request):
        feedback = {
            'permission': True
        }

        # TODO: hardcode
        feedback['data'] = {
            'code': 200,
            'message': u'所有出口设备类型列表信息',
            'info': orgconf.EXPORT_DEVICE_TYPE_INFO.values()
        }

        return JsonResponse(data=feedback)


class AddressAPI(NatrixAPIView):
    """宽带信息接口

        """
    permission_classes = (OrganizationPermission,)
    authentication_classes = []

    def get(self, request):
        feedback = {
            'permission': True
        }
        try:

            province = request.GET.get('province')
            city = request.GET.get('city')
            address = request.GET.get('address')
            feedback['data'] = {
                "code": 200,
                "message": u"地址信息详情查询成功!",
                "info": {
                    'province': province,
                    'city': city,
                    'address': address,
                    'postcode': None,
                    'comment': None
                }
            }
            try:
                address_obj = Address.objects.get(
                    Q(region__province=province) &
                    Q(region__city=city) &
                    Q(address=address)
                )
                feedback['data']['info']['postcode'] = address_obj.postcode
                feedback['data']['info']['comment'] = ''

            except Address.DoesNotExist:
                pass

        except natrix_exception.BaseException as e:
            logger.info(e.get_log())

        return JsonResponse(data=feedback)


class NetworkAPI(NatrixAPIView):
    permission_classes = (OrganizationPermission,)
    authentication_classes = []

    def get(self, request):
        feedback = {
            'permission': True
        }
        try:

            segment = request.GET.get('segment')
            feedback['data'] = {
                "code": 200,
                "message": u"宽带详情查询成功!",
                "info": {
                    'segment': segment,
                    'segment_type': 'mix',
                    'gateway': None,
                    'comment': None
                }
            }
            try:
                network_obj = Network.objects.get(segment=segment)
                feedback['data']['info'] = {
                    'segment': network_obj.segment,
                    'segment_type': network_obj.segment_type,
                    'gateway': network_obj.gateway,
                    'comment': network_obj.comment
                }
            except Network.DoesNotExist:
                pass


        except natrix_exception.BaseException as e:
            logger.info(e.get_log())

        return JsonResponse(data=feedback)


class ContactAPI(NatrixAPIView):
    permission_classes = (OrganizationPermission,)
    authentication_classes = []

    def get(self, request):
        feedback = {
            'permission': True
        }
        try:

            email = request.GET.get('email')
            feedback['data'] = {
                "code": 200,
                "message": u"联系人详情查询成功!",
                "info": {
                    'email': email,
                    'name': None,
                    'telephone': None,
                    'wechat': None,
                    'comment': None,
                    'identity': 'user'

                }
            }
            try:
                contact_obj = Contact.objects.get(email=email)
                feedback['data']['info'] = {
                    'email': contact_obj.email,
                    'name': contact_obj.name,
                    'telephone': contact_obj.telephone,
                    'wechat': contact_obj.wechat,
                    'comment': contact_obj.comment,
                    'identity': 'user'
                }
            except Contact.DoesNotExist:
                pass

        except natrix_exception.BaseException as e:
            logger.info(e.get_log())

        return JsonResponse(data=feedback)


class BroadbandAPI(NatrixAPIView):
    """宽带信息接口

    """
    permission_classes = (OrganizationPermission,)
    authentication_classes = []

    def get(self, request):
        feedback = {
            'permission': True
        }

        try:
            broadband_id = request.GET.get('id', None)

            try:
                serializer = IDSerializer(data=request.GET)
                if serializer.is_valid(Broadband):
                    broadband = serializer.get_db()
                else:
                    feedback['data'] = ErrorCode.parameter_invalid(
                        'id', reason=json.dumps(serializer.errors, ensure_ascii=False))
                    raise natrix_exception.ParameterInvalidException(parameter='id')

                broadband_info = dict()
                broadband_info["name"] = broadband.name
                broadband_info["operator"] = broadband.operator.name
                broadband_info["operator_verbosename"] = orgconf.OPERATOR_DICT.get(
                    broadband.operator.name, {}).get('verbose_name', '')
                broadband_info["access_type"] = broadband.access_type
                broadband_info["access_type_verbosename"] = orgconf.BROADBAND_INFO.get(
                    broadband.access_type, {}).get('verbose_name', '')
                broadband_info["speed"] = broadband.speed
                broadband_info["start_time"] = broadband.start_time
                broadband_info["end_time"] = broadband.end_time
                broadband_info["staff_contact"] = broadband.staff_contact
                broadband_info["staff_contact_telephone"] = broadband.staff_contact_telephone
                broadband_info["staff_contact_email"] = broadband.staff_contact_email
                broadband_info["isp_contact"] = broadband.isp_contact
                broadband_info["isp_contact_telephone"] = broadband.isp_contact_telephone
                broadband_info["isp_contact_email"] = broadband.isp_contact_email
                broadband_info["comment"] = broadband.comment

                feedback['data'] = {
                    "code": 200,
                    "message": u"宽带详情查询成功!",
                    "info": broadband_info

                }

            except Broadband.DoesNotExist:
                feedback['data'] = ErrorCode.parameter_invalid('id',
                                                               reason=u'数据库中不存在相应数据')
                raise natrix_exception.ParameterInvalidException(parameter='id')

        except natrix_exception.BaseException as e:
            logger.info(e.get_log())

        return JsonResponse(data=feedback)


