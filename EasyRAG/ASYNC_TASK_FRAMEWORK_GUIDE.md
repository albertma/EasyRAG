# EasyRAG 异步任务框架使用指南

## 概述

EasyRAG 异步任务框架基于 Celery 构建，提供了灵活、可扩展的文档解析解决方案。该框架支持动态配置解析步骤，支持断点续传、任务管理、批量处理等功能。

## 架构设计

### 核心组件

1. **Celery 应用** (`celery_app.py`)
   - 配置 Celery 应用和任务路由
   - 设置任务队列和结果后端

2. **基础工作流** (`base_workflow.py`)
   - 定义工作流步骤抽象基类
   - 提供工作流执行引擎

3. **解析步骤** (`document_parsing_steps.py`)
   - 实现具体的解析步骤
   - 支持文件获取、解析、向量化等操作

4. **工作流实现** (`document_parsing_workflow.py`)
   - 提供多种预定义工作流
   - 支持自定义工作流配置

5. **Celery 任务** (`celery_tasks.py`)
   - 定义异步任务接口
   - 提供任务管理功能

## 快速开始

### 1. 安装依赖

```bash
pip install celery redis
```

### 2. 启动 Celery Worker

```bash
# 启动 Celery Worker
celery -A EasyRAG.celery_app worker --loglevel=info

# 启动 Celery Beat（如果需要定时任务）
celery -A EasyRAG.celery_app beat --loglevel=info

# 启动 Flower（监控界面）
celery -A EasyRAG.celery_app flower
```

### 3. 基本使用

```python
from EasyRAG.tasks.celery_tasks import parse_document_simple_task

# 启动文档解析任务
result = parse_document_simple_task.delay("document_id_123")

# 获取结果
task_result = result.get()
print(f"解析结果: {task_result}")
```

## 工作流类型

### 1. 简化版工作流 (SimpleDocumentParsingWorkflow)

适用于快速解析，包含核心步骤：

```python
from EasyRAG.tasks.celery_tasks import parse_document_simple_task

result = parse_document_simple_task.delay("document_id")
```

**包含步骤：**
- initialize: 初始化解析环境
- get_file_content: 获取文件内容
- parse_file: 解析文件
- process_chunks: 处理文本块
- update_final_status: 更新最终状态

### 2. 高级工作流 (AdvancedDocumentParsingWorkflow)

适用于复杂文档，包含所有步骤：

```python
from EasyRAG.tasks.celery_tasks import parse_document_advanced_task

result = parse_document_advanced_task.delay("document_id")
```

**包含步骤：**
- 所有简化版步骤
- extract_blocks: 提取块信息
- 更长的超时时间和重试次数
- 更丰富的解析配置

### 3. 自定义工作流 (CustomDocumentParsingWorkflow)

根据需求自定义步骤：

```python
from EasyRAG.tasks.celery_tasks import parse_document_custom_task

# 定义自定义步骤
custom_steps = ["initialize", "get_file_content", "parse_file", "process_chunks"]

# 自定义配置
custom_config = {
    "parse_file": {
        "parser_config": {
            "ocr_enabled": False,
            "image_extraction": False,
            "table_extraction": True
        }
    }
}

result = parse_document_custom_task.delay("document_id", custom_steps, custom_config)
```

## 工作流配置

### 配置结构

```python
workflow_config = {
    "workflow_name": "CustomWorkflow",
    "description": "自定义工作流",
    "version": "1.0",
    "steps": {
        "initialize": {
            "enabled": True,
            "timeout": 60,
            "retry_count": 3
        },
        "get_file_content": {
            "enabled": True,
            "timeout": 300,
            "retry_count": 3,
            "cache_enabled": True,
            "cache_expire": 3600
        },
        "parse_file": {
            "enabled": True,
            "timeout": 1800,
            "retry_count": 2,
            "cache_enabled": True,
            "cache_expire": 7200,
            "parser_config": {
                "ocr_enabled": True,
                "image_extraction": True,
                "table_extraction": True
            }
        },
        "extract_blocks": {
            "enabled": True,
            "timeout": 600,
            "retry_count": 3,
            "cache_enabled": True,
            "cache_expire": 7200
        },
        "process_chunks": {
            "enabled": True,
            "timeout": 3600,
            "retry_count": 2,
            "vector_config": {
                "dimension": 1024,
                "similarity": "cosine",
                "batch_size": 100
            }
        },
        "update_final_status": {
            "enabled": True,
            "timeout": 60,
            "retry_count": 3,
            "cleanup_enabled": True
        }
    },
    "global_config": {
        "max_concurrent_steps": 1,
        "enable_caching": True,
        "enable_logging": True,
        "enable_metrics": True
    }
}
```

