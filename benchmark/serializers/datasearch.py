# -*- coding: utf-8 -*-
"""

"""
from __future__ import unicode_literals
import time

from benchmark.backends.command_dispatcher.store import origin_search

MAX_TIME_POINTS = 200
MAX_DIST_POINTS = 50

def get_interval(start_time, end_time, interval):
    avg_interval = (end_time - start_time) / MAX_TIME_POINTS
    return interval if interval > avg_interval else avg_interval


def ping_loss_region(task_id, start_time, end_time):

    es_condition = {
        'query': {
            'bool': {
                'must': [
                    {'term': {'_type': 'ping'}},
                    {'term': {'task_id': task_id}},
                    {'range': {'task_generate_time': {'gte': start_time, 'lte': end_time}}}
                ]
            }
        },
        'aggs': {
            'bucket_aggs': {
                'terms': {
                    'field': 'province',
                    'size': 1000
                },
                'aggs': {
                    'sum_loss': {
                        'sum': {'field': 'packet_loss'}
                    },
                    'sum_receive': {
                        'sum': {'field': 'packet_receive'}
                    },
                    'sum_send': {
                        'sum': {'field': 'packet_send'}
                    }
                }
            }
        },
    }
    res = origin_search(body=es_condition, size=0)

    analyse_data = res.get('aggregations', {}).get('bucket_aggs').get('buckets')

    analyse_values = []
    for record in analyse_data:
        key = record.get('key')
        sum_loss = record.get('sum_loss').get('value')
        sum_send = record.get('sum_send').get('value')
        analyse_values.append({
            'name': key,
            'value': sum_loss / sum_send if sum_send else 0
        })

    return analyse_values


def ping_delay_region(task_id, start_time, end_time):
    es_condition = {
        'query': {
            'bool': {
                'must': [
                    {'term': {'_type': 'ping'}},
                    {'term': {'task_id': task_id}},
                    {'range': {'task_generate_time': {'gte': start_time, 'lte': end_time}}}
                ]
            }
        },
        'aggs': {
            'bucket_aggs': {
                'terms': {
                    'field': 'province',
                    'size': 1000
                },
                'aggs': {
                    'avg_avgtime': {
                        'avg': {'field': 'avg_time'}
                    }
                }
            }
        },
    }
    res = origin_search(body=es_condition, size=0)

    analyse_data = res.get('aggregations', {}).get('bucket_aggs').get('buckets')

    analyse_values = []
    for record in analyse_data:
        key = record.get('key')
        avg_value = record.get('avg_avgtime').get('value')
        analyse_values.append({
            'name': key,
            'value': avg_value
        })

    return analyse_values


def ping_loss_time(task_id, start_time, end_time, interval):

    analyse_interval = get_interval(start_time, end_time, interval)

    es_condition = {
        'query': {
            'bool': {
                'must': [
                    {'term': {'_type': 'ping'}},
                    {'term': {'task_id': task_id}},
                    {'range': {'task_generate_time': {'gte': start_time, 'lte': end_time}}}
                ]
            }
        },
        'aggs': {
            'histogram_datas': {
                'date_histogram': {
                    'field': 'task_generate_time',
                    'interval': analyse_interval,
                    'extended_bounds': {
                        'min': start_time,
                        'max': end_time
                    }
                },
                'aggs': {
                    'sum_loss': {
                        'sum': {'field': 'packet_loss'}
                    },
                    'sum_send': {
                        'sum': {'field': 'packet_send'}
                    }
                }
            }
        },
    }
    res = origin_search(body=es_condition, size=0)

    analyse_data = res.get('aggregations', {}).get('histogram_datas').get('buckets')

    loss_values = []
    x_axis = []
    for record in analyse_data:
        key = record.get('key')
        sum_loss = record.get('sum_loss').get('value')
        sum_send = record.get('sum_send').get('value')
        x_axis.append(key)
        loss_values.append(sum_loss / sum_send if sum_send else 0.0)

    lines = [
        {
            'name': 'packet_loss',
            'values': loss_values
        }
    ]
    return x_axis, lines


