# -*- coding: utf-8 -*-
"""
Maintain device and terminal state machine.
The state machine contains two states: fine and danger.
  - fine to fine :  alive continuous
  - fine to danger:  timeout or power off
  - danger to danger: dead continuous and
  - danger to fine: repost

We store the state info in cache, and all related variables are prefix with 'terminal_alive_'.
The state info structure:
{
   'last_alert_state': True, #True is fine, and False is dead or dangerous
   'curr_state': False,
   'update_time': 0,
   'first_alert_time': 0,
   'alert_times': 0,
   'timestamp': 0,
}

"""
from __future__ import unicode_literals, absolute_import
import time, logging, copy

from django.core.cache import cache

from natrix.common import exception as natrix_exception

logger = logging.getLogger(__name__)

INIT_STATE = {
    'last_alert_state': True,
    'curr_state': True,
    'update_time': time.time(),
    'first_alert_time': 0,
    'alert_times': 0,
    'timestamp': time.time()
}

class AliveStateObject(object):
    cache_prefix = 'terminal_alive_{}'

    def __init__(self, pk):
        self.pk = pk
        self.cache_key = self.cache_prefix.format(pk)

        state_info = cache.get(self.cache_key)
        if state_info is None:
            state_info = copy.deepcopy(INIT_STATE)
            state_info['timestamp'] = time.time()

        self.last_alert_state = state_info['last_alert_state']

        self.state_info = state_info

    def get_alert_times(self):
        return self.state_info.get('alert_times')

    def update_state(self, state):
        self.state_info['curr_state'] = state
        self.state_info['update_time'] = time.time()

        cache.set(self.cache_key, self.state_info)

        return self.state_info

    def time_out(self):
        logger.info('{} is timeout'.format(self.pk))
        curr_time = time.time()

        self.state_info['last_alert_state'] = False
        self.state_info['alert_times'] += 1
        self.state_info['timestamp'] = curr_time

        self.state_info['curr_state'] = False

        if self.state_info['alert_times'] == 1:
            self.state_info['first_alert_time'] = curr_time

        cache.set(self.cache_key, self.state_info)

    def power_off(self):
        logger.info('{} is poweroff'.format(self.pk))

        curr_time = time.time()

        self.state_info['last_alert_state'] = False
        self.state_info['alert_times'] += 1
        self.state_info['timestamp'] = curr_time
        if self.state_info['alert_times'] == 1:
            self.state_info['first_alert_time'] = curr_time

        cache.set(self.cache_key, self.state_info)

    def recovery(self):
        logger.info('{} is recovery'.format(self.pk))

        curr_time = time.time()

        self.state_info['last_alert_state'] = True
        self.state_info['alert_times'] = 0
        self.state_info['timestamp'] = curr_time
        self.state_info['first_alert_time'] = 0

        cache.set(self.cache_key, self.state_info)

    def dead_continuous(self):
        logger.info('{} is dead'.format(self.pk))

        curr_time = time.time()

        self.state_info['alert_times'] += 1
        self.state_info['timestamp'] = curr_time
        cache.set(self.cache_key, self.state_info)

    def alive_continuous(self):
        logger.info('{} is aliving'.format(self.pk))

        curr_time = time.time()

        self.state_info['timestamp'] = curr_time
        cache.set(self.cache_key, self.state_info)

    def keep_alive(self, timeout=60):
        try:
            curr_time = time.time()
            last_alert_state = self.state_info.get('last_alert_state')
            curr_state = self.state_info.get('curr_state')
            update_time = self.state_info.get('update_time')

            if curr_time - update_time > timeout:
                self.curr_alert_state = False
                self.time_out()
                return self

            # continuous alive
            if curr_state and last_alert_state:
                self.curr_alert_state = True

                self.alive_continuous()
                return self

            # recovery
            if curr_state and not last_alert_state:
                self.curr_alert_state = True

                self.recovery()
                return self

            # poweroff
            if not curr_state and last_alert_state:
                self.curr_alert_state = False

                self.power_off()
                return self

            # dead continuous
            if not curr_state and not last_alert_state:
                self.curr_alert_state = False

                self.dead_continuous()
                return self

        except Exception as e:
            logger.error('Keep alive with error: {}'.format(e))
            raise natrix_exception.ClassInsideException(message='keep alive failed: {}'.format(e))

    def get_event(self):
        if not hasattr(self, 'curr_alert_state'):
            logger.error('The event only exist after you call keep_alive ({}).'.format(self.pk))
            raise natrix_exception.ClassInsideException(message=u'Call get_event before keep_alive.')

        if self.last_alert_state:
            if self.curr_alert_state:
                return 'aliving', 0
            else:
                # first loss of communication
                return 'dead-first', self.state_info['update_time']
        else:
            if self.curr_alert_state:
                return 'recovery', self.state_info['update_time']
            else:
                return 'dead', self.state_info['timestamp'] - self.state_info['first_alert_time']

    def get_curr_state(self):
        if not hasattr(self, 'curr_alert_state'):
            logger.error('The event only exist after you call keep_alive ({}).'.format(self.pk))
            raise natrix_exception.ClassInsideException(message=u'Call get_event before keep_alive.')
        return self.curr_alert_state


class AliveStateAPI(object):
    """
    This class offers the operations about terminal state machine.

    - update_state: when server receive an terminal post infomation, it must update the terminal or terminal device state.

    - keep_alive: this method will be called by Celery task (terminal_guardian) periodically. It maintain the state of
        terminal and terminal device.

    """

    @staticmethod
    def update_state(pk, state=True):
        """Update state.

        :param pk:
        :param state:
        :return:
        """
        state_instance = AliveStateObject(pk=pk)
        state_instance.update_state(state)

        return state_instance

    @staticmethod
    def keep_alive(pk, timeout=300):
        state_instance = AliveStateObject(pk=pk)

        state_instance.keep_alive(timeout)

        return state_instance













