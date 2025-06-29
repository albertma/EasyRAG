import redis
import json
import pickle
import logging
from typing import Any, Optional, Union, Dict, List
from datetime import timedelta
import hashlib
import os

logger = logging.getLogger(__name__)


class RedisUtils:
    """Redis 工具类，兼容 Redis Cluster 和 Redis 单例模式"""
    
    def __init__(self, host: str = 'localhost', port: int = 6379, db: int = 0, 
                 password: Optional[str] = None, cluster_mode: bool = False,
                 cluster_nodes: Optional[List[str]] = None, **kwargs):
        """初始化 Redis 连接"""
        try:
            if cluster_mode:
                self._init_cluster_mode(cluster_nodes, password, **kwargs)
            else:
                self._init_single_mode(host, port, db, password, **kwargs)
            
            self.redis_client.ping()
            mode = "集群" if cluster_mode else "单例"
            logger.info(f"Redis {mode} 连接成功")
            
        except Exception as e:
            logger.error(f"Redis 连接失败: {e}")
            raise
    
    def _init_cluster_mode(self, cluster_nodes: List[str], password: Optional[str], **kwargs):
        """初始化集群模式"""
        if not cluster_nodes:
            raise ValueError("集群模式需要提供 cluster_nodes 参数")
        
        startup_nodes = []
        for node in cluster_nodes:
            if ":" in node:
                host, port = node.split(":", 1)
                startup_nodes.append({"host": host, "port": int(port)})
            else:
                startup_nodes.append({"host": node, "port": 6379})
        
        self.redis_client = redis.RedisCluster(
            startup_nodes=startup_nodes,
            password=password,
            decode_responses=True,
            **kwargs
        )
        self.cluster_mode = True
    
    def _init_single_mode(self, host: str, port: int, db: int, password: Optional[str], **kwargs):
        """初始化单例模式"""
        self.redis_client = redis.Redis(
            host=host,
            port=port,
            db=db,
            password=password,
            decode_responses=True,
            **kwargs
        )
        self.cluster_mode = False
    
    def set_cache(self, key: str, value: Any, expire: Optional[Union[int, timedelta]] = None) -> bool:
        """设置缓存"""
        try:
            serialized_value = self._serialize_value(value)
            
            if isinstance(expire, timedelta):
                expire_seconds = int(expire.total_seconds())
            else:
                expire_seconds = expire
            
            if expire_seconds:
                result = self.redis_client.setex(key, expire_seconds, serialized_value)
            else:
                result = self.redis_client.set(key, serialized_value)
            
            return bool(result)
        except Exception as e:
            logger.error(f"设置缓存失败 {key}: {e}")
            return False
    
    def get_cache(self, key: str, default: Any = None) -> Any:
        """获取缓存"""
        try:
            value = self.redis_client.get(key)
            if value is None:
                return default
            
            return self._deserialize_value(value)
        except Exception as e:
            logger.error(f"获取缓存失败 {key}: {e}")
            return default
    
    def delete_cache(self, key: str) -> bool:
        """删除缓存"""
        try:
            result = self.redis_client.delete(key)
            return bool(result)
        except Exception as e:
            logger.error(f"删除缓存失败 {key}: {e}")
            return False
    
    def exists_cache(self, key: str) -> bool:
        """检查缓存是否存在"""
        try:
            return bool(self.redis_client.exists(key))
        except Exception as e:
            logger.error(f"检查缓存存在性失败 {key}: {e}")
            return False
    
    def clear_cache(self, pattern: str = "*") -> int:
        """批量删除缓存"""
        try:
            if self.cluster_mode:
                return self._clear_cache_cluster(pattern)
            else:
                keys = self.redis_client.keys(pattern)
                if keys:
                    return self.redis_client.delete(*keys)
                return 0
        except Exception as e:
            logger.error(f"批量删除缓存失败: {e}")
            return 0
    
    def _clear_cache_cluster(self, pattern: str) -> int:
        """集群模式下的批量删除缓存"""
        total_deleted = 0
        
        try:
            cluster_nodes = self.redis_client.cluster_nodes()
            
            for node_id, node_info in cluster_nodes.items():
                if isinstance(node_info, dict) and node_info.get('flags', '').find('master') != -1:
                    host = node_info.get('host', 'localhost')
                    port = node_info.get('port', 6379)
                else:
                    node_parts = node_info.split(' ')
                    if len(node_parts) >= 2:
                        host_port = node_parts[1].split(':')
                        if len(host_port) == 2:
                            host, port = host_port[0], int(host_port[1])
                        else:
                            continue
                    else:
                        continue
                
                node_client = redis.Redis(
                    host=host,
                    port=port,
                    password=self.redis_client.connection_pool.connection_kwargs.get('password'),
                    decode_responses=True
                )
                
                try:
                    keys = node_client.keys(pattern)
                    if keys:
                        result = node_client.delete(*keys)
                        total_deleted += result
                except Exception as e:
                    logger.warning(f"删除节点 {host}:{port} 上的缓存失败: {e}")
                finally:
                    node_client.close()
            
            return total_deleted
        except Exception as e:
            logger.error(f"集群批量删除缓存失败: {e}")
            return total_deleted
    
    def _serialize_value(self, value: Any) -> str:
        """序列化值"""
        try:
            return json.dumps(value, ensure_ascii=False, default=str)
        except (TypeError, ValueError):
            try:
                return pickle.dumps(value).hex()
            except Exception:
                return str(value)
    
    def _deserialize_value(self, value: str) -> Any:
        """反序列化值"""
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            try:
                if len(value) > 0 and all(c in '0123456789abcdefABCDEF' for c in value):
                    return pickle.loads(bytes.fromhex(value))
                else:
                    return value
            except Exception:
                return value
    
    def health_check(self) -> bool:
        """健康检查"""
        try:
            self.redis_client.ping()
            return True
        except Exception as e:
            logger.error(f"Redis 健康检查失败: {e}")
            return False


