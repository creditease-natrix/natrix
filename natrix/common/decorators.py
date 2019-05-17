# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import logging

from django.http.response import JsonResponse


logger = logging.getLogger(__name__)


def natrix_permission(is_permitted):
    def issue_permit(view_func):
        def wrapped_view(*args, **kwargs):
            if callable(is_permitted) is False:
                logger.error(u'Set an error function: is_permitted!')
                permit = False
            elif len(args) < 1:
                logger.error(u'Missing parameter: request!')
                permit = False
            else:
                permit = is_permitted(args[0])

            feedback = {
                'permission': False
            }
            if not permit:
                return JsonResponse(data=feedback)
            else:
                return view_func(*args, **kwargs)

        return wrapped_view

    return issue_permit

