# 异步任务框架使用指南

## 概述

异步任务框架是一个基于Redis分布式锁的高性能任务处理系统，支持多实例部署、优先级队列、任务监控等功能。该框架专为EasyRAG项目设计，可以高效处理各种异步任务，如文档解析、邮件发送、数据处理等。

## 主要特性

- ✅ **分布式锁**: 基于Redis的分布式锁机制，防止重复处理
- ✅ **多实例支持**: 支持多个任务处理实例同时运行
- ✅ **优先级队列**: 支持任务优先级，优先处理重要任务
- ✅ **异步处理**: 基于asyncio的异步任务处理
- ✅ **任务监控**: 实时监控任务状态和进度
- ✅ **错误处理**: 完善的异常处理和重试机制
- ✅ **可扩展**: 支持自定义任务处理器
- ✅ **Redis缓存**: 任务状态持久化到Redis

## 架构设计

```
┌─────────────────────────────────────────────────────────────┐
│                    主应用程序 (Django)                      │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │ 任务提交    │  │ 状态查询    │  │ 任务取消    │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                  异步任务框架                                │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │ 任务队列    │  │ 工作线程池  │  │ 任务处理器  │        │
│  │ (Priority)  │  │ (ThreadPool)│  │ (Handlers)  │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Redis缓存层                              │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │  分布式锁   │  │  任务缓存   │  │  状态缓存   │        │
│  │ (Locks)     │  │ (Tasks)     │  │ (Status)    │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
└─────────────────────────────────────────────────────────────┘
```

## 快速开始

### 1. 启动任务框架

```bash
# 使用Django管理命令启动
python manage.py start_async_task_framework --workers 4 --queue-size 100

# 或在代码中启动
from EasyRAG.task_app.async_task_framework import start_task_framework
start_task_framework(max_workers=4, queue_size=100)
```

### 2. 提交任务

```python
from EasyRAG.task_app.async_task_framework import submit_task, TaskPriority

# 提交文档解析任务
task_id = submit_task(
    task_type="DocumentParseTaskHandler",
    task_data={
        'document_id': 'doc_123',
        'user_id': 'user_456',
        'resume_from': 'INIT'
    },
    priority=TaskPriority.HIGH.value,
    timeout=300
)

print(f"任务已提交，ID: {task_id}")
```

### 3. 查询任务状态

```python
from EasyRAG.task_app.async_task_framework import get_task_status

# 获取任务状态
task = get_task_status(task_id)
if task:
    print(f"任务状态: {task.status.value}")
    print(f"进度: {task.progress}%")
    print(f"消息: {task.message}")
```

### 4. 取消任务

```python
from EasyRAG.task_app.async_task_framework import cancel_task

# 取消任务
success = cancel_task(task_id)
if success:
    print("任务已取消")
```

## 任务类型

### 内置任务处理器

1. **DocumentParseTaskHandler**: 文档解析任务
2. **EmailSendTaskHandler**: 邮件发送任务
3. **DataProcessTaskHandler**: 数据处理任务
4. **FileUploadTaskHandler**: 文件上传任务
5. **ReportGenerationTaskHandler**: 报告生成任务
6. **NotificationTaskHandler**: 通知发送任务
7. **BackupTaskHandler**: 备份任务

### 自定义任务处理器

```python
from EasyRAG.task_app.async_task_framework import TaskHandler
from typing import Dict, Any

class CustomTaskHandler(TaskHandler):
    """自定义任务处理器"""
  
    def can_handle(self, task_type: str) -> bool:
        return task_type == "CustomTaskHandler"
  
    async def handle_task(self, task: Task) -> Dict[str, Any]:
        """处理任务的具体实现"""
        try:
            # 获取任务数据
            data = task.task_data
          
            # 执行任务逻辑
            result = await self._process_custom_task(data)
          
            return {
                'success': True,
                'result': result,
                'message': '自定义任务完成'
            }
          
        except Exception as e:
            raise Exception(f"自定义任务失败: {e}")
  
    async def _process_custom_task(self, data: Dict[str, Any]):
        """处理自定义任务的具体逻辑"""
        # 实现具体的任务处理逻辑
        pass

# 注册自定义处理器
from EasyRAG.task_app.async_task_framework import register_task_handler
register_task_handler(CustomTaskHandler)
```

