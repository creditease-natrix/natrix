# -*- coding: utf-8 -*-
"""

"""

from __future__ import unicode_literals, absolute_import
import time

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
                second /= c
                time_info.append('{} {}'.format(value, unit))

        time_info.reverse()

        return ' '.join(time_info)

    @staticmethod
    def timestamp_presentation(timestamp):
        return time.strftime('%Y%m%d%H%M%S', time.localtime(timestamp))