def ping_delay_time(task_id, start_time, end_time, interval):

    analyse_interval = get_interval(start_time, end_time, interval)

    es_condition = {
        'query': {
            'bool': {
                'must': [
                    {'term': {'_type': 'ping'}},
                    {'term': {'task_id': task_id}},
                    {'range': {'task_generate_time': {'gte': start_time, 'lte': end_time}}}
                ]
            }
        },
        'aggs': {
            'histogram_datas': {
                'date_histogram': {
                    'field': 'task_generate_time',
                    'interval': analyse_interval,
                    'extended_bounds': {
                        'min': start_time,
                        'max': end_time
                    }
                },
                'aggs': {
                    'avg_avgtime': {
                        'avg': {'field': 'avg_time'}
                    },
                    'avg_mintime': {
                        'avg': {'field': 'min_time'}
                    },
                    'avg_maxtime': {
                        'avg': {'field': 'max_time'}
                    }
                }
            }
        },
    }
    res = origin_search(body=es_condition, size=0)

    analyse_data = res.get('aggregations', {}).get('histogram_datas').get('buckets')

    avg_values = []
    min_values = []
    max_values = []
    x_axis = []
    for record in analyse_data:
        key = record.get('key')
        avg_time = record.get('avg_avgtime').get('value')
        min_time = record.get('avg_mintime').get('value')
        max_time = record.get('avg_maxtime').get('value')

        x_axis.append(key)
        avg_values.append(avg_time)
        min_values.append(min_time)
        max_values.append(max_time)

    lines = [
        {
            'name': 'avg_value',
            'values': avg_values
        },
        {
            'name': 'min_value',
            'values': min_values
        },
        {
            'name': 'max_value',
            'values': max_values
        }
    ]
    return x_axis, lines


def ping_exception_time(task_id, start_time, end_time, interval):

    analyse_interval = get_interval(start_time, end_time, interval)

    es_condition = {
        'query': {
            'bool': {
                'must': [
                    {'term': {'_type': 'error'}},
                    {'term': {'task_id': task_id}},
                    {'range': {'task_generate_time': {'gte': start_time, 'lte': end_time}}}
                ]
            }
        },
        'aggs': {
            'histogram_datas': {
                'date_histogram': {
                    'field': 'task_generate_time',
                    'interval': analyse_interval,
                    'extended_bounds': {
                        'min': start_time,
                        'max': end_time
                    }
                }
            }
        },
    }
    res = origin_search(body=es_condition, size=0)

    analyse_data = res.get('aggregations', {}).get('histogram_datas').get('buckets')

    exception_values = []
    x_axis = []
    for record in analyse_data:
        key = record.get('key')
        x_axis.append(key)
        exception_values.append(record.get('doc_count'))

    lines = [
        {
            'name': 'exception',
            'values': exception_values
        },
    ]
    return x_axis, lines


def ping_delay_dist(task_id, start_time, end_time, interval):

    max_condition = {
        'query': {
            'bool': {
                'must': [
                    {'term': {'_type': 'ping'}},
                    {'term': {'task_id': task_id}},
                    {'range': {'task_generate_time': {'gte': start_time, 'lte': end_time}}}
                ]
            }
        },
        "aggs": {
            "max_value": {
                "max": {"field": "max_time"}
            }
        }
    }
    res = origin_search(body=max_condition, size=0)
    analyse_interval = res.get('aggregations', {}).get('max_value', {}).get('value', 1000) / MAX_DIST_POINTS

    interval = analyse_interval if analyse_interval > 20 else 20

    es_condition = {
        'query': {
            'bool': {
                'must': [
                    {'term': {'_type': 'ping'}},
                    {'term': {'task_id': task_id}},
                    {'range': {'task_generate_time': {'gte': start_time, 'lte': end_time}}}
                ]
            }
        },
        'aggs': {
            'avg_time_range': {
                'histogram': {
                    'field': 'avg_time',
                    'interval': interval
                }
            },
            'min_time_range': {
                'histogram': {
                    'field': 'min_time',
                    'interval': interval
                }
            },
            'max_time_range': {
                'histogram': {
                    'field': 'max_time',
                    'interval': interval
                }
            }
        },
    }
    res = origin_search(body=es_condition, size=0)

    analyse_data = {}
    avg_data = res.get('aggregations', {}).get('avg_time_range').get('buckets')
    for record in avg_data:
        key = int(record.get('key'))
        analyse_data[key] = {
            'avg_time': record.get('doc_count')
        }
    min_data = res.get('aggregations', {}).get('min_time_range').get('buckets')
    for record in min_data:
        key = int(record.get('key'))
        if key in analyse_data:
            analyse_data[key]['min_time'] = record.get('doc_count')
        else:
            analyse_data[key] = {
                'min_time': record.get('doc_count')
            }
    max_data = res.get('aggregations', {}).get('max_time_range').get('buckets')
    for record in max_data:
        key = int(record.get('key'))
        if key in analyse_data:
            analyse_data[key]['max_time'] = record.get('doc_count')
        else:
            analyse_data[key] = {
                'max_time': record.get('doc_count')
            }

    avg_values = []
    min_values = []
    max_values = []
    x_axis = []

    x_list = sorted(analyse_data.keys())

    for x_value in x_list:
        x_axis.append('{}-{}'.format(x_value, x_value+interval))
        avg_values.append(analyse_data[x_value].get('avg_time', 0))
        min_values.append(analyse_data[x_value].get('min_time', 0))
        max_values.append(analyse_data[x_value].get('max_time', 0))

    lines = [
        {
            'name': 'avg_value',
            'values': avg_values
        },
        {
            'name': 'min_value',
            'values': min_values
        },
        {
            'name': 'max_value',
            'values': max_values
        },
    ]
    return x_axis, lines