### 配置选项说明

#### 步骤配置选项

- **enabled**: 是否启用该步骤
- **timeout**: 步骤超时时间（秒）
- **retry_count**: 重试次数
- **cache_enabled**: 是否启用缓存
- **cache_expire**: 缓存过期时间（秒）

#### 解析器配置选项

- **ocr_enabled**: 是否启用OCR
- **image_extraction**: 是否提取图片
- **table_extraction**: 是否提取表格
- **equation_extraction**: 是否提取公式
- **layout_analysis**: 是否进行布局分析

#### 向量化配置选项

- **dimension**: 向量维度
- **similarity**: 相似度计算方法
- **batch_size**: 批处理大小
- **enable_reranking**: 是否启用重排序

## 任务管理

### 1. 获取任务进度

```python
from EasyRAG.tasks.celery_tasks import get_parse_progress_task

progress_result = get_parse_progress_task.delay("task_id")
progress = progress_result.get()
print(f"任务进度: {progress}")
```

### 2. 取消任务

```python
from EasyRAG.tasks.celery_tasks import cancel_parse_task

cancel_result = cancel_parse_task.delay("task_id")
cancel_status = cancel_result.get()
print(f"取消结果: {cancel_status}")
```

### 3. 重试任务

```python
from EasyRAG.tasks.celery_tasks import retry_parse_task

# 从指定步骤开始重试
retry_result = retry_parse_task.delay("task_id", resume_from="parse_file")
retry_status = retry_result.get()
print(f"重试结果: {retry_status}")
```

### 4. 批量处理

```python
from EasyRAG.tasks.celery_tasks import batch_parse_documents_task

document_ids = ["doc_001", "doc_002", "doc_003"]
batch_config = {"workflow_type": "simple"}

result = batch_parse_documents_task.delay(document_ids, batch_config)
batch_result = result.get()
print(f"批量处理结果: {batch_result}")
```

## 断点续传

支持从指定步骤开始续传：

```python
from EasyRAG.tasks.celery_tasks import parse_document_task

# 从 parse_file 步骤开始续传
result = parse_document_task.delay(
    "document_id", 
    workflow_config, 
    resume_from="parse_file"
)
```

## 缓存机制

框架支持多级缓存：

1. **文件内容缓存**: 缓存下载的文件内容
2. **解析结果缓存**: 缓存文件解析结果
3. **块信息缓存**: 缓存提取的块信息
4. **处理结果缓存**: 缓存向量化处理结果

缓存配置：

```python
{
    "cache_enabled": True,
    "cache_expire": 3600  # 1小时过期
}
```

## 错误处理

### 1. 任务重试

```python
# 自动重试配置
{
    "retry_count": 3,
    "retry_backoff": True,
    "retry_backoff_max": 600
}
```

### 2. 异常处理

```python
try:
    result = parse_document_task.delay("document_id")
    task_result = result.get()
    
    if task_result["success"]:
        print("解析成功")
    else:
        print(f"解析失败: {task_result['error']}")
        
except Exception as e:
    print(f"任务执行异常: {e}")
```

## 监控和日志

### 1. 任务状态监控

```python
# 获取任务详细信息
task_info = {
    "task_id": "task_123",
    "status": "RUNNING",
    "progress": 50.0,
    "message": "正在解析文件",
    "started_at": "2024-01-01T10:00:00",
    "error": None
}
```

