# -*- coding: utf-8 -*-
"""In-memory representation of command state.

We maintain command information in memory, there are three types of data about command information.
 - Command Register
    This type information records unfinished command batches. A command batch is identified by
    command_uuid and a timestamp, and with a list of terminals.
    So the command register structure likes:

    'benchmark_command_register': set(['command_uuid_1', 'command_uuid_2'])
    'benchmark_command_register_[command_uuid]': {
        'info': {    // protocol related information
            'protocol': 'http',
        },
        'batches': {
            timestamp_1: set(['terminal_1', 'terminal_2']),
        }
    }

 - Command Status
    The command status is a Finite-State Machine, which includes running and finished states.
    Each command is a FSM, which identified by command_uuid, terminal and timestamp(microsecond).
    So the command status structure likes:
    'benchmark_state_[command_uuid]-[terminal]-[timestamp]: {
        'command_generate_time': timestamp,
        'state': 'running/finished',
        'task_tags': [{'task_id': 111, 'task_generate_time': 111111}]
    }

 - Last Command Response
    The newest command response depends on terminal_request_send_time which is in terminal response.

    So the last command response structure likes:
    '[command_uuid]-[terminal]': {
        'timestamp': 11111, //this is terminal_request_send_time, microsecond
        'data': {}    // store data formatrer
    }
"""

from __future__ import unicode_literals
import logging, time, copy
import pprint

from django.core.cache import cache

from natrix.common import exception as natrix_exception

logger = logging.getLogger(__name__)

REGISTER_KEY = 'benchmark_command_register'
REGISTER_LOCK = 'benchmark_register_lock'
COMMAND_REGISTER_KEY = 'benchmark_command_register_{command_uuid}'
COMMAND_REGISTER_LOCK = 'benchmark_command_register_{command_uuid}_lock'

COMMAND_STATE_KEY = 'benchmark_state_{command_uuid}_{terminal}_{timestamp}'

RESPONSE_KEY = 'benchmark_response_{command_uuid}_{terminal}'
RESPONSE_LOCK = 'benchmark_response_{command_uuid}_{terminal}_lock'

COMMAND_ACCEPTABLE_TIME = 10000  #microsecond

class CacheLock(object):

    @staticmethod
    def get_lock(lock_name):
        return cache.lock(lock_name)

    @staticmethod
    def release_lock(lock):
        return lock.release()


class CacheOpt(object):

    @staticmethod
    def get(key):
        return cache.get(key)

    @staticmethod
    def set(key, data, timeout=None):
        return cache.set(key, data, timeout=timeout)

    @staticmethod
    def delete(key):
        return cache.delete(key)


