# EasyRAG Celery框架使用说明

## 概述

EasyRAG项目集成了Celery框架来实现RAG文档的异步解析工作。该框架支持解析步骤的动态配置、任务监控、断点续传等功能，提供了灵活、可扩展的文档处理解决方案。

## 主要特性

- ✅ **异步处理**: 基于Celery的异步任务处理
- ✅ **动态配置**: 解析步骤可根据文档配置动态修改
- ✅ **工作流引擎**: 支持多种预定义和自定义工作流
- ✅ **任务监控**: 实时监控任务状态和进度
- ✅ **断点续传**: 支持从指定步骤恢复解析
- ✅ **批量处理**: 支持批量文档解析
- ✅ **错误处理**: 完善的异常处理和重试机制
- ✅ **缓存机制**: Redis缓存支持，提高处理效率
- ✅ **可扩展**: 支持自定义解析步骤和工作流

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 启动Redis服务

```bash
# 启动Redis服务
redis-server

# 或使用Docker
docker run -d -p 6379:6379 redis:latest
```

### 3. 启动Celery Worker

```bash
# 使用Django管理命令启动
python manage.py start_celery_worker --workers 4 --concurrency 4

# 或直接使用Celery命令
celery -A EasyRAG.celery_app worker --loglevel=info --concurrency=4
```

### 4. 启动监控界面（可选）

```bash
# 启动Flower监控界面
python manage.py start_celery_monitor --port 5555

# 或直接使用Celery命令
celery -A EasyRAG.celery_app flower --port=5555
```

### 5. 运行演示

```bash
# 运行完整演示
python start_celery_demo.py

# 或运行使用示例
python example_celery_usage.py
```

## 工作流类型

### 1. 简化版工作流

适用于快速解析，只包含核心步骤：

```python
from EasyRAG.tasks.celery_tasks import parse_document_simple_task

# 启动简化版解析
result = parse_document_simple_task.delay(document_id)
```

### 2. 高级工作流

适用于复杂文档解析，包含所有步骤和高级配置：

```python
from EasyRAG.tasks.celery_tasks import parse_document_advanced_task

# 启动高级解析
result = parse_document_advanced_task.delay(document_id)
```

### 3. 自定义工作流

根据需求自定义解析步骤：

```python
from EasyRAG.tasks.celery_tasks import parse_document_custom_task

# 自定义步骤
custom_steps = ['initialize', 'get_file_content', 'parse_file', 'process_chunks']

# 启动自定义解析
result = parse_document_custom_task.delay(document_id, custom_steps)
```

### 4. 完整自定义配置

提供完整的配置控制：

```python
from EasyRAG.tasks.celery_tasks import parse_document_task

# 完整自定义配置
workflow_config = {
    'workflow_name': 'CustomDocumentParsingWorkflow',
    'description': '自定义文档解析工作流',
    'version': '1.0',
    'steps': {
        'initialize': {
            'enabled': True,
            'description': '初始化解析环境',
            'timeout': 60,
            'retry_count': 3
        },
        'get_file_content': {
            'enabled': True,
            'description': '获取文件内容',
            'timeout': 300,
            'retry_count': 3,
            'cache_enabled': True,
            'cache_expire': 3600
        },
        'parse_file': {
            'enabled': True,
            'description': '解析文件内容',
            'timeout': 1800,
            'retry_count': 2,
            'cache_enabled': True,
            'cache_expire': 7200,
            'parser_config': {
                'ocr_enabled': True,
                'image_extraction': True,
                'table_extraction': True
            }
        },
        'extract_blocks': {
            'enabled': False,  # 禁用此步骤
            'description': '提取块信息'
        },
        'process_chunks': {
            'enabled': True,
            'description': '处理文本块',
            'timeout': 3600,
            'retry_count': 2,
            'vector_config': {
                'dimension': 1024,
                'similarity': 'cosine',
                'batch_size': 100
            }
        },
        'update_final_status': {
            'enabled': True,
            'description': '更新最终状态',
            'timeout': 60,
            'retry_count': 3,
            'cleanup_enabled': True
        }
    },
    'global_config': {
        'max_concurrent_steps': 1,
        'enable_caching': True,
        'enable_logging': True,
        'enable_metrics': True
    }
}

# 启动自定义解析
result = parse_document_task.delay(document_id, workflow_config)
```

