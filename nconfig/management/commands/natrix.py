#!/usr/bin/env python
# -*- coding:utf-8 -*-

import os
import psutil
import shutil
import subprocess
try:
    import ConfigParser as configparser
except ImportError:
    import configparser

from django.core import management
from django.core.management.base import BaseCommand
from django.conf import settings

from rbac.api import init_admin_configuration
from terminal.api import initializations as terminal_api


class NatrixConfig(configparser.ConfigParser):
    def __init__(self, defaults=None):
        configparser.ConfigParser.__init__(self, defaults=None)

    def optionxform(self, optionstr):
        return optionstr


def get_project_dir():
    # return os.path.dirname(os.path.dirname(os.path.dirname(
    #                         os.path.dirname(os.path.abspath(__file__)))))

    return settings.BASE_DIR


class Command(BaseCommand):
    """
    1. check natrix.ini configuration
        elasticsearch
        rabbitmq
    2. pip install requirements.ini
    3. create database
        init database
    4. init elasticsearch
    5. create related directory
    6. copy configuration and systemd files
    7. systemctl daemon-reload, start and enable natrix-related systemd service
    8. print help information
    """

    base_dir = get_project_dir()

    def handle(self, *args, **options):

        self.step_separator()
        self.prompt('natrix initialization starting ......')

        self.install_requirements()
        self.build_database()
        self.init_apps()
        self.init_log_dir()
        # TODO: does systemd is necessary?
        # self.init_service()
        # self.service_reload()

    def install_requirements(self, step=1):
        self.prompt(f'{step}. Installing requirements ......')
        requirement_command = "pip install -r {}/requirements_basic.txt".format(self.base_dir)
        self.prompt(f'requirement install command:  {requirement_command}')
        requirement_status, requirement_result = subprocess.getstatusoutput(requirement_command)
        self.prompt(f'requirement install result: "{requirement_result}"')

        if requirement_status != 0:
            self.prompt(f'requirement install result: "{requirement_result}"')
            exit(101)

    def build_database(self, step=2):
        self.prompt(f'{step}. Initialize database ......')

        apps = ['rbac', 'terminal', 'benchmark', 'sentinel', 'infrastructure']
        for app in apps:
            self.prompt(f'database makemigrations of application: {app}')
            management.call_command("makemigrations", app, verbosity=0, interactive=False)
        self.prompt(f'database migrate of application: {apps}')
        management.call_command("migrate", verbosity=0, interactive=False)

    def init_apps(self, step=3):

        self.prompt(f'{step}. Initialize applications ......')

        self.prompt(f' (1) Initialize RBAC applciation')
        init_admin_configuration()

        self.prompt(f' (2) Initialize Terminal application')
        management.call_command("loaddata", 'init_data.json')
        terminal_api.initialize()

    def init_log_dir(self, step=4):
        self.prompt(f'{step}. create related natrix directories ......')

        dir_log = '/var/log/natrix/'
        if not os.path.exists(dir_log):
            os.makedirs(dir_log)

    def init_service(self, step=5):
        # TODO: does systemd is necessary?
        # dir_config = '/etc/natrix/'
        # or /usr/lib/systemd/system/
        # dir_systemd = '/etc/systemd/system/'
        self.prompt(f'{step}. copy systemd service files ......')
        config = NatrixConfig()
        # natrix.service
        self.prompt('copy natrix.service file')
        natrix_file = '/etc/systemd/system/natrix.service'
        sample_natrix_file = self.base_dir + "/nconfig/systemd/natrix.service"
        self.prompt("copying configuration sample file from {} to {} ......".format(sample_natrix_file, natrix_file))
        shutil.copyfile(sample_natrix_file, natrix_file)
        config.read(natrix_file)
        config.set('Service', 'WorkingDirectory', self.base_dir)
        config.write(open(natrix_file, "w"))

        # natrix-celery-beat.service
        self.prompt("copy natrix-celery-beat.service file")
        celery_beat_file = "/etc/systemd/system/natrix-celery-beat.service"
        sample_celery_beat_file = self.base_dir + "/nconfig/systemd/natrix-celery-beat.service"
        self.prompt(
            "copying configuration sample file from {} to {} ......".format(sample_celery_beat_file, celery_beat_file))
        shutil.copyfile(sample_celery_beat_file, celery_beat_file)
        config.read(celery_beat_file)
        config.set('Service', 'WorkingDirectory', self.base_dir)
        config.write(open(celery_beat_file, "w"))

        # natrix-celery.service
        self.prompt("copy natrix-celery.service file")
        celery_file = "/etc/systemd/system/natrix-celery.service"
        sample_celery_file = self.base_dir + "/nconfig/systemd/natrix-celery.service"
        self.prompt("copying configuration sample file from {} to {} ......".format(sample_celery_file, celery_file))
        shutil.copyfile(sample_celery_file, celery_file)
        config.read(celery_file)
        config.set('Service', 'WorkingDirectory', self.base_dir)
        celery_command = "/bin/sh -c \'celery multi {} -A natrix --pidfile=/var/run/celery_file.pid --logfile=/var/log/natrix/celery_file.log --loglevel=info --concurrency={}\'"
        cpu_core = psutil.cpu_count()
        concurrency = cpu_core if cpu_core > 6 else 6
        celery_command_start = celery_command.format("start", str(concurrency))
        config.set('Service', 'ExecStart', celery_command_start)
        celery_command_stop = "/bin/sh -c \'celery multi {} -A natrix --pidfile=/var/run/celery_file.pid\'".format(
            "stopwait")
        config.set('Service', 'ExecStop', celery_command_stop)
        celery_command_restart = celery_command.format("restart", str(concurrency))
        config.set('Service', 'ExecReload', celery_command_restart)
        config.write(open(celery_file, "w"))

    def service_reload(self, step=6):
        # run 'systemctl daemon-reload' to reload units
        self.prompt(f'{step}. start and enable natrix-related systemd service')
        # must add shell=True
        daemon_reload_command = "systemctl daemon-reload"
        daemon_reload_process = subprocess.Popen(daemon_reload_command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                                 stderr=subprocess.PIPE, shell=True)
        # communicate() returns a tuple (stdout, stderr)
        daemon_reload_result = daemon_reload_process.communicate()
        self.prompt("daemon reload command \"{}\" result: {}".format(daemon_reload_command, daemon_reload_result))

        # start and enable service
        services = ["natrix.service", "natrix-celery.service", "natrix-celery-beat.service"]
        for service in services:
            start_service = "systemctl start {}".format(service)
            start_status, start_result = subprocess.getstatusoutput(start_service)
            if start_status == 0:
                self.prompt("start service {} successfully:\n {}".format(start_service, start_result))
            else:
                self.prompt("start service {} unsuccessfully:\n {}".format(start_service, start_result))
            enable_service = "systemctl enable {}".format(service)
            enable_status, enable_result = subprocess.getstatusoutput(enable_service)
            if enable_status == 0:
                self.prompt("enable service {} successfully:\n {}".format(enable_service, enable_result))
            else:
                self.prompt("enable service {} unsuccessfully:\n {}".format(enable_service, enable_result))

    def step_separator(self):
        print('#' * 80)

    def prompt(self, message):
        print(message)







