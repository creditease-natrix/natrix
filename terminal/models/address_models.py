# -*- coding: utf-8 -*-
"""

"""

from __future__ import unicode_literals
import logging
import pprint

from django.db import models

from .common_models import HistorySave

logger = logging.getLogger(__name__)


class Region(HistorySave):
    """Region

    Region model includes province and city.

    """
    citycode = models.CharField(primary_key=True, max_length=10)
    province = models.CharField(null=False, max_length=20)
    city = models.CharField(null=False, unique=True, max_length=20)

    @staticmethod
    def get_provinces():
        """获取所有的省份信息列表
        :return:
        """
        provinces = []
        regions = Region.objects.all()
        for region in regions:
            if region.province not in provinces:
                provinces.append(region.province)
        return provinces

    @staticmethod
    def get_cities(provinces):
        """对应省份的城市列表信息

        :param provinces:
        :return:
        """
        cities = []
        regions = Region.objects.filter(province__in=provinces)
        for region in regions:
            if region.city not in cities:
                cities.append(region.city)
        return cities

    @staticmethod
    def query_region(provinces, cities):
        """区域查询

        :param provinces:
        :param citys:
        :return:
        """

        if cities and not (u'全部' in cities or 'all' in cities):
            return list(Region.objects.filter(city__in=cities))
        elif provinces and not (u'全部' in provinces or 'all' in provinces):
            return list(Region.objects.filter(province__in=provinces))
        else:
            return list(Region.objects.all())

    def __unicode__(self):
        return '{}-{}'.format(self.province, self.city)


class Address(HistorySave):
    """Address

    """
    region = models.ForeignKey(Region, on_delete=models.CASCADE)
    address = models.CharField("地址", max_length=500, null=False)
    postcode = models.CharField("邮政编码", max_length=500, null=True)

    def __unicode__(self):
        return '{}-{}'.format(self.region, self.address)