def http_request_region(task_id, start_time, end_time):

    es_condition = {
        'query': {
            'bool': {
                'must': [
                    {'term': {'_type': 'http'}},
                    {'term': {'task_id': task_id}},
                    {'range': {'task_generate_time': {'gte': start_time, 'lte': end_time}}}
                ]
            }
        },
        'aggs': {
            'bucket_aggs': {
                'terms': {
                    'field': 'province',
                    'size': 1000
                },
                'aggs': {
                    'avg_total_time': {
                        'avg': {'field': 'total_time'}
                    }
                }
            }
        },
    }
    res = origin_search(body=es_condition, size=0)

    analyse_data = res.get('aggregations', {}).get('bucket_aggs').get('buckets')

    analyse_values = []
    for record in analyse_data:
        key = record.get('key')
        avg_time = record.get('avg_total_time').get('value')

        analyse_values.append({
            'name': key,
            'value': avg_time
        })

    return analyse_values


def http_parsetime_region(task_id, start_time, end_time):

    es_condition = {
        'query': {
            'bool': {
                'must': [
                    {'term': {'_type': 'http'}},
                    {'term': {'task_id': task_id}},
                    {'range': {'task_generate_time': {'gte': start_time, 'lte': end_time}}}
                ]
            }
        },
        'aggs': {
            'bucket_aggs': {
                'terms': {
                    'field': 'province',
                    'size': 1000
                },
                'aggs': {
                    'avg_parse_time': {
                        'avg': {'field': 'period_nslookup'}
                    }
                }
            }
        },
    }
    res = origin_search(body=es_condition, size=0)

    analyse_data = res.get('aggregations', {}).get('bucket_aggs').get('buckets')

    analyse_values = []
    for record in analyse_data:
        key = record.get('key')
        avg_time = record.get('avg_parse_time').get('value')

        analyse_values.append({
            'name': key,
            'value': avg_time
        })

    return analyse_values


def http_request_time(task_id, start_time, end_time, interval):

    analyse_interval = get_interval(start_time, end_time, interval)

    es_condition = {
        'query': {
            'bool': {
                'must': [
                    {'term': {'_type': 'http'}},
                    {'term': {'task_id': task_id}},
                    {'range': {'task_generate_time': {'gte': start_time, 'lte': end_time}}}
                ]
            }
        },
        'aggs': {
            'histogram_datas': {
                'date_histogram': {
                    'field': 'task_generate_time',
                    'interval': analyse_interval,
                    'extended_bounds': {
                        'min': start_time,
                        'max': end_time
                    }
                },
                'aggs': {
                    'avg_total': {
                        'avg': {'field': 'total_time'}
                    },
                    'avg_nslookup': {
                        'avg': {'field': 'period_nslookup'}
                    },
                    'avg_tcp': {
                        'avg': {'field': 'period_tcp_connect'}
                    },
                }
            }
        },
    }
    res = origin_search(body=es_condition, size=0)

    analyse_data = res.get('aggregations', {}).get('histogram_datas').get('buckets')

    total_values = []
    nslookup_values = []
    tcp_values = []
    x_axis = []
    for record in analyse_data:
        key = record.get('key')
        x_axis.append(key)
        total_values.append(record.get('avg_total').get('value'))
        nslookup_values.append(record.get('avg_nslookup').get('value'))
        tcp_values.append(record.get('avg_tcp').get('value'))


    lines = [
        {
            'name': 'namelookup_time',
            'values': nslookup_values
        },
        {
            'name': 'period_tcp_connect',
            'values': tcp_values
        },
        {
            'name': 'total_time',
            'values': total_values
        }
    ]

    return x_axis, lines


