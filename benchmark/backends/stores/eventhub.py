
from copy import deepcopy
import time
import json
import requests
from typing import List, Dict

from .base import BaseStoreClient
from natrix.common import exception as natrix_exception
from natrix.common.natrixlog import NatrixLogging
from benchmark.types.events import benchmark_command_mapping


logger = NatrixLogging(name=__name__)


class EventhubClient(BaseStoreClient):

    service_url = None

    def __init__(self, service_url=None):
        if service_url:
            EventhubClient.service_url = service_url

    def create_event(self, event_data):
        request_url = self.service_url + '/v1/event/manage/create'
        try:
            res = requests.post(request_url, json=event_data)
            result = json.loads(res.text)
            if result.get('ret') > 0:
                raise Exception(result.get('msg'))
        except Exception as e:
            logger.error('An Error when storing eventhub: {}'.format(e))

    def put(self, event: Dict):
        request_url = self.service_url + '/v1/event/receive/single'
        try:
            event['time'] = int(time.time() * 1000)
            res = requests.post(request_url, json=event)
            result = json.loads(res.text)
            logger.debug(f'evenhub response {result}')
            if result.get('ret') > 0:
                logger.error(f'Store event to eventhub with error: {result}')
                raise natrix_exception.NetworkException(result.get('msg'))
        except Exception as e:
            raise natrix_exception.NetworkException(message=f'{e}')

    def puts(self, events: List):
        request_url = self.service_url + '/v1/event/receive/batch'
        try:
            curr_timestamp =  int(time.time() * 1000)
            for event in events:
                event['time'] = curr_timestamp
            res = requests.post(request_url, json=events)
            result = json.loads(res.text)
            logger.debug(f'evenhub response {result}')
            if result.get('ret') > 0:
                logger.error(f'Store event to eventhub with error: {result}')
                raise natrix_exception.NetworkException(result.get('msg'))
        except Exception as e:
            raise natrix_exception.NetworkException(message=f'{e}')

    def init_store_service(self):
        benchmark_event_data = deepcopy(benchmark_command_mapping)
        common_part = benchmark_event_data.pop('common')
        fields = common_part.get('properties', {})
        common_list = []
        for name, finfo in fields.items():
            common_list.append(self._field_transform(name, finfo))

        for event_name, record in benchmark_event_data.items():

            field_list = []
            fields = record.get('properties', {})
            for name, finfo in fields.items():
                field_info = self._field_transform(name, finfo)
                field_list.append(field_info)

            field_list.extend(common_list)
            event_data = {
                'event_type': {
                    'name': event_name
                },
                'field_type': field_list
            }
            self.create_event(event_data)

    def _field_transform(self, name, info):
        origin_type = info.get('type', None)
        if origin_type == 'string' or origin_type == 'keyword' or origin_type == 'text':
            field_type = 'str'
        elif origin_type == 'date':
            field_type = 'int'
        elif origin_type == 'integer':
            field_type = 'int'
        elif origin_type == 'double':
            field_type = 'float'
        elif origin_type == 'nested':
            field_type = 'list'
        elif origin_type == 'object':
            field_type = 'dict'

        return {
            'name': name,
            'type': field_type,
            'desc': {}
        }




