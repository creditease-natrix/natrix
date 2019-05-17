# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django import forms

from django.contrib.auth.models import User
from natrix.common.forms import EagleChoiceField, EagleMultipleChoiceField, EagleCharField

from rbac.models import GroupRole, Assign
from rbac.conf import ROLES

class UserAddForm(forms.Form):

    user = EagleChoiceField(label=u"用户")
    roles = EagleMultipleChoiceField(label=u"角色")

    def init(self, request):
        user_rbac = request.user_rbac
        if user_rbac and user_rbac.get_group():
            group = user_rbac.get_group()
            grs = GroupRole.objects.filter(group=group)
            role_select = []
            for gr in grs:
                role_select.append((gr.role.id,
                                    ROLES.get(gr.role.name, {}).get('verbose_name')))

            self.fields['roles'].choices = set(role_select)

            assign_gr = Assign.objects.filter(group=group).values("user")
            user_ids = set()
            for v in assign_gr:
                user_ids.add(v.get('user'))

            users = User.objects.exclude(pk__in=user_ids).order_by('username')
            user_select = []
            for u in users:
                user_select.append((u.id, u.username))

            self.fields['user'].choices = user_select


class UserEditForm(forms.Form):
    user = EagleChoiceField(label=u"用户", required=False)
    roles = EagleMultipleChoiceField(label=u"角色")

    def init(self, user, roles, select_roles):

        self.fields['user'].choices = set([(user.id, user.username) ])
        self.fields['user'].initial = set([(user.id, user.username) ])


        role_list = []
        for r in roles:
            role_list.append((r.id,
                              ROLES.get(r.name, {}).get('verbose_name')))

        self.fields['roles'].choices = role_list

        ids = []
        for r in select_roles:
            ids.append(r.id)
        self.fields['roles'].initial = ids



class GroupAddForm(forms.Form):
    name = EagleCharField(label=u"组名称")