# STATISTIC http status code
def http_exception_time(task_id, start_time, end_time, interval):

    analyse_interval = get_interval(start_time, end_time, interval)

    es_condition = {
        'query': {
            'bool': {
                'must': [
                    {'term': {'_type': 'error'}},
                    {'term': {'task_id': task_id}},
                    {'range': {'task_generate_time': {'gte': start_time, 'lte': end_time}}}
                ]
            }
        },
        'aggs': {
            'histogram_datas': {
                'date_histogram': {
                    'field': 'task_generate_time',
                    'interval': analyse_interval,
                    'extended_bounds': {
                        'min': start_time,
                        'max': end_time
                    }
                }
            }
        },
    }
    res = origin_search(body=es_condition, size=0)

    analyse_data = res.get('aggregations', {}).get('histogram_datas').get('buckets')

    exception_values = []
    x_axis = []
    for record in analyse_data:
        key = record.get('key')
        x_axis.append(key)
        exception_values.append(record.get('doc_count'))

    lines = [
        {
            'name': 'exception',
            'values': exception_values
        },
    ]
    return x_axis, lines


def http_result_dist(task_id, start_time, end_time):

    httperror_condition = {
        'query': {
            'bool': {
                'must': [
                    {'term': {'_type': 'http'}},
                    {'term': {'task_id': task_id}},
                    {'range': {'task_generate_time': {'gte': start_time, 'lte': end_time}}}
                ]
            }
        },
        'aggs': {
            'bucket_aggs': {
                'terms': {
                    'field': 'status_code',
                    'size': 1000
                }
            }
        },
    }
    res = origin_search(body=httperror_condition, size=0)
    http_analyse_data = res.get('aggregations', {}).get('bucket_aggs', {}).get('buckets', [])

    error_condition = {
        'query': {
            'bool': {
                'must': [
                    {'term': {'_type': 'error'}},
                    {'term': {'task_id': task_id}},
                    {'range': {'task_generate_time': {'gte': start_time, 'lte': end_time}}}
                ]
            }
        },
        'aggs': {
            'bucket_aggs': {
                'terms': {
                    'field': 'errorcode',
                    'size': 1000
                }
            }
        },
    }
    res = origin_search(body=error_condition, size=0)
    error_analyse_data = res.get('aggregations', {}).get('bucket_aggs', {}).get('buckets', [])

    analyse_values = []
    for record in http_analyse_data:
        analyse_values.append(
            {
                'name': record.get('key'),
                'value': record.get('doc_count')
            }
        )
    for record in error_analyse_data:
        analyse_values.append(
            {
                'name': record.get('key'),
                'value': record.get('doc_count')
            }
        )

    return analyse_values


def http_stage_dist(task_id, start_time, end_time):

    es_condition = {
        'query': {
            'bool': {
                'must': [
                    {'term': {'_type': 'http'}},
                    {'term': {'task_id': task_id}},
                    {'range': {'task_generate_time': {'gte': start_time, 'lte': end_time}}}
                ]
            }
        },
        'aggs': {
            'period_nslookup': {
                'avg': {'field': 'period_nslookup'}
            },
            'period_tcp_connect': {
                'avg': {'field': 'period_tcp_connect'}
            },
            'period_ssl_connect': {
                'avg': {'field': 'period_ssl_connect'}
            },
            'period_request': {
                'avg': {'field': 'period_request'}
            },
            'period_response': {
                'avg': {'field': 'period_response'}
            },
            'period_transfer': {
                'avg': {'field': 'period_transfer'}
            },
        },
    }
    res = origin_search(body=es_condition, size=0)

    analyse_data = res.get('aggregations', {})

    analyse_keys = ['period_nslookup', 'period_tcp_connect',
                    'period_ssl_connect', 'period_request',
                    'period_response', 'period_transfer']
    analyse_values = []
    for key in analyse_keys:
        analyse_values.append({
            'name': key,
            'value': analyse_data.get(key, {}).get('value', 0)
        })

    return analyse_values


