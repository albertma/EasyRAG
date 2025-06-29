from rest_framework import permissions
import logging

logger = logging.getLogger(__name__)

class KnowledgeBasePermission(permissions.BasePermission):
    """
    知识库权限控制
    只允许知识库所有者或超级用户编辑
    """
    def has_knowledge_base_permission(self, request, view, obj):
        return request.user.is_superuser or obj.created_by == request.user or \
            (obj.permission == 'team' and request.user in obj.created_by.team.all())
    
    def has_document_permission(self, request, parent_obj, obj):
        if request.user.is_superuser or obj.created_by == request.user:
            return True
        if parent_obj.permission == 'team':
            return request.user in parent_obj.created_by.team.all()
        return False


class FileStoragePermission(permissions.BasePermission):
    """
    文件存储权限控制
    控制文件的上传、下载、删除等操作权限
    """
    def has_permission(self, request, view):
        """
        检查用户是否有权限访问文件存储
        """
        # 检查用户是否已认证
        if not request.user.is_authenticated:
            return False
            
        # 检查用户是否有文件存储权限
        if not hasattr(request.user, 'has_file_storage_permission'):
            return False
            
        return request.user.has_file_storage_permission()
    
    def has_object_permission(self, request, view, obj):
        """
        检查用户是否有权限操作特定文件
        """
        # 超级用户可以操作所有文件
        if request.user.is_superuser:
            return True
            
        # 检查文件所有者权限
        if hasattr(obj, 'created_by') and obj.created_by == request.user:
            return True
            
        # 检查团队权限
        if hasattr(obj, 'knowledge_base'):
            kb = obj.knowledge_base
            if kb.permission == 'team' and request.user in kb.created_by.team.all():
                return True
                
        return False


class DocumentPermission(permissions.BasePermission):
    """
    文档权限控制
    控制文档的访问和操作权限
    """
    def has_permission(self, request, view):
        """
        检查用户是否有权限访问文档
        """
        if not request.user.is_authenticated:
            return False
            
        # 检查用户是否有文档操作权限
        if not hasattr(request.user, 'has_document_permission'):
            return False
            
        return request.user.has_document_permission()
    
    def has_object_permission(self, request, view, obj):
        """
        检查用户是否有权限操作特定文档
        """
        # 超级用户可以操作所有文档
        if request.user.is_superuser:
            return True
            
        # 检查文档所有者权限
        if obj.created_by == request.user:
            return True
            
        # 检查知识库权限
        kb = obj.knowledge_base
        if kb.permission == 'team' and request.user in kb.created_by.team.all():
            return True
            
        return False