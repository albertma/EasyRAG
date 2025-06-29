from typing import List, Dict, Any, Optional, Tuple
from django.db import transaction
from django.utils import timezone
from django.core.exceptions import ValidationError
from rest_framework.exceptions import ValidationError as DRFValidationError
import uuid
import logging

from EasyRAG.common import file_utils
from EasyRAG.common.rag_comp_factory import RAGComponentFactory
from .models import File, File2Document, KnowledgeBase, Document
from .serializers import KnowledgeBaseSerializer, DocumentSerializer

logger = logging.getLogger(__name__)


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
        
        try:
            uuid.UUID(knowledge_base_id)
        except (ValueError, TypeError):
            raise DRFValidationError('knowledge_base_id format invalid')
        
        kb = KnowledgeBase.objects.get(knowledge_base_id=knowledge_base_id)
        if not self.user.can_access_knowledge_base(kb):
            raise DRFValidationError('您没有权限访问该知识库')
        
        return Document.objects.filter(knowledge_base_id=knowledge_base_id).order_by('-created_at')
    
    def get_document(self, document_id: str) -> Document:
        """获取文档"""
        if not document_id:
            raise DRFValidationError('document_id is required')
        
        try:
            uuid.UUID(document_id)
        except (ValueError, TypeError):
            raise DRFValidationError('document_id format invalid')
        
        try:
            document = Document.objects.get(document_id=document_id)
            if not self.user.can_access_knowledge_base(document.knowledge_base):
                raise DRFValidationError('您没有权限操作该文档')
            return document
        except Document.DoesNotExist:
            raise DRFValidationError('文档不存在')
    
    def perform_document_action(self, document_id: str, action: str) -> Optional[Document]:
        """执行文档操作"""
        document = self.get_document(document_id)
        
        try:
            with transaction.atomic():
                if action == "start_parse":
                    # TODO: 实现文档解析逻辑
                    document.status = 'processing'
                    document.progress = '0'
                    document.progress_msg = '开始解析文档'
                    document.progress_begin_at = timezone.now()
                    
                elif action == "stop_parse":
                    # TODO: 实现停止解析逻辑
                    document.status = 'stopped'
                    document.progress_msg = '解析已停止'
                    
                elif action == "delete":
                    # 删除文档及其关联的File记录
                    try:
                        file2doc = File2Document.objects.get(document=document)
                        file2doc.file.delete()  # 这会同时删除File记录和MinIO中的文件
                        file2doc.delete()
                    except File2Document.DoesNotExist:
                        # 如果没有关联的File记录，直接删除Document
                        pass
                    
                    document.delete()
                    return None  # 删除操作不返回文档对象
                    
                elif action == "refresh":
                    # TODO: 实现刷新逻辑
                    document.status = 'init'
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