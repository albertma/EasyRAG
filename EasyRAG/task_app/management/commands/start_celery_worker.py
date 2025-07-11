from django.core.management.base import BaseCommand
from django.conf import settings
import subprocess
import sys
import os


class Command(BaseCommand):
    help = '启动Celery worker进程'

    def add_arguments(self, parser):
        parser.add_argument(
            '--workers',
            type=int,
            default=4,
            help='Worker进程数量 (默认: 4)'
        )
        parser.add_argument(
            '--queues',
            type=str,
            default='rag_tasks,document_parsing,workflow_tasks',
            help='要处理的队列列表，用逗号分隔 (默认: rag_tasks,document_parsing,workflow_tasks)'
        )
        parser.add_argument(
            '--loglevel',
            type=str,
            default='info',
            choices=['debug', 'info', 'warning', 'error', 'critical'],
            help='日志级别 (默认: info)'
        )
        parser.add_argument(
            '--concurrency',
            type=int,
            default=4,
            help='每个worker的并发数 (默认: 4)'
        )

    def handle(self, *args, **options):
        workers = options['workers']
        queues = options['queues']
        loglevel = options['loglevel']
        concurrency = options['concurrency']

        self.stdout.write(
            self.style.SUCCESS(f'启动Celery worker...')
        )
        self.stdout.write(f'Workers: {workers}')
        self.stdout.write(f'Queues: {queues}')
        self.stdout.write(f'Log level: {loglevel}')
        self.stdout.write(f'Concurrency: {concurrency}')

        try:
            # 构建Celery worker命令
            cmd = [
                'celery',
                '-A', 'EasyRAG.celery_app',
                'worker',
                '--loglevel=' + loglevel,
                '--concurrency=' + str(concurrency),
                '--queues=' + queues,
                '--hostname=worker@%h',
                '--pidfile=/tmp/celery_worker.pid',
                '--logfile=/tmp/celery_worker.log'
            ]

            # 启动Celery worker
            self.stdout.write(f'执行命令: {" ".join(cmd)}')
            subprocess.run(cmd, check=True)

        except subprocess.CalledProcessError as e:
            self.stdout.write(
                self.style.ERROR(f'启动Celery worker失败: {e}')
            )
            sys.exit(1)
        except KeyboardInterrupt:
            self.stdout.write(
                self.style.WARNING('收到中断信号，正在停止Celery worker...')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'启动Celery worker时发生错误: {e}')
            )
            sys.exit(1)