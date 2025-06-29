# Redis 工具类使用指南

## 概述

`RedisUtils` 是一个兼容 Redis 单例模式和集群模式的缓存工具类，提供了简单易用的缓存操作接口。

## 特性

- ✅ **双模式支持**: 同时支持 Redis 单例模式和集群模式
- ✅ **自动序列化**: 支持 JSON 和 Pickle 格式的自动序列化/反序列化
- ✅ **环境变量配置**: 支持通过环境变量进行配置
- ✅ **错误处理**: 完善的异常处理机制
- ✅ **健康检查**: 提供连接健康检查功能
- ✅ **批量操作**: 支持批量删除缓存
- ✅ **过期时间**: 支持设置缓存过期时间
- ✅ **便捷函数**: 提供全局便捷函数

## 安装依赖

```bash
pip install redis
```

## 基本使用

### 1. 单例模式

```python
from common.redis_utils import RedisUtils

# 创建 Redis 实例
redis_utils = RedisUtils(
    host='localhost',
    port=6379,
    db=0,
    password=None  # 如果有密码，在这里设置
)

# 设置缓存
success = redis_utils.set_cache("user:123", {"name": "张三", "age": 25})

# 获取缓存
user_data = redis_utils.get_cache("user:123")

# 删除缓存
success = redis_utils.delete_cache("user:123")

# 检查缓存是否存在
exists = redis_utils.exists_cache("user:123")
```

### 2. 集群模式

```python
from common.redis_utils import RedisUtils

# 集群节点配置
cluster_nodes = [
    "localhost:7000",
    "localhost:7001", 
    "localhost:7002",
    "localhost:7003",
    "localhost:7004",
    "localhost:7005"
]

# 创建集群模式实例
redis_utils = RedisUtils(
    cluster_mode=True,
    cluster_nodes=cluster_nodes,
    password=None  # 如果有密码，在这里设置
)

# 使用方式与单例模式相同
redis_utils.set_cache("cluster:test", "集群测试数据")
data = redis_utils.get_cache("cluster:test")
```

### 3. 全局实例

```python
from common.redis_utils import get_redis_instance, set_cache, get_cache

# 获取全局实例
redis_utils = get_redis_instance()

# 使用便捷函数
set_cache("global:test", "全局测试数据")
data = get_cache("global:test")
```

## 环境变量配置

可以通过环境变量来配置 Redis 连接参数：

### 单例模式环境变量

```bash
export REDIS_HOST=localhost
export REDIS_PORT=6379
export REDIS_DB=0
export REDIS_PASSWORD=your_password
export REDIS_CLUSTER_MODE=false
```

### 集群模式环境变量

```bash
export REDIS_CLUSTER_MODE=true
export REDIS_CLUSTER_NODES=localhost:7000,localhost:7001,localhost:7002
export REDIS_PASSWORD=your_password
```

### 其他配置选项

```bash
export REDIS_MAX_CONNECTIONS=10
export REDIS_CONNECT_TIMEOUT=5
export REDIS_SOCKET_TIMEOUT=5
```

## 高级功能

### 1. 设置过期时间

```python
from datetime import timedelta

# 使用秒数
redis_utils.set_cache("temp:data", "临时数据", expire=60)

# 使用 timedelta
redis_utils.set_cache("temp:data", "临时数据", expire=timedelta(minutes=1))
```

### 2. 批量操作

```python
# 批量删除缓存
deleted_count = redis_utils.clear_cache("user:*")
print(f"删除了 {deleted_count} 个缓存")
```

### 3. 复杂数据结构

```python
# 支持各种数据类型
complex_data = {
    "user": {
        "id": 123,
        "name": "李四",
        "roles": ["admin", "user"],
        "settings": {
            "theme": "dark",
            "language": "zh-CN"
        }
    },
    "timestamp": time.time(),
    "tags": ["important", "urgent"]
}

redis_utils.set_cache("complex:data", complex_data)
retrieved_data = redis_utils.get_cache("complex:data")
```

### 4. 健康检查

```python
# 检查 Redis 连接状态
is_healthy = redis_utils.health_check()
if is_healthy:
    print("Redis 连接正常")
else:
    print("Redis 连接异常")
```

