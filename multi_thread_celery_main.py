#!/usr/bin/env python3
"""
多线程Celery任务处理系统

包含以下组件：
1. 生产者线程：从数据库获取PENDING状态的任务，放入待处理队列
2. 消费者线程：从队列获取任务，执行任务
3. 队列管理：保证队列中任务唯一，最大长度1000
4. 重启恢复：重启时继续执行RUNNING状态的任务
"""

import os
import time
import threading
import queue
import uuid
from typing import Dict, Any, Optional
from datetime import datetime
from enum import Enum

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'EasyRAG.settings')

import django
django.setup()

from EasyRAG.task_app.models import Task, TaskStatus, TaskType
from EasyRAG.celery_app import app

class TaskProcessorConfig:
    """任务处理器配置"""
    
    def __init__(self):
        # 队列配置
        self.max_queue_size = 1000
        
        # 线程配置
        self.consumer_threads = 3  # 消费者线程数量
        self.producer_enabled = True  # 是否启用生产者线程
        self.monitor_enabled = True  # 是否启用监控线程
        
        # 任务处理配置
        self.batch_size = 100  # 每次从数据库获取的任务数量
        self.producer_interval = 2  # 生产者检查间隔（秒）
        self.monitor_interval = 3  # 监控检查间隔（秒）
        
        # Celery 配置
        self.celery_task_timeout = 3600  # Celery 任务超时时间（秒）
        self.celery_result_expires = 3600  # Celery 结果过期时间（秒）

