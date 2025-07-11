from django.apps import AppConfig
from EasyRAG import settings
import logging

logger = logging.getLogger(__name__)

class RagAppConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "EasyRAG.rag_app"
    
    def ready(self):
        """应用启动时初始化 RAG 组件"""
        try:
            # 延迟导入，避免循环依赖
            from EasyRAG.rag_service.rag_manager import RAGManager
            
            # 从 settings 获取配置
            vector_db_type = getattr(settings, 'VECTOR_DATABASE_TYPE', 'elasticsearch')
            file_storage_type = getattr(settings, 'FILE_STORAGE_TYPE', 'minio')
            file_parser_type = getattr(settings, 'FILE_PARSER_TYPE', 'mineru')
            
            # 初始化 RAG 组件工厂
            logger.info(f"In rag_app.apps.ready init rag manager")
            rag_manager = RAGManager.instance()
            
            rag_manager.factory.setup(
                vector_database_type=vector_db_type,
                file_storage_type=file_storage_type,
                file_parser_type=file_parser_type
            )
            
            logger.info(f"RAG components initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize RAG components: {e}")
            # 不抛出异常，避免阻止Django启动
