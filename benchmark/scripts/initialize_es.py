# -*- coding: utf-8 -*-
"""Initialize ES about benchmark

"""

from __future__ import unicode_literals
import copy

from elasticsearch.client import Elasticsearch
from elasticsearch.client import IndicesClient

from benchmark.configurations import adapter_conf


benchmark_command_mapping = {
    'common': {
        'properties': {
            # command info
            'command_uuid': {
                'type': 'keyword'
            },
            'command_generate_time': {
                'type': 'date',
                'format': 'epoch_millis'
            },
            'task_id': {
                'type': 'keyword'
            },
            'task_generate_time': {
                'type': 'date',
                'format': 'epoch_millis'
            },

            # terminal info
            'terminal': {
                'type': 'keyword'
            },
            'organization_id':{
                'type': 'string',
            },
            'organization_name': {
                'type': 'string',
            },
            'organization_isp': {
                'type': 'keyword'
            },
            'province': {
                'type': 'keyword'
            },
            'city': {
                'type': 'keyword'
            },

            # timestamp info
            'terminal_request_receive_time': {
                'type': 'date',
                'format': 'epoch_millis'
            },
            'terminal_request_send_time': {
                'type': 'date',
                'format': 'epoch_millis'
            },
            'terminal_response_receive_time': {
                'type': 'date',
                "format": "epoch_millis"

            },
            'terminal_response_return_time': {
                'type': 'date',
                "format": "epoch_millis"

            },
            'response_process_time': {
                'type': 'date',
                "format": "epoch_millis"
            },
        }
    },
    'ping': {
        'properties': {
            'destination': {
                'type': 'keyword'
            },
            'destination_ip': {
                'type': 'keyword'
            },
            'destination_location': {
                'type': 'object'
            },
            'packet_send': {
                'type': 'integer'
            },
            'packet_receive': {
                'type': 'integer'
            },
            'packet_loss': {
                'type': 'integer'
            },
            'packet_size': {
                'type': 'integer'
            },
            'avg_time': {
                'type': 'double'
            },
            'max_time': {
                'type': 'double'
            },
            'min_time': {
                'type': 'double'
            },

        }
    },
    'http': {
        'properties': {
            'url': {
                'type': 'keyword'
            },
            'last_url': {
                'type': 'keyword'
            },
            'status_code': {
                'type': 'integer'
            },
            'redirect_count': {
                'type': 'integer'
            },
            'redirect_time': {
                'type': 'double'
            },
            'remote_ip': {
                'type': 'keyword'
            },
            'remote_location': {
                'type': 'nested'
            },
            'remote_port': {
                'type': 'integer'
            },
            'local_ip': {
                'type': 'keyword'
            },
            'local_location': {
                'type': 'nested'
            },
            'local_port': {
                'type': 'integer'
            },
            'total_time': {
                'type': 'double'
            },
            'period_nslookup': {
                'type': 'double'
            },
            'period_tcp_connect': {
                'type': 'double'
            },
            'period_ssl_connect': {
                'type': 'double'
            },
            'period_request': {
                'type': 'double'
            },
            'period_response': {
                'type': 'double'
            },
            'period_transfer': {
                'type': 'double'
            },
            'size_upload': {
                'type': 'double'
            },
            'size_download': {
                'type': 'double'
            },
            'speed_upload': {
                'type': 'double'
            },
            'speed_download': {
                'type': 'double'
            },
            'response_header': {
                'type': 'text'
            },
            'response_body': {
                'type': 'text'
            },
        }
    },
    'dns': {
        'properties': {
            'destination': {
                'type': 'keyword'
            },
            # unit: ms
            'ptime': {
                'type': 'double'
            },
            'dns_server': {
                'type': 'object'
            },
            # list of parse ip: ip address and location info
            'ips': {
                'type': 'nested'
            },
        }
    },
    'traceroute': {
        'properties': {
            'hop': {
                'type': 'integer'
            },
            'paths': {
                'type': 'nested'
            }
        }
    },
    'error': {
        'properties': {
            'errorcode': {
                'type': 'integer'
            },
            'errorinfo': {
                'type': 'text'
            }
        }

    }
}


def initializer():
    print('--------------initialize es in benchmark-------------')
    es_connection = Elasticsearch(hosts=adapter_conf.ES_SERVICE_URL,
                                  port=adapter_conf.ES_SERVICE_PORT)
    es_client = IndicesClient(es_connection)

    if es_client.exists(adapter_conf.BENCHMARK_INDEX):
        print('Index({}) is already exist, you maybe initialize brefore!'.format(adapter_conf.BENCHMARK_INDEX))
    else:
        es_connection.indices.create(adapter_conf.BENCHMARK_INDEX)

    common_part = benchmark_command_mapping['common']
    type_list = ['ping', 'http', 'dns', 'traceroute', 'error']
    # type_list = ['error']
    for protocol in type_list:
            data = copy.deepcopy(common_part)
            data['properties'].update(benchmark_command_mapping[protocol]['properties'])
            es_connection.indices.put_mapping(index=adapter_conf.BENCHMARK_INDEX,
                                          doc_type=protocol,
                                          body={protocol: data})


if __name__ == '__main__':
    initializer()
