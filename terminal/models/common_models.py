# -*- coding: utf-8 -*-
"""

"""
from __future__ import unicode_literals
import simplejson
import logging

from django.core.serializers import serialize
from django.db import models
from django.db.models.query import QuerySet
from django.contrib.auth.models import User, Group


logger = logging.getLogger(__name__)


OPERATIONS = (
    ("delete", '删除'),
    ('modify', '修改')
)

class MyEncoder(simplejson.JSONEncoder):
    """ 自定义序列化类

    继承自simplejson的编码基类，用于处理复杂类型的编码
    """

    def default(self, obj):
        if isinstance(obj, QuerySet):
            return simplejson.loads(serialize('json', obj))
        if isinstance(obj, models.Model):
            return simplejson.loads(serialize('json', [obj])[1:-1])
        # if hasattr(obj, 'isoformat'):
        #     # 处理日期类型
        #     return obj.isoformat()
        return simplejson.JSONEncoder.default(self, obj)


class History(models.Model):
    """历史记录存储

    """
    model_name = models.CharField(max_length=100)
    pk_field = models.CharField(max_length=100)
    serializers_str = models.CharField(max_length=2000)
    operator = models.ForeignKey(User, null=True)
    operator_group = models.ForeignKey(Group, null=True)
    operation = models.CharField(choices=OPERATIONS, default='modify', max_length=20)
    operate_date = models.DateTimeField("修改时间", auto_now=True)


class HistorySave(models.Model):
    """历史追踪Model

    对于继承该Model数据的变更将存在History表中
    """
    def save(self, operator=None, operator_group=None, *args, **kwargs):
        if self.pk:
            try:
                old_obj = self.__class__.objects.get(pk=self.pk)
                encoder = MyEncoder()
                old_json_inst = encoder.default(old_obj)
                now_json_inst = encoder.default(self)

                logger.debug('old object : {}'.format(old_json_inst))
                logger.debug('now object : {}'.format(now_json_inst))

                if now_json_inst != old_json_inst:
                    History.objects.create(
                        model_name=old_json_inst['model'],
                        pk_field=old_json_inst['pk'],
                        serializers_str=old_json_inst['fields'],
                        operation='modify',
                        operator=operator,
                        operator_group=operator_group
                    )
            except self.__class__.DoesNotExist:
                pass
        super(HistorySave, self).save(*args, **kwargs)

    def delete(self, operator=None, operator_gruop=None, *args, **kwargs):
        old_obj = self.__class__.objects.get(pk=self.pk)
        encoder = MyEncoder()
        old_json_inst = encoder.default(old_obj)
        History.objects.create(
            model_name=old_json_inst['model'],
            pk_field=old_json_inst['pk'],
            serializers_str=old_json_inst['fields'],
            operation='delete',
            operator=operator,
            operator_group=operator_gruop
        )
        super(HistorySave, self).delete(*args, **kwargs)

    class Meta:
        abstract = True

