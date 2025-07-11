from enum import Enum
from typing import List, Dict, Any, Optional, Tuple
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError as DRFValidationError
import uuid
import logging

from EasyRAG.common import file_utils
from EasyRAG.rag_service.rag_comp_factory import RAGComponentFactory
from EasyRAG.rag_service.rag_manager import RAGDocumentStatus, get_rag_manager
from EasyRAG.common.utils import generate_uuid
from EasyRAG.task_app.models import Task
from .models import File, File2Document, KnowledgeBase, Document
from .serializers import KnowledgeBaseSerializer, DocumentSerializer

logger = logging.getLogger(__name__)

class RAGAction(Enum):
    START_PARSE = 'start_parse'
    STOP_PARSE = 'stop_parse'
    DELETE = 'delete'
    RESUME_PARSE = 'resume_parse'

class KnowledgeBaseViewModel:
    """知识库视图模型"""
    
    def __init__(self, user):
        self.user = user
        self.file_storage = RAGComponentFactory.instance().get_default_file_storage()
    
    def get_queryset(self, is_swagger_fake_view: bool = False):
        """
        根据用户权限过滤知识库
        - 超级用户可以查看所有知识库
        - 普通用户只能查看自己创建的知识库
        """
        if is_swagger_fake_view:
            return KnowledgeBase.objects.none()
            
        if self.user.is_superuser:
            return KnowledgeBase.objects.all()
        return KnowledgeBase.objects.filter(created_by=self.user)
    
    def create_knowledge_base(self, data: Dict[str, Any]) -> KnowledgeBase:
        """创建知识库"""
        try:
            with transaction.atomic():
                serializer = KnowledgeBaseSerializer(data=data)
                if serializer.is_valid():
                    return serializer.save(created_by=self.user)
                else:
                    raise DRFValidationError(serializer.errors)
        except Exception as e:
            logger.error(f"Knowledge base creation failed: {e}")
            raise DRFValidationError(f'创建知识库失败: {str(e)}')
    
    def get_knowledge_base(self, knowledge_base_id: str) -> KnowledgeBase:
        """获取知识库"""
        try:
            kb = KnowledgeBase.objects.get(pk=knowledge_base_id)
            if not self.user.can_access_knowledge_base(kb):
                raise DRFValidationError('您没有权限访问该知识库')
            return kb
        except KnowledgeBase.DoesNotExist:
            raise DRFValidationError('知识库不存在')
    
    def update_knowledge_base(self, knowledge_base_id: str, data: Dict[str, Any]) -> KnowledgeBase:
        """更新知识库"""
        try:
            with transaction.atomic():
                kb = self.get_knowledge_base(knowledge_base_id)
                serializer = KnowledgeBaseSerializer(kb, data=data, partial=True)
                if serializer.is_valid():
                    return serializer.save()
                else:
                    raise DRFValidationError(serializer.errors)
        except Exception as e:
            logger.error(f"Knowledge base update failed: {e}")
            raise DRFValidationError(f'更新知识库失败: {str(e)}')
    
    def delete_knowledge_base(self, knowledge_base_id: str) -> bool:
        """删除知识库"""
        try:
            with transaction.atomic():
                kb = self.get_knowledge_base(knowledge_base_id)
                kb.delete()
                return True
        except Exception as e:
            logger.error(f"Knowledge base deletion failed: {e}")
            raise DRFValidationError(f'删除知识库失败: {str(e)}')


