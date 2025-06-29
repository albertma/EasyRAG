from django.apps import AppConfig
from EasyRAG import settings


class RagAppConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "EasyRAG.rag_app"
    
    def ready(self):
        """应用启动时初始化 RAG 组件"""
        from EasyRAG.common.rag_comp_factory import RAGComponentFactory
        
        # 从 settings 获取配置
        vector_db_type = getattr(settings, 'VECTOR_DATABASE_TYPE', 'elasticsearch')
        file_storage_type = getattr(settings, 'FILE_STORAGE_TYPE', 'minio')
        file_parser_type = getattr(settings, 'FILE_PARSER_TYPE', 'mineru')
        
        # 初始化 RAG 组件工厂
        factory = RAGComponentFactory.instance()
        factory.setup(
            vector_database_type=vector_db_type,
            file_storage_type=file_storage_type,
            file_parser_type=file_parser_type
        )
