from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Callable


class DocumentParser(ABC):
    def __init__(self):
        pass
    
    @abstractmethod
    def parse(self,
              doc_info: Dict[str, Any], 
              file_info: Dict[str, Any], 
              knowledge_base_info: Dict[str, Any],
              config: Dict[str, Any],
              callback: Optional[Callable] = None,
              resume_from: Optional[str] = None) -> Dict[str, Any]:
        """
        解析文档
        
        Args:
            doc_id: 文档ID
            doc_info: 文档信息
            file_info: 文件信息
            config: 配置
            callback: 状态更新回调函数，接收doc_id和update_fields参数
            resume_from: 断点续传的起始步骤
            
        Returns:
            解析结果
        """
        pass
    
    @abstractmethod
    def get_step_status(self, doc_id: str, step: str) -> Dict[str, Any]:
        """
        获取指定步骤的状态
        
        Args:
            doc_id: 文档ID
            step: 步骤名称
            
        Returns:
            步骤状态信息
        """
        pass
    
    