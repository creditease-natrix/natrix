#!/usr/bin/env python
# -*- coding:utf-8 -*-


import commands
import logging
import os
import psutil
import shutil
import subprocess
import time
from django.core import management
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, User
from logging.handlers import RotatingFileHandler
from nconfig import natrixconfig
from rbac.models import Role, Assign, GroupRole, UserInfo


logger = logging.getLogger(__name__)
ln = "natrix_install"
logger = logging.getLogger(ln)
logger.setLevel(logging.DEBUG)

# create log path first
logging_path = "/var/log/natrix/"
if not os.path.exists(logging_path):
    os.makedirs(logging_path)

# create file handler which logs even debug messages
fn = logging_path + ln + '.log'
file_max_bytes = 10485760
file_backup_counts = 10
file_logging_format = "%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s"
file_logging_date_format = "%Y/%m/%d %H:%M:%S"
fh = RotatingFileHandler(filename=fn, maxBytes=file_max_bytes, backupCount=file_backup_counts)
fh.setLevel(logging.DEBUG)
fh_fmt = logging.Formatter(fmt=file_logging_format, datefmt=file_logging_date_format)
fh.setFormatter(fh_fmt)

# create console handler with a higher log level
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
# create formatter and add it to the handlers
console_logging_format = "%(message)s"
ch_fmt = logging.Formatter(fmt=console_logging_format)
ch.setFormatter(ch_fmt)

