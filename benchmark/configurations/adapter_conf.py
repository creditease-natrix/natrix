# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import
import os
try:
    import ConfigParser as configparser
except ImportError:
    import configparser


"""

"""


# unresponse and unconsume
COMMAND_TIMEOUT = 300


REQUEST_QUEUE = {
    'name_template': '',
    'exchange_template': ''

}

DEAD_QUEUE = {
    'name': 'natrix_command_dead',
    'exchange': 'natrix_command_dlx',
    'routing_key': 'dead_command'
}


###################################################
# response MQ configuration:
#       terminal post result to 'response exchange'
#
############################






###########################
# ES
################

root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
config_file = root_dir + "/natrix.ini"
config = configparser.ConfigParser()
config.read(config_file)

ES_SERVICE_URL = config.get("ELASTICSEARCH", "host")
ES_SERVICE_PORT = config.get("ELASTICSEARCH", "port")
BENCHMARK_INDEX = 'benchmark10'