class TaskProcessor:
    """任务处理器"""
    
    def __init__(self, config: TaskProcessorConfig = None):
        self.config = config or TaskProcessorConfig()
        self.task_queue = queue.Queue(maxsize=self.config.max_queue_size)
        self.processing_tasks = set()  # 正在处理的任务ID集合
        self.running = False
        self.lock = threading.Lock()
        
        # 线程
        self.producer_thread = None
        self.consumer_thread_list = []
        self.monitor_thread = None
        
    def start(self):
        """启动任务处理器"""
        print("启动任务处理器...")
        self.running = True
        
        # 启动生产者线程
        self.producer_thread = threading.Thread(
            target=self._producer_worker, 
            name="TaskProducer",
            daemon=True
        )
        self.producer_thread.start()
        print("✅ 生产者线程已启动")
        
        # 启动消费者线程
        for i in range(self.config.consumer_threads):
            consumer_thread = threading.Thread(
                target=self._consumer_worker,
                name=f"TaskConsumer-{i+1}",
                daemon=True
            )
            consumer_thread.start()
            self.consumer_thread_list.append(consumer_thread)
            print(f"✅ 消费者线程 {i+1} 已启动")
        
        # 启动监控线程
        self.monitor_thread = threading.Thread(
            target=self._monitor_worker,
            name="TaskMonitor",
            daemon=True
        )
        self.monitor_thread.start()
        print("✅ 监控线程已启动")
        
        # 恢复RUNNING状态的任务
        self._recover_running_tasks()
        
    def stop(self):
        """停止任务处理器"""
        print("停止任务处理器...")
        self.running = False
        
        # 等待线程结束
        if self.producer_thread:
            self.producer_thread.join(timeout=5)
        
        for thread in self.consumer_thread_list:
            thread.join(timeout=5)
        
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        
        print("✅ 任务处理器已停止")
    
    def _recover_running_tasks(self):
        """恢复RUNNING状态的任务"""
        try:
            with self.lock:
                running_tasks = Task.objects.filter(status=TaskStatus.RUNNING.value)
                count = 0
                
                for task in running_tasks:
                    if task.task_id not in self.processing_tasks:
                        # 将RUNNING状态的任务重新放入队列
                        try:
                            self.task_queue.put_nowait(task.task_id)
                            self.processing_tasks.add(task.task_id)
                            count += 1
                            print(f"🔄 恢复RUNNING任务: {task.task_id}")
                        except queue.Full:
                            print(f"⚠️  队列已满，无法恢复任务: {task.task_id}")
                            break
                
                if count > 0:
                    print(f"✅ 恢复了 {count} 个RUNNING状态的任务")
                else:
                    print("ℹ️  没有需要恢复的RUNNING状态任务")
                    
        except Exception as e:
            print(f"❌ 恢复RUNNING任务失败: {e}")
    
    def _producer_worker(self):
        """生产者线程：从数据库获取PENDING任务"""
        print("生产者线程开始工作...")
        
        while self.running:
            try:
                # 获取PENDING状态的任务
                with self.lock:
                    pending_tasks = Task.objects.filter(
                    status=TaskStatus.PENDING.value).order_by('priority', 'created_at')[:self.config.batch_size]
                
                added_count = 0
                for task in pending_tasks:
                    if not self.running:
                        break
                    
                    # 检查任务是否已在队列中
                    if task.task_id not in self.processing_tasks:
                        try:
                            # 尝试添加到队列
                            self.task_queue.put_nowait(task.task_id)
                            self.processing_tasks.add(task.task_id)
                            added_count += 1
                            print(f"📥 添加任务到队列: {task.task_id} ({task.task_name})")
                        except queue.Full:
                            print(f"⚠️  队列已满 ({self.max_queue_size})，停止添加任务")
                            break
                
                if added_count > 0:
                    print(f"📊 本次添加了 {added_count} 个任务到队列")
                
                # 等待一段时间再检查
                time.sleep(self.config.producer_interval)
                
            except Exception as e:
                print(f"❌ 生产者线程异常: {e}")
                time.sleep(5)  # 异常时等待更长时间
    
    def _consumer_worker(self):
        """消费者线程：处理队列中的任务"""
        thread_name = threading.current_thread().name
        print(f"{thread_name} 开始工作...")
        
        while self.running:
            try:
                # 从队列获取任务ID
                task_id = self.task_queue.get(timeout=5)
                
                if not self.running:
                    break
                
                # 处理任务
                self._process_task(task_id, thread_name)
                
                # 标记任务完成
                self.task_queue.task_done()
                
            except queue.Empty:
                # 队列为空，继续等待
                continue
            except Exception as e:
                print(f"❌ {thread_name} 异常: {e}")
                time.sleep(1)
    
    def _monitor_worker(self):
        """监控线程：监控 Celery 任务状态"""
        thread_name = threading.current_thread().name
        print(f"{thread_name} 开始工作...")
        
        while self.running:
            try:
                # 监控所有 Celery 任务
                self._monitor_all_celery_tasks()
                
                # 等待一段时间再检查
                time.sleep(self.config.monitor_interval)
                
            except Exception as e:
                print(f"❌ {thread_name} 异常: {e}")
                time.sleep(5)
    
    def _process_task(self, task_id: str, thread_name: str):
        """处理单个任务"""
        try:
            # 获取任务
            task = Task.objects.get(task_id=task_id)
            
            print(f"🔄 {thread_name} 开始处理任务: {task_id} ({task.task_name})")
            
            # 更新任务状态为RUNNING
            task.status = TaskStatus.RUNNING.value
            task.started_at = datetime.now()
            task.save()
            
            # 执行任务
            success = self._execute_task(task)
            
            # 更新任务状态
            if success:
                task.status = TaskStatus.COMPLETED.value
                task.progress = 100.0
                task.message = "任务执行成功"
                print(f"✅ {thread_name} 任务执行成功: {task_id}")
            else:
                task.status = TaskStatus.FAILED.value
                task.message = "任务执行失败"
                print(f"❌ {thread_name} 任务执行失败: {task_id}")
            
            task.completed_at = datetime.now()
            task.save()
            
        except Task.DoesNotExist:
            print(f"⚠️  {thread_name} 任务不存在: {task_id}")
        except Exception as e:
            print(f"❌ {thread_name} 处理任务异常: {e}")
            # 更新任务状态为失败
            try:
                task = Task.objects.get(task_id=task_id)
                task.status = TaskStatus.FAILED.value
                task.error = str(e)
                task.completed_at = datetime.now()
                task.save()
            except:
                pass
        finally:
            # 从处理中集合移除
            with self.lock:
                self.processing_tasks.discard(task_id)
    
    def _monitor_celery_task(self, task: Task):
        """监控 Celery 任务状态"""
        try:
            if not task.instance_id:
                return
            
            from EasyRAG.celery_app import app
            from celery.result import AsyncResult
            
            # 获取 Celery 任务结果
            celery_result = AsyncResult(task.instance_id, app=app)
            
            if celery_result.ready():
                if celery_result.successful():
                    # 任务成功完成
                    result = celery_result.result
                    task.status = TaskStatus.COMPLETED.value
                    task.progress = 100.0
                    task.message = f"Celery 任务完成: {result.get('message', '成功')}"
                    print(f"✅ Celery 任务完成: {task.instance_id}")
                else:
                    # 任务失败
                    task.status = TaskStatus.FAILED.value
                    task.error = str(celery_result.info)
                    task.message = f"Celery 任务失败: {task.instance_id}"
                    print(f"❌ Celery 任务失败: {task.instance_id}")
                
                task.completed_at = datetime.now()
                task.save()
                
            elif celery_result.state == 'PROGRESS':
                # 更新进度
                meta = celery_result.info
                if meta:
                    task.progress = meta.get('current', 0)
                    task.message = meta.get('status', '处理中')
                    task.save()
                    
        except Exception as e:
            print(f"❌ 监控 Celery 任务异常: {e}")
    
    def _monitor_all_celery_tasks(self):
        """监控所有 Celery 任务"""
        try:
            with self.lock:
                running_tasks = Task.objects.filter(
                    status=TaskStatus.RUNNING.value,
                    instance_id__isnull=False
                )
                
                for task in running_tasks:
                    self._monitor_celery_task(task)
                    
        except Exception as e:
            print(f"❌ 监控 Celery 任务异常: {e}")
    
    def _execute_task(self, task: Task) -> bool:
        """执行任务的具体逻辑"""
        try:
            print(f"🔧 执行任务: {task.task_id} - {task.task_name}")
            print(f"   任务类型: {task.task_type}")
            print(f"   任务数据: {task.task_data}")
            
            # 模拟任务执行
            if task.task_type == TaskType.RAG_PARSING_DOCUMENT.value:
                return self._execute_rag_parsing_task(task)
            else:
                print(f"⚠️  未知任务类型: {task.task_type}")
                return False
                
        except Exception as e:
            print(f"❌ 执行任务异常: {e}")
            return False
    
    def _execute_rag_parsing_task(self, task: Task) -> bool:
        """执行RAG文档解析任务"""
        try:
            print(f"📄 开始解析文档...")
            
            # 从任务数据中提取参数
            task_data = task.task_data
            document_id = task_data.get('document_id')
            workflow_config = task_data.get('workflow_config', {})
            
            if not document_id:
                print(f"❌ 任务数据中缺少 document_id: {task_data}")
                return False
            
            # 调用 Celery 任务
            from EasyRAG.tasks.celery_rag_tasks import parse_document_task
            
            print(f"🚀 启动 Celery 任务: document_id={document_id}")
            
            # 启动 Celery 任务
            celery_result = parse_document_task.delay(document_id, workflow_config)
            
            # 更新任务状态，记录 Celery 任务ID
            task.instance_id = celery_result.id
            task.message = f"Celery 任务已启动: {celery_result.id}"
            task.save()
            
            print(f"✅ Celery 任务启动成功: {celery_result.id}")
            return True
            
        except Exception as e:
            print(f"❌ 文档解析失败: {e}")
            return False
    
    def get_queue_status(self) -> Dict[str, Any]:
        """获取队列状态"""
        with self.lock:
            return {
                "queue_size": self.task_queue.qsize(),
                "max_queue_size": self.config.max_queue_size,
                "consumer_threads": self.config.consumer_threads,
                "processing_tasks_count": len(self.processing_tasks),
                "processing_tasks": list(self.processing_tasks),
                "running": self.running,
                "config": {
                    "batch_size": self.config.batch_size,
                    "producer_interval": self.config.producer_interval,
                    "monitor_interval": self.config.monitor_interval
                }
            }

