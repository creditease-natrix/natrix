# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging
import json


from django.views.decorators.csrf import csrf_exempt
from django.http.response import JsonResponse

from natrix.common.errorcode import ErrorCode

from terminal.models import Region
logger = logging.getLogger(__name__)



# TODO: use rest-api decorator

@csrf_exempt
def get_provinces(request):
    feedback = {
        'permission': True
    }

    feedback['data'] = {
        'code': 200,
        'message': u'省份列表信息',
        'info': Region.get_provinces()
    }

    return JsonResponse(data=feedback)


@csrf_exempt
def get_cities(request):
    if request.method == 'POST':
        feedback = {
            'permission': True
        }
        try:
            post_data = json.loads(request.body)
            provinces = post_data.get('provinces')
            feedback['data'] = {
                'code': 200,
                'message': u'市列表信息',
                'info': Region.get_cities(provinces)
            }
        except Exception as e:
            logger.info(e)
            feedback['data'] = ErrorCode.parameter_invalid('provinces')
    else:
        feedback = {
            'permission': False
        }

    return JsonResponse(data=feedback)
