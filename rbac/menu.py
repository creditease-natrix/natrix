# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import copy
import logging

from django.urls import reverse

logger = logging.getLogger(__name__)


BENCHMARK_MENU = {
    'name': u'云拨测',
    'tag': [None, ],

    'menu': [
        {
            'name': u'即时测',
            'type': 'link',
            'desc': u'即时测页面——PING选项',
            'reverse_name': 'natrix_vue',
            'path': 'pingAnalysis',
            'reverse_args': [],
            'tag': [None]

        },
        # {
        #     'name': u'组管理',
        #     'type': 'link',
        #     'reverse_name': 'user_manage',
        #     'desc': u'组管理',
        #     'reverse_args': [],
        #     'tag': ['login']
        # },
    ]
}

# 提供树莓派和职场的管理tab，主要用于管理员组
ADMIN_MENU = {
    'name': u'管理系统',
    'tag': ['administrator'],
    'menu': [
        {
            'name': u'终端管理',
            'type': 'category',
            'desc': u'终端管理',
            'tag': ['login'],
            'children': [
                {
                    'name': u'终端概览',
                    'type': 'link',
                    'desc': u'终端信息概览',
                    'reverse_name': 'natrix_vue',
                    'path': 'terminalOverview',
                    'reverse_args': []
                },
                {
                    'name': u'终端列表',
                    'type': 'link',
                    'desc': u'终端信息列表',
                    'reverse_name': 'natrix_vue',
                    'path': 'terminalSite',
                    'reverse_args': []
                },
                {
                    'name': u'终端设备列表',
                    'type': 'link',
                    'desc': u'终端设备列表信息',
                    'reverse_name': 'natrix_vue',
                    'path': 'terminalList',
                    'reverse_args': []
                },
                {
                    'name': u'终端设备校验',
                    'type': 'link',
                    'desc': u'终端设备校验信息',
                    'reverse_name': 'natrix_vue',
                    'path': 'terminalCheckList',
                    'reverse_args': []
                }
            ]
        },

        {
            'name': u'组织管理',
            'type': 'category',
            'desc': u'组织管理',
            'tag': ['administrator'],
            'children': [
                {
                    'name': u'组织信息管理',
                    'type': 'link',
                    'desc': u'组织信息管理',
                    'reverse_name': 'natrix_vue',
                    'path': 'workInfoManage',
                    'reverse_args': []
                },
            ],
        },
    ]

}


MENU_SHOW = [BENCHMARK_MENU, ADMIN_MENU]

#   menu菜单最多两层
def reverse_menu(title=u'', menu=[], tags=set([None,])):
    """parse menu configuration

    :param title:
    :param menu:
    :param tags:
    :return:
    """
    cmenu = {
        'title': title,
    }
    if not (isinstance(menu, list) and isinstance(tags, set)):
        logger.error(u'Generate menu error: {}'.format(title))
        return None
    menuinfo = []
    for item in menu:
        menuitem = copy.deepcopy(item)
        tag = menuitem.get('tag', [None, ])
        if tags.isdisjoint(tag):
            continue

        type = menuitem.get('type', None)
        if type == 'link':
            menuitem['url'] = reverse(menuitem.get('reverse_name', ''))
        elif type == 'category':
            children = menuitem.get('children', [])
            for child in children:
                child['url'] = reverse(child.get('reverse_name', ''))
        menuinfo.append(menuitem)
    # if len(menuinfo) == 0:
    #     return None

    cmenu['menus'] = menuinfo
    return cmenu


def get_menu(request):
    menus = []
    tags = [None]
    if hasattr(request, 'user_rbac'):
        user_rbac = request.user_rbac
        if not user_rbac is None:
            tags.append('login')
            group = user_rbac.get_group()
            if group and hasattr(group, 'name'):
                tags.append(group.name)
            if group and group.name == 'admin_group':
                tags.append('administrator')

    user_tags = set(tags)
    for pannel in MENU_SHOW:
        pannel_tags = set(pannel.get('tag', [None, ]))
        if user_tags.isdisjoint(pannel_tags):
            continue
        pannel_menu = reverse_menu(title=pannel.get('name', 'Unkown'),
                                   menu=pannel.get('menu', []),
                                   tags=user_tags)
        menus.append(pannel_menu)

    return menus







