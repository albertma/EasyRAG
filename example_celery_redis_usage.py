#!/usr/bin/env python3
"""
Celery 中使用 redis_utils 的示例

这个示例展示了如何在 Celery 任务中使用 redis_utils 进行缓存管理、
状态存储和任务协调。
"""

import os
import time
from typing import Dict, Any

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'EasyRAG.settings')

def example_celery_redis_usage():
    """演示 Celery 中使用 redis_utils 的各种场景"""
    
    print("=== Celery 中使用 redis_utils 示例 ===")
    
    try:
        # 导入必要的模块
        import django
        django.setup()
        
        from EasyRAG.tasks.celery_rag_tasks import (
            parse_document_task, 
            get_parse_progress_task,
            clear_task_cache_task
        )
        from EasyRAG.common.redis_utils import get_redis_instance, set_cache, get_cache, delete_cache
        
        # 1. 获取 Redis 实例
        print("\n1. 获取 Redis 实例...")
        redis_utils = get_redis_instance()
        print(f"   Redis 实例: {type(redis_utils).__name__}")
        print(f"   健康检查: {'✅ 正常' if redis_utils.health_check() else '❌ 异常'}")
        
        # 2. 任务状态缓存
        print("\n2. 任务状态缓存示例...")
        test_task_id = "test_task_123"
        task_status = {
            "task_id": test_task_id,
            "status": "RUNNING",
            "progress": 50,
            "message": "正在处理文档",
            "started_at": "2024-01-01T10:00:00"
        }
        
        # 存储任务状态
        cache_key = f"task_status:{test_task_id}"
        set_cache(cache_key, task_status, expire=3600)
        print(f"   存储任务状态: {cache_key}")
        
        # 获取任务状态
        retrieved_status = get_cache(cache_key)
        print(f"   获取任务状态: {retrieved_status}")
        
        # 3. 启动文档解析任务
        print("\n3. 启动文档解析任务...")
        document_id = "test_doc_456"
        workflow_config = {
            "workflow_type": "simple",
            "description": "测试文档解析"
        }
        
        # 启动任务
        result = parse_document_task.delay(document_id, workflow_config)
        task_id = result.id
        print(f"   任务已启动，ID: {task_id}")
        
        # 4. 监控任务进度
        print("\n4. 监控任务进度...")
        for i in range(5):
            time.sleep(2)
            
            # 从缓存获取任务状态
            task_cache_key = f"task_status:{task_id}"
            cached_status = get_cache(task_cache_key)
            
            if cached_status:
                print(f"   进度 {i+1}: {cached_status.get('status')} - {cached_status.get('progress')}%")
            else:
                print(f"   进度 {i+1}: 缓存中未找到任务状态")
        
        # 5. 批量任务缓存
        print("\n5. 批量任务缓存示例...")
        batch_tasks = [
            {"id": "batch_1", "status": "pending"},
            {"id": "batch_2", "status": "running"},
            {"id": "batch_3", "status": "completed"}
        ]
        
        # 存储批量任务信息
        batch_key = "batch_tasks:test_batch"
        set_cache(batch_key, batch_tasks, expire=7200)
        print(f"   存储批量任务: {batch_key}")
        
        # 获取批量任务信息
        retrieved_batch = get_cache(batch_key)
        print(f"   获取批量任务: {len(retrieved_batch)} 个任务")
        
        # 6. 任务协调示例
        print("\n6. 任务协调示例...")
        coordinator_key = "task_coordinator:test_coord"
        coordinator_data = {
            "active_tasks": 3,
            "completed_tasks": 10,
            "failed_tasks": 1,
            "last_update": time.time()
        }
        set_cache(coordinator_key, coordinator_data, expire=1800)
        print(f"   存储协调器数据: {coordinator_key}")
        
        # 更新协调器数据
        current_data = get_cache(coordinator_key)
        if current_data:
            current_data["active_tasks"] -= 1
            current_data["completed_tasks"] += 1
            current_data["last_update"] = time.time()
            set_cache(coordinator_key, current_data, expire=1800)
            print(f"   更新协调器数据: 活跃任务 {current_data['active_tasks']}")
        
        # 7. 缓存清理
        print("\n7. 缓存清理示例...")
        
        # 清理特定任务缓存
        clear_result = clear_task_cache_task.delay(test_task_id)
        clear_status = clear_result.get()
        print(f"   清理任务缓存: {clear_status}")
        
        # 清理测试缓存
        delete_cache(cache_key)
        delete_cache(batch_key)
        delete_cache(coordinator_key)
        print("   清理测试缓存完成")
        
        # 8. 错误处理和重试
        print("\n8. 错误处理和重试示例...")
        
        # 模拟任务失败缓存
        failed_task_id = "failed_task_789"
        failed_status = {
            "task_id": failed_task_id,
            "status": "FAILED",
            "error": "模拟错误",
            "retry_count": 2,
            "max_retries": 3
        }
        set_cache(f"task_status:{failed_task_id}", failed_status, expire=3600)
        
        # 检查是否需要重试
        failed_task = get_cache(f"task_status:{failed_task_id}")
        if failed_task and failed_task.get("retry_count", 0) < failed_task.get("max_retries", 3):
            print(f"   任务 {failed_task_id} 可以重试")
            # 这里可以启动重试任务
        else:
            print(f"   任务 {failed_task_id} 已达到最大重试次数")
        
        # 清理失败任务缓存
        delete_cache(f"task_status:{failed_task_id}")
        
        print("\n✅ 所有示例执行完成！")
        
    except Exception as e:
        print(f"❌ 示例执行失败: {e}")
        import traceback
        traceback.print_exc()


