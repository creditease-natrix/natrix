# -*- coding: utf-8 -*-
"""

"""
from __future__ import unicode_literals
import json

from django.http import JsonResponse
from django.db.models import Q
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from rest_framework.decorators import permission_classes as natrix_permission_classes

from natrix.common.errorcode import ErrorCode
from natrix.common.natrix_views.views import NatrixAPIView, LoginAPIView, natrix_api_view, RoleBasedAPIView
from natrix.common.natrix_views.permissions import LoginPermission
from natrix.common.natrix_views.serializers import IDSerializer
from natrix.common import exception as natrix_exception
from natrix.common.natrixlog import NatrixLogging

from terminal.models import Address
from terminal.models import Organization, Contact
from terminal.configurations import organization_conf as orgconf
from terminal.serializers import organization_serializer

logger = NatrixLogging(__name__)


class OrganizationAPI(RoleBasedAPIView):
    """组织部门管理API

    所有关于组织管理相关接口，如标准接口（增删改查）和额外接口（）

    """
    natrix_roles = ['admin_role']

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
                if self.get_group() != organization.group:
                    feedback['data'] = ErrorCode.parameter_invalid(
                        'id', reason='There is not organization({}) in your group!'.format(organization.pk))
                    raise natrix_exception.ParameterInvalidException(parameter='id')
            else:
                feedback['data'] = ErrorCode.parameter_invalid(
                    'id', reason=json.dumps(serializer.errors, ensure_ascii=False))
                raise natrix_exception.ParameterInvalidException(parameter='id')

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
                "message": u"Organization detailed information!",
                "info": {
                    "organization": org_info,
                    "addresses": addresses_info,
                    "contacts": contacts_info,
                    "devices": devices_info,
                    "children": children_info
                }
            }

        except natrix_exception.NatrixBaseException as e:
            logger.info(e.get_log())

        return JsonResponse(data=feedback)

    def post(self, request, format=None):
        feedback = {
            'permission': True
        }

        if not self.has_permission(self.natrix_roles):
            feedback['data'] = ErrorCode.permission_deny('You dont have permission')
            return JsonResponse(data=feedback)

        user = request.user_rbac.user
        group = self.get_group()
        try:
            post_data = request.data
            serializer = organization_serializer.OrganizationSerializer(
                user=user, group=group, data=post_data)
            if serializer.is_valid():
                serializer.save()
            else:
                logger.error('Create organization error: {}'.format(serializer.format_errors()))
                feedback['data'] = ErrorCode.parameter_invalid('Organization Creation',
                                                               serializer.format_errors())
                raise natrix_exception.ParameterInvalidException(parameter='Organization Creation')

            feedback['data'] = {
                        'code': 200,
                        'message': u'Add a new organization successfully！'
                    }
        except natrix_exception.NatrixBaseException as e:
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

        if not self.has_permission(self.natrix_roles):
            feedback['data'] = ErrorCode.permission_deny('You dont have permission')
            return JsonResponse(data=feedback)

        try:
            user = request.user_rbac.user
            group = self.get_group()

            request_data = request.data
            serializer = organization_serializer.OrganizationSerializer(
                user=user, group=group, data=request_data)

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

        except natrix_exception.NatrixBaseException as e:
            logger.info(e.get_log())

        return JsonResponse(data=feedback)

    def delete(self, request, format=None):
        feedback = {
            'permission': True
        }

        if not self.has_permission(self.natrix_roles):
            feedback['data'] = ErrorCode.permission_deny('You dont have permission')
            return JsonResponse(data=feedback)

        try:
            group = self.get_group()
            user = self.get_user()

            post_data = request.GET
            serializer = IDSerializer(data=post_data)
            if serializer.is_valid(Organization):
                organization = serializer.get_db()
                if organization.id == 1:
                    feedback['data'] = ErrorCode.parameter_invalid('id', reason='The organization is not exist!')
                    raise natrix_exception.ParameterInvalidException(parameter='id')
                elif organization.get_children().count() > 0:
                    feedback['data'] = ErrorCode.parameter_invalid(
                                        'id', reason='There are sub-organizations in this organization')
                    raise natrix_exception.ParameterInvalidException(parameter='id')
                elif organization.group != self.get_group():
                    feedback['data'] = ErrorCode.parameter_invalid(
                        'id', reason='There is not organization({}) in your group!'.format(organization.pk)
                    )
                    raise natrix_exception.ParameterInvalidException(parameter='id')
                else:
                    organization.delete(user, group)
                    feedback['data'] = {
                        'code': 200,
                        'message': 'Delete organization successfully!'
                    }
            else:
                feedback['data'] = ErrorCode.parameter_invalid(
                    'id', reason=json.dumps(serializer.errors, ensure_ascii=False))
                raise natrix_exception.ParameterInvalidException(parameter='id')
        except natrix_exception.ClassInsideException as e:
            logger.info(e.get_log())
            feedback['data'] = ErrorCode.sp_code_bug('IDSerializer error')
        except natrix_exception.NatrixBaseException as e:
            logger.info(e.get_log())

        return JsonResponse(data=feedback)

    @staticmethod
    @natrix_api_view(['GET'])
    @natrix_permission_classes((LoginPermission, ))
    def get_full_path(request):
        """获取组织链信息

        :param request:
        :return:
        """
        feedback = {
            'permission': True
        }
        try:
            user_group = request.user_rbac.get_group() if request.user_rbac else None

            if user_group is None:
                feedback['data'] = ErrorCode.permission_deny('You must add a group!')
                raise natrix_exception.PermissionException(reason='User without a group')

            serializer = IDSerializer(data=request.GET)
            if serializer.is_valid(Organization):
                organization = serializer.get_db()
            else:
                feedback['data'] = ErrorCode.parameter_invalid(
                    'id', reason=json.dumps(serializer.errors, ensure_ascii=False))
                raise natrix_exception.ParameterInvalidException(parameter='id')

            if not (organization.group == user_group):
                feedback['data'] = ErrorCode.parameter_invalid(
                    'id', reason='There is not organization({}) in your group!'.format(request.GET.get('id'))
                )
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

        except natrix_exception.NatrixBaseException as e:
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
            user_group = request.user_rbac.get_group() if request.user_rbac else None

            if user_group is None:
                feedback['data'] = ErrorCode.permission_deny('You must add a group!')
                raise natrix_exception.PermissionException(reason='User without a group')


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
                if item.group != user_group:
                    continue

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

        except natrix_exception.NatrixBaseException as e:
            logger.info(e.get_log())

        return JsonResponse(data=feedback)


