# -*- coding: utf-8 -*-
"""

"""

from __future__ import unicode_literals, absolute_import
import logging

from django.http.response import JsonResponse

from natrix.common.natrix_views.views import NonAuthenticatedAPIView
from natrix.common.errorcode import ErrorCode
from natrix.common import exception as natrix_exception

from terminal.serializers import common_serializer

logger = logging.getLogger(__name__)


class TerminalListAPI(NonAuthenticatedAPIView):
    """The common termina list api.

    """
    def post(self, request, format=None):
        feedback = {
            'permission': True
        }
        try:
            post_data = request.data

            serializer = common_serializer.TerminalFilterSerializer(data=post_data, group=self.get_group())
            if serializer.is_valid():
                res = list(serializer.query_result())
                feedback['data'] = {
                    'code': 200,
                    'message': 'Terminal list info',
                    'info': res
                }
            else:
                logger.error('Parameter Error: {}'.format(serializer.format_errors()))
                feedback['data'] = ErrorCode.parameter_invalid(
                    'terminallist', reason=serializer.format_errors()
                )

        except Exception as e:
            natrix_exception.natrix_traceback()
            logger.error('Common terminal list post ERROR')
            feedback['data'] = ErrorCode.sp_code_bug('Common terminal list post')

        return JsonResponse(data=feedback)


class TerminalCountAPI(NonAuthenticatedAPIView):
    """

    """
    def post(self, request, format=None):
        feedback = {
            'permission': True
        }
        try:
            post_data = request.data
            serializer = common_serializer.TerminalFilterSerializer(data=post_data, group=self.get_group())
            if serializer.is_valid():
                terminals = serializer.query_terminals()
                feedback['data'] = {
                    'code': 200,
                    'message': 'Terminal count info',
                    'info': {
                        'alive': len(terminals)
                    }
                }
            else:
                logger.error('Parameter Error: {}'.format(serializer.format_errors()))
                feedback['data'] = ErrorCode.parameter_invalid(
                    'terminalcount', reason=serializer.format_errors()
                )

        except Exception as e:
            logger.error('Common terminal count post ERROR: {}'.format(e))
            feedback['data'] = ErrorCode.sp_code_bug(e)

        return JsonResponse(data=feedback)
