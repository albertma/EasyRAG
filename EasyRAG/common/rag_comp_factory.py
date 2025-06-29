from EasyRAG import settings
from EasyRAG.file_storage.file_storage import FileStorage
from EasyRAG.file_storage.minio_storage import MinioStorage
from EasyRAG.vectors.vectors import ElasticsearchVectors
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class RAGComponentFactory:
    
    _instance = None
    def __init__(self):
        self.vector_database_type = None
        self.file_storage_type = None
        self.file_parser_type = None
        self.vector_database = None
        self.file_storage = None
        self.file_parser = None
        
    
    def setup(self, vector_database_type: str, file_storage_type: str, file_parser_type: str):
        self.vector_database_type = vector_database_type.lower()
        self.file_storage_type = file_storage_type.lower()
        self.file_parser_type = file_parser_type.lower()
        
    @staticmethod
    def instance():
        if RAGComponentFactory._instance is None:
            RAGComponentFactory._instance = RAGComponentFactory()
        return RAGComponentFactory._instance
    
    def get_default_vector_database(self, index_name: str) -> ElasticsearchVectors:
        if self.vector_database is None:
            if self.vector_database_type == "elasticsearch":
                es_hosts = settings.ELASTICSEARCH_CONFIG.get("hosts")
                vector_size = settings.ELASTICSEARCH_CONFIG.get("vector_size")
                similarity = settings.ELASTICSEARCH_CONFIG.get("similarity")
                self.vector_database = ElasticsearchVectors(es_hosts=es_hosts, 
                                                            index_name=index_name, 
                                                            vector_size=vector_size, 
                                                            similarity=similarity)
            else:
                raise ValueError(f"Unsupported vector storage type: {self.vector_database_type}")
        return self.vector_database

    def get_default_file_storage(self) -> FileStorage:
        """获取默认文件存储"""
        if self.file_storage is None:
            logger.info(f"Get_default_file_storage()-file_storage_type: {self.file_storage_type}")    
            if self.file_storage_type == "minio":
                self.file_storage = MinioStorage(endpoint=settings.MINIO_CONFIG.get("endpoint"), 
                                                access_key=settings.MINIO_CONFIG.get("access_key"), 
                                                secret_key=settings.MINIO_CONFIG.get("secret_key"))
        return self.file_storage
    

   
   