def create_test_tasks():
    """创建测试任务"""
    print("创建测试任务...")
    
    # 清理旧任务
    Task.objects.filter(status__in=[
        TaskStatus.PENDING.value,
        TaskStatus.RUNNING.value
    ]).delete()
    
    # 创建测试任务
    test_tasks = [
        {
            "task_name": "解析PDF文档1",
            "task_type": TaskType.RAG_PARSING_DOCUMENT.value,
            "task_data": {
                "document_id": "doc_001",
                "workflow_config": {
                    "workflow_type": "simple",
                    "description": "简化版文档解析",
                    "steps": {
                        "initialize": {"enabled": True},
                        "get_file_content": {"enabled": True},
                        "parse_file": {"enabled": True},
                        "process_chunks": {"enabled": True},
                        "update_final_status": {"enabled": True}
                    }
                }
            },
            "priority": 1
        },
        {
            "task_name": "解析Word文档1", 
            "task_type": TaskType.RAG_PARSING_DOCUMENT.value,
            "task_data": {
                "document_id": "doc_002",
                "workflow_config": {
                    "workflow_type": "advanced",
                    "description": "高级文档解析",
                    "steps": {
                        "initialize": {"enabled": True, "timeout": 60},
                        "get_file_content": {"enabled": True, "timeout": 300},
                        "parse_file": {"enabled": True, "timeout": 1800},
                        "extract_blocks": {"enabled": True, "timeout": 600},
                        "process_chunks": {"enabled": True, "timeout": 3600},
                        "update_final_status": {"enabled": True, "timeout": 60}
                    }
                }
            },
            "priority": 2
        },
        {
            "task_name": "解析Excel文档1",
            "task_type": TaskType.RAG_PARSING_DOCUMENT.value,
            "task_data": {
                "document_id": "doc_003",
                "workflow_config": {
                    "workflow_type": "custom",
                    "description": "自定义文档解析",
                    "custom_steps": ["initialize", "get_file_content", "parse_file"],
                    "custom_config": {
                        "parse_file": {
                            "parser_config": {
                                "ocr_enabled": True,
                                "image_extraction": True
                            }
                        }
                    }
                }
            },
            "priority": 3
        },
        {
            "task_name": "解析PDF文档2",
            "task_type": TaskType.RAG_PARSING_DOCUMENT.value,
            "task_data": {
                "document_id": "doc_004",
                "workflow_config": {
                    "workflow_type": "simple",
                    "description": "简化版文档解析",
                    "steps": {
                        "initialize": {"enabled": True},
                        "get_file_content": {"enabled": True},
                        "parse_file": {"enabled": True},
                        "process_chunks": {"enabled": True},
                        "update_final_status": {"enabled": True}
                    }
                }
            },
            "priority": 1
        },
        {
            "task_name": "解析Word文档2",
            "task_type": TaskType.RAG_PARSING_DOCUMENT.value,
            "task_data": {
                "document_id": "doc_005",
                "workflow_config": {
                    "workflow_type": "advanced",
                    "description": "高级文档解析",
                    "steps": {
                        "initialize": {"enabled": True, "timeout": 60},
                        "get_file_content": {"enabled": True, "timeout": 300},
                        "parse_file": {"enabled": True, "timeout": 1800},
                        "extract_blocks": {"enabled": True, "timeout": 600},
                        "process_chunks": {"enabled": True, "timeout": 3600},
                        "update_final_status": {"enabled": True, "timeout": 60}
                    }
                }
            },
            "priority": 2
        }
    ]
    
    created_count = 0
    for task_data in test_tasks:
        task = Task.objects.create(
            task_id=str(uuid.uuid4()).replace('-', ''),
            task_name=task_data["task_name"],
            task_type=task_data["task_type"],
            task_data=task_data["task_data"],
            priority=task_data["priority"],
            status=TaskStatus.PENDING.value,
            message="等待处理",
            retry_count=0,
            max_retries=3,
            timeout=300
        )
        created_count += 1
        print(f"📝 创建任务: {task.task_id} - {task.task_name}")
    
    print(f"✅ 创建了 {created_count} 个测试任务")
    return created_count

