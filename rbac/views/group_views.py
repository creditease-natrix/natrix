# -*- coding: utf-8 -*-
"""

"""
import logging

from django.http.response import JsonResponse
from django.db import transaction
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.conf import settings

from django.contrib.auth.models import Group, User

from natrix.common.natrix_views import views as natrix_views
from natrix.common.natrix_views import permissions as natrix_permissions
from natrix.common import exception as natrix_exception
from natrix.common.errorcode import ErrorCode

from rbac.models import GroupInfo, Assign, Role, GroupRole
from rbac.api import init_rbac
logger = logging.getLogger(__name__)


class GroupAPI(natrix_views.NatrixAPIView):
    permission_classes = (natrix_permissions.LoginPermission,)
    authentication_classes = []

    def get(self, request):
        feedback = {
            'permission': True
        }
        request_data = request.GET
        groupname = request_data.get('groupname', None)
        try:
            if groupname is not None:
                group = Group.objects.get(name=groupname)
            else:
                group = self.get_group()

            group_roles = GroupRole.objects.filter(group=group)

            info = {
                'groupname': group.name,
                'roles': [{'name': gr.role.name, 'desc': gr.role.desc} for gr in group_roles]
            }

            feedback['data'] = {
                'code': 200,
                'message': 'Group users information',
                'info': info
            }

        except Group.DoesNotExist as e:
            natrix_exception.natrix_traceback()
            feedback['data'] = ErrorCode.sp_code_bug(e)

        return JsonResponse(data=feedback)

    def post(self, request, format=None):
        """groupname can not email address.


        :param request:
        :param format:
        :return:
        """
        feedback = {
            'permission': True
        }
        request_data = request.data
        try:
            # groupname cant be an email address
            groupname = request_data['groupname']
            description = request_data.get('description', None)

            if groupname.find('@') != -1:
                feedback['data'] = ErrorCode.parameter_invalid('groupname', 'The groupname cant contian @!')
                raise natrix_exception.ParameterInvalidException()

            try:
                Group.objects.get(name=groupname)
                feedback['data'] = ErrorCode.parameter_invalid('groupname', 'The group is Exist!')
            except Group.DoesNotExist:
                group = Group.objects.create(name=groupname)
                GroupInfo.objects.create(group=group, desc=description)
                user = self.get_user()
                init_rbac(user, group)

                feedback['data'] = {
                    'code': 200,
                    'message': 'Group creatation successful!'
                }

        except KeyError as e:
            natrix_exception.natrix_traceback()
            feedback['data'] = ErrorCode.parameter_missing('groupname')
        except natrix_exception.NatrixBaseException as e:
            logger.info('{}'.format(e))

        except Exception as e:
            natrix_exception.natrix_traceback()
            feedback['data'] = ErrorCode.sp_code_bug(e)


        return JsonResponse(data=feedback)


