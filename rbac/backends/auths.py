# -*- coding: utf-8 -*-
import logging

from django.db import transaction
from django_auth_ldap.backend import LDAPBackend

from rbac.api import create_group, init_rbac, init_userinfo


logger = logging.getLogger(__name__)


class NatrixLDAPBackend(LDAPBackend):
    """Natrix LDAP Backend

    Natrix LDAP Backend add rbac initialization processing.

    NOTE:
        This class dependence LDAPBackend，so the change of LDAPBackend will affect this class.

    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            with transaction.atomic():
                # Create a user in django
                user = super(NatrixLDAPBackend, self).authenticate(
                    request, username=username, password=password, **kwargs)

                if user:
                    # new user
                    if getattr(self, 'built_flag', True):
                        user.email = username
                        user.save()

                        init_userinfo(user)

                        group = create_group(username)
                        if group:
                            init_rbac(user, group)
                        else:
                            logger.info(f'Exist the group named {username}, so cant map a group.')
        except Exception as e:
            logger.info(f'Authentication with NatrixLDAPBackend with error: {e}')
            user = None

        return user

    def get_or_build_user(self, username, ldap_user):
        """
        """
        user, built = super(NatrixLDAPBackend,
                            self).get_or_build_user(username, ldap_user)
        self.built_flag = built

        return (user, built)


