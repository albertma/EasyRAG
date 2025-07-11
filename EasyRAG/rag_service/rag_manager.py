from enum import Enum
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError as DRFValidationError
from typing import Any, Dict
import logging
from pydantic import BaseModel

from EasyRAG.common.rag_model import ChunkConfig, KeywordQuestionConfig, LLMModelConfig, UserDefaultLLMConfig
from EasyRAG.common.utils import generate_uuid
from EasyRAG.rag_service.rag_comp_factory import RAGComponentFactory

from EasyRAG.common.rag_model import LLM_CHAT_MODEL_TYPE, LLM_EMBEDDING_MODEL_TYPE, LLM_IMG_TO_TEXT_MODEL_TYPE, LLM_RERANK_MODEL_TYPE, LLM_SPEECH_TO_TEXT_MODEL_TYPE
from EasyRAG.task_app.models import Task, TaskStatus, TaskType
from EasyRAG.user_app.models import User

logger = logging.getLogger(__name__)

# 全局变量
_rag_manager = None


class RAGDocumentStatus(Enum):
    INIT = 'INIT'
    PROCESSING = 'PROCESSING'
    END = 'END'
    STOP = 'STOP'
    
    



class RAGManager:
    _instance = None
     
    @classmethod
    def instance(cls):
        if cls._instance is None:
            cls._instance = RAGManager()
        return cls._instance
    
    def __init__(self):
        # 延迟初始化，避免循环导入
        self._document_parser = None
        self.factory = RAGComponentFactory.instance()
        
    @property
    def document_parser(self):
        """延迟加载文档解析器"""
        if self._document_parser is None:
            # 延迟导入，避免循环依赖
            from EasyRAG.file_parser.mineru_parser import MinerUDocumentParser
            self._document_parser = MinerUDocumentParser()
        return self._document_parser
        
    def get_llm_config_by_user_id(self, user_id: str) -> UserDefaultLLMConfig:
        return self._load_user_llm_config(user_id)
   
    def get_chunk_config_by_document_id(self, document_id: str) -> ChunkConfig:
        # 延迟导入，避免循环导入
        from EasyRAG.rag_app.models import Document
        
        document = Document.objects.get(document_id=document_id)
        if document is None:
            raise ValueError(f"Document not found: {document_id}")
        if document.chunk_config is None:
            raise ValueError(f"Chunk config not found: {document_id}")
        return document.chunk_config
    
    def create_parse_document_task(self, document_id: str, workflow_config: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        创建文档解析任务（使用Celery异步框架）
        
        Args:
            document_id: 文档ID
            workflow_config: 工作流配置
            
        Returns:
            任务创建结果
        """
        logger.info(f"create_parse_document_task(): document_id: {document_id}")
        
        try:
            from EasyRAG.rag_app.models import Document
            document = Document.objects.get(document_id=document_id)
            
            if document.status in [RAGDocumentStatus.PROCESSING.value, 
                                   RAGDocumentStatus.END.value, 
                                   RAGDocumentStatus.STOP.value]:
                logger.error(f"Document {document_id} status is {document.status}, cannot start parse")
                raise ValueError(f"Document {document_id} status is {document.status}, cannot start parse")
            
            # 更新文档状态
            with transaction.atomic():
                document.status = RAGDocumentStatus.PROCESSING.value
                document.progress = '0'
                document.progress_msg = '开始解析文档'
                document.progress_begin_at = timezone.now()
                document.save()
            
            # 使用Celery任务框架
            from EasyRAG.tasks.celery_rag_tasks import parse_document_task
            
            # 准备任务数据
            task_data = {
                'document_id': document_id,
                'parser_config': document.parser_config,
                'document_metadata': document.metadata,
                'document_location': document.document_location,
                'workflow_config': workflow_config or {}
            }
            
            # 启动Celery任务
            result = parse_document_task.delay(document_id, workflow_config)
            
            # 创建任务记录
            task = Task.objects.create(
                task_id=result.id,
                task_name=f"Parse Document {document_id}",
                task_type=TaskType.RAG_PARSING_DOCUMENT.value,
                task_related_id=document_id,
                task_data=task_data,
                status=TaskStatus.PENDING.value,
                message='开始解析文档',
                created_by=str(document.created_by.id) if document.created_by else None
            )
            
            logger.info(f"成功创建解析任务: {result.id}")
            
            return {
                "success": True,
                "task_id": result.id,
                "document_id": document_id,
                "message": "解析任务已启动"
            }
            
        except Document.DoesNotExist:
            error_msg = f"文档不存在: {document_id}"
            logger.error(error_msg)
            raise DRFValidationError(error_msg)
        except Exception as e:
            logger.error(f"Failed to start parse document: {e}")
            raise DRFValidationError(f'开始解析文档失败: {str(e)}')
    
    def start_document_parse(self, document_id: str, user: User, resume_from: str = None) -> Dict[str, Any]:
        """
        启动文档解析（支持断点续传）
        
        Args:
            document_id: 文档ID
            user: 用户对象
            resume_from: 断点续传的起始步骤
            
        Returns:
            启动结果
        """
        try:
            from EasyRAG.rag_app.models import Document
            document = Document.objects.get(document_id=document_id)
            
            # 权限检查
            if not user.can_access_knowledge_base(document.knowledge_base):
                return {
                    'success': False,
                    'message': '您没有权限操作该文档'
                }
            
            # 使用Celery任务框架
            from EasyRAG.tasks.celery_rag_tasks import parse_document_task
            
            # 默认使用简化版工作流
            workflow_config = {
                "workflow_type": "simple",
                "description": "文档解析"
            }
            
            # 启动任务
            result = parse_document_task.delay(document_id, workflow_config, resume_from)
            
            return {
                'success': True,
                'message': '文档解析已启动',
                'document_id': document_id,
                'task_id': result.id,
                'status': 'PROCESSING'
            }
            
        except Document.DoesNotExist:
            return {
                'success': False,
                'message': '文档不存在'
            }
        except Exception as e:
            logger.error(f"启动文档解析失败: {e}")
            return {
                'success': False,
                'message': f'启动解析失败: {str(e)}'
            }
    
    def stop_document_parse(self, document_id: str, user: User) -> Dict[str, Any]:
        """
        停止文档解析
        
        Args:
            document_id: 文档ID
            user: 用户对象
            
        Returns:
            停止结果
        """
        try:
            from EasyRAG.rag_app.models import Document
            document = Document.objects.get(document_id=document_id)
            
            # 权限检查
            if not user.can_access_knowledge_base(document.knowledge_base):
                return {
                    'success': False,
                    'message': '您没有权限操作该文档'
                }
            
            # 查找相关的任务
            task = Task.objects.filter(
                task_related_id=document_id,
                task_type=TaskType.RAG_PARSING_DOCUMENT.value,
                status__in=[TaskStatus.PENDING.value, TaskStatus.RUNNING.value]
            ).first()
            
            if task:
                # 使用Celery任务框架取消任务
                from EasyRAG.tasks.celery_rag_tasks import cancel_parse_task
                cancel_result = cancel_parse_task.delay(task.task_id)
                cancel_status = cancel_result.get()
                
                if cancel_status.get('success'):
                    # 更新文档状态
                    document.status = 'STOPPED'
                    document.progress_msg = '解析已停止'
                    document.save()
                    
                    return {
                        'success': True,
                        'message': '文档解析已停止',
                        'document_id': document_id,
                        'status': 'STOPPED'
                    }
                else:
                    return {
                        'success': False,
                        'message': f'停止解析失败: {cancel_status.get("error")}'
                    }
            else:
                # 没有找到运行中的任务，直接更新文档状态
                document.status = 'STOPPED'
                document.progress_msg = '解析已停止'
                document.save()
                
                return {
                    'success': True,
                    'message': '文档解析已停止',
                    'document_id': document_id,
                    'status': 'STOPPED'
                }
            
        except Document.DoesNotExist:
            return {
                'success': False,
                'message': '文档不存在'
            }
        except Exception as e:
            logger.error(f"停止文档解析失败: {e}")
            return {
                'success': False,
                'message': f'停止解析失败: {str(e)}'
            }
    
    def get_parse_status(self, document_id: str, user: User) -> Dict[str, Any]:
        """
        获取文档解析状态
        
        Args:
            document_id: 文档ID
            user: 用户对象
            
        Returns:
            解析状态信息
        """
        try:
            from EasyRAG.rag_app.models import Document
            document = Document.objects.get(document_id=document_id)
            
            # 权限检查
            if not user.can_access_knowledge_base(document.knowledge_base):
                return {
                    'success': False,
                    'message': '您没有权限查看该文档'
                }
            
            # 查找相关的任务
            task = Task.objects.filter(
                task_related_id=document_id,
                task_type=TaskType.RAG_PARSING_DOCUMENT.value
            ).order_by('-created_at').first()
            
            if task:
                # 使用Celery任务框架获取进度
                from EasyRAG.tasks.celery_rag_tasks import get_parse_progress_task
                progress_result = get_parse_progress_task.delay(task.task_id)
                progress = progress_result.get()
                
                return {
                    'success': True,
                    'document_id': document_id,
                    'task_id': task.task_id,
                    'document_status': document.status,
                    'document_progress': document.progress,
                    'document_message': document.progress_msg,
                    'task_status': progress.get('status'),
                    'task_progress': progress.get('progress'),
                    'task_message': progress.get('message'),
                    'started_at': progress.get('started_at'),
                    'completed_at': progress.get('completed_at'),
                    'error': progress.get('error')
                }
            else:
                # 没有找到任务，返回文档状态
                return {
                    'success': True,
                    'document_id': document_id,
                    'document_status': document.status,
                    'document_progress': document.progress,
                    'document_message': document.progress_msg,
                    'task_status': None,
                    'task_progress': None,
                    'task_message': None
                }
            
        except Document.DoesNotExist:
            return {
                'success': False,
                'message': '文档不存在'
            }
        except Exception as e:
            logger.error(f"获取解析状态失败: {e}")
            return {
                'success': False,
                'message': f'获取状态失败: {str(e)}'
            }
    
    def stop_parse_document_task(self, document_id: str, user: User) -> Dict[str, Any]:
        """
        停止文档解析
        
        Args:
            document_id: 文档ID
            user: 用户对象
            
        Returns:
            停止结果
        """
        try:
            # 延迟导入，避免循环依赖
          
            
            # 验证文档存在和权限
            from EasyRAG.rag_app.models import Document
            document = Document.objects.get(document_id=document_id)
            
            if not user.can_access_knowledge_base(document.knowledge_base):
                return {
                    'success': False,
                    'message': '您没有权限操作该文档'
                }
            
            # 查找并取消相关任务
            # 这里需要根据实际情况查找任务ID，暂时简化处理
            # 实际应用中可能需要维护文档ID到任务ID的映射
            
            # 更新文档状态
            document.status = 'stopped'
            document.progress_msg = '解析已停止'
            document.save()
            
            return {
                'success': True,
                'message': '文档解析已停止',
                'document_id': document_id,
                'status': 'stopped'
            }
            
        except Document.DoesNotExist:
            return {
                'success': False,
                'message': '文档不存在'
            }
        except Exception as e:
            logger.error(f"停止文档解析失败: {e}")
            return {
                'success': False,
                'message': f'停止解析失败: {str(e)}'
            }
            
    def start_parse_document_task(self, task_count: int = 1) -> bool:
        """
        开始文档解析任务
        """
        from EasyRAG.task_app.models import Task
        
        tasks = Task.objects.filter(task_status=TaskStatus.RUNNING.value).order_by('created_at asc').limit(task_count)
        # enqueue task to task_queue
        
            
            
        
        return True
    
    
    
    
    
    def _load_user_llm_config(self, user_id: str) -> UserDefaultLLMConfig:
        # 延迟导入，避免循环导入
        from EasyRAG.llm_app.models import LLMModelUserConfig
        
        llm_model_user_config_list = LLMModelUserConfig.objects.filter(owner=user_id)
        if llm_model_user_config_list is None or len(llm_model_user_config_list) == 0:
            return None 
    
        chat_config = None
        embedding_config = None
        image2text_config = None
        speech2text_config = None
        reranker_config = None
    
        for llm_model_user_config in llm_model_user_config_list:
            
            logger.info(f"_load_user_llm_config(): llm_model_user_config: {llm_model_user_config}")
            base_url = llm_model_user_config.instance_config.get("url", None)
            api_key = llm_model_user_config.instance_config.get("api_key", None)
            provider = llm_model_user_config.instance_config.get("provider", None)
            
            llm_config = LLMModelConfig(model_name=llm_model_user_config.config_value, 
                                                   model_type=llm_model_user_config.config_type, 
                                                   model_provider=provider,
                                                   model_provider_url=base_url,
                                                   api_key=api_key)
            if llm_model_user_config.config_type == LLM_CHAT_MODEL_TYPE:
                chat_config = llm_config
            elif llm_model_user_config.config_type == LLM_EMBEDDING_MODEL_TYPE:
                embedding_config = llm_config
            elif llm_model_user_config.config_type == LLM_IMG_TO_TEXT_MODEL_TYPE:
                image2text_config = llm_config
            elif llm_model_user_config.config_type == LLM_SPEECH_TO_TEXT_MODEL_TYPE:
                speech2text_config = llm_config
            elif llm_model_user_config.config_type == LLM_RERANK_MODEL_TYPE:
                reranker_config = llm_config
            else:
                logger.error(f"_load_user_default_config(): Unsupported config type: {llm_model_user_config.config_type}")
                raise ValueError(f"Unsupported config type: {llm_model_user_config.config_type}")
        
        if chat_config is None or embedding_config is None:
            logger.error(f"_load_user_default_config(): chat_config or embedding_config is None")
            raise ValueError("chat_config or embedding_config is None")
        return UserDefaultLLMConfig(chat_config=chat_config, 
                                embedding_config=embedding_config, 
                                image2text_config=image2text_config, 
                                speech2text_config=speech2text_config, 
                                reranker_config=reranker_config)

def get_rag_manager() -> RAGManager:
    """获取全局RAGManager实例"""
    global _rag_manager
    if _rag_manager is None:
        _rag_manager = RAGManager.instance()
    return _rag_manager


    
    
    

