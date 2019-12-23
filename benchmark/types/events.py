

class BaseEvent:
    def __init__(self, command_uuid: str, command_generate_time: float, task_id, task_generate_time,
                 terminal, organization_id, organization_name, organization_isp, province, city,
                 terminal_request_receive_time, terminal_request_send_time,
                 terminal_response_receive_time, terminal_response_return_time, response_process_time):
        self.command_uuid = command_uuid
        self.command_generate_time = command_generate_time
        self.task_id = task_id
        self.task_generate_time = task_generate_time
        self.terminal = terminal
        self.organization_id = organization_id
        self.organization_name = organization_name
        self.organization_isp = organization_isp
        self.province = province
        self.city = city
        self.terminal_request_receive_time = terminal_request_receive_time
        self.terminal_request_send_time = terminal_request_send_time
        self.terminal_response_receive_time = terminal_response_receive_time
        self.terminal_response_return_time = terminal_response_return_time
        self.response_process_time = response_process_time


class PingEvent(BaseEvent):

    def __init__(self, destination, destination_ip, destination_location,
                 packet_send, packet_receive, packet_loss, packet_size):
        ...


# ES mapping
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
            # 'organization_id':{
            #     'type': 'string',
            # },
            # 'organization_name': {
            #     'type': 'string',
            # },
            # 'organization_isp': {
            #     'type': 'keyword'
            # },
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
                'type': 'object'
            },
            'remote_port': {
                'type': 'integer'
            },
            'local_ip': {
                'type': 'keyword'
            },
            'local_location': {
                'type': 'object'
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

    },
    'responseDiscard': {
        'properties': {
            'expired_time': {
                'type': 'double'
            },
            'dial_data': {
                'type': 'object'
            }
        }
    }
}


