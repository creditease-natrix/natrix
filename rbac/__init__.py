# -*- coding: utf-8 -*-
SESSION_KEY = '_user_rbac_group_id'


def change_rbac_group(request, group):
    user_rbac = request.user_rbac
    user_rbac.change_group(group)

    group = user_rbac.group
    request.session[SESSION_KEY] = group._meta.pk.value_to_string(group)



