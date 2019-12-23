# -*- coding: utf-8 -*-
"""

"""
import time


def time_timestamp(time_object):
    """millisecond

    :param time_object:
    :return:
    """

    timestamp = (time.mktime(time_object.timetuple()) - time.timezone) * 1000

    return timestamp


def timestamp_utc(timestamp):
    pass


class TimeProcessor(object):

    @staticmethod
    def second_presentation(second):
        carry_list = (
            (60, 'seconds'),
            (60, 'minutes'),
            (24, 'hours'),
        )
        time_info = []
        second = int(second)
        for c, unit, in carry_list:
            if second != 0:
                value = second % c
                second = int(second / c)
                time_info.append('{} {}'.format(value, unit))

        time_info.reverse()

        return ' '.join(time_info)

    @staticmethod
    def timestamp_presentation(timestamp):
        return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(timestamp))