def dns_parsetime_region(task_id, start_time, end_time):

    es_condition = {
        'query': {
            'bool': {
                'must': [
                    {'term': {'_type': 'dns'}},
                    {'term': {'task_id': task_id}},
                    {'range': {'task_generate_time': {'gte': start_time, 'lte': end_time}}}
                ]
            }
        },
        'aggs': {
            'bucket_aggs': {
                'terms': {
                    'field': 'province',
                    'size': 1000
                },
                'aggs': {
                    'avg_parsetime': {
                        'avg': {'field': 'ptime'}
                    }
                }
            }
        },
    }
    res = origin_search(body=es_condition, size=0)

    analyse_data = res.get('aggregations', {}).get('bucket_aggs').get('buckets')

    analyse_values = []
    for record in analyse_data:
        key = record.get('key')
        avg_value = record.get('avg_parsetime').get('value')
        analyse_values.append({
            'name': key,
            'value': avg_value
        })

    return analyse_values

# TODO: redefine dns type in es
def dns_parseresult_region(task_id, start_time, end_time):

    es_condition = {
        'query': {
            'bool': {
                'must': [
                    {'term': {'_type': 'dns'}},
                    {'term': {'task_id': task_id}},
                    {'range': {'task_generate_time': {'gte': start_time, 'lte': end_time}}}
                ]
            }
        }
    }
    res = origin_search(body=es_condition, size=1000)

    analyse_data = res.get('hits', {}).get('hits', [])

    analyse_st = {}
    for record in analyse_data:
        ips = record.get('_source', {}).get('ips', [])
        for parse in ips:
            city = parse.get('location', {}).get('city', None)
            if city in analyse_st:
                analyse_st[city] += 1
            else:
                analyse_st[city] = 1

    return [{'name': city, 'value': value} for city, value in analyse_st.items()]


def dns_parsetime_time(task_id, start_time, end_time, interval):

    analyse_interval = get_interval(start_time, end_time, interval)

    es_condition = {
        'query': {
            'bool': {
                'must': [
                    {'term': {'_type': 'dns'}},
                    {'term': {'task_id': task_id}},
                    {'range': {'task_generate_time': {'gte': start_time, 'lte': end_time}}}
                ]
            }
        },
        'aggs': {
            'histogram_datas': {
                'date_histogram': {
                    'field': 'task_generate_time',
                    'interval': analyse_interval,
                    'extended_bounds': {
                        'min': start_time,
                        'max': end_time
                    }
                },
                'aggs': {
                    'avg_parsetime': {
                        'avg': {'field': 'ptime'}
                    }

                }
            }
        },
    }
    res = origin_search(body=es_condition, size=0)

    analyse_data = res.get('aggregations', {}).get('histogram_datas').get('buckets')

    avg_values = []
    x_axis = []
    for record in analyse_data:
        key = record.get('key')
        avg_time = record.get('avg_parsetime').get('value')

        x_axis.append(key)
        avg_values.append(avg_time)

    lines = [
        {
            'name': 'parse_time',
            'values': avg_values
        },
    ]

    return x_axis, lines


def dns_exception_time(task_id, start_time, end_time, interval):

    analyse_interval = get_interval(start_time, end_time, interval)

    es_condition = {
        'query': {
            'bool': {
                'must': [
                    {'term': {'_type': 'error'}},
                    {'term': {'task_id': task_id}},
                    {'range': {'task_generate_time': {'gte': start_time, 'lte': end_time}}}
                ]
            }
        },
        'aggs': {
            'histogram_datas': {
                'date_histogram': {
                    'field': 'task_generate_time',
                    'interval': analyse_interval,
                    'extended_bounds': {
                        'min': start_time,
                        'max': end_time
                    }
                }
            }
        },
    }
    res = origin_search(body=es_condition, size=0)

    analyse_data = res.get('aggregations', {}).get('histogram_datas').get('buckets')

    exception_values = []
    x_axis = []
    for record in analyse_data:
        key = record.get('key')
        x_axis.append(key)
        exception_values.append(record.get('doc_count'))

    lines = [
        {
            'name': 'exception',
            'values': exception_values
        },
    ]

    return x_axis, lines
