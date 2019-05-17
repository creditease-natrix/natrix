# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging
import json

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import authenticate, login, logout

from django.views.generic import View
from django.views.generic import TemplateView
from django.shortcuts import render
from django.shortcuts import redirect
from django.http import JsonResponse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib.auth.models import User, Group
from django.views.decorators.csrf import csrf_exempt

from natrix.common import common_views
from rbac.models import Assign, Role, UserRBAC, GroupRole, UserInfo
from rbac import forms
from rbac import api
from .menu import get_menu


import rbac
# Create your views here.

logger = logging.getLogger(__name__)


class RBACView(common_views.BaseRBACView):
    permission_role = ['admin_role',]

    def get_context_data(self, *args, **kwargs):
        self.other_response = None
        context = super(RBACView,
                        self).get_context_data(*args, **kwargs)
        context['permission'] = self.has_permission()
        return context


class BaseView(View):
    pass


class StaffRbacView(common_views.BaseRBACView):
    """StaffRbacView为RBAC管理视图提供的父类，必须为登录用户才能进行访问！"""
    permission_role = ['admin_role']

    def is_admin_role(self):
        """判断当前用户是否是管理员"""
        user_rbac = self.request.user_rbac
        if user_rbac and user_rbac.has_role(str("admin_role")):
            return True
        else:
            return False


class BaseTemplateView(TemplateView, BaseView):

    def get_context_data(self, *args, **kwargs):
        context = super(BaseTemplateView,
                        self).get_context_data(*args, **kwargs)
        return context


class ChangeGroupView(LoginRequiredMixin, BaseView):
    """raspi入口登录修改，'组切换'逻辑"""

    def get(self, *args, **kwargs):
        group_id = int(self.kwargs['id'])

        group = Group.objects.get(id=group_id)

        rbac.change_rbac_group(self.request, group)

        api.update_last_login(self.request.user, group)


        pre_url = self.kwargs.get('url', None)
        pre_url = pre_url if not pre_url is None else '/'
        response = redirect(pre_url)

        # return HttpResponseRedirect('/')
        return response


class PortalChangeGroupView(LoginRequiredMixin, BaseView):
    """切换用户组：用于通过portal入口进入的用户"""
    def get(self, *args, **kwargs):
        group_id = int(self.kwargs['id'])
        pre_url = self.kwargs.get('url', None)
        pre_url = pre_url if not pre_url is None else '/'

        group = Group.objects.get(id=group_id)
        rbac.change_rbac_group(self.request, group)

        api.update_last_login(self.request.user, group)

        response = redirect(pre_url)

        # return HttpResponseRedirect('/benchmark/portal/task')
        return response


class UserManageView(RBACView):
    """RBAC用户管理界面，列表界面"""
    template_name = "user/userlist.html"

    def get_context_data(self, *args, **kwargs):
        context = super(UserManageView, self).get_context_data(*args, **kwargs)

        rbac = self.request.user_rbac
        group = rbac.get_group()
        relations = Assign.objects.filter(group=group)
        user_role_dict = {}

        for r in relations:
            user = r.user
            if user_role_dict.get(user.id, None) is None:
                user_role_dict[user.id] = {"name": user.username,
                                           "id": user.id,
                                           "email": user.email,
                                           "phone": user.userinfo.phone if hasattr(user, 'userinfo') else '',
                                           "roles":[]}

            user_role_dict[user.id]["roles"].append(r.role.name)

        paginator = Paginator(user_role_dict.values(), context['per_page'])
        page = self.request.GET.get('page')
        try:
            user_page = paginator.page(page)
        except PageNotAnInteger:
            user_page = paginator.page(1)
        except EmptyPage:
            user_page = paginator.page(paginator.num_pages)

        context['page'] = page
        context["info_dict"] = user_page
        return context