class OrganizationSummaryAPI(LoginAPIView):

    def get(self, request, format=None):
        feedback = {
            'permission': True
        }
        try:
            id = request.GET.get('id')
            try:
                org_instance = Organization.objects.get(id=id, group=self.get_group())
                serializer = organization_serializer.OrganizationSerializer(instance=org_instance)
                feedback['data'] = {
                    'code': 200,
                    'message': u'Terminal device summary info!',
                    'info': serializer.summary_presentation()
                }
            except Organization.DoesNotExist:
                feedback['data'] = ErrorCode.parameter_invalid('id', reason=u'Organization record is not exist！')
                raise natrix_exception.ParameterInvalidException(parameter='id')
            except natrix_exception.NatrixBaseException as e:
                feedback['data'] = ErrorCode.sp_code_bug(e.get_log())
                raise natrix_exception.ClassInsideException(message=e.get_log())
        except natrix_exception.NatrixBaseException as e:
            logger.info(e.get_log())

        return JsonResponse(data=feedback)


class OrganizationList(LoginAPIView):
    """组织部门列表API

    """

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
                if parent == 1:
                    org_parent = Organization.objects.get(id=parent)
                else:
                    org_parent = Organization.objects.get(id=parent, group=self.get_group())
            except Organization.DoesNotExist:
                feedback['data'] = ErrorCode.parameter_invalid('parent',
                                                               reason='The organization is not exist！')
                raise natrix_exception.ParameterInvalidException(parameter='parent')

            origin_orgs = []
            parents = [org_parent]
            user_group = self.get_group()
            while len(parents) > 0:
                children = list(Organization.objects.filter(parent__in=parents, group=user_group))
                origin_orgs.extend(children)
                parents = children

            organizations = []
            if search:
                for orgitem in origin_orgs:
                    if search in orgitem.name:
                        organizations.append(orgitem)
                        continue
            else:
                organizations = origin_orgs

            data = {
                'code': 200,
                'message': u'职场信息列表',
                'item_count': len(organizations)
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

        except natrix_exception.NatrixBaseException as e:
            logger.info(e.get_log())

        return JsonResponse(data=feedback)


class AddressAPI(LoginAPIView):
    """
    """

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
            except Address.MultipleObjectsReturned:
                pass

        except natrix_exception.NatrixBaseException as e:
            logger.info(e.get_log())

        return JsonResponse(data=feedback)


class ContactAPI(LoginAPIView):

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

        except natrix_exception.NatrixBaseException as e:
            logger.info(e.get_log())

        return JsonResponse(data=feedback)

