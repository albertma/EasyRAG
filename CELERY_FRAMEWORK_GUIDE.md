# Celery框架使用指南

## 概述

EasyRAG项目使用Celery框架来实现RAG文档的异步解析工作。该框架支持解析步骤的动态配置、任务监控、断点续传等功能，提供了灵活、可扩展的文档处理解决方案。

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

## 架构设计

```
┌─────────────────────────────────────────────────────────────┐
│                    Django应用层                             │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │ RAGManager  │  │ ViewModels  │  │ API Views   │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   Celery任务层                              │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │ 任务定义    │  │ 任务队列    │  │ 任务执行    │        │
│  │ (Tasks)     │  │ (Queues)    │  │ (Workers)   │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   工作流引擎层                              │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │ 基础工作流  │  │ 文档解析    │  │ 自定义工作流│        │
│  │ (BaseWorkflow)│  │ (DocumentParsing)│  │ (CustomWorkflow)│        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   解析步骤层                                │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │ 初始化步骤  │  │ 文件解析    │  │ 块处理      │        │
│  │ (Initialize)│  │ (ParseFile) │  │ (ProcessChunks)│        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   存储层                                   │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │ 文件存储    │  │ 向量数据库  │  │ Redis缓存   │        │
│  │ (MinIO)     │  │ (Elasticsearch)│  │ (Cache)     │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
└─────────────────────────────────────────────────────────────┘
```

## 快速开始

### 1. 环境准备

确保已安装所需依赖：

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

### 4. 启动Celery Beat（可选）

```bash
# 启动定时任务调度器
python manage.py start_celery_beat

# 或直接使用Celery命令
celery -A EasyRAG.celery_app beat --loglevel=info
```

### 5. 启动监控界面（可选）

```bash
# 启动Flower监控界面
python manage.py start_celery_monitor --port 5555

# 或直接使用Celery命令
celery -A EasyRAG.celery_app flower --port=5555
```

## 工作流类型

### 1. 简化版工作流 (SimpleDocumentParsingWorkflow)

适用于快速解析，只包含核心步骤：

```python
from EasyRAG.tasks.celery_tasks import parse_document_simple_task

# 启动简化版解析
result = parse_document_simple_task.delay(document_id)
```

包含步骤：
- initialize: 初始化解析环境
- get_file_content: 获取文件内容
- parse_file: 解析文件
- process_chunks: 处理文本块
- update_final_status: 更新最终状态

### 2. 高级工作流 (AdvancedDocumentParsingWorkflow)

适用于复杂文档解析，包含所有步骤和高级配置：

```python
from EasyRAG.tasks.celery_tasks import parse_document_advanced_task

# 启动高级解析
result = parse_document_advanced_task.delay(document_id)
```

包含步骤：
- initialize: 初始化解析环境（增强版）
- get_file_content: 获取文件内容（带缓存）
- parse_file: 解析文件（OCR、图像提取、表格提取等）
- extract_blocks: 提取块信息
- process_chunks: 处理文本块（向量化、重排序等）
- update_final_status: 更新最终状态

### 3. 自定义工作流 (CustomDocumentParsingWorkflow)

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

## 解析步骤详解

### 1. InitializeStep (初始化步骤)

- **功能**: 初始化解析环境，验证文档存在性
- **配置选项**:
  - timeout: 超时时间（默认60秒）
  - retry_count: 重试次数（默认3次）

### 2. GetFileContentStep (获取文件内容步骤)

- **功能**: 从存储系统获取文件内容
- **配置选项**:
  - timeout: 超时时间（默认300秒）
  - retry_count: 重试次数（默认3次）
  - cache_enabled: 是否启用缓存
  - cache_expire: 缓存过期时间

### 3. ParseFileStep (解析文件步骤)

- **功能**: 解析文件内容，提取文本、图像、表格等
- **配置选项**:
  - timeout: 超时时间（默认1800秒）
  - retry_count: 重试次数（默认2次）
  - cache_enabled: 是否启用缓存
  - cache_expire: 缓存过期时间
  - parser_config: 解析器配置
    - ocr_enabled: 是否启用OCR
    - image_extraction: 是否提取图像
    - table_extraction: 是否提取表格

### 4. ExtractBlocksStep (提取块信息步骤)

- **功能**: 从解析结果中提取块信息
- **配置选项**:
  - timeout: 超时时间（默认600秒）
  - retry_count: 重试次数（默认3次）
  - cache_enabled: 是否启用缓存
  - cache_expire: 缓存过期时间

### 5. ProcessChunksStep (处理文本块步骤)

- **功能**: 处理文本块，进行向量化和存储
- **配置选项**:
  - timeout: 超时时间（默认3600秒）
  - retry_count: 重试次数（默认2次）
  - vector_config: 向量配置
    - dimension: 向量维度
    - similarity: 相似度算法
    - batch_size: 批处理大小

### 6. UpdateFinalStatusStep (更新最终状态步骤)

- **功能**: 更新文档最终状态，清理临时文件
- **配置选项**:
  - timeout: 超时时间（默认60秒）
  - retry_count: 重试次数（默认3次）
  - cleanup_enabled: 是否启用清理

