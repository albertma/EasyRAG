from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    """
    自定义用户模型
    扩展了Django默认的用户模型
    """
    team = models.ManyToManyField('self', symmetrical=False, related_name='team_members', blank=True)
    
    class Meta:
        db_table = 'users'
    
    def __str__(self):
        return self.username
    
    def has_file_storage_permission(self) -> bool:
        """
        检查用户是否有文件存储权限
        Returns:
            bool: 是否有权限
        """
        # 超级用户和活跃用户都有文件存储权限
        return self.is_active and (self.is_superuser or self.is_staff)
    
    def has_document_permission(self) -> bool:
        """
        检查用户是否有文档操作权限
        Returns:
            bool: 是否有权限
        """
        # 超级用户和活跃用户都有文档操作权限
        return self.is_active and (self.is_superuser or self.is_staff)
    
    def can_access_knowledge_base(self, knowledge_base) -> bool:
        """
        检查用户是否可以访问特定知识库
        Args:
            knowledge_base: 知识库对象
        Returns:
            bool: 是否可以访问
        """
        # 超级用户可以访问所有知识库
        if self.is_superuser:
            return True
            
        # 知识库创建者可以访问
        if knowledge_base.created_by == self:
            return True
            
        # 团队知识库的团队成员可以访问
        if knowledge_base.permission == 'team':
            return self in knowledge_base.created_by.team.all()
            
        return False
    
    