class FileUploadViewModel:
    """文件上传视图模型"""
    
    def __init__(self, user):
        self.user = user
        self.file_storage = RAGComponentFactory.instance().get_default_file_storage()
    
    def validate_upload_request(self, files: List, knowledge_base_id: str) -> KnowledgeBase:
        """验证上传请求"""
        if not knowledge_base_id:
            raise DRFValidationError('knowledge_base_id is required')
        
        if len(files) > 20:
            raise DRFValidationError('最多只能上传20个文件')
        
        try:
            kb = KnowledgeBase.objects.get(pk=knowledge_base_id)
            if not self.user.can_access_knowledge_base(kb):
                raise DRFValidationError('您没有权限访问该知识库')
            return kb
        except KnowledgeBase.DoesNotExist:
            raise DRFValidationError('知识库不存在')
    
    def validate_file_size(self, file, max_size_mb: int = 20) -> None:
        """验证文件大小"""
        if file.size > max_size_mb * 1024 * 1024:
            raise DRFValidationError(f'文件 {file.name} 超过{max_size_mb}MB限制')
    
    def process_single_file(self, file, knowledge_base: KnowledgeBase) -> Dict[str, Any]:
        """处理单个文件上传"""
        try:
            with transaction.atomic():
                # 1. 上传文件到MinIO
                file_info = file_utils.parse_file_info(file)
                logger.info(f"Parse file {file.name} success, file_info: {file_info}")
                minio_url = self.file_storage.upload_file(
                    bucket_name="kb-"+str(knowledge_base.knowledge_base_id), 
                    object_name=file.name, 
                    object_data=file, 
                    object_size=file.size, 
                    metadata={}
                )
                logger.info(f"upload file {file.name} to bucket {knowledge_base.knowledge_base_id} success, minio_url: {minio_url}, file_info: {file_info}")
                
                # 2. 创建File记录
                file_obj = File.objects.create(
                    file_name=file.name,
                    file_location=minio_url,
                    file_size=file.size,
                    file_type=file_info['file_type'],
                    file_source='local',
                    created_by=self.user,
                    file_status='active'
                )
            
                # 3. 创建Document记录
                doc = Document.objects.create(
                    knowledge_base=knowledge_base,
                    document_name=file.name,
                    document_location=minio_url,
                    token_num=0,
                    chunk_num=0,
                    is_active=True,
                    parser_config={},
                    parser_id='',
                    source_type='local',
                    run_id='',
                    status='init',
                    metadata={},
                    progress='init',
                    progress_msg='',
                    progress_begin_at=timezone.now(),
                    progress_duration=0,
                    created_by=self.user
                )
                
                # 4. 创建File2Document关联记录
                file2doc = File2Document.objects.create(
                    file=file_obj,
                    document=doc
                )
                
                # 5. 返回结果
                return {
                    'file_id': str(file_obj.file_id),
                    'file_name': file_obj.file_name,
                    'file_location': file_obj.file_location,
                    'file_size': file_obj.file_size,
                    'file_type': file_obj.file_type,
                    'file_source': file_obj.file_source,
                    'file_status': file_obj.file_status,
                    'created_by': file_obj.created_by.username,
                    'created_at': file_obj.created_at,
                    'document_id': str(doc.document_id),
                    'document_name': doc.document_name,
                    'document_location': doc.document_location
                }
                
        except Exception as e:
            
            logger.error(f"Failed to process file {file.name}: {e}")
            raise DRFValidationError(f'处理文件 {file.name} 失败: {str(e)}')
    
    def process_batch_upload(self, files: List, knowledge_base_id: str) -> Dict[str, Any]:
        """处理批量文件上传"""
        knowledge_base = self.validate_upload_request(files, knowledge_base_id)
        
        results = []
        failed_files = []
        
        for file in files:
            try:
                self.validate_file_size(file)
                result = self.process_single_file(file, knowledge_base)
                results.append(result)
                logger.info(f"process_batch_upload() Successfully created document {file.name}, result: {result}")
            except Exception as e:
                logger.error(f"process_batch_upload() Failed to upload file {file.name}: {e}")
                failed_files.append({
                    'file_name': file.name,
                    'error': str(e)
                })
                # 继续处理下一个文件，不中断整个批量上传过程
                continue
        
        return {
            'documents': results,
            'total_files': len(files),
            'successful_uploads': len(results),
            'failed_uploads': len(failed_files),
            'failed_files': failed_files if failed_files else None
        }