## 缓存机制

### 1. 文件内容缓存

```python
# 缓存文件内容
cache_key = f"file_content_{document_id}"
set_cache(cache_key, file_content, expire=3600)

# 获取缓存的文件内容
file_content = get_cache(cache_key)

# 删除缓存
delete_cache(cache_key)
```

### 2. 解析结果缓存

```python
# 缓存解析结果
cache_key = f"parse_result_{document_id}"
set_cache(cache_key, parse_result, expire=7200)

# 获取缓存的解析结果
parse_result = get_cache(cache_key)
```

### 3. 块信息缓存

```python
# 缓存块信息
cache_key = f"block_info_{document_id}"
set_cache(cache_key, block_info_list, expire=7200)

# 获取缓存的块信息
block_info_list = get_cache(cache_key)
```

## 错误处理

### 1. 任务重试机制

```python
# 自动重试配置
CELERY_TASK_ANNOTATIONS = {
    '*': {
        'retry_backoff': True,
        'retry_backoff_max': 600,
        'max_retries': 3,
    }
}
```

### 2. 异常处理

```python
try:
    result = parse_document_task.delay(document_id)
    task_result = result.get(timeout=300)
    
    if task_result.get('success'):
        print("任务执行成功")
    else:
        print(f"任务执行失败: {task_result.get('error')}")
        
except Exception as e:
    print(f"任务执行异常: {e}")
```

### 3. 断点续传

```python
# 从指定步骤恢复
result = parse_document_task.delay(
    document_id, 
    workflow_config, 
    resume_from='parse_file'
)
```

## 监控和日志

### 1. 任务监控

使用Flower监控界面：

```bash
# 启动监控界面
python manage.py start_celery_monitor --port 5555

# 访问监控界面
# http://localhost:5555
```

### 2. 日志配置

```python
# Django设置中的日志配置
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': 'django.log',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'EasyRAG.tasks': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}
```

### 3. 性能监控

```python
# 任务执行时间监控
import time
from celery import current_task

def monitor_task_performance(func):
    def wrapper(*args, **kwargs):
        start_time = time.time()
        
        try:
            result = func(*args, **kwargs)
            
            # 更新任务状态
            if current_task:
                current_task.update_state(
                    state='PROGRESS',
                    meta={
                        'execution_time': time.time() - start_time,
                        'status': 'completed'
                    }
                )
            
            return result
            
        except Exception as e:
            # 记录错误信息
            if current_task:
                current_task.update_state(
                    state='FAILURE',
                    meta={
                        'execution_time': time.time() - start_time,
                        'error': str(e)
                    }
                )
            raise
    
    return wrapper
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

### 3. 自定义任务

```python
from EasyRAG.celery_app import app

@app.task(bind=True, name='EasyRAG.tasks.custom_parse_task')
def custom_parse_task(self, document_id: str, custom_config: Dict[str, Any] = None):
    """自定义解析任务"""
    task_id = self.request.id
    
    try:
        # 创建自定义工作流
        workflow = CustomDocumentParsingWorkflow(custom_config)
        
        # 执行工作流
        result = workflow.execute({
            "document_id": document_id,
            "task_id": task_id
        })
        
        return result
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
```

## 最佳实践

### 1. 任务设计原则

- **单一职责**: 每个任务只负责一个特定的功能
- **幂等性**: 任务可以重复执行而不产生副作用
- **可恢复性**: 支持断点续传和错误恢复
- **可监控**: 提供详细的状态和进度信息

### 2. 性能优化

- **批量处理**: 对于大量文档，使用批量处理任务
- **缓存策略**: 合理使用缓存减少重复计算
- **并发控制**: 根据系统资源调整并发数
- **超时设置**: 为每个步骤设置合理的超时时间

### 3. 错误处理

- **重试机制**: 为临时性错误设置重试
- **错误分类**: 区分可恢复和不可恢复的错误
- **日志记录**: 详细记录错误信息和上下文
- **监控告警**: 设置错误率监控和告警

### 4. 配置管理

- **环境变量**: 使用环境变量管理敏感配置
- **配置验证**: 验证配置的完整性和正确性
- **默认值**: 为配置项提供合理的默认值
- **文档化**: 详细记录配置项的含义和用法

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

### 2. 调试技巧

```python
# 启用详细日志
CELERY_WORKER_LOG_LEVEL = 'DEBUG'

# 使用同步模式调试
CELERY_TASK_ALWAYS_EAGER = True

# 查看任务状态
from EasyRAG.task_app.models import Task
task = Task.objects.get(task_id='task_id')
print(f"任务状态: {task.status}")
print(f"任务消息: {task.message}")
```

### 3. 性能调优

```python
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

## 总结

Celery框架为EasyRAG项目提供了强大的异步文档解析能力，支持灵活的配置和扩展。通过合理使用工作流、缓存机制和监控工具，可以构建高效、可靠的文档处理系统。

关键要点：
1. 根据文档类型和需求选择合适的工作流
2. 合理配置缓存和超时参数
3. 实现完善的错误处理和监控
4. 遵循最佳实践进行开发和部署
5. 定期进行性能优化和故障排查