class CommandAPI(object):

    @staticmethod
    def registry_command(command_uuid, terminal, command_timestamp, command_info, task_info):
        """

        :param command_uuid:
        :param command_info:
        :return operation: None(Do nothing, occur error), update(add task info), create(a new record)
        """
        def add_command_register():
            register_lock = CacheLock.get_lock(REGISTER_LOCK)
            try:
                register_lock.acquire()
                register_data = CacheOpt.get(REGISTER_KEY)
                if register_data is None:
                    logger.debug('Initialize Register .....')
                    register_data = set()

                if command_uuid not in register_data:
                    logger.info('Registry a new command ({})'.format(command_uuid))
                    register_data.add(command_uuid)
                    CacheOpt.set(REGISTER_KEY, register_data)
            finally:
                CacheLock.release_lock(register_lock)

        def add_terminal_record(command_timestamp):
            command_register_lock = CacheLock.get_lock(
                            COMMAND_REGISTER_LOCK.format(command_uuid=command_uuid))

            try:
                command_register_key = COMMAND_REGISTER_KEY.format(command_uuid=command_uuid)
                command_register_lock.acquire()

                command_register_record = CacheOpt.get(command_register_key)
                if command_register_record is None:
                    command_register_record = {
                        'info': command_info,
                        'batches': {}
                    }

                # Command State Machine process
                finished = False
                for key, terminals in command_register_record['batches'].items():
                    if command_timestamp - key > COMMAND_ACCEPTABLE_TIME:
                        continue

                    if terminal not in terminals:
                        continue
                    command_state_key = COMMAND_STATE_KEY.format(command_uuid=command_uuid,
                                                                 terminal=terminal,
                                                                 timestamp=key)
                    command_state = CacheOpt.get(command_state_key)
                    if command_state is None:
                        logger.error('There is an registry command without state machine: '
                                     '{}-{}-{}'.format(command_uuid, terminal, key))
                        continue

                    if command_state['state'] == 'finished':
                        continue

                    command_state['task_tags'].append(task_info)
                    CacheOpt.set(command_state_key, command_state)
                    finished = True
                    break

                if finished:
                    logger.debug('Update command state!')
                    return 'update'
                else:
                    if command_timestamp in command_register_record['batches']:
                        command_register_record['batches'][command_timestamp].add(terminal)
                    else:
                        command_register_record['batches'][command_timestamp] = set([terminal])
                    CacheOpt.set(command_register_key, command_register_record)

                    command_state_key = COMMAND_STATE_KEY.format(command_uuid=command_uuid,
                                                                 terminal=terminal,
                                                                 timestamp=command_timestamp)
                    CacheOpt.set(command_state_key, {
                        'command_generate_time': command_timestamp,
                        'state': 'running',
                        'task_tags': [task_info]
                    })
                    return 'create'

            except Exception as e:
                natrix_exception.natrix_traceback()
                logger.error('Add terminal record (set command state machine) with error: {}'.format(e))
                return None
            finally:
                CacheLock.release_lock(command_register_lock)

        try:
            command_timestamp = int(command_timestamp * 1000)
            add_command_register()
            operation = add_terminal_record(command_timestamp)
            return operation
        except Exception as e:
            natrix_exception.natrix_traceback()
            logger.error('Registry command({}-{}) occur error: {}'.format(
                command_uuid, terminal, e))
            return None

    @staticmethod
    def erase_command(command_uuid, terminal, command_timestamp):

        def erase_command_record(command_timestamp):
            command_register_lock = CacheLock.get_lock(
                COMMAND_REGISTER_LOCK.format(command_uuid=command_uuid))

            try:
                command_register_key = COMMAND_REGISTER_KEY.format(command_uuid=command_uuid)
                command_state_key = COMMAND_STATE_KEY.format(command_uuid=command_uuid,
                                                             terminal=terminal,
                                                             timestamp=command_timestamp)
                command_register_lock.acquire()

                command_register_record = CacheOpt.get(command_register_key)
                if command_register_record is None:
                    logger.error('Erase on a non-exist command register({})!'.format(command_uuid))
                    return None

                if command_timestamp not in command_register_record['batches']:
                    logger.error('Erase on a non-exist command batches({}-{})'.format(
                        command_uuid, command_timestamp
                    ))
                    return None

                if terminal not in command_register_record['batches'][command_timestamp]:
                    logger.error('Erase on a non-exist command instance({}-{}-{})'.format(
                        command_uuid, command_timestamp, terminal
                    ))
                    return None

                command_state = CacheOpt.get(command_state_key)
                if command_state is None:
                    logger.error('Erase on a non-exist command state({}-{}-{})'.format(
                        command_uuid, command_timestamp, terminal
                    ))
                    return None

                if command_state['state'] != 'running':
                    logger.error('Erase an ({}) command({}-{}-{})'.format(
                        command_state['state'], command_uuid, command_timestamp, terminal
                    ))
                    return None

                task_tags = command_state['task_tags']
                command_register_record['batches'][command_timestamp].remove(terminal)
                CacheOpt.set(command_register_key, command_register_record)
                CacheOpt.delete(command_state_key)

                return task_tags
            except Exception as e:
                natrix_exception.natrix_traceback()
                logger.error('Erase command state with error: {}'.format(e))
                return None
            finally:
                CacheLock.release_lock(command_register_lock)

        try:
            command_timestamp = int(command_timestamp * 1000)

            task_tags = erase_command_record(command_timestamp)

            return task_tags

        except Exception as e:
            natrix_exception.natrix_traceback()
            logger.error('Erase command({}-{}-{}) occur error: {}'.format(
                command_uuid, terminal, command_timestamp, e))

            return None

    @staticmethod
    def get_command_protocol(command_uuid):
        """Get command protocol information, this is a read operation.

        Command protocol type can't be changed, so in this method without lock.

        :param command_uuid:
        :return:
        """
        try:
            command_key = COMMAND_REGISTER_KEY.format(command_uuid=command_uuid)
            command_register = CacheOpt.get(command_key)
            if command_register is None:
                logger.error('Get an non-exist command: ({})'.format(command_uuid))
                return None

            command_info = command_register.get('info', None)
            if command_info is None:
                logger.error('Command({}) without "info" field, '
                             'confirm register operation is right!'.format(command_uuid))
                return None
            protocol_type = command_info.get('protocol', None)
            if protocol_type is None:
                logger.error('Command({}) info without "protocol" field, '
                             'confirm register operation is right'.format(command_uuid))
                return None

            return protocol_type

        except Exception as e:
            natrix_exception.natrix_traceback()
            logger.error('Getting command({}) protocol occur error: {}.'.format(command_uuid, e))
            return None

    @staticmethod
    def available_response(command_uuid, terminal, freshness=60000):
        """Get available response, this is a read operation.

        Last Command Response records the last dial response that a terminal posts. If the timestamp
        field in the Command Reponse is not expired, we think the response data can be reused.

        :param freshness:
        :return:
        """
        try:
            response_key = RESPONSE_KEY.format(command_uuid=command_uuid, terminal=terminal)

            response_record = CacheOpt.get(response_key)

            if response_record is None:
                logger.info('Do not hit command({}-{}) response'.format(command_uuid, terminal))
                return None

            response_timestamp = response_record.get('timestamp', None)
            if response_timestamp is None:
                logger.error('Command({}-{}) response format is wrong!'.format(
                    command_uuid, terminal))
                return None

            delta = time.time() * 1000 - response_timestamp
            if delta > freshness:
                # Don't hit the command response
                logger.info('Do not hit command({}-{}) response'.format(command_uuid, terminal))
                return None
            elif delta < 0:
                logger.error('The command({}-{}) response is in the future'.format(
                    command_uuid, terminal))
                return None
            else:
                logger.info('Hit the command({}-{}) response'.format(command_uuid, terminal))
                return response_record.get('data')
        except Exception as e:
            natrix_exception.natrix_traceback()
            logger.error('Getting command({}-{}) response occur error: {}'.format(
                command_uuid, terminal, e))
            return None

    @staticmethod
    def update_response(command_uuid, terminal, data):
        """Update reponse data, this is a write operation.

        :param command_uuid:
        :param terminal:
        :param data:
        :return:
        """

        try:
            response_lock = CacheLock.get_lock(RESPONSE_LOCK.format(command_uuid=command_uuid,
                                                                    terminal=terminal))
            response_key = RESPONSE_KEY.format(command_uuid=command_uuid, terminal=terminal)
            response_lock.acquire()

            timestamp = data.get('terminal_request_send_time', None)
            if timestamp is None:
                logger.error('Update response with an wrong format response data: {}'.format(data))
                return None

            response_record = {
                'timestamp': timestamp,
                'data': data
            }
            CacheOpt.set(response_key, response_record, timeout=None)
        except Exception as e:
            natrix_exception.natrix_traceback()
            logger.error('Update response record with error: {}'.format(e))
            return None
        finally:
            # release lock
            CacheLock.release_lock(response_lock)

    @staticmethod
    def clean_expired_commands(freshness=300000):
        """

        :param freshness:
        :return:
        """
        def clean_register(command_uuid, curr_time):
            command_register_lock = CacheLock.get_lock(
                    COMMAND_REGISTER_LOCK.format(command_uuid=command_uuid))
            try:
                expired_command = []
                remain_command = {}

                command_register_key = COMMAND_REGISTER_KEY.format(command_uuid=command_uuid)
                command_register_lock.acquire()
                command_register_record = CacheOpt.get(command_register_key)

                for key, v in command_register_record['batches'].items():
                    if curr_time - key < freshness:
                        remain_command[key] = v
                        continue

                    for terminal in v:
                        command_state_key = COMMAND_STATE_KEY.format(
                            command_uuid=command_uuid, terminal=terminal, timestamp=key)

                        command_state_record = CacheOpt.get(command_state_key)
                        task_tags = command_state_record.get('task_tags')

                        expired_command.append({
                            'command_uuid': command_uuid,
                            'timestamp': int(key) / 1000.0,
                            'terminal': terminal,
                            'task_tags': task_tags
                        })

                        CacheOpt.delete(command_state_key)


                command_register_record['batches'] = remain_command
                CacheOpt.set(command_register_key, command_register_record)

                return expired_command
            except Exception as e:
                natrix_exception.natrix_traceback()
                logger.error('Remove terminal record (clean expired commands) with error: {}'.format(e))
                return None
            finally:
                CacheLock.release_lock(command_register_lock)

        command_list = list(CacheOpt.get(REGISTER_KEY))
        curr_time = time.time() * 1000
        expired_list = []

        for command_uuid in command_list:
            expired_commands = clean_register(command_uuid, curr_time)
            expired_list.extend(expired_commands)

        return expired_list