## 任务管理

### 1. 启动解析任务

```python
from EasyRAG.tasks.celery_tasks import parse_document_task

# 基本用法
result = parse_document_task.delay(document_id)

# 带配置
result = parse_document_task.delay(document_id, workflow_config)

# 断点续传
result = parse_document_task.delay(document_id, workflow_config, resume_from='parse_file')
```

### 2. 批量解析任务

```python
from EasyRAG.tasks.celery_tasks import batch_parse_documents_task

# 批量解析
document_ids = ['doc1', 'doc2', 'doc3']
batch_config = {
    'workflow_type': 'simple',
    'batch_size': 2,
    'max_concurrent': 1
}

result = batch_parse_documents_task.delay(document_ids, batch_config)
```

### 3. 查询任务状态

```python
from EasyRAG.tasks.celery_tasks import get_parse_progress_task

# 查询任务进度
progress_result = get_parse_progress_task.delay(task_id)
progress = progress_result.get()

print(f"任务状态: {progress.get('status')}")
print(f"进度: {progress.get('progress')}%")
print(f"消息: {progress.get('message')}")
```

### 4. 取消任务

```python
from EasyRAG.tasks.celery_tasks import cancel_parse_task

# 取消任务
cancel_result = cancel_parse_task.delay(task_id)
success = cancel_result.get()

if success.get('success'):
    print("任务取消成功")
else:
    print(f"任务取消失败: {success.get('message')}")
```

### 5. 重试任务

```python
from EasyRAG.tasks.celery_tasks import retry_parse_task

# 重试任务
retry_result = retry_parse_task.delay(task_id, resume_from='parse_file')
success = retry_result.get()

if success.get('success'):
    print("任务重试成功")
else:
    print(f"任务重试失败: {success.get('message')}")
```

## 在RAGManager中使用

### 1. 启动文档解析

```python
from EasyRAG.rag_service.rag_manager import get_rag_manager

rag_manager = get_rag_manager()

# 启动简化版解析
result = rag_manager.start_document_parse(
    document_id='doc_123',
    user=user,
    workflow_type='simple'
)

# 启动高级解析
result = rag_manager.start_document_parse(
    document_id='doc_123',
    user=user,
    workflow_type='advanced'
)

# 启动自定义解析（断点续传）
result = rag_manager.start_document_parse(
    document_id='doc_123',
    user=user,
    workflow_type='custom',
    resume_from='parse_file'
)
```

### 2. 停止文档解析

```python
result = rag_manager.stop_document_parse(
    document_id='doc_123',
    user=user
)
```

### 3. 查询解析状态

```python
status = rag_manager.get_parse_status(
    document_id='doc_123',
    user=user
)

print(f"文档状态: {status.get('document_status')}")
print(f"任务状态: {status.get('task_status')}")
print(f"进度: {status.get('document_progress')}%")
```

## 监控和调试

### 1. 使用Flower监控界面

启动监控界面后，访问 http://localhost:5555 可以查看：

- 任务队列状态
- Worker状态
- 任务执行历史
- 实时任务进度
- 错误日志

### 2. 查看日志

```bash
# 查看Celery Worker日志
tail -f /tmp/celery_worker.log

# 查看Celery Beat日志
tail -f /tmp/celery_beat.log

# 查看Django日志
tail -f django.log
```

### 3. 调试模式

```python
# 启用同步模式调试
CELERY_TASK_ALWAYS_EAGER = True

# 启用详细日志
CELERY_WORKER_LOG_LEVEL = 'DEBUG'
```

## 配置说明

### 1. Django设置配置

在 `EasyRAG/settings.py` 中已配置：

