from django.core.management.base import BaseCommand
from django.conf import settings
import subprocess
import sys
import os


class Command(BaseCommand):
    help = '启动Celery beat调度器'

    def add_arguments(self, parser):
        parser.add_argument(
            '--loglevel',
            type=str,
            default='info',
            choices=['debug', 'info', 'warning', 'error', 'critical'],
            help='日志级别 (默认: info)'
        )
        parser.add_argument(
            '--schedule',
            type=str,
            default='/tmp/celerybeat-schedule',
            help='调度文件路径 (默认: /tmp/celerybeat-schedule)'
        )

    def handle(self, *args, **options):
        loglevel = options['loglevel']
        schedule = options['schedule']

        self.stdout.write(
            self.style.SUCCESS(f'启动Celery beat调度器...')
        )
        self.stdout.write(f'Log level: {loglevel}')
        self.stdout.write(f'Schedule file: {schedule}')

        try:
            # 构建Celery beat命令
            cmd = [
                'celery',
                '-A', 'EasyRAG.celery_app',
                'beat',
                '--loglevel=' + loglevel,
                '--schedule=' + schedule,
                '--pidfile=/tmp/celery_beat.pid',
                '--logfile=/tmp/celery_beat.log'
            ]

            # 启动Celery beat
            self.stdout.write(f'执行命令: {" ".join(cmd)}')
            subprocess.run(cmd, check=True)

        except subprocess.CalledProcessError as e:
            self.stdout.write(
                self.style.ERROR(f'启动Celery beat失败: {e}')
            )
            sys.exit(1)
        except KeyboardInterrupt:
            self.stdout.write(
                self.style.WARNING('收到中断信号，正在停止Celery beat...')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'启动Celery beat时发生错误: {e}')
            )
            sys.exit(1)