## 任务优先级

### 优先级枚举

```python
from EasyRAG.task_app.async_task_framework import TaskPriority

# 优先级定义
TaskPriority.URGENT    # 紧急 (0)
TaskPriority.HIGH      # 高 (1)
TaskPriority.NORMAL    # 普通 (2)
TaskPriority.LOW       # 低 (3)
```

### 使用优先级

```python
# 提交高优先级任务
high_priority_task = submit_task(
    task_type="EmailSendTaskHandler",
    task_data={'to_email': 'urgent@example.com', 'subject': '紧急通知'},
    priority=TaskPriority.HIGH.value
)

# 提交低优先级任务
low_priority_task = submit_task(
    task_type="DataProcessTaskHandler",
    task_data={'data_source': 'logs.csv'},
    priority=TaskPriority.LOW.value
)
```

## 分布式锁机制

### 锁的工作原理

- 每个任务都会获取一个唯一的分布式锁
- 锁的键格式：`lock:async_task:task:{task_id}`
- 锁的默认超时时间：5分钟
- 使用Lua脚本确保原子性操作

### 锁的使用场景

```python
from EasyRAG.task_app.async_task_framework import DistributedLock
from EasyRAG.common.redis_utils import get_redis_instance

redis_client = get_redis_instance()
lock = DistributedLock(redis_client, "custom_operation:123", timeout=300)

# 方法一：使用上下文管理器
with lock:
    # 执行需要锁保护的操作
    perform_critical_operation()

# 方法二：手动获取和释放
if lock.acquire(timeout=10):
    try:
        perform_critical_operation()
    finally:
        lock.release()
```

## 多实例部署

### 启动多个实例

```bash
# 实例1
python manage.py start_async_task_framework --workers 4 --instance-id "worker-1"

# 实例2
python manage.py start_async_task_framework --workers 4 --instance-id "worker-2"

# 实例3
python manage.py start_async_task_framework --workers 2 --instance-id "worker-3"
```

### 实例间协作

- 所有实例共享同一个Redis缓存
- 任务队列在Redis中统一管理
- 分布式锁确保任务不会重复处理
- 每个实例独立处理任务，互不干扰

## 监控和调试

### 获取统计信息

```python
from EasyRAG.task_app.async_task_framework import get_task_stats

# 获取任务框架统计信息
stats = get_task_stats()
print(f"总任务数: {stats['total_tasks']}")
print(f"已完成: {stats['completed_tasks']}")
print(f"失败: {stats['failed_tasks']}")
print(f"队列大小: {stats['queue_size']}")
print(f"实例ID: {stats['instance_id']}")
```

### 日志配置

```python
import logging

# 设置日志级别
logging.getLogger('EasyRAG.task_app.async_task_framework').setLevel(logging.DEBUG)
logging.getLogger('EasyRAG.task_app.task_handlers').setLevel(logging.DEBUG)
```

### Redis监控

```bash
# 查看Redis中的任务数据
redis-cli keys "async_task:task:*"
redis-cli keys "lock:async_task:*"

# 查看特定任务
redis-cli get "async_task:task:your_task_id"
```

## 在Django视图中使用

### 视图集成示例

```python
from rest_framework.views import APIView
from rest_framework.response import Response
from EasyRAG.task_app.async_task_framework import submit_task, get_task_status, TaskPriority

class DocumentParseView(APIView):
    def post(self, request):
        """启动文档解析"""
        document_id = request.data.get('document_id')
        user_id = request.user.id
      
        # 提交解析任务
        task_id = submit_task(
            task_type="DocumentParseTaskHandler",
            task_data={
                'document_id': document_id,
                'user_id': user_id,
                'resume_from': request.data.get('resume_from')
            },
            priority=TaskPriority.HIGH.value
        )
      
        return Response({
            'task_id': task_id,
            'message': '文档解析任务已提交'
        })

class TaskStatusView(APIView):
    def get(self, request, task_id):
        """查询任务状态"""
        task = get_task_status(task_id)
      
        if task:
            return Response({
                'task_id': task.task_id,
                'status': task.status.value,
                'progress': task.progress,
                'message': task.message,
                'error': task.error
            })
        else:
            return Response({'error': '任务不存在'}, status=404)
```

