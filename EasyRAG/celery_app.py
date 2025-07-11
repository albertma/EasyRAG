import os
from celery import Celery
from django.conf import settings

# 设置默认Django设置模块
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'EasyRAG.settings')

# 创建Celery应用
app = Celery('EasyRAGTasks')

# 使用Django的设置
app.config_from_object('django.conf:settings', namespace='CELERY')

# 自动发现任务
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

# Celery配置
app.conf.update(
    # 任务序列化格式
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Asia/Shanghai',
    enable_utc=True,
    
    # 任务路由
    task_routes={
        'EasyRAG.tasks.*': {'queue': 'rag_tasks'},
        'EasyRAG.tasks.document_parsing.*': {'queue': 'document_parsing'},
        'EasyRAG.tasks.workflow.*': {'queue': 'workflow_tasks'},
    },
    
    # 任务执行配置
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    
    # 结果后端配置 - 使用 redis_utils 的配置
    result_backend=settings.CELERY_RESULT_BACKEND,
    
    # 任务结果过期时间
    result_expires=3600,
    
    # 任务重试配置
    task_annotations={
        '*': {
            'retry_backoff': True,
            'retry_backoff_max': 600,
            'max_retries': 3,
        }
    },
    
    # 工作流配置
    task_always_eager=False,
    task_eager_propagates=True,
)

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