class GroupUserAPI(natrix_views.NatrixAPIView):
    permission_classes = (natrix_permissions.LoginPermission,)
    authentication_classes = []

    def get(self, request):
        feedback = {
            'permission': True
        }
        try:
            request_data = request.GET
            username = request_data.get('username', None)

            if username is not None:
                user = User.objects.get(username=username)
            else:
                user = self.get_user()
            group = self.get_group()
            info = {
                'username': user.username,
                'email': user.email,
            }
            assigns = Assign.objects.filter(user=user, group=group)
            info['roles'] = [{'name': a.role.name, 'desc': a.role.desc } for a in assigns]

            feedback['data'] = {
                'code': 200,
                'message': 'Group member information!',
                'info': info
            }

        except User.DoesNotExist as e:
            natrix_exception.natrix_traceback()
            feedback['data'] = ErrorCode.sp_code_bug(e)
        except Exception as e:
            natrix_exception.natrix_traceback()
            feedback['data'] = ErrorCode.sp_code_bug(e)

        return JsonResponse(data=feedback)

    def post(self, request, format=None):
        """Must admin_role has the permission

        :param request:
        :param format:
        :return:
        """
        feedback = {
            'permission': True
        }
        try:
            if not request.user_rbac.is_admin():
                feedback['data'] = ErrorCode.permission_deny('You is not admin role!')
                raise natrix_exception.PermissionException()

            reqeust_data = request.data
            username = reqeust_data.get('username', None)
            roles = reqeust_data.get('roles', [])
            if username is None:
                feedback['data'] = ErrorCode.parameter_missing('username')
                raise natrix_exception.PermissionException()


            if not roles:
                feedback['data'] = ErrorCode.parameter_missing('roles')
                raise natrix_exception.PermissionException()

            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist as e:
                feedback['data'] = ErrorCode.parameter_invalid('username', reason='User is not exist')
                raise natrix_exception.ParameterInvalidException()

            group = self.get_group()
            assign_count = Assign.objects.filter(user=user, group=group).count()
            if assign_count > 0:
                feedback['data'] = ErrorCode.parameter_invalid('username', reason='User had joined group!')
                raise natrix_exception.ParameterInvalidException()

            role_list = Role.objects.filter(name__in=roles)
            for r in role_list:
                Assign.objects.create(user=user, group=group, role=r)

            feedback['data'] = {
                'code': 200,
                'message': 'Add new member successfully!'
            }

        except natrix_exception.NatrixBaseException as e:
            logger.info('{}'.format(e))

        except Exception as e:
            natrix_exception.natrix_traceback()
            feedback['data'] = ErrorCode.sp_code_bug(e)

        return JsonResponse(data=feedback)

    def put(self, request, format=None):
        feedback = {
            'permission': True
        }
        try:
            if not request.user_rbac.is_admin():
                feedback['data'] = ErrorCode.permission_deny('You is not admin role!')
                raise natrix_exception.PermissionException()

            request_data = request.data
            username = request_data.get('username', None)
            roles = request_data.get('roles', [])
            if username is None:
                feedback['data'] = ErrorCode.parameter_missing('username')
                raise natrix_exception.PermissionException()
            if not roles:
                feedback['data'] = ErrorCode.parameter_missing('roles')
                raise natrix_exception.PermissionException()

            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist as e:
                feedback['data'] = ErrorCode.parameter_invalid('username', reason='User is not exist')
                raise natrix_exception.ParameterInvalidException()

            group = self.get_group()
            assigns = Assign.objects.filter(user=user, group=group)
            if assigns.count() == 0:
                feedback['data'] = ErrorCode.parameter_invalid('username', reason='User had not joined group!')
                raise natrix_exception.ParameterInvalidException()

            with transaction.atomic():
                for a in assigns:
                    a.delete()

                role_list = Role.objects.filter(name__in=roles)
                for r in role_list:
                    Assign.objects.create(user=user, group=group, role=r)

            feedback['data'] = {
                'code': 200,
                'message': 'Edit member successfully!'
            }

        except natrix_exception.NatrixBaseException as e:
            logger.info('{}'.format(e))
        except Exception as e:
            natrix_exception.natrix_traceback()
            feedback['data'] = ErrorCode.sp_code_bug(e)


        return JsonResponse(data=feedback)

    def delete(self, request):
        feedback = {
            'permission': True
        }
        try:
            if not request.user_rbac.is_admin():
                feedback['data'] = ErrorCode.permission_deny('You is not admin role!')
                raise natrix_exception.PermissionException()

            request_data = request.GET
            username = request_data.get('username', None)

            if username is None:
                feedback['data'] = ErrorCode.parameter_missing('username')
                raise natrix_exception.PermissionException()
            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist as e:
                feedback['data'] = ErrorCode.parameter_invalid('username', reason='User is not exist')
                raise natrix_exception.ParameterInvalidException()

            group = self.get_group()
            if group.name == username or (username==settings.ADMIN_USERNAME and
                                          group.name == settings.ADMIN_GROUP):
                feedback['data'] = ErrorCode.parameter_invalid(
                    'username', 'Can not remove yourself from your default group')
                raise natrix_exception.ParameterInvalidException()

            assigns = Assign.objects.filter(user=user, group=group)
            for a in assigns:
                a.delete()

            feedback['data'] = {
                'code': 200,
                'message': 'Remove member successfully!'
            }

        except natrix_exception.NatrixBaseException as e:
            logger.info('{}'.format(e))
        except Exception as e:
            natrix_exception.natrix_traceback()
            feedback['data'] = ErrorCode.sp_code_bug(e)


        return JsonResponse(data=feedback)


class GroupUserList(natrix_views.NatrixAPIView):
    permission_classes = (natrix_permissions.LoginPermission,)
    authentication_classes = []

    def get(self, request):
        feedback = {
            'permission': True
        }
        try:
            request_data = request.GET
            is_paginate = request_data.get('is_paginate', None)
            pagenum = request_data.get('pagenum', 1)
            if is_paginate is None:
                feedback['data'] = ErrorCode.parameter_missing('is_paginate')
                raise natrix_exception.PermissionException()
            group_members = request.user_rbac.get_colleague()

            feedback['data'] = {
                'code': 200,
                'message': 'Group member list',
                'item_count': len(group_members),
                'opt_permission': False,
                'info': []
            }
            if request.user_rbac.is_admin():
                feedback['data']['opt_permission'] = True

            if is_paginate.upper() == 'TRUE':
                per_page = self.get_per_page()
                paginator = Paginator(group_members, per_page)
                try:
                    current_page_query = paginator.page(pagenum)
                except PageNotAnInteger:
                    current_page_query = paginator.page(1)
                except EmptyPage:
                    current_page_query = paginator.page(paginator.num_pages)

                group_members = list(current_page_query)

                feedback['data']['page_num'] = current_page_query.number
                feedback['data']['page_count'] = paginator.num_pages
            group = self.get_group()
            for record in group_members:
                assigns = Assign.objects.filter(user=record, group=group)

                feedback['data']['info'].append({
                    'username': record.username,
                    'email': record.email,
                    'roles': [a.role.name for a in assigns]
                })

        except natrix_exception.NatrixBaseException as e:
            logger.info('{}'.format(e))
        except Exception as e:
            natrix_exception.natrix_traceback()
            feedback['data'] = ErrorCode.sp_code_bug(e)


        return JsonResponse(data=feedback)