# add the handlers to logger
logger.addHandler(ch)
logger.addHandler(fh)


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
    def handle(self, *args, **options):
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

        separator = "#" * 80
        logger.info(separator)
        logger.info("natrix initialization starting ......")

        logger.info("1. checking and verifying natrix.ini ......")

        logger.info("2. installing requirements ......")
        requirement_command = "pip install -r {}/requirements_basic.txt".format(base_dir)
        logger.debug("requirement install command:\n \"{}\"".format(requirement_command))
        requirement_status, requirement_result = commands.getstatusoutput(requirement_command)
        if requirement_status == 0:
            logger.debug("requirement install result:\n \"{}\"".format(requirement_result))
        else:
            logger.error("requirement install result:\n \"{}\"".format(requirement_result))
            exit(101)

        # makemigrations
        # migrate
        # loaddata
        logger.info("3. initialize database ......")
        db_username = "natrix"
        db_password = "changeme"
        apps = ["benchmark", "infrastructure", "rbac", "terminal"]
        for app in apps:
            logger.debug("database makemigrations of application: {}".format(app))
            management.call_command("makemigrations", app, verbosity=0, interactive=False)
            logger.debug("database migrate of application: {}".format(app))
            management.call_command("migrate", app, verbosity=0, interactive=False)
        logger.debug("database migrate")
        management.call_command("migrate", verbosity=0, interactive=False)
        logger.debug("database initialize data")
        management.call_command("loaddata", "init_data.json", verbosity=0, interactive=False)
        logger.debug("create user natrix")
        user = User.objects.filter(username="natrix")
        if not user:
            user = User.objects.create_superuser(username=db_username, email="admin@natrix.com", password=db_password)
            user.save()
        logger.debug("create group natrix")
        group = Group.objects.filter(name="admin")
        if not group:
            group = Group.objects.create(name="admin_group")
            group.save()
        logger.debug("initialize rbac")
        admin_role, _ = Role.objects.get_or_create(name="admin", desc="管理员")
        admin_group_role = GroupRole.objects.create(group=group, role=admin_role)
        admin_group_role.save()
        admin_assgin = Assign.objects.create(user=user, group=group, role=admin_role)
        admin_assgin.save()
        admin_user_info = UserInfo.objects.create(user=user)
        admin_user_info.save()

        logger.info("4. initialize elasticsearch index ......")
        logger.info("initialize benchmark elasticsearch index")
        from benchmark.scripts.initialize_es import initializer as benchmark_initializer
        benchmark_initializer()
        logger.info("initialize terminal elasticsearch index")
        from terminal.scripts.initialize_es import initializer as terminal_initializer
        terminal_initializer()

        logger.info("5. create related natrix directories ......")
        dir_config = "/etc/natrix/"
        dir_log = "/var/log/natrix/"
        # or /usr/lib/systemd/system/
        dir_systemd = "/etc/systemd/system/"
        dirs = [dir_config, dir_log, dir_systemd]
        for dir in dirs:
            if not os.path.exists(dir):
                os.makedirs(dir)

        """
        natrix.service
            WorkingDirectory
        natrix-celery.service
            WorkingDirectory
            concurrency
        natrix-celery-beat.service
            WorkingDirectory
        """
        logger.info("6. copy systemd service files ......")
        config = natrixconfig.NatrixConfig()
        # natrix.service
        logger.debug("copy natrix.service file")
        natrix_file = "/etc/systemd/system/natrix.service"
        sample_natrix_file = base_dir + "/nconfig/systemd/natrix.service"
        logger.debug("copying configuration sample file from {} to {} ......".format(sample_natrix_file, natrix_file))
        shutil.copyfile(sample_natrix_file, natrix_file)
        config.read(natrix_file)
        config.set('Service', 'WorkingDirectory', base_dir)
        config.write(open(natrix_file, "w"))

        # natrix-celery-beat.service
        logger.debug("copy natrix-celery-beat.service file")
        celery_beat_file = "/etc/systemd/system/natrix-celery-beat.service"
        sample_celery_beat_file = base_dir + "/nconfig/systemd/natrix-celery-beat.service"
        logger.debug("copying configuration sample file from {} to {} ......".format(sample_celery_beat_file, celery_beat_file))
        shutil.copyfile(sample_celery_beat_file, celery_beat_file)
        config.read(celery_beat_file)
        config.set('Service', 'WorkingDirectory', base_dir)
        config.write(open(celery_beat_file, "w"))

        # natrix-celery.service
        logger.debug("copy natrix-celery.service file")
        celery_file = "/etc/systemd/system/natrix-celery.service"
        sample_celery_file = base_dir + "/nconfig/systemd/natrix-celery.service"
        logger.debug("copying configuration sample file from {} to {} ......".format(sample_celery_file, celery_file))
        shutil.copyfile(sample_celery_file, celery_file)
        config.read(celery_file)
        config.set('Service', 'WorkingDirectory', base_dir)
        celery_command = "/bin/sh -c \'celery multi {} -A natrix --pidfile=/var/run/celery_file.pid --logfile=/var/log/natrix/celery_file.log --loglevel=info --concurrency={}\'"
        cpu_core = psutil.cpu_count()
        concurrency = cpu_core if cpu_core > 6 else 6
        celery_command_start = celery_command.format("start", str(concurrency))
        config.set('Service', 'ExecStart', celery_command_start)
        celery_command_stop = "/bin/sh -c \'celery multi {} -A natrix --pidfile=/var/run/celery_file.pid\'".format("stopwait")
        config.set('Service', 'ExecStop', celery_command_stop)
        celery_command_restart = celery_command.format("restart", str(concurrency))
        config.set('Service', 'ExecReload', celery_command_restart)
        config.write(open(celery_file, "w"))

        # run 'systemctl daemon-reload' to reload units
        logger.debug("7. start and enable natrix-related systemd service")
        # must add shell=True
        daemon_reload_command = "systemctl daemon-reload"
        daemon_reload_process = subprocess.Popen(daemon_reload_command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        # communicate() returns a tuple (stdout, stderr)
        daemon_reload_result = daemon_reload_process.communicate()
        logger.debug("daemon reload command \"{}\" result: {}".format(daemon_reload_command, daemon_reload_result))

        # start and enable service
        services = ["natrix.service", "natrix-celery.service", "natrix-celery-beat.service"]
        for service in services:
            start_service = "systemctl start {}".format(service)
            start_status, start_result = commands.getstatusoutput(start_service)
            if start_status == 0:
                logger.info("start service {} successfully:\n {}".format(start_service, start_result))
            else:
                logger.error("start service {} unsuccessfully:\n {}".format(start_service, start_result))
            enable_service = "systemctl enable {}".format(service)
            enable_status, enable_result = commands.getstatusoutput(enable_service)
            if enable_status == 0:
                logger.info("enable service {} successfully:\n {}".format(enable_service, enable_result))
            else:
                logger.error("enable service {} unsuccessfully:\n {}".format(enable_service, enable_result))

        logger.info("natrix initialization finished")
        logger.info(separator)

        # print help information
        logger.info("\n")
        logger.info(separator)
        help_info = "natrix server started\n"
        help_info += "access website: \n"
        help_info += "    http://127.0.0.1:8000\n"
        help_info += "login in using: \n"
        help_info += "    db_username={}, db_password={}\n".format(db_username, db_password)
        help_info += "there are 3 natrix services:\n"
        help_info += "    natrix.service\n"
        help_info += "    natrix-celery.service\n"
        help_info += "    natrix-celery-beat.service\n"
        help_info += "find logs of natrix services:\n"
        help_info += "    /var/log/natrix/\n"
        logger.info(help_info)
        logger.info(separator)