def example_redis_utils_features():
    """演示 redis_utils 的各种功能"""
    
    print("\n=== redis_utils 功能演示 ===")
    
    try:
        from EasyRAG.common.redis_utils import get_redis_instance, set_cache, get_cache, delete_cache, exists_cache
        
        redis_utils = get_redis_instance()
        
        # 1. 基本操作
        print("\n1. 基本缓存操作...")
        
        # 设置缓存
        set_cache("test_key", "test_value", expire=60)
        print("   设置缓存: test_key = test_value")
        
        # 检查缓存是否存在
        exists = exists_cache("test_key")
        print(f"   缓存存在: {exists}")
        
        # 获取缓存
        value = get_cache("test_key")
        print(f"   获取缓存: {value}")
        
        # 删除缓存
        deleted = delete_cache("test_key")
        print(f"   删除缓存: {deleted}")
        
        # 2. 复杂数据结构
        print("\n2. 复杂数据结构...")
        
        complex_data = {
            "user": {
                "id": 123,
                "name": "张三",
                "roles": ["admin", "user"]
            },
            "tasks": [
                {"id": "task1", "status": "running"},
                {"id": "task2", "status": "completed"}
            ],
            "metadata": {
                "created_at": "2024-01-01T10:00:00",
                "version": "1.0"
            }
        }
        
        set_cache("complex_data", complex_data, expire=300)
        retrieved_data = get_cache("complex_data")
        print(f"   复杂数据存储和获取: {'✅ 成功' if retrieved_data == complex_data else '❌ 失败'}")
        
        # 3. 批量操作
        print("\n3. 批量操作...")
        
        # 批量设置
        for i in range(5):
            set_cache(f"batch_key_{i}", f"batch_value_{i}", expire=60)
        
        # 批量获取
        batch_values = []
        for i in range(5):
            value = get_cache(f"batch_key_{i}")
            batch_values.append(value)
        
        print(f"   批量操作: 设置了 {5} 个键，获取了 {len([v for v in batch_values if v is not None])} 个值")
        
        # 批量删除
        deleted_count = 0
        for i in range(5):
            if delete_cache(f"batch_key_{i}"):
                deleted_count += 1
        
        print(f"   批量删除: 删除了 {deleted_count} 个键")
        
        # 4. 过期时间测试
        print("\n4. 过期时间测试...")
        
        set_cache("expire_test", "will_expire_soon", expire=2)
        print("   设置2秒过期的缓存")
        
        # 立即获取
        immediate_value = get_cache("expire_test")
        print(f"   立即获取: {immediate_value}")
        
        # 等待过期
        time.sleep(3)
        expired_value = get_cache("expire_test")
        print(f"   过期后获取: {expired_value}")
        
        # 5. 清理测试数据
        print("\n5. 清理测试数据...")
        delete_cache("complex_data")
        print("   测试数据清理完成")
        
        print("\n✅ redis_utils 功能演示完成！")
        
    except Exception as e:
        print(f"❌ redis_utils 功能演示失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("Celery 中使用 redis_utils 的完整示例")
    print("=" * 50)
    
    # 运行示例
    example_celery_redis_usage()
    example_redis_utils_features()
    
    print("\n" + "=" * 50)
    print("示例执行完成！")
    print("\n主要功能:")
    print("1. 任务状态缓存和监控")
    print("2. 批量任务管理")
    print("3. 任务协调和同步")
    print("4. 错误处理和重试机制")
    print("5. 缓存清理和管理")
    print("6. 复杂数据结构支持")
    print("7. 过期时间管理") 