### 2. 日志记录

框架自动记录详细日志：

- 任务开始/结束
- 步骤执行状态
- 错误和异常信息
- 性能指标

### 3. Flower 监控

启动 Flower 监控界面：

```bash
celery -A EasyRAG.celery_app flower
```

访问 http://localhost:5555 查看任务监控界面。

## 性能优化

### 1. 并发控制

```python
{
    "global_config": {
        "max_concurrent_steps": 1,  # 限制并发步骤数
        "worker_prefetch_multiplier": 1  # 限制预取任务数
    }
}
```

### 2. 批处理优化

```python
{
    "process_chunks": {
        "vector_config": {
            "batch_size": 100  # 增加批处理大小
        }
    }
}
```

### 3. 缓存优化

```python
{
    "get_file_content": {
        "cache_enabled": True,
        "cache_expire": 7200  # 延长缓存时间
    }
}
```

## 扩展开发

### 1. 添加新的解析步骤

```python
from EasyRAG.tasks.base_workflow import WorkflowStep

class CustomStep(WorkflowStep):
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        # 实现自定义步骤逻辑
        self.update_progress(50, "执行自定义步骤")
        
        # 处理逻辑
        result = self._process_custom_logic(context)
        
        return result
    
    def _process_custom_logic(self, context):
        # 自定义处理逻辑
        pass
```

### 2. 创建新的工作流

```python
from EasyRAG.tasks.document_parsing_workflow import DocumentParsingWorkflow

class CustomWorkflow(DocumentParsingWorkflow):
    def get_workflow_steps(self):
        steps = []
        # 添加自定义步骤
        steps.append(CustomStep("custom_step", {}))
        return steps
```

### 3. 添加新的Celery任务

```python
from EasyRAG.celery_app import app

@app.task(bind=True, name='EasyRAG.tasks.custom_task')
def custom_task(self, *args, **kwargs):
    # 实现自定义任务逻辑
    pass
```

## 最佳实践

### 1. 任务设计

- 保持任务粒度适中
- 合理设置超时时间
- 实现幂等性操作
- 添加适当的重试机制

### 2. 错误处理

- 记录详细的错误信息
- 实现优雅的降级策略
- 提供清晰的错误消息
- 支持手动重试

### 3. 性能优化

- 使用缓存减少重复计算
- 合理设置批处理大小
- 监控任务执行时间
- 优化资源使用

### 4. 监控和维护

- 定期检查任务队列状态
- 监控系统资源使用
- 清理过期的缓存数据
- 备份重要的任务数据

## 故障排除

### 1. 常见问题

**任务卡住**
```bash
# 检查Worker状态
celery -A EasyRAG.celery_app inspect active

# 重启Worker
celery -A EasyRAG.celery_app control restart
```

**内存不足**
```python
# 减少批处理大小
"batch_size": 50

# 启用垃圾回收
import gc
gc.collect()
```

**网络超时**
```python
# 增加超时时间
"timeout": 1800

# 添加重试机制
"retry_count": 5
```

### 2. 调试技巧

```python
# 启用详细日志
import logging
logging.getLogger('EasyRAG.tasks').setLevel(logging.DEBUG)

# 检查任务状态
from EasyRAG.task_app.models import Task
task = Task.objects.get(task_id="task_id")
print(f"任务状态: {task.status}")
print(f"错误信息: {task.error}")
```

## 总结

EasyRAG 异步任务框架提供了强大而灵活的文档解析解决方案。通过合理配置工作流、使用缓存机制、实现错误处理，可以构建高效、可靠的文档解析系统。

框架的主要优势：

1. **灵活性**: 支持动态配置解析步骤
2. **可扩展性**: 易于添加新的步骤和工作流
3. **可靠性**: 支持断点续传和错误重试
4. **可监控性**: 提供详细的任务状态和日志
5. **高性能**: 支持缓存和批处理优化

通过本指南，您可以快速上手并充分利用框架的功能来构建自己的文档解析系统。