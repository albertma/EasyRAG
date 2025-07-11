from typing import Dict, Any, List
import logging

from .base_workflow import BaseWorkflow
from .document_parsing_steps import (
    InitializeStep
    # OCRStep, GetFileContentStep, ParseFileStep, 
    # ExtractBlocksStep, ProcessChunksStep, UpdateFinalStatusStep
)

logger = logging.getLogger(__name__)


class DocumentParsingWorkflow(BaseWorkflow):
    """文档解析工作流"""
    
    def __init__(self, workflow_config: Dict[str, Any] = None):
        super().__init__(workflow_config)
        self.workflow_name = "DocumentParsingWorkflow"
    
    def get_workflow_steps(self) -> List:
        """获取工作流步骤列表"""
        steps = []
        
        # 从配置中读取步骤配置
        steps_config = self.workflow_config.get("steps", {})
        
        # 初始化步骤
        if steps_config.get("initialize", {}).get("enabled", True):
            init_config = steps_config.get("initialize", {})
            steps.append(InitializeStep("initialize", init_config))
        
        # 获取文件内容步骤
        if steps_config.get("get_file_content", {}).get("enabled", True):
            get_file_config = steps_config.get("get_file_content", {})
            steps.append(GetFileContentStep("get_file_content", get_file_config))
        
        # 解析文件步骤
        if steps_config.get("parse_file", {}).get("enabled", True):
            parse_config = steps_config.get("parse_file", {})
            steps.append(ParseFileStep("parse_file", parse_config))
        
        # 提取块信息步骤
        if steps_config.get("extract_blocks", {}).get("enabled", True):
            extract_config = steps_config.get("extract_blocks", {})
            steps.append(ExtractBlocksStep("extract_blocks", extract_config))
        
        # 处理文本块步骤
        if steps_config.get("process_chunks", {}).get("enabled", True):
            process_config = steps_config.get("process_chunks", {})
            steps.append(ProcessChunksStep("process_chunks", process_config))
        
        # 更新最终状态步骤
        if steps_config.get("update_final_status", {}).get("enabled", True):
            update_config = steps_config.get("update_final_status", {})
            steps.append(UpdateFinalStatusStep("update_final_status", update_config))
        
        return steps
    
    def get_workflow_config_template(self) -> Dict[str, Any]:
        """获取工作流配置模板"""
        return {
            "workflow_name": "DocumentParsingWorkflow",
            "description": "文档解析工作流",
            "version": "1.0",
            "steps": {
                "initialize": {
                    "enabled": True,
                    "description": "初始化解析环境",
                    "timeout": 60,
                    "retry_count": 3
                },
                "get_file_content": {
                    "enabled": True,
                    "description": "获取文件内容",
                    "timeout": 300,
                    "retry_count": 3,
                    "cache_enabled": True,
                    "cache_expire": 3600
                },
                "parse_file": {
                    "enabled": True,
                    "description": "解析文件内容",
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
                    "description": "提取块信息",
                    "timeout": 600,
                    "retry_count": 3,
                    "cache_enabled": True,
                    "cache_expire": 7200
                },
                "process_chunks": {
                    "enabled": True,
                    "description": "处理文本块",
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
                    "description": "更新最终状态",
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
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """验证工作流配置"""
        try:
            # 检查必需的配置项
            if "workflow_name" not in config:
                logger.error("Missing workflow_name in config")
                return False
            
            if "steps" not in config:
                logger.error("Missing steps in config")
                return False
            
            # 检查步骤配置
            required_steps = ["initialize", "get_file_content", "parse_file", 
                            "extract_blocks", "process_chunks", "update_final_status"]
            
            for step_name in required_steps:
                if step_name not in config["steps"]:
                    logger.warning(f"Step {step_name} not found in config")
            
            return True
            
        except Exception as e:
            logger.error(f"Config validation failed: {e}")
            return False
    
    def create_custom_workflow(self, step_names: List[str]) -> 'DocumentParsingWorkflow':
        """创建自定义工作流"""
        custom_config = self.workflow_config.copy()
        custom_config["steps"] = {}
        
        # 只启用指定的步骤
        for step_name in step_names:
            if step_name in self.workflow_config.get("steps", {}):
                custom_config["steps"][step_name] = self.workflow_config["steps"][step_name]
            else:
                # 使用默认配置
                custom_config["steps"][step_name] = {"enabled": True}
        
        return DocumentParsingWorkflow(custom_config)


class SimpleDocumentParsingWorkflow(DocumentParsingWorkflow):
    """简化版文档解析工作流"""
    
    def __init__(self):
        # 只包含核心步骤的简化配置
        simple_config = {
            "workflow_name": "SimpleDocumentParsingWorkflow",
            "description": "简化版文档解析工作流",
            "steps": {
                "initialize": {"enabled": True},
                "get_file_content": {"enabled": True},
                "parse_file": {"enabled": True},
                "process_chunks": {"enabled": True},
                "update_final_status": {"enabled": True}
            }
        }
        super().__init__(simple_config)


class AdvancedDocumentParsingWorkflow(DocumentParsingWorkflow):
    """高级文档解析工作流"""
    
    def __init__(self):
        # 包含所有步骤的高级配置
        advanced_config = {
            "workflow_name": "AdvancedDocumentParsingWorkflow",
            "description": "高级文档解析工作流",
            "steps": {
                "initialize": {
                    "enabled": True,
                    "timeout": 120,
                    "retry_count": 5
                },
                "get_file_content": {
                    "enabled": True,
                    "timeout": 600,
                    "retry_count": 5,
                    "cache_enabled": True,
                    "cache_expire": 7200
                },
                "parse_file": {
                    "enabled": True,
                    "timeout": 3600,
                    "retry_count": 3,
                    "cache_enabled": True,
                    "cache_expire": 14400,
                    "parser_config": {
                        "ocr_enabled": True,
                        "image_extraction": True,
                        "table_extraction": True,
                        "equation_extraction": True,
                        "layout_analysis": True
                    }
                },
                "extract_blocks": {
                    "enabled": True,
                    "timeout": 1200,
                    "retry_count": 5,
                    "cache_enabled": True,
                    "cache_expire": 14400
                },
                "process_chunks": {
                    "enabled": True,
                    "timeout": 7200,
                    "retry_count": 3,
                    "vector_config": {
                        "dimension": 1024,
                        "similarity": "cosine",
                        "batch_size": 50,
                        "enable_reranking": True
                    }
                },
                "update_final_status": {
                    "enabled": True,
                    "timeout": 120,
                    "retry_count": 5,
                    "cleanup_enabled": True,
                    "backup_enabled": True
                }
            },
            "global_config": {
                "max_concurrent_steps": 1,
                "enable_caching": True,
                "enable_logging": True,
                "enable_metrics": True,
                "enable_monitoring": True
            }
        }
        super().__init__(advanced_config)


class CustomDocumentParsingWorkflow(DocumentParsingWorkflow):
    """自定义文档解析工作流"""
    
    def __init__(self, custom_steps: List[str], custom_config: Dict[str, Any] = None):
        """
        创建自定义工作流
        
        Args:
            custom_steps: 要执行的步骤列表
            custom_config: 自定义配置
        """
        config = custom_config or {}
        config["workflow_name"] = "CustomDocumentParsingWorkflow"
        config["description"] = f"自定义文档解析工作流: {', '.join(custom_steps)}"
        config["steps"] = {}
        
        # 为每个自定义步骤创建配置
        for step_name in custom_steps:
            config["steps"][step_name] = {"enabled": True}
        
        super().__init__(config)