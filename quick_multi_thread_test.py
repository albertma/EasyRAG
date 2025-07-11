#!/usr/bin/env python3
"""
快速多线程Celery任务测试脚本

这个脚本提供了一个简化的多线程Celery任务测试，用于快速验证功能。

使用方法:
1. 确保Redis服务已启动
2. 启动Celery Worker: celery -A EasyRAG.celery_app worker --loglevel=info --concurrency=4
3. 运行此脚本: python quick_multi_thread_test.py
"""

import os
import threading
import time
import random
from typing import Dict, Any, List
from datetime import datetime

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'EasyRAG.settings')

def check_redis():
    """检查Redis服务"""
    try:
        from EasyRAG.common.redis_utils import get_redis_instance
        is_health = get_redis_instance().health_check()
        if not is_health:
            print("❌ Redis服务未运行")
            return False
        print("✅ Redis服务已运行")
        return True
    except Exception as e:
        print(f"❌ Redis服务未运行: {e}")
        return False

class QuickTaskExecutor(threading.Thread):
    """快速任务执行器"""
    
    def __init__(self, thread_id: int, num_tasks: int):
        super().__init__()
        self.thread_id = thread_id
        self.num_tasks = num_tasks
        self.results = []
        
    def run(self):
        """执行任务"""
        print(f"线程 {self.thread_id} 开始执行 {self.num_tasks} 个任务")
        
        try:
            # 导入Django设置
            import django
            django.setup()
            
            # 导入Celery任务
            from EasyRAG.tasks.celery_rag_tasks import parse_document_task
            
            for i in range(self.num_tasks):
                try:
                    # 创建测试文档ID
                    document_id = f"doc_thread{self.thread_id}_task{i}_{random.randint(1000, 9999)}"
                    
                    # 创建简单的工作流配置
                    workflow_config = {
                        "workflow_type": "simple",
                        "description": f"线程{self.thread_id}的任务{i}",
                        "steps": {
                            "initialize": {"enabled": True},
                            "get_file_content": {"enabled": True},
                            "parse_file": {"enabled": True},
                            "process_chunks": {"enabled": True},
                            "update_final_status": {"enabled": True}
                        }
                    }
                    
                    print(f"线程 {self.thread_id} 启动任务 {i+1}/{self.num_tasks}: {document_id}")
                    
                    # 启动Celery任务
                    result = parse_document_task.delay(document_id, workflow_config)
                    
                    self.results.append({
                        'thread_id': self.thread_id,
                        'task_id': result.id,
                        'document_id': document_id,
                        'status': 'STARTED',
                        'timestamp': datetime.now().isoformat()
                    })
                    
                    # 稍微延迟，避免任务堆积
                    time.sleep(0.5)
                    
                except Exception as e:
                    print(f"线程 {self.thread_id} 任务 {i+1} 启动失败: {e}")
                    self.results.append({
                        'thread_id': self.thread_id,
                        'document_id': document_id,
                        'status': 'FAILED',
                        'error': str(e),
                        'timestamp': datetime.now().isoformat()
                    })
                    
        except Exception as e:
            print(f"线程 {self.thread_id} 执行失败: {e}")
        
        print(f"线程 {self.thread_id} 完成，成功启动 {len([r for r in self.results if r['status'] == 'STARTED'])} 个任务")

def monitor_tasks(all_results: List[Dict], duration: int = 30):
    """监控任务状态"""
    print(f"\n开始监控任务状态，持续 {duration} 秒...")
    
    start_time = time.time()
    completed_tasks = set()
    
    while time.time() - start_time < duration:
        try:
            # 导入Django设置
            import django
            django.setup()
            
            from EasyRAG.common.redis_utils import get_cache
            
            # 检查每个任务的状态
            for result in all_results:
                if result['status'] == 'STARTED' and 'task_id' in result:
                    task_id = result['task_id']
                    
                    if task_id not in completed_tasks:
                        # 从Redis获取任务状态
                        task_status = get_cache(f"task_status:{task_id}")
                        
                        if task_status:
                            status = task_status.get('status', 'UNKNOWN')
                            progress = task_status.get('progress', 0)
                            worker_id = task_status.get('worker_id', 'UNKNOWN')
                            
                            if status == 'COMPLETED':
                                print(f"✅ 任务完成 - 线程: {result['thread_id']}, 任务ID: {task_id}, Worker: {worker_id}")
                                completed_tasks.add(task_id)
                            elif status == 'FAILED':
                                print(f"❌ 任务失败 - 线程: {result['thread_id']}, 任务ID: {task_id}, Worker: {worker_id}")
                                completed_tasks.add(task_id)
                            elif status == 'RUNNING':
                                print(f"🔄 任务进行中 - 线程: {result['thread_id']}, 进度: {progress}%, Worker: {worker_id}")
            
            # 检查完成率
            if all_results:
                started_tasks = [r for r in all_results if r['status'] == 'STARTED']
                if started_tasks:
                    completion_rate = len(completed_tasks) / len(started_tasks) * 100
                    print(f"📊 任务完成率: {completion_rate:.1f}% ({len(completed_tasks)}/{len(started_tasks)})")
            
            time.sleep(3)  # 每3秒检查一次
            
        except Exception as e:
            print(f"监控任务状态时出错: {e}")
            time.sleep(3)
    
    print("任务监控结束")

def main():
    """主函数"""
    print("快速多线程Celery任务测试")
    print("=" * 40)
    
    # 检查Redis服务
    if not check_redis():
        print("请先启动Redis服务")
        return
    
    # 创建多个线程执行任务
    num_threads = 3
    tasks_per_thread = 5
    all_results = []
    
    print(f"将使用 {num_threads} 个线程，每个线程执行 {tasks_per_thread} 个任务")
    
    # 创建并启动线程
    threads = []
    for i in range(num_threads):
        thread = QuickTaskExecutor(i + 1, tasks_per_thread)
        threads.append(thread)
        thread.start()
    
    # 等待所有线程完成
    for thread in threads:
        thread.join()
        all_results.extend(thread.results)
    
    # 统计结果
    print(f"\n任务启动统计:")
    print(f"总任务数: {len(all_results)}")
    print(f"成功启动: {len([r for r in all_results if r['status'] == 'STARTED'])}")
    print(f"启动失败: {len([r for r in all_results if r['status'] == 'FAILED'])}")
    
    # 显示详细结果
    print(f"\n详细结果:")
    for result in all_results:
        if result['status'] == 'STARTED':
            print(f"✅ 线程 {result['thread_id']} - 任务ID: {result['task_id']} - 文档: {result['document_id']}")
        else:
            print(f"❌ 线程 {result['thread_id']} - 文档: {result['document_id']} - 错误: {result.get('error', '未知错误')}")
    
    # 监控任务进度
    if any(r['status'] == 'STARTED' for r in all_results):
        monitor_tasks(all_results, duration=60)  # 监控1分钟
    
    print("\n测试完成！")

if __name__ == '__main__':
    main() 