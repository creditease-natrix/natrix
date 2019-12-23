# -*- coding: utf-8 -*-
"""

"""
import sys, traceback

def natrix_traceback():
    ex, val, tb = sys.exc_info()
    traceback.print_exception(ex, val, tb)


class NatrixBaseException(Exception):
    """This exception class is the basic class for all exception in raspi object.
    """
    def __init__(self, err='Natrix BaseException'):
        Exception.__init__(self, err)

    def get_log(self):
        pass


class ParameterException(NatrixBaseException):
    """The exception about parameter.

    It was raised when you call a method, but some parameters aren't satisfactory.
    Such as wrong type, invalid value,

    """

    def __init__(self, err='Natrix ParameterException', parameter=''):
        self.err = err
        self.parameter = parameter

    def get_log(self):
        ex, val, tb = sys.exc_info()
        traceback.print_exception(ex, val, tb)
        return '{0}: {1}'.format(self.err, self.parameter)


class ParameterTypeException(ParameterException):
    """The exception about error type parameter.

    """

    def __init__(self, err='Natrix ParameterTypeException', parameter=''):
        super(ParameterTypeException, self).__init__(err=err,
                                                     parameter=parameter)


class ParameterMissingException(ParameterException):
    """The exception about missing parameter.

    """
    def __init__(self, err='Natrix ParameterMisssingException', parameter=''):
        super(ParameterMissingException, self).__init__(err=err,
                                                        parameter=parameter)


class ParameterInvalidException(ParameterException):
    """The exception about invalid parameter value.

    """

    def __init__(self, err='Natrix ParameterInvalidException', parameter=''):
        super(ParameterInvalidException, self).__init__(err=err,
                                                        parameter=parameter)


class ParameterOutscopeException(ParameterInvalidException):
    """

    """
    def __init__(self, err='Natrix ParameterOutscopeException', parameter=''):
        super(ParameterOutscopeException, self).__init__(err=err,
                                                         parameter=parameter)


class DatabaseException(NatrixBaseException):
    """The exception about db operation.

    """

    def __init__(self, err='Natrix DatabaseException', model='', business=''):
        self.err = err
        self.model = model
        self.business = business

    def get_log(self):
        return '{0}: {1} @ {2}'.format(self.err, self.business, self.model)


class DatabaseDeleteException(DatabaseException):
    """

    """

    def __init__(self, err='Natrix DatabaseDeleteException', model='', business=''):
        super(DatabaseDeleteException, self).__init__(err=err,
                                                      model=model,
                                                      business=business)


class DatabaseTransactionException(DatabaseException):
    """数据库事务异常

    """
    def __init__(self, err='Natrix DatabaseTransactionException', model='', business=''):
        super(DatabaseTransactionException, self).__init__(err=err,
                                                           model=model,
                                                           business=business)


class PermissionException(NatrixBaseException):
    """ The exception about permission

    """
    def __init__(self, err='Natrix PermissionException', reason=''):
        self.err = err
        self.reason = reason

    def get_log(self):
        return u'{}: {}'.format(self.err, self.reason)


class ClassInsideException(NatrixBaseException):
    """

    """
    def __init__(self, err='Natrix ClassInsideException', message=''):
        self.err = err
        self.message = message

    def get_log(self):
        return u'{0}: {1}'.format(self.err, self.message)


class ApplicationException(NatrixBaseException):

    def __init__(self, err='Natrix ApplicationException', message=''):
        self.err = err
        self.message = u'Natrix项目其中异常, {}'.format(message)

    def get_log(self):
        return u'{0}: {1}'.format(self.err, self.message)


class TriggerBugException(NatrixBaseException):
    """

    """
    def __init__(self, err='Natrix TriggerBugException', message=''):
        self.err = err
        self.message = message

    def get_log(self):
        return u'{}: {}'.format(self.err, self.message)


class CeleryException(NatrixBaseException):
    """

    """
    def __init__(self, err='Natrix Celery Exception', message=''):
        self.err = err
        self.message = message

    def get_log(self):
        return u'{0}: {1}'.format(self.err, self.message)


class NetworkException(NatrixBaseException):
    """

    """
    def __init__(self, err='Natrix Network Exception', message=''):
        self.err = err
        self.message = message

    def get_log(self):
        return u'{0}: {1}'.format(self.err, self.message)
