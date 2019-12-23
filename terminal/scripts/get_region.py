"""Synchronize district info from AMAP(高德）site.

"""
from __future__ import unicode_literals

import requests

from terminal.models import Region


result = requests.get("http://restapi.amap.com/v3/config/district?key=83fe2e12ea46262ed9964ecc27a735e3&subdistrict=2&extensions=base")
region_data = result.json().get("districts")


def insert_region():
    for item in region_data:
        for province_data in item.get("districts"):
            for city_data in province_data.get("districts"):
                if city_data.get("citycode"):
                    try:
                        region = Region.objects.get(citycode=city_data.get("citycode"))
                        if region.province != province_data.get("name"):
                            region.province = province_data.get("name")
                        if region.city != city_data.get("name"):
                            region.city = city_data.get("name")
                        region.save()
                    except Region.DoesNotExist:
                        Region.objects.create(
                            citycode=city_data.get("citycode"),
                            province=province_data.get("name"),
                            city=city_data.get("name")
                        )
    return "update success!"


if __name__ == '__main__':
    insert_region()
