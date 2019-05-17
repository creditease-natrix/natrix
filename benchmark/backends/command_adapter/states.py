# -*- coding: utf-8 -*-
"""提供command_adapter中关于command状态管理功能接口

"""

from __future__ import unicode_literals
import logging, time, copy

from django.core.cache import cache

from benchmark.configurations import adapter_conf

logger = logging.getLogger(__name__)

# save the status of command
ALIVE_COMMANDS = 'benchmark_adapter_valid_commands'
# save the information of command
COMMAND_INFO = 'benchmark_adapter_command_info'
# the lock used to operate ALIVE_COMMANDS and COMMAND_INFO
ALIVE_COMMANDS_LOCK = 'benchmark_adapter_valid_commands_lock'

COMMAND_WAIT_TERMINAL_TEMPLATE = 'benchmark_adapter_{command_id}_{timestamp}'
COMMAND_WAIT_TERMINAL_LOCK_TEMPLATE = 'benchmark_adapter_{command_id}_{timestamp}_lock'

class AdapterCommandStatus(object):
    """关于Adapter中Command Status管理的相关方法

    后端与终端交互部分（Command Distributor）与上层业务逻辑解耦，该部分需要维护接收到command实例的生命周期，
    其中command实例为command_uuid + generate_timestamp。

    有两种数据结构用来维护command的声明周期：
    - benchmark_adapter_valid_commands （ALIVE_COMMANDS）
      字典类型，其中key为command_uuid，value为时间戳（对应的command实例）
      {
        '[command_uuid]': [timestamp1, timestamp2],
        ......
      }
      访问该数据结构要获取command集合锁（benchmark_adapter_valid_commands_lock）
    - benchmark_adapter_{command_id}_{timestamp}
      集合类型，保存该command实例为完成的终端集合
      访问该数据结构
      访问该数据结构要获取command实例锁（benchmark_adapter_{command_id}_{timestamp}_lock）

    """
    # TODO: 注意死锁问题，先使用才类中的方法，顺序获取command集合锁和command实例锁。

    @staticmethod
    def add_command_cache(command_uuid, timestamp, terminals, type):
        """Add a command record in cache.

        When command_adapter receive a command, it must generate a record in cache.

        - benchmark_adapter_valid_commands
          It's a dictionary, store the command instance witch is identified by command_uuid
          and timestamp.
        - benchmark_adapter_{command_id}_{timestamp}
          It's a set, store terminals(mac address) where this command will be sent.

        :param command_uuid:
        :param timestamp:
        :param terminals:
        :return:
        """
        # Initialize alive command
        alive_command_lock = cache.lock(ALIVE_COMMANDS_LOCK)
        try:
            alive_command_lock.acquire()

            # update alive command info
            alive_commands = cache.get(ALIVE_COMMANDS)
            if alive_commands is None:
                alive_commands = dict()

            if not command_uuid in alive_commands:
                alive_commands[command_uuid] = []
            if not (timestamp in alive_commands[command_uuid]):
                alive_commands[command_uuid].append(timestamp)
                # update alive commands in cache
                cache.set(ALIVE_COMMANDS, alive_commands, timeout=None)

            commands_info = cache.get(COMMAND_INFO)
            if commands_info is None:
                commands_info = dict()
            if not (command_uuid in commands_info):
                commands_info[command_uuid] = {
                    'type': type
                }
                cache.set(COMMAND_INFO, commands_info, timeout=None)

        finally:
            alive_command_lock.release()

        # Initialize command info
        command_info_lock_name = COMMAND_WAIT_TERMINAL_LOCK_TEMPLATE.format(
                        command_id=command_uuid, timestamp=timestamp)
        command_info_name = COMMAND_WAIT_TERMINAL_TEMPLATE.format(
                        command_id=command_uuid, timestamp=timestamp)

        command_info_lock = cache.lock(command_info_lock_name)
        try:
            command_info_lock.acquire()
            command_info = cache.get(command_info_name)
            if not command_info is None:
                logger.warning('Command({}) is repeat, we will merge the terminal.'.format(command_info_name))
                command_info.update(terminals)
            else:
                command_info = set(terminals)

            cache.set(command_info_name, command_info, timeout=None)
        finally:
            command_info_lock.release()

    @staticmethod
    def remove_command_cache(command_uuid, timestamp, terminal):
        """移除特定command的一个记录

        用于command响应、消费超时和响应超时后的状态更新

        :param command_uuid:
        :param timestamp:
        :param terminal:
        :return: (command_exist, record_exist)
        """
        command_exist = False
        record_exist = False

        alive_command_lock = cache.lock(ALIVE_COMMANDS_LOCK)
        try:
            alive_command_lock.acquire()
            alive_commands = cache.get(ALIVE_COMMANDS)

            if command_uuid in alive_commands:
                instance_list = alive_commands[command_uuid]
                if timestamp in instance_list:
                    command_exist = True
                else:
                    logger.info('read the nonexistent command instance: {}-{}'.format(command_uuid, timestamp))
            else:
                logger.info('read the nonexistent command : {}'.format(command_uuid))
        finally:
            alive_command_lock.release()

        if not command_exist:
            return command_exist, record_exist

        command_info_lock_name = COMMAND_WAIT_TERMINAL_LOCK_TEMPLATE.format(
            command_id=command_uuid, timestamp=timestamp)
        command_info_name = COMMAND_WAIT_TERMINAL_TEMPLATE.format(
            command_id=command_uuid, timestamp=timestamp)

        command_info_lock = cache.lock(command_info_lock_name)
        try:
            command_info_lock.acquire()
            command_info = cache.get(command_info_name)
            if command_info is None:
                command_exist = False
            else:
                if terminal in command_info:
                    command_info.discard(terminal)
                    cache.set(command_info_name, command_info, timeout=None)
                    logger.info('remove command record: {}'.format(terminal))
                    record_exist = True
                else:
                    logger.info('remove a nonexistent command record: {}'.format(terminal))
        except Exception as e:
            logger.error('There is an uncatch exception')
            command_exist = False
            record_exist = False
        finally:
            command_info_lock.release()

        return command_exist, record_exist

    @staticmethod
    def clean_command_cache():
        """清除command所有信息

        清理超时未响应的命令，并返回相关信息

        :return:
        """
        timeout_command = {}
        alive_command_lock = cache.lock(ALIVE_COMMANDS_LOCK)
        # Retrieve and remove timeout command instance record
        try:
            alive_command_lock.acquire()

            alive_commands = cache.get(ALIVE_COMMANDS)
            alive_commands_backup = copy.deepcopy(alive_commands)
            if alive_commands is None:
                alive_commands = dict()
            now_timestamp = time.time()
            for command_uuid, timestamps in alive_commands_backup.items():
                for t in timestamps:
                    if now_timestamp - t > adapter_conf.COMMAND_TIMEOUT:
                        # remove t from alive_commands
                        alive_commands[command_uuid].remove(t)

                        if not command_uuid in timeout_command:
                            timeout_command[command_uuid] = dict()
                        timeout_command[command_uuid][t] = None

            cache.set(ALIVE_COMMANDS, alive_commands, timeout=None)
        finally:
            alive_command_lock.release()

        # clean all timeout command instance
        for command_uuid, command_set in list(timeout_command.items()):
            timestamps = list(command_set.keys())
            for t in timestamps:
                command_info_lock_name = COMMAND_WAIT_TERMINAL_LOCK_TEMPLATE.format(
                    command_id=command_uuid, timestamp=t)
                command_info_name = COMMAND_WAIT_TERMINAL_TEMPLATE.format(
                    command_id=command_uuid, timestamp=t)
                command_info_lock = cache.lock(command_info_lock_name)
                try:
                    command_info_lock.acquire()
                    command_info = cache.get(command_info_name)
                    if not command_info is None:
                       timeout_command[command_uuid][t] = command_info

                    cache.delete(command_info_name)
                finally:
                    command_info_lock.release()

        return timeout_command

    @staticmethod
    def get_command_type(command_uuid):
        """Obtain the command type

        :param command_uuid:
        :return:
        """

        commands_info = cache.get(COMMAND_INFO)
        if commands_info is None:
            return None

        command = commands_info.get(command_uuid, None)
        if command is None:
            return None
        else:
            return command.get('type', None)