class UserAddView(LoginRequiredMixin, BaseTemplateView):
    """用户添加界面"""
    template_name = "user/user_add.html"

    def get_context_data(self, *args, **kwargs):
        context = super(UserAddView, self).get_context_data(*args, **kwargs)
        request = self.request
        add_form = forms.UserAddForm()
        add_form.init(request)

        context["add_form"] = add_form
        return context

    def post(self, request, *args, **kwargs):
        curr_user_rbac = request.user_rbac
        if not curr_user_rbac.has_role(str("admin_role")):
            messages.add_message(request, messages.ERROR, "你没有权限添加用户")
            response = redirect('user_manage')
            return response

        form_data = forms.UserAddForm(request.POST)
        form_data.init(request)

        if form_data.is_valid():
            form_cleaned = form_data.cleaned_data
            user_id = form_cleaned["user"]
            role_ids = form_cleaned["roles"]
            try:
                user = User.objects.get(pk=user_id)
                user_rbac = UserRBAC(user)
                roles = Role.objects.filter(pk__in=role_ids)
                group = curr_user_rbac.get_group()
                users = Assign.objects.filter(group=group).values("user")
                id_set = set()
                for u in users:
                    id_set.add(u.get('user'))
                if user.id in id_set:
                    raise ExistDataException
                if len(roles) == 0:
                    raise Role.DoesNotExist
                if group is None:
                    raise Group.DoesNotExist
                for r in roles:
                    result = user_rbac.assign(role=r, group=group)
                    if not result:
                        raise TypeError
                messages.add_message(request, messages.SUCCESS, "添加用户成功！")

            except User.DoesNotExist:
                messages.add_message(request, messages.ERROR, "不存在指定用户！")
            except Role.DoesNotExist:
                messages.add_message(request, messages.ERROR, "不存在指定的角色！")
            except Group.DoesNotExist:
                messages.add_message(request, messages.ERROR, "不存在指定的组！")
            except TypeError:
                messages.add_message(request, messages.ERROR, "赋权失败！")
            except ExistDataException:
                messages.add_message(request, messages.ERROR, "数据已存在！")

            response = redirect('user_manage')
            return response
        else:
            messages.add_message(request, messages.ERROR, form_data.errors)

        return render(request, "user/user_add.html",{"add_form": form_data})


class UserEditView(StaffRbacView):
    """用户角色修改视图"""
    template_name = "user/user_edit.html"

    def get_context_data(self, *args, **kwargs):
        context = super(UserEditView, self).get_context_data(*args, **kwargs)
        return context

    def post(self, request, *args, **kwargs):

        response = redirect('user_manage')
        if not self.has_permission():
            messages.add_message(request, messages.ERROR, "你没有权限编辑用户")
            return response

        user_id = kwargs.get('userid', None)
        if not user_id is None:
            user_id = int(user_id)
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                messages.add_message(request, messages.ERROR, "编辑用户不存在")
                return response

            # 初始化edit_form
            user_rbac = request.user_rbac
            group = user_rbac.get_group()
            group_roles = GroupRole.objects.filter(group=group)
            roles = []
            for gr in group_roles:
                roles.append(gr.role)

            assigns = Assign.objects.filter(group=group, user=user)
            select_roles = []
            for a in assigns:
                select_roles.append(a.role)

            edit_form = forms.UserEditForm()
            edit_form.init(user, roles, select_roles)
            form_data = forms.UserEditForm(request.POST)
            form_data.init(user, roles, select_roles)

            if form_data.is_valid():
                form_cleaned = form_data.cleaned_data
                role_ids = form_cleaned["roles"]
                roles = Role.objects.filter(pk__in=role_ids)
                Assign.objects.filter(group=group, user=user).delete()
                for r in roles:
                    try:
                        Assign.objects.get(role=r, group=group, user=user)
                    except Assign.DoesNotExist:
                        Assign.objects.create(role=r, group=group, user=user)
                messages.add_message(request, messages.SUCCESS, "用户信息已修改")
                return response
            else:
                messages.add_message(request, messages.ERROR, form_data.errors)

        return render(request, "user/user_edit.html", {"edit_form": form_data,
                                                       "user_id": user_id})

    def get(self, request, *args, **kwargs):
        response = redirect('user_manage')
        if not self.is_admin_role():
            messages.add_message(request, messages.ERROR, "你没有权限编辑用户")
            return response
        context = self.get_context_data(*args, **kwargs)

        user_id = kwargs.get('userid', None)
        if user_id is None:
            messages.add_message(request, messages.ERROR, "传入错误用户信息！")
        else:
            user_id = int(user_id)
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                messages.add_message(request, messages.ERROR, "编辑用户不存在")
                return response

            user_rbac = request.user_rbac
            group = user_rbac.get_group()
            group_roles = GroupRole.objects.filter(group=group)
            roles = []
            for gr in group_roles:
                roles.append(gr.role)

            assigns = Assign.objects.filter(group=group,user=user)
            select_roles = []
            for a in assigns:
                select_roles.append(a.role)

            edit_form = forms.UserEditForm()
            edit_form.init(user, roles, select_roles)

            context['edit_form'] = edit_form
            context['user_id'] = user_id


        return self.render_to_response(context)


