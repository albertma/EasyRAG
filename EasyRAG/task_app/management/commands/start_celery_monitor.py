from django.core.management.base import BaseCommand
from django.conf import settings
import subprocess
import sys
import os


class Command(BaseCommand):
    help = '启动Celery监控界面'

    def add_arguments(self, parser):
        parser.add_argument(
            '--port',
            type=int,
            default=5555,
            help='监控端口 (默认: 5555)'
        )
        parser.add_argument(
            '--host',
            type=str,
            default='localhost',
            help='监控主机 (默认: localhost)'
        )

    def handle(self, *args, **options):
        port = options['port']
        host = options['host']

        self.stdout.write(
            self.style.SUCCESS(f'启动Celery监控界面...')
        )
        self.stdout.write(f'Host: {host}')
        self.stdout.write(f'Port: {port}')
        self.stdout.write(f'访问地址: http://{host}:{port}')

        try:
            # 构建Celery flower命令
            cmd = [
                'celery',
                '-A', 'EasyRAG.celery_app',
                'flower',
                '--port=' + str(port),
                '--host=' + host,
                '--broker=' + settings.CELERY_BROKER_URL,
                '--result-backend=' + settings.CELERY_RESULT_BACKEND
            ]

            # 启动Celery flower
            self.stdout.write(f'执行命令: {" ".join(cmd)}')
            subprocess.run(cmd, check=True)

        except subprocess.CalledProcessError as e:
            self.stdout.write(
                self.style.ERROR(f'启动Celery监控失败: {e}')
            )
            sys.exit(1)
        except KeyboardInterrupt:
            self.stdout.write(
                self.style.WARNING('收到中断信号，正在停止Celery监控...')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'启动Celery监控时发生错误: {e}')
            )
            sys.exit(1)