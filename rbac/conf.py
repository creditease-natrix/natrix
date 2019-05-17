# -*- coding: utf-8 -*-
from __future__ import unicode_literals


ROLES = {
    'admin_role':{
        'verbose_name': u'组管理角色',
        'help': u'最高权限',
        'name': 'admin_role'
    },
    'task_role':{
        'verbose_name': u'任务管理角色',
        'help': u'拥有创建、修改、删除本组任务的权限',
        'name': 'task_role'

    },
    'alert_role':{
        'verbose_name': u'告警管理角色',
        'help': u'拥有创建、修改、删除本组告警的权限',
        'name': 'alert_role'

    },
    'read_role':{
        'verbose_name': u'只读角色',
        'help': u'只拥有读权限，最低权限',
        'name': 'alert_role'
    }
}

