from abc import ABC, abstractmethod
from typing import Optional, BinaryIO, Dict, Any


class FileStorage(ABC):
    """
    文件存储抽象基类
    定义了文件存储的基本接口
    """
    
    @abstractmethod
    def upload_file(self, bucket_name: str, 
                    object_name: str, 
                    object_data: BinaryIO, 
                    object_size: int,
                    metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        上传文件
        Args:
            file_obj: 文件对象
            file_name: 文件名
            metadata: 文件元数据
        Returns:
            str: 文件访问URL
        """
        pass
    
    @abstractmethod
    def download_file(self, file_path: str) -> BinaryIO:
        """
        下载文件
        Args:
            file_path: 文件路径
        Returns:
            BinaryIO: 文件对象
        """
        pass
    
    @abstractmethod
    def delete_file(self, file_path: str) -> bool:
        """
        删除文件
        Args:
            file_path: 文件路径
        Returns:
            bool: 是否删除成功
        """
        pass
    
    @abstractmethod
    def get_file_url(self, file_path: str) -> str:
        """
        获取文件访问URL
        Args:
            file_path: 文件路径
        Returns:
            str: 文件访问URL
        """
        pass
    
    @abstractmethod
    def get_file_metadata(self, file_path: str) -> Dict[str, Any]:
        """
        获取文件元数据
        Args:
            file_path: 文件路径
        Returns:
            Dict[str, Any]: 文件元数据
        """
        pass
    
    @abstractmethod
    def get_file_content(self, file_path: str) -> BinaryIO:
        """
        获取文件内容
        Args:
            file_path: 文件路径
        Returns:
            BinaryIO: 文件对象
        """
        pass