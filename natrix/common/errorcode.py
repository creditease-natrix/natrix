# -*- coding: utf-8 -*-

from __future__ import unicode_literals


class ErrorCode(object):
    """

    """

    @staticmethod
    def parameter_missing(parameter):
        data = {
            'code': 401,
            'subcode': 'isv.missing-parameter:{}'.format(parameter),
            'message': u'参数缺失：{}'.format(parameter)
        }
        return data

    @staticmethod
    def parameter_invalid(parameter, reason=''):
        data = {
            'code': 402,
            'subcode': 'isv.invalid-paramete:{}'.format(parameter),
            'message': u'无效参数：{}  {}'.format(parameter, reason)
        }
        return data

    @staticmethod
    def db_opt_deny(source, operation, reason):
        """数据库操作被拒绝

        :param source: string, 数据源（建议采用model名称）
        :param operation: string, 操作行为：add, edit, delete......
        :param reason: string, 原因
        :return:
        """
        data = {
            'code': 403,
            'subcode': 'isv.{}-deny-{}:{}'.format(operation,
                                                  source,
                                                  reason),
            'message': reason
        }
        return data

    @staticmethod
    def data_nonexist(source, condition):
        data = {
            'code': 404,
            'subcode': 'isv.{}-not-exist:{}'.format(source,
                                                    condition),
            'message': u'数据不存在'
        }
        return data

    @staticmethod
    def permission_deny(message=u'Permission Issues'):
        data = {
            'code': 405,
            'subcode': 'isv.permission-deny',
            'message': message
        }
        return data

    @staticmethod
    def unauthenticated(message=u'Authentication failed!'):
        data = {
            'code': 406,
            'subcode': 'isv,unauthenticated',
            'message': message
        }
        return data

    @staticmethod
    def sp_db_fault(aspect):
        data = {
            'code': 501,
            'subcode': 'sp.db_fault:{}'.format(aspect),
            'message': u'后台处理业务({})发生错误，请与Natrix管理员联系'.format(aspect)
        }
        return data

    @staticmethod
    def sp_code_bug(aspect):
        """

        :param aspect:
        :return:
        """
        data = {
            'code': 502,
            'subcode': 'sp.code_bug:{}'.format(aspect),
            'message': u'后台代码存在Bug: {}. 请与Natrix管理员联系'.format(aspect)
        }
        return data
