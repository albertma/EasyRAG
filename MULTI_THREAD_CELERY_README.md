# 多线程 Celery 任务处理系统

## Celery 特性使用

### 1. delay() 方法 - 异步任务提交
```python
celery_result = parse_document_task.delay(document_id, workflow_config)
```

### 2. AsyncResult - 任务状态查询
```python
celery_result = AsyncResult(task.instance_id, app=app)
if celery_result.ready():
    result = celery_result.result
```

### 3. 线程数量控制
```python
config = TaskProcessorConfig()
config.consumer_threads = 5  # 设置消费者线程数
processor = TaskProcessor(config)
```

## 配置选项
- consumer_threads: 消费者线程数量
- max_queue_size: 队列最大长度
- batch_size: 批处理大小
- producer_interval: 生产者检查间隔
- monitor_interval: 监控检查间隔 