```python
# Celery 配置
CELERY_BROKER_URL = f"redis://{REDIS_CONFIG['host']}:{REDIS_CONFIG['port']}/{REDIS_CONFIG['db']}"
CELERY_RESULT_BACKEND = f"redis://{REDIS_CONFIG['host']}:{REDIS_CONFIG['port']}/{REDIS_CONFIG['db']}"

CELERY_TASK_SERIALIZER = 'json'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'Asia/Shanghai'
CELERY_ENABLE_UTC = True

# Celery 任务路由
CELERY_TASK_ROUTES = {
    'EasyRAG.tasks.*': {'queue': 'rag_tasks'},
    'EasyRAG.tasks.document_parsing.*': {'queue': 'document_parsing'},
    'EasyRAG.tasks.workflow.*': {'queue': 'workflow_tasks'},
}

# Celery 任务执行配置
CELERY_TASK_ACKS_LATE = True
CELERY_WORKER_PREFETCH_MULTIPLIER = 1
CELERY_TASK_RESULT_EXPIRES = 3600

# Celery 任务重试配置
CELERY_TASK_ANNOTATIONS = {
    '*': {
        'retry_backoff': True,
        'retry_backoff_max': 600,
        'max_retries': 3,
    }
}
```

### 2. 环境变量配置

```bash
# Redis配置
export REDIS_HOST=localhost
export REDIS_PORT=6379
export REDIS_DB=0
export REDIS_PASSWORD=your_password

# Celery配置
export CELERY_WORKER_CONCURRENCY=4
export CELERY_WORKER_LOG_LEVEL=info
```

## 故障排除

### 1. 常见问题

**问题**: Celery worker无法启动
**解决方案**: 
- 检查Redis连接配置
- 确认Django设置正确加载
- 检查依赖包是否安装完整

**问题**: 任务执行失败
**解决方案**:
- 检查任务日志获取详细错误信息
- 验证输入参数的正确性
- 确认相关服务（MinIO、Elasticsearch）正常运行

**问题**: 任务执行缓慢
**解决方案**:
- 增加worker并发数
- 优化解析配置
- 检查系统资源使用情况

### 2. 性能优化

```bash
# 调整worker配置
celery -A EasyRAG.celery_app worker --concurrency=8 --prefetch-multiplier=1

# 调整队列配置
CELERY_TASK_ROUTES = {
    'EasyRAG.tasks.document_parsing.*': {'queue': 'high_priority'},
    'EasyRAG.tasks.*': {'queue': 'default'},
}

# 调整缓存配置
CELERY_TASK_RESULT_EXPIRES = 7200  # 2小时
```

## 扩展开发

### 1. 自定义解析步骤

```python
from EasyRAG.tasks.base_workflow import WorkflowStep

class CustomParseStep(WorkflowStep):
    """自定义解析步骤"""
    
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行自定义解析逻辑"""
        self.update_progress(10, "开始自定义解析")
        
        try:
            # 实现自定义解析逻辑
            document = context.get("document")
            
            # 自定义处理
            custom_result = self._custom_parse(document)
            
            self.update_progress(100, "自定义解析完成")
            
            return {
                "custom_result": custom_result
            }
            
        except Exception as e:
            self.update_progress(0, f"自定义解析失败: {e}")
            raise
    
    def _custom_parse(self, document):
        """自定义解析方法"""
        # 实现具体的解析逻辑
        pass
```

### 2. 自定义工作流

```python
from EasyRAG.tasks.document_parsing_workflow import DocumentParsingWorkflow

class CustomDocumentParsingWorkflow(DocumentParsingWorkflow):
    """自定义文档解析工作流"""
    
    def get_workflow_steps(self) -> List:
        """获取自定义工作流步骤"""
        steps = super().get_workflow_steps()
        
        # 添加自定义步骤
        custom_step = CustomParseStep("custom_parse", {
            "enabled": True,
            "timeout": 300,
            "retry_count": 2
        })
        
        # 在指定位置插入自定义步骤
        steps.insert(3, custom_step)  # 在parse_file之后插入
        
        return steps
```

## 总结

Celery框架为EasyRAG项目提供了强大的异步文档解析能力，支持灵活的配置和扩展。通过合理使用工作流、缓存机制和监控工具，可以构建高效、可靠的文档处理系统。

关键要点：
1. 根据文档类型和需求选择合适的工作流
2. 合理配置缓存和超时参数
3. 实现完善的错误处理和监控
4. 遵循最佳实践进行开发和部署
5. 定期进行性能优化和故障排查

更多详细信息请参考：
- `CELERY_FRAMEWORK_GUIDE.md` - 详细使用指南
- `example_celery_usage.py` - 使用示例
- `start_celery_demo.py` - 演示脚本