class DocumentViewModel:
    """文档视图模型"""
    
    def __init__(self, user):
        self.user = user
    
    def get_documents_by_knowledge_base(self, knowledge_base_id: str, is_swagger_fake_view: bool = False) -> List[Document]:
        """获取指定知识库下的文档列表"""
        if is_swagger_fake_view:
            return Document.objects.none()
        
        if not knowledge_base_id:
            raise DRFValidationError('knowledge_base_id is required')
        
        
        kb = KnowledgeBase.objects.get(knowledge_base_id=knowledge_base_id)
        if not self.user.can_access_knowledge_base(kb):
            raise DRFValidationError('您没有权限访问该知识库')
        
        return Document.objects.filter(knowledge_base_id=knowledge_base_id).order_by('-created_at')
    
    def get_document(self, document_id: str) -> Document:
        """获取文档"""
        if not document_id:
            raise DRFValidationError('document_id is required')
        
        
        try:
            document = Document.objects.get(document_id=document_id)
            if not self.user.can_access_knowledge_base(document.knowledge_base):
                raise DRFValidationError('您没有权限操作该文档')
            return document
        except Document.DoesNotExist:
            raise DRFValidationError('文档不存在')
    
    def perform_document_action(self, document_id: str, action: str) -> Optional[Document]:
        """执行文档操作"""
        logger.info(f"In perform_document_action, document_id: {document_id}, action: {action}")
        if not action:
            raise DRFValidationError('action is required')
        if not document_id:
            raise DRFValidationError('document_id is required')
       
        if action not in [action.value for action in RAGAction]:
            raise DRFValidationError(f'action: {action} is invalid')
       
        document = self.get_document(document_id)
        if document is None:
            raise DRFValidationError('文档不存在')
        if not self.user.can_access_knowledge_base(document.knowledge_base):
            logger.error(f"User {self.user.id} does not have access to knowledge base {document.knowledge_base}")
            raise DRFValidationError('您没有权限操作该文档')
        
        rag_manager = get_rag_manager()
        try:
            with transaction.atomic():
                if action == RAGAction.START_PARSE.value:
                    rag_manager.create_parse_document_task(document_id)
                    
                elif action == RAGAction.STOP_PARSE.value:
                    rag_manager.stop_parse_document_task(document_id, self.user)
                    
                elif action == RAGAction.DELETE.value:
                    # 删除文档及其关联的File记录
                    if document.status in [RAGDocumentStatus.PROCESSING.value]:
                        raise DRFValidationError(f"Document {document_id} status is {document.status}, cannot delete")
                    # TODO: 删除文档及其关联的File记录
                    
                elif action == RAGAction.RESUME_PARSE.value:
                    document.status = RAGDocumentStatus.PROCESSING.value
                    document.progress = '0'
                    document.progress_msg = '文档已刷新'
                else:
                    raise DRFValidationError('action is invalid')
                
                # 保存文档状态
                document.save()
                return document
                
        except Exception as e:
            logger.error(f"Document action failed: {e}")
            raise DRFValidationError(f'操作失败: {str(e)}') 
   
        
    
    def _delete_document(self, document: Document) -> Document:
        """删除文档"""
        logger.info(f"In _delete_document, document: {document}")
        return document
    
    def _refresh_document(self, document: Document) -> Document:
        """刷新文档"""
        logger.info(f"In _refresh_document, document: {document}")
        return document

    def start_parser_document(self, document_id: str, resume_from: Optional[str] = None) -> Dict[str, Any]:
        """
        启动文档解析
        
        Args:
            document_id: 文档ID
            resume_from: 断点续传的起始步骤
            
        Returns:
            解析启动结果
        """
        logger.info(f"In start_parser_document, document_id: {document_id}, resume_from: {resume_from}")
        
        # 验证文档存在和权限
        document = self.get_document(document_id)
        
        # 使用RAGManager启动解析
        rag_manager = get_rag_manager()
        result = rag_manager.start_document_parse(document_id, self.user, resume_from)
        
        if result['success']:
            return {
                'message': result['message'],
                'document_id': result['document_id'],
                'task_id': result.get('task_id'),
                'status': result['status']
            }
        else:
            raise DRFValidationError(result['message'])
    
    def stop_parser_document(self, document_id: str) -> Dict[str, Any]:
        """
        停止文档解析
        
        Args:
            document_id: 文档ID
            
        Returns:
            停止结果
        """
        logger.info(f"In stop_parser_document, document_id: {document_id}")
        
        # 验证文档存在和权限
        document = self.get_document(document_id)
        
        # 使用RAGManager停止解析
        rag_manager = get_rag_manager()
        result = rag_manager.stop_document_parse(document_id, self.user)
        
        if result['success']:
            return {
                'message': result['message'],
                'document_id': result['document_id'],
                'status': result['status']
            }
        else:
            raise DRFValidationError(result['message'])
    
    def get_parser_status(self, document_id: str) -> Dict[str, Any]:
        """
        获取文档解析状态
        
        Args:
            document_id: 文档ID
            
        Returns:
            解析状态信息
        """
        logger.info(f"In get_parser_status, document_id: {document_id}")
        
        # 验证文档存在和权限
        document = self.get_document(document_id)
        
        # 使用RAGManager获取状态
        rag_manager = get_rag_manager()
        result = rag_manager.get_parse_status(document_id, self.user)
        
        if result['success']:
            return result
        else:
            raise DRFValidationError(result['message'])