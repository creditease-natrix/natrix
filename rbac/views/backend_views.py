# -*- coding: utf-8 -*-
"""

"""
import logging
import json, uuid

from django.http.response import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from natrix.common.natrix_views import views as natrix_views
from natrix.common.errorcode import ErrorCode
from rbac.models import UserInfo
logger = logging.getLogger(__name__)


@csrf_exempt
def abstreming_notify_api(request):
    """

    :param request:
    :return:
    """
    request_data = json.loads(request.body if request.body else '{}')

    type = request_data.get('type', None)
    user_infos = request_data.get('users', None)

    if type is None:
        return JsonResponse(data=ErrorCode.parameter_missing('type'))

    if not isinstance(user_infos, list):
        return JsonResponse(data=ErrorCode.parameter_invalid('user_infos', 'Must be a list'))

    for record in user_infos:
        if isinstance(record, uuid.UUID):
            continue
        try:
            ...
        except ValueError:
            return JsonResponse()



    users = UserInfo.objects.filter(uuid__in=user_infos)

    if type == 'email':
        to_list = [u.user.email for u in users if u.user and u.user.email]
    elif type == 'sms':
        to_list = [u.phone for u in users if u.phone]
    else:
        to_list = []

    return JsonResponse(data={
        'code': 200,
        'to': list(set(to_list))
    })