### 5. 缓存键生成

```python
# 生成规范的缓存键
cache_key = redis_utils.generate_cache_key(
    "user", 
    "profile", 
    user_id=123, 
    version="v1"
)
# 结果: user:profile:user_id:123:version:v1
```

## 在 Django 项目中使用

### 1. 在 settings.py 中配置

```python
# settings.py

# Redis 配置
REDIS_CONFIG = {
    "host": os.getenv('REDIS_HOST', 'localhost'),
    "port": int(os.getenv('REDIS_PORT', '6379')),
    "db": int(os.getenv('REDIS_DB', '0')),
    "password": os.getenv('REDIS_PASSWORD'),
    "cluster_mode": os.getenv('REDIS_CLUSTER_MODE', 'false').lower() == 'true',
    "cluster_nodes": os.getenv('REDIS_CLUSTER_NODES', '').split(',') if os.getenv('REDIS_CLUSTER_NODES') else None,
}
```

### 2. 在视图中使用

```python
# views.py
from common.redis_utils import get_redis_instance

def my_view(request):
    redis_utils = get_redis_instance()
  
    # 缓存用户数据
    user_id = request.user.id
    cache_key = f"user:{user_id}:profile"
  
    # 尝试从缓存获取
    user_profile = redis_utils.get_cache(cache_key)
  
    if user_profile is None:
        # 缓存未命中，从数据库获取
        user_profile = UserProfile.objects.get(user_id=user_id)
        # 设置缓存，过期时间1小时
        redis_utils.set_cache(cache_key, user_profile, expire=3600)
  
    return JsonResponse(user_profile)
```

### 3. 在模型中使用

```python
# models.py
from common.redis_utils import get_redis_instance

class User(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
  
    def get_cache_key(self):
        return f"user:{self.id}:data"
  
    def get_cached_data(self):
        redis_utils = get_redis_instance()
        return redis_utils.get_cache(self.get_cache_key())
  
    def set_cached_data(self, data):
        redis_utils = get_redis_instance()
        redis_utils.set_cache(self.get_cache_key(), data, expire=3600)
  
    def clear_cache(self):
        redis_utils = get_redis_instance()
        redis_utils.delete_cache(self.get_cache_key())
```

## 测试

### 运行简单测试

```bash
cd EasyRAG/common
python test_redis_simple.py
```

### 运行完整示例

```bash
cd EasyRAG/common
python redis_usage_example.py
```

## 错误处理

所有 Redis 操作都包含异常处理：

```python
try:
    redis_utils = RedisUtils(host='localhost', port=6379)
    success = redis_utils.set_cache("test", "value")
    if success:
        print("缓存设置成功")
    else:
        print("缓存设置失败")
except Exception as e:
    print(f"Redis 操作异常: {e}")
```

## 性能优化建议

1. **连接池**: 使用连接池管理连接
2. **批量操作**: 尽量使用批量操作减少网络开销
3. **合理过期时间**: 根据数据特性设置合适的过期时间
4. **键命名规范**: 使用统一的键命名规范
5. **监控**: 定期检查 Redis 性能和连接状态

## 常见问题

### Q: 如何切换单例模式和集群模式？

A: 通过 `cluster_mode` 参数控制：

- `cluster_mode=False` (默认): 单例模式
- `cluster_mode=True`: 集群模式

### Q: 集群模式下批量删除如何工作？

A: 集群模式下会遍历所有主节点，在每个节点上执行删除操作。

### Q: 支持哪些数据类型？

A: 支持所有可序列化的 Python 数据类型，包括：

- 基本类型: str, int, float, bool
- 容器类型: list, tuple, dict, set
- 自定义对象: 通过 Pickle 序列化

### Q: 如何处理连接失败？

A: 所有操作都有异常处理，连接失败时会抛出异常，建议在应用层进行重试。

## 更新日志

- **v1.0.0**: 初始版本，支持单例模式和集群模式
- 支持环境变量配置
- 支持自动序列化/反序列化
- 支持健康检查
- 支持批量操作
