
from django.test import TestCase

from benchmark.backends.command_dispatcher.serializers.response import (
    PingSerializer
)

class ResponseTestCase(TestCase):

    def pingResponse(self):
        data = {
            'destination': 'www.baidu.com',
            'destination_ip': '1.1.1.1',
            'destination_location': None,
            'packet_send': 3,
            'packet_receive': 0,
            'packet_loss': 3,
            'packet_size': 55,
            'avg_time': 20,
            'max_time': None,
            'min_time': '12.1',
        }
        serializer = PingSerializer(data=data)
        if serializer.is_valid():
            print('validate succesffully, ', serializer.validated_data)
        else:
            print(serializer.errors)