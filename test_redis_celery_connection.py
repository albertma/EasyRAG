#!/usr/bin/env python3
"""
测试 RedisUtils 和 Celery Redis 连接一致性

这个脚本测试 RedisUtils 和 Celery 的 Redis 连接配置是否一致，
确保两者都能成功连接到 Redis 服务器。
"""

import os
import sys
from typing import Dict, Any

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'EasyRAG.settings')

def test_redis_utils_connection():
    """测试 RedisUtils 连接"""
    print("=== 测试 RedisUtils 连接 ===")
    try:
        from EasyRAG.common.redis_utils import get_redis_instance
        
        # 获取 Redis 实例
        redis_utils = get_redis_instance()
        
        # 测试连接
        is_healthy = redis_utils.health_check()
        if is_healthy:
            print("✅ RedisUtils 连接成功")
            
            # 测试读写
            test_key = "test_redis_utils_connection"
            test_value = {"message": "RedisUtils 连接测试", "timestamp": "2024-01-01"}
            
            # 写入测试
            write_success = redis_utils.set_cache(test_key, test_value, expire=60)
            if write_success:
                print("✅ RedisUtils 写入测试成功")
                
                # 读取测试
                read_value = redis_utils.get_cache(test_key)
                if read_value and read_value.get("message") == "RedisUtils 连接测试":
                    print("✅ RedisUtils 读取测试成功")
                    
                    # 清理测试数据
                    redis_utils.delete_cache(test_key)
                    print("✅ RedisUtils 清理测试数据成功")
                else:
                    print("❌ RedisUtils 读取测试失败")
            else:
                print("❌ RedisUtils 写入测试失败")
        else:
            print("❌ RedisUtils 连接失败")
            return False
            
    except Exception as e:
        print(f"❌ RedisUtils 连接测试异常: {e}")
        return False
    
    return True

def test_celery_redis_connection():
    """测试 Celery Redis 连接"""
    print("\n=== 测试 Celery Redis 连接 ===")
    try:
        from EasyRAG import settings
        from EasyRAG.celery_app import app
        import redis
        
        # 获取连接信息
        broker_url = settings.CELERY_BROKER_URL
        result_backend = settings.CELERY_RESULT_BACKEND
        
        print(f"Broker URL: {broker_url}")
        print(f"Result Backend: {result_backend}")
        
        # 测试连接
        try:
            # 直接测试 Redis 连接
            # 从 broker URL 解析连接参数
            if broker_url.startswith('redis://'):
                # 解析 redis://username:password@host:port/db 格式
                url_parts = broker_url.replace('redis://', '').split('@')
                if len(url_parts) == 2:
                    auth_part, host_part = url_parts
                    if ':' in auth_part:
                        username, password = auth_part.split(':', 1)
                    else:
                        username, password = '', auth_part
                    
                    host_port_db = host_part.split('/')
                    host_port = host_port_db[0]
                    db = int(host_port_db[1]) if len(host_port_db) > 1 else 0
                    
                    if ':' in host_port:
                        host, port = host_port.split(':')
                        port = int(port)
                    else:
                        host, port = host_port, 6379
                else:
                    # 没有认证信息
                    host_port_db = broker_url.replace('redis://', '').split('/')
                    host_port = host_port_db[0]
                    db = int(host_port_db[1]) if len(host_port_db) > 1 else 0
                    username, password = '', ''
                    
                    if ':' in host_port:
                        host, port = host_port.split(':')
                        port = int(port)
                    else:
                        host, port = host_port, 6379
            else:
                raise ValueError(f"不支持的 Redis URL 格式: {broker_url}")
            
            # 创建 Redis 连接测试
            if username and password:
                redis_client = redis.Redis(
                    host=host, 
                    port=port, 
                    db=db, 
                    username=username, 
                    password=password,
                    decode_responses=True
                )
            elif password:
                redis_client = redis.Redis(
                    host=host, 
                    port=port, 
                    db=db, 
                    password=password,
                    decode_responses=True
                )
            else:
                redis_client = redis.Redis(
                    host=host, 
                    port=port, 
                    db=db,
                    decode_responses=True
                )
            
            # 测试连接
            redis_client.ping()
            print("✅ Celery Redis 连接成功")
            
            # 测试 Celery 应用配置
            if app.conf.broker_url == broker_url:
                print("✅ Celery 应用配置正确")
            else:
                print("⚠️  Celery 应用配置与设置不一致")
                print(f"  应用配置: {app.conf.broker_url}")
                print(f"  设置配置: {broker_url}")
            
            return True
                
        except Exception as e:
            print(f"❌ Celery Redis 连接测试异常: {e}")
            return False
            
    except Exception as e:
        print(f"❌ Celery Redis 配置测试异常: {e}")
        return False

def test_redis_config_consistency():
    """测试 Redis 配置一致性"""
    print("\n=== 测试 Redis 配置一致性 ===")
    try:
        from EasyRAG import settings
        
        # 获取配置
        redis_config = settings.REDIS_CONFIG
        celery_broker_url = settings.CELERY_BROKER_URL
        celery_result_backend = settings.CELERY_RESULT_BACKEND
        
        print("Redis 配置:")
        print(f"  Host: {redis_config['host']}")
        print(f"  Port: {redis_config['port']}")
        print(f"  DB: {redis_config['db']}")
        print(f"  Username: {redis_config.get('username', 'None')}")
        print(f"  Password: {'*' * len(redis_config['password']) if redis_config['password'] else 'None'}")
        
        print("\nCelery 配置:")
        print(f"  Broker URL: {celery_broker_url}")
        print(f"  Result Backend: {celery_result_backend}")
        
        # 检查配置是否一致
        expected_broker_url = f"redis://{redis_config.get('username', '')}:{redis_config['password']}@{redis_config['host']}:{redis_config['port']}/{redis_config['db']}"
        
        if expected_broker_url == celery_broker_url:
            print("✅ Redis 配置一致")
            return True
        else:
            print("❌ Redis 配置不一致")
            print(f"  期望: {expected_broker_url}")
            print(f"  实际: {celery_broker_url}")
            return False
            
    except Exception as e:
        print(f"❌ 配置一致性测试异常: {e}")
        return False

def main():
    """主函数"""
    print("RedisUtils 和 Celery Redis 连接一致性测试")
    print("=" * 50)
    
    # 测试配置一致性
    config_ok = test_redis_config_consistency()
    
    # 测试 RedisUtils 连接
    redis_utils_ok = test_redis_utils_connection()
    
    # 测试 Celery Redis 连接
    celery_ok = test_celery_redis_connection()
    
    # 总结
    print("\n" + "=" * 50)
    print("测试总结:")
    print(f"  配置一致性: {'✅ 通过' if config_ok else '❌ 失败'}")
    print(f"  RedisUtils 连接: {'✅ 通过' if redis_utils_ok else '❌ 失败'}")
    print(f"  Celery Redis 连接: {'✅ 通过' if celery_ok else '❌ 失败'}")
    
    if config_ok and redis_utils_ok and celery_ok:
        print("\n🎉 所有测试通过！RedisUtils 和 Celery 连接配置一致且正常工作。")
        return True
    else:
        print("\n⚠️  存在配置问题，请检查 Redis 配置。")
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1) 