class GroupAddView(LoginRequiredMixin, BaseTemplateView):
    """组添加界面"""
    template_name = "user/group_add.html"

    def get_context_data(self, *args, **kwargs):
        context = super(GroupAddView, self).get_context_data(*args, **kwargs)

        return context

    def post(self, *args, **kwargs):
        request = self.request
        post_data = request.POST
        curr_user_rbac = request.user_rbac
        action = post_data.get('action', None)
        if action and curr_user_rbac:
            if action == "add":
                group_name = post_data.get("group_name", None)
                if group_name is None:
                    result = {
                        "code": 1,
                        "msg": "给定错误的组名称！"
                    }
                    return JsonResponse(result)
                groups = Group.objects.filter(name=group_name).all()
                if len(groups) == 0:
                    group = api.create_group(group_name)
                    if group:
                        api.init_rbac(curr_user_rbac.user, group)

                    else:
                        logger.info("初始化rbac角色失败！")
                        result = {
                            "code": 1,
                            "msg": "创建组失败！"
                        }
                        return JsonResponse(result)
                    result = {
                        "code": 0,
                        "msg": "创建组成功！"
                    }
                    return JsonResponse(result)

                else:
                    result = {
                        "code": 1,
                        "msg": "该组名称也存在！"
                    }
                    return JsonResponse(result)
            else:
                pass
        else:
            result = {
                "code": 1,
                "msg": "创建失败"
            }
            return JsonResponse(result)


def user_del(request, userid):
    """用户删除逻辑"""
    curr_user_rbac = request.user_rbac
    response = redirect('user_manage')

    if curr_user_rbac and userid:
        if curr_user_rbac.has_role(str("admin_role")):
            group = curr_user_rbac.get_group()
            user = None
            try:
                user = User.objects.get(pk=userid)
            except User.DoesNotExist:
                messages.add_message(request, messages.ERROR, u"删除用户不存在！")
                return response

            if group and user:
                Assign.objects.filter(user=user, group=group).delete()
                messages.add_message(request, messages.SUCCESS, u"用户删除成功")
            else:
                messages.add_message(request, messages.ERROR, u"您要删除的用户信息有误！")
            return response
        else:
            messages.add_message(request, messages.ERROR, u"您没有权限删除用户！")
            return response

    else:
        messages.add_message(request, messages.ERROR, u"您当前的权限环境有问题！")
        return response


class UserView(StaffRbacView):
    template_name = 'user/userinfo.html'

    def get_context_data(self, *args, **kwargs):
        context = super(UserView, self).get_context_data(*args, **kwargs)
        groups = self.get_groups()
        if not hasattr(self.request.user, 'userinfo'):
            UserInfo.objects.create(user=self.request.user)


        context['groups'] = groups
        context['page_choices'] = [5, 10, 20, 50]
        return context

    def post(self, request, *args, **kwargs):
        response = redirect('userinfo')
        data = request.POST
        email = data.get('email', '').strip()
        phone = data.get('phone', '').strip()
        per_page = data.get('per_page', '10').strip()
        per_page = int(per_page)

        user = self.get_user()
        if user.email != email:
            user.email = email
            user.save()

        try:
            userinfo = UserInfo.objects.get(user=user)
        except UserInfo.DoesNotExist:
            userinfo = UserInfo()
            userinfo.user = user

        userinfo.phone = phone
        userinfo.per_page = per_page
        userinfo.save()
        messages.add_message(request, messages.SUCCESS, u'信息修改成功！')
        return response



