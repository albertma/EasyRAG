#!/usr/bin/env python3
"""
测试 Celery 任务路由
"""

import os
import time

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'EasyRAG.settings')

import django
django.setup()

from EasyRAG.tasks.celery_rag_tasks import parse_document_task
from EasyRAG.celery_app import app

def test_celery_routing():
    """测试 Celery 任务路由"""
    print("测试 Celery 任务路由...")
    
    # 提交任务
    result = parse_document_task.delay("test_doc_001", {"test": "config"})
    
    print(f"任务ID: {result.id}")
    print(f"任务状态: {result.state}")
    print(f"任务名称: {result.task}")
    
    # 检查任务是否被正确路由
    print(f"任务队列: {result.backend}")
    
    # 等待任务完成
    try:
        task_result = result.get(timeout=30)
        print(f"任务结果: {task_result}")
    except Exception as e:
        print(f"任务执行异常: {e}")
    
    print("路由测试完成")

if __name__ == '__main__':
    test_celery_routing() 