# 全局 Redis 实例
_redis_instance = None


def get_redis_instance(host: str = None, port: int = None, db: int = None, 
                      password: str = None, cluster_mode: bool = None,
                      cluster_nodes: List[str] = None, **kwargs) -> RedisUtils:
    """获取全局 Redis 实例"""
    global _redis_instance
    
    if cluster_mode is None:
        cluster_mode = os.getenv('REDIS_CLUSTER_MODE', 'false').lower() == 'true'
    
    if cluster_mode:
        if cluster_nodes is None:
            cluster_nodes_str = os.getenv('REDIS_CLUSTER_NODES', '')
            cluster_nodes = [node.strip() for node in cluster_nodes_str.split(',') if node.strip()]
        
        if not cluster_nodes:
            raise ValueError("集群模式需要提供 cluster_nodes 参数或设置 REDIS_CLUSTER_NODES 环境变量")
    else:
        if host is None:
            host = os.getenv('REDIS_HOST', 'localhost')
        if port is None:
            port = int(os.getenv('REDIS_PORT', '6379'))
        if db is None:
            db = int(os.getenv('REDIS_DB', '0'))
    
    if password is None:
        password = os.getenv('REDIS_PASSWORD')
    
    if _redis_instance is None:
        if cluster_mode:
            _redis_instance = RedisUtils(
                cluster_mode=True,
                cluster_nodes=cluster_nodes,
                password=password,
                **kwargs
            )
        else:
            _redis_instance = RedisUtils(
                host=host,
                port=port,
                db=db,
                password=password,
                **kwargs
            )
    
    return _redis_instance


# 便捷函数
def set_cache(key: str, value: Any, expire: Optional[Union[int, timedelta]] = None) -> bool:
    """设置缓存"""
    redis_utils = get_redis_instance()
    return redis_utils.set_cache(key, value, expire)


def get_cache(key: str, default: Any = None) -> Any:
    """获取缓存"""
    redis_utils = get_redis_instance()
    return redis_utils.get_cache(key, default)


def delete_cache(key: str) -> bool:
    """删除缓存"""
    redis_utils = get_redis_instance()
    return redis_utils.delete_cache(key)


def exists_cache(key: str) -> bool:
    """检查缓存是否存在"""
    redis_utils = get_redis_instance()
    return redis_utils.exists_cache(key)


def clear_cache(pattern: str = "*") -> int:
    """批量删除缓存"""
    redis_utils = get_redis_instance()
    return redis_utils.clear_cache(pattern) 