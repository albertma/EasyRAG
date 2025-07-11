from enum import Enum
from django.db import models
class TaskType(Enum):
    RAG_PARSING_DOCUMENT = 'RAG_PARSING_DOCUMENT'
    

class TaskStatus(Enum):
    """任务状态枚举"""
    PENDING = "PENDING"      # 待处理
    RUNNING = "RUNNING"      # 运行中
    STOP = "STOP"            # 停止
    COMPLETED = "COMPLETED"  # 已完成
    FAILED = "FAILED"        # 失败
    CANCELLED = "CANCELLED"  # 已取消
    TIMEOUT = "TIMEOUT"      # 超时


class TaskPriority(Enum):
    """任务优先级枚举"""
    LOW = 3
    NORMAL = 2
    HIGH = 1
    URGENT = 0

class Task(models.Model):
    task_id = models.CharField(max_length=128, primary_key=True)
    task_name = models.CharField(max_length=128)
    task_type = models.CharField(max_length=128)
    task_related_id = models.CharField(max_length=128, null=True)
    task_data = models.JSONField()
    priority = models.IntegerField(default=TaskPriority.NORMAL.value)
    status = models.CharField(max_length=128, default=TaskStatus.PENDING.value)
    progress = models.FloatField(default=0.0)
    message = models.TextField()
    retry_count = models.IntegerField(default=0)
    max_retries = models.IntegerField(default=3)
    timeout = models.IntegerField(default=300)
    instance_id = models.CharField(max_length=128, null=True)
    created_by = models.CharField(max_length=128, null=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    started_at = models.DateTimeField(null=True)
    completed_at = models.DateTimeField(null=True)
    error = models.TextField(null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)
    
    
    class Meta:
        db_table = 'tasks'
        verbose_name = 'Task'
        verbose_name_plural = 'Tasks'