def main():
    """主函数"""
    print("多线程Celery任务处理系统")
    print("=" * 50)
    
    # 创建测试任务
    create_test_tasks()
    
    # 创建配置
    config = TaskProcessorConfig()
    config.consumer_threads = 5  # 设置5个消费者线程
    config.max_queue_size = 2000  # 设置队列最大长度
    config.batch_size = 50  # 每次处理50个任务
    
    # 创建任务处理器
    processor = TaskProcessor(config)
    
    try:
        # 启动处理器
        processor.start()
        
        # 监控运行状态
        print("\n开始监控任务处理状态...")
        while True:
            status = processor.get_queue_status()
            print(f"\n📊 队列状态:")
            print(f"   队列大小: {status['queue_size']}/{status['max_queue_size']}")
            print(f"   消费者线程: {status['consumer_threads']}")
            print(f"   正在处理: {status['processing_tasks_count']}")
            print(f"   运行状态: {'运行中' if status['running'] else '已停止'}")
            print(f"   配置信息: 批处理大小={status['config']['batch_size']}, "
                  f"生产者间隔={status['config']['producer_interval']}s, "
                  f"监控间隔={status['config']['monitor_interval']}s")
            
            # 显示正在处理的任务
            if status['processing_tasks']:
                print(f"   处理中的任务: {', '.join(status['processing_tasks'][:5])}")
                if len(status['processing_tasks']) > 5:
                    print(f"   ... 还有 {len(status['processing_tasks']) - 5} 个任务")
            
            time.sleep(5)
            
    except KeyboardInterrupt:
        print("\n收到中断信号，正在停止...")
    finally:
        # 停止处理器
        processor.stop()
        
        # 显示最终状态
        final_status = processor.get_queue_status()
        print(f"\n📊 最终状态:")
        print(f"   队列大小: {final_status['queue_size']}")
        print(f"   正在处理: {final_status['processing_tasks_count']}")
        
        print("\n🎉 任务处理系统已停止")

