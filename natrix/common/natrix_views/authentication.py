# -*- coding: utf-8 -*-
"""

"""
from __future__ import unicode_literals
import logging

from rest_framework import authentication

logger = logging.getLogger(__name__)


class NonAuthentication(authentication.BaseAuthentication):
    """None Authencation Class

    Don't require authentication,

    """

    def authenticate(self, request):
        user = getattr(request._request, 'user', None)
        group = getattr(request._request, 'group', None)

        setattr(request, 'user', user)
        setattr(request, 'group', group)
        return (user, None)

    def authenticate_header(self, request):
        return None

