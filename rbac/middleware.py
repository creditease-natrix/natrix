# -*- coding: utf-8 -*-

from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.contrib.auth.models import Group
from django.utils.deprecation import MiddlewareMixin

import rbac
from rbac.models import UserRBAC


def get_user_rbac(request):
    user = request.user

    if isinstance(user, AnonymousUser):
        return None
    
    user_rbac = UserRBAC(user)
    groups = user_rbac.groups()
    if not groups:
        return user_rbac
    try:
        if not user_rbac.group:
            group_id = Group._meta.pk.to_python(
                request.session[rbac.SESSION_KEY])
            group = Group.objects.get(pk=group_id)
            user_rbac.change_group(group)
    except KeyError:
        user_rbac.change_group(groups[0][0])
        
    return user_rbac


class RBACMiddleware(MiddlewareMixin):
    def process_request(self, request):
        assert hasattr(request, 'user'), (
            "The Django rbac middleware requires auth middleware "
            "to be installed. Edit your MIDDLEWARE%s settings to insert "
            "'django.contrib.auth.middleware.AuthenticationMiddleware' "
            "before 'rbac.middleware.RBACMiddleware'."
        ) % ("_CLASSES" if settings.MIDDLEWARE is None else "")

        request.user_rbac = get_user_rbac(request)