def demo_dynamic_config():
    """演示动态配置示例"""
    print("\n" + "="*50)
    print("动态配置示例")
    print("="*50)
    
    # 示例1: 高并发配置
    high_concurrency_config = TaskProcessorConfig()
    high_concurrency_config.consumer_threads = 10
    high_concurrency_config.max_queue_size = 5000
    high_concurrency_config.batch_size = 200
    high_concurrency_config.producer_interval = 1
    print("高并发配置:")
    print(f"  消费者线程: {high_concurrency_config.consumer_threads}")
    print(f"  队列大小: {high_concurrency_config.max_queue_size}")
    print(f"  批处理大小: {high_concurrency_config.batch_size}")
    
    # 示例2: 低资源配置
    low_resource_config = TaskProcessorConfig()
    low_resource_config.consumer_threads = 2
    low_resource_config.max_queue_size = 500
    low_resource_config.batch_size = 20
    low_resource_config.producer_interval = 5
    print("\n低资源配置:")
    print(f"  消费者线程: {low_resource_config.consumer_threads}")
    print(f"  队列大小: {low_resource_config.max_queue_size}")
    print(f"  批处理大小: {low_resource_config.batch_size}")
    
    # 示例3: 平衡配置
    balanced_config = TaskProcessorConfig()
    balanced_config.consumer_threads = 5
    balanced_config.max_queue_size = 2000
    balanced_config.batch_size = 100
    balanced_config.producer_interval = 2
    print("\n平衡配置:")
    print(f"  消费者线程: {balanced_config.consumer_threads}")
    print(f"  队列大小: {balanced_config.max_queue_size}")
    print(f"  批处理大小: {balanced_config.batch_size}")

if __name__ == '__main__':
    # 运行动态配置示例
    demo_dynamic_config()
    
    # 运行主程序
    main() 