def get_userinfo(request):
    feedback = {
        'permission': True
    }
    userinfo = {}
    if hasattr(request, 'user_rbac'):
        user_rbac = request.user_rbac
        if user_rbac:
            groups = map(lambda x: x[0], user_rbac.groups())

            feedback['data'] = {
                'code': 200,
                'user': user_rbac.user.username,
                'curr_group': user_rbac.get_group().name if user_rbac.get_group() else None,
                'groups': map(lambda g: {'id': g.id, 'name': g.name}, groups)
            }
        else:
            feedback['data'] = {
                'code': 400,
                'message': u'用户未登录'
            }

    return JsonResponse(data=feedback)


def get_colleagues(request):
    feedback = {
        'permission': True
    }
    if hasattr(request, 'user'):
        colleagues = request.user_rbac.get_colleague()
        feedback['data'] = {
            'code': 200,
            'message': u'同组用户信息列表',
            'colleagures': map(lambda c: {'id': c.id,
                                          'name': c.username,
                                          'email': c.email if c.email else '',
                                          'phone': '' if c.userinfo.phone is None or c.userinfo.phone=='None' else c.userinfo.phone
                                          },
                               colleagues)
        }

    else:
        feedback['data'] = {
            'code': 400,
            'message': u'用户未登录'
        }

    return JsonResponse(data=feedback)

@csrf_exempt
def change_group(request):
    # data = request.POST
    data = json.loads(request.body if request.body else '{}')


    group_id = data.get('id', None)
    try:
        if group_id is None:
            logger.error(u'dashboard切换组逻辑，未传递组信息！')
            raise RequestParamError
        group = Group.objects.get(id=group_id)

        rbac.change_rbac_group(request, group)
        api.update_last_login(request.user, group)


        return get_userinfo(request)
    except RequestParamError:
        return get_userinfo(request)
    except Group.DoesNotExist:
        logger.error(u'要切换的组不存在！')
        return get_userinfo(request)



@csrf_exempt
def front_login(request):
    feedback = {
        'permission': True
    }
    data = json.loads(request.body if request.body else '{}')

    username = data.get('username', None)
    password = data.get('password', None)

    if not (username is None or password is None):
        user = authenticate(username=username,
                            password=password)

        if user is not None:
            login(request, user)
            feedback['data'] = {'message': u'登录成功！',
                                'sessionid': request.session.session_key,
                                'username': username,
                                'code': 200}
            return JsonResponse(data=feedback)
        else:
            feedback['data'] = {
                'message': u'用户名或者密码错误！',
                'code': 400
            }
            return JsonResponse(data=feedback)
    else:
        feedback['data'] = {'message': u'参数错误！',
                            'code': 400}
        return JsonResponse(data=feedback)


@csrf_exempt
def front_logout(request):
    feedback = {
        'permission': True
    }
    result = logout(request)

    feedback['data'] = {
        'code': 200,
        'message': u'登出成功！'
    }

    return JsonResponse(data=feedback)


def layout_menu(request):
    menu = get_menu(request)
    return JsonResponse(data={
        'menuinfo': menu
    })




class ExistDataException(Exception):
    pass

# 请求参数错误
class RequestParamError(Exception):
    pass


# class PortalChangeGroupView(BaseView):
#     def get(self, *args, **kwargs):
#         group_id = int(self.kwargs['id'])
#         pre_url = self.kwargs.get('url', None)
#         pre_url = pre_url if not pre_url is None else '/'
#
#         group = Group.objects.get(id=group_id)
#         rbac.change_rbac_group(self.request, group)
#
#         response = redirect(pre_url)
#
#         # return HttpResponseRedirect(pre_url)
#         return response






