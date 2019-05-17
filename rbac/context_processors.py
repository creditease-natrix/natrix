# -*- coding: utf-8 -*-

def rbac(request):
    if hasattr(request, 'user_rbac'):
        user_rbac = request.user_rbac
    else:
        user_rbac = None

    return {
        'user_rbac': user_rbac
    }