## 配置选项

### 环境变量配置

```bash
# Redis配置
export REDIS_HOST=localhost
export REDIS_PORT=6379
export REDIS_PASSWORD=your_password

# 任务框架配置
export ASYNC_TASK_WORKERS=4
export ASYNC_TASK_QUEUE_SIZE=100
export ASYNC_TASK_REDIS_PREFIX=async_task
```

### Django设置配置

```python
# settings.py

# 异步任务框架配置
ASYNC_TASK_CONFIG = {
    'max_workers': int(os.getenv('ASYNC_TASK_WORKERS', '4')),
    'queue_size': int(os.getenv('ASYNC_TASK_QUEUE_SIZE', '100')),
    'redis_prefix': os.getenv('ASYNC_TASK_REDIS_PREFIX', 'async_task'),
    'default_timeout': 300,
    'default_retries': 3,
}
```

## 性能优化

### 1. 工作线程配置

```python
# 根据CPU核心数设置工作线程
import multiprocessing

cpu_count = multiprocessing.cpu_count()
workers = min(cpu_count * 2, 8)  # 最多8个线程

start_task_framework(max_workers=workers)
```

### 2. 队列大小优化

```python
# 根据内存情况设置队列大小
queue_size = 1000  # 大内存服务器
start_task_framework(queue_size=queue_size)
```

### 3. Redis连接池

```python
# 在settings.py中配置Redis连接池
REDIS_CONFIG = {
    'host': 'localhost',
    'port': 6379,
    'max_connections': 20,
    'socket_timeout': 5,
    'socket_connect_timeout': 5,
}
```

## 故障排除

### 常见问题

**问题**: Redis连接失败

```
解决方案: 检查Redis服务是否启动，配置是否正确
```

**问题**: 任务卡在PENDING状态

```
解决方案: 检查任务框架是否启动，工作线程是否正常
```

**问题**: 分布式锁获取失败

```
解决方案: 检查Redis连接，确认锁没有被其他进程占用
```

**问题**: 任务执行超时

```
解决方案: 增加任务超时时间，或优化任务处理逻辑
```

### 调试技巧

```python
# 启用详细日志
import logging
logging.basicConfig(level=logging.DEBUG)

# 检查Redis连接
from EasyRAG.common.redis_utils import get_redis_instance
redis_client = get_redis_instance()
print(f"Redis连接状态: {redis_client.health_check()}")

# 检查任务队列
from EasyRAG.task_app.async_task_framework import get_task_framework
framework = get_task_framework()
print(f"队列中的任务数: {framework.task_queue.qsize()}")
```

## 最佳实践

### 1. 任务设计

- 任务应该是幂等的，支持重复执行
- 合理设置任务超时时间
- 实现适当的错误处理和重试机制
- 避免在任务中执行长时间阻塞操作

### 2. 资源管理

- 合理配置工作线程数量
- 监控内存和CPU使用情况
- 定期清理过期的Redis缓存
- 使用连接池管理数据库连接

### 3. 监控和告警

- 监控任务执行时间
- 设置任务失败率告警
- 监控Redis内存使用情况
- 记录关键操作的日志

### 4. 扩展性考虑

- 支持水平扩展，添加更多工作实例
- 实现任务优先级机制
- 支持任务依赖关系
- 考虑使用消息队列进行任务分发

## 总结

异步任务框架为EasyRAG项目提供了强大的异步任务处理能力，支持分布式部署、优先级队列、任务监控等功能。通过合理配置和使用，可以显著提高系统的并发处理能力和可靠性。

主要优势：

- 高性能：基于异步处理和线程池
- 高可靠：分布式锁和错误处理机制
- 易扩展：支持自定义任务处理器
- 易监控：完善的统计和日志功能
- 易部署：支持多实例部署
