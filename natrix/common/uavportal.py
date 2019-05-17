# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import logging
import json
import time

from Crypto.Cipher import AES
from binascii import b2a_hex, a2b_hex

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s - %(name)s (%(lineno)s) - %(levelname)s: %(message)s",
                    datefmt='%Y.%m.%d %H:%M:%S')

class UavAES():
    """
    接入UAV，采用的令牌（token）解密方式。
    """
    def __init__(self, key='UavappHubaEs_keY'):
        self.key = key
        self.mode = AES.MODE_CBC

    def encrypt(self, text):
        pass


    def decrypt(self, text):
        """解密"""
        cryptor = AES.new(self.key, self.mode, self.key)
        try:
            plain_text = cryptor.decrypt(a2b_hex(text))
            return True, plain_text
        except TypeError:
            logger.error(u"解码失败！")
            return False, "解码失败"


    def get_info(self, text):
        """
        获取UAV传递密文解密后的字典对象
        """
        flag, context = self.decrypt(text)
        if flag:
            return self.jsonify_context(context)
        else:
            return None


    def jsonify_context(self, context):
        """
        处理解密后的内容，UAV加密采用PKCS5padding的方式，该方法增加了去除填充的功能
        """
        if context and isinstance(context, str) and len(context) > 0:
            offset = ord(context[-1])
            dict_str = context[0: -1*offset].strip()
            try:
                info = json.loads(dict_str)
                return info
            except TypeError:
                logging.error("UAV传入内容不是合法Json语句")
                return None
        else:
            logging.error("UAV传入内容没有数据")
            return None


class UAVSession():
    """
    获取UAV访问的session
    """

    def __init__(self, context):
        self.context = context
        self.create_time = int(time.time()*1000)
        self.is_session = self.__available__()


    def __available__(self):
        """
        判断session是否有效, 并生成self.session：
            1、数据解析成功；
            2、数据内容(是否存在userId,timeStamp，以及时间间隔小于10s)
        """
        uav_aes = UavAES()
        info = uav_aes.get_info(self.context)
        if info is None:
            logger.error('创建UAV-session未获取到数据')
            return False

        if info.get('userId', None) is None:
            logger.error('UAV未传入userId')
            return False
        else:
            self.username = info.get('userId')
            logger.info("UAV用户请求登录：%s" % info.get('userId'))

        if info.get('timeStamp', None) is None:
            logger.error('未传入时间戳，不能创建用户')
            return False

        timeStamp = info.get('timeStamp')
        if timeStamp.isdigit():
            time_stamp = int(timeStamp)
            self.time_stamp = time_stamp
            time_out = self.create_time-time_stamp

            if 0 < time_out < 10000000:
                self.session = info
                return True
            else:
                logger.error("数据超时:%s(time_stamp) and %s(now), 超时%s毫秒"%
                             (time_stamp, self.create_time, time_out))
                return False
        else:
            logger.error("数据格式不规范， 时间戳不是数值")
            return False


    def is_available(self):
        return self.is_session


    def get_available_user(self):
        # 获取有效的user信息，即session为有效session
        if self.is_session:
            return self.session.get('userId')
        else:
            return None


    def get_timestamp(self):
        if hasattr(self, 'time_stamp'):
            return self.time_stamp
        else:
            return None


    def get_username(self):
        # 获取username信息，可能session为无效的（时间超时）
        if hasattr(self, 'username'):
            return self.username
        else:
            return None




if __name__ == '__main__':
    token = '8ca2fb1a1409e9c43e992fdb9cb3ff0a1f9024e54460f140f9293aade618e61d24d3f62392a75508c1b1570310485da5b831f93f9f2b707c28f5d8c5ae7012b7'
    uav_session = UAVSession(token)
    print uav_session.get_user()


