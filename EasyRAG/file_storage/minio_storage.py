from EasyRAG import settings
from EasyRAG.file_storage.file_storage import FileStorage
from minio import Minio
from typing import Optional, BinaryIO, Dict, Any
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
class MinioStorage(FileStorage):
    """
    MinIO文件存储实现
    使用MinIO作为文件存储后端
    """
    
    def __init__(self, endpoint: str = None, access_key: str = None, secret_key: str = None, secure: bool = False):
        """
        初始化MinIO客户端
        Args:
            endpoint: MinIO服务器地址
            access_key: 访问密钥
            secret_key: 密钥
            secure: 是否使用HTTPS
        """
        self.endpoint = endpoint or settings.MINIO_CONFIG.get("endpoint")
        self.access_key = access_key or settings.MINIO_CONFIG.get("access_key")
        self.secret_key = secret_key or settings.MINIO_CONFIG.get("secret_key")
        self.secure = secure
        logger.info(f"Initializing MinIO client with endpoint: {self.endpoint}, access_key: {self.access_key}, secret_key: {self.secret_key}, secure: {self.secure}")
        self.client = Minio(
            self.endpoint,
            access_key=self.access_key,
            secret_key=self.secret_key,
            secure=self.secure
        )
    
    def _ensure_bucket_exists(self, bucket_name: str) -> None:
        """
        确保存储桶存在
        Args:
            bucket_name: 存储桶名称
        """
        if not self.client.bucket_exists(bucket_name):
            self.client.make_bucket(bucket_name)
    
    def upload_file(self, 
                    bucket_name: str,  
                    object_name: str, 
                    object_data: BinaryIO, 
                    object_size: int,
                    metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        上传文件到MinIO
        Args:
            bucket_name: 存储桶名称
            object_name: 对象名称
            object_data: 文件数据
            object_size: 文件大小
            metadata: 文件元数据
        Returns:
            str: 文件访问URL
        """
        try:
            # 确保存储桶存在
            logger.info(f"Going to ensure bucket {bucket_name} exists")
            self._ensure_bucket_exists(bucket_name)
            
            # 上传文件
            result = self.client.put_object(
                bucket_name,
                object_name,
                object_data,
                length=object_size,
                content_type=(metadata or {}).get('content_type', 'application/octet-stream'),
                metadata=metadata or {}
            )
            
            # 检查上传是否成功
            if result is None:
                raise Exception("文件上传失败：返回结果为空")
            
            logger.info(f"Uploaded file {object_name} to bucket {bucket_name} success")
            
            # 构建文件访问URL
            file_url = self.get_file_url(f"{bucket_name}/{object_name}")
            logger.info(f"File URL: {file_url}")
            
            return file_url
            
        except Exception as e:
            logger.error(f"Upload file {object_name} to bucket {bucket_name} failed: {e}")
            raise Exception(f"文件上传失败: {str(e)}")
    
    def download_file(self, file_path: str) -> BinaryIO:
        """
        从MinIO下载文件
        Args:
            file_path: 文件路径 (格式: bucket_name/object_name)
        Returns:
            BinaryIO: 文件对象
        """
        try:
            bucket_name, object_name = file_path.split('/', 1)
            response = self.client.get_object(bucket_name, object_name)
            return response
        except Exception as e:
            raise Exception(f"文件下载失败: {str(e)}")
    
    def delete_file(self, file_path: str) -> bool:
        """
        从MinIO删除文件
        Args:
            file_path: 文件路径 (格式: bucket_name/object_name)
        Returns:
            bool: 是否删除成功
        """
        try:
            bucket_name, object_name = file_path.split('/', 1)
            self.client.remove_object(bucket_name, object_name)
            return True
        except Exception as e:
            raise Exception(f"文件删除失败: {str(e)}")
    
    def get_file_url(self, file_path: str) -> str:
        """
        获取MinIO文件访问URL
        Args:
            file_path: 文件路径 (格式: bucket_name/object_name)
        Returns:
            str: 文件访问URL
        """
        try:
            # 处理文件路径，支持带前缀的 bucket 名称
            if '/' in file_path:
                bucket_name, object_name = file_path.split('/', 1)
            else:
                raise ValueError("文件路径格式错误，应为 bucket_name/object_name")
            
            # 构建访问URL
            protocol = "https" if self.secure else "http"
            url = f"{protocol}://{self.endpoint}/{bucket_name}/{object_name}"
            
            logger.info(f"Generated file URL: {url}")
            return url
            
        except Exception as e:
            logger.error(f"Get file URL failed for {file_path}: {e}")
            raise Exception(f"获取文件URL失败: {str(e)}")
    
    def get_file_metadata(self, file_path: str) -> Dict[str, Any]:
        """
        获取MinIO文件元数据
        Args:
            file_path: 文件路径 (格式: bucket_name/object_name)
        Returns:
            Dict[str, Any]: 文件元数据
        """
        try:
            bucket_name, object_name = file_path.split('/', 1)
            stat = self.client.stat_object(bucket_name, object_name)
            return {
                'size': stat.size,
                'content_type': stat.content_type,
                'last_modified': stat.last_modified,
                'metadata': stat.metadata
            }
        except Exception as e:
            raise Exception(f"获取文件元数据失败: {str(e)}")

    def get_file_content(self, bucket_name:str, file_path: str) -> str:
        """
        获取文件内容
        Args:
            file_path: 文件路径
        Returns:
            str: 文件内容
        """
        response = self.client.get_object(bucket_name, file_path)
        file_content = response.read()
        response.close()
        return file_content
    
    def fput_object(self, bucket_name: str, object_name: str, file_path: str = None, content_type: str = None, data: BinaryIO = None, length: int = None):
        """
        上传文件到MinIO
        Args:
            bucket_name: 存储桶名称
            object_name: 对象名称
            file_path: 文件路径（当使用文件路径时）
            content_type: 内容类型
            data: 数据流（当使用数据流时）
            length: 数据长度（当使用数据流时）
        """
        if data is not None and length is not None:
            # 使用数据流上传
            return self.client.put_object(
                bucket_name,
                object_name,
                data,
                length=length,
                content_type=content_type or 'application/octet-stream'
            )
        elif file_path is not None:
            # 使用文件路径上传
            return self.client.fput_object(bucket_name, object_name, file_path, content_type=content_type)
        else:
            raise ValueError("必须提供 file_path 或 data+length 参数")
    
    def set_bucket_policy(self, bucket_name: str, policy: str):
        """
        设置存储桶策略
        Args:
            bucket_name: 存储桶名称
            policy: 策略JSON字符串
        """
        return self.client.set_bucket_policy(bucket_name, policy)