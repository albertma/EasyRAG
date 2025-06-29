from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from unittest.mock import patch, MagicMock

from .models import KnowledgeBase, Document
from .viewmodels import KnowledgeBaseViewModel, FileUploadViewModel, DocumentViewModel

User = get_user_model()


class KnowledgeBaseViewModelTest(TestCase):
    """知识库视图模型测试"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.superuser = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpass123'
        )
        self.viewmodel = KnowledgeBaseViewModel(self.user)
        self.superviewmodel = KnowledgeBaseViewModel(self.superuser)
    
    def test_get_queryset_normal_user(self):
        """测试普通用户获取知识库列表"""
        # 创建知识库
        kb1 = KnowledgeBase.objects.create(
            name='Test KB 1',
            description='Test Description 1',
            created_by=self.user,
            permission='private',
            parser_config={},
            embed_id='test_embed'
        )
        kb2 = KnowledgeBase.objects.create(
            name='Test KB 2',
            description='Test Description 2',
            created_by=self.superuser,
            permission='private',
            parser_config={},
            embed_id='test_embed'
        )
        
        # 普通用户只能看到自己创建的知识库
        queryset = self.viewmodel.get_queryset()
        self.assertEqual(queryset.count(), 1)
        self.assertEqual(queryset.first(), kb1)
    
    def test_get_queryset_superuser(self):
        """测试超级用户获取知识库列表"""
        # 创建知识库
        kb1 = KnowledgeBase.objects.create(
            name='Test KB 1',
            description='Test Description 1',
            created_by=self.user,
            permission='private',
            parser_config={},
            embed_id='test_embed'
        )
        kb2 = KnowledgeBase.objects.create(
            name='Test KB 2',
            description='Test Description 2',
            created_by=self.superuser,
            permission='private',
            parser_config={},
            embed_id='test_embed'
        )
        
        # 超级用户可以看到所有知识库
        queryset = self.superviewmodel.get_queryset()
        self.assertEqual(queryset.count(), 2)
    
    def test_get_queryset_swagger_fake_view(self):
        """测试Swagger假视图模式"""
        queryset = self.viewmodel.get_queryset(is_swagger_fake_view=True)
        self.assertEqual(queryset.count(), 0)
    
    def test_create_knowledge_base(self):
        """测试创建知识库"""
        data = {
            'name': 'Test KB',
            'description': 'Test Description',
            'permission': 'private',
            'parser_config': {},
            'embed_id': 'test_embed'
        }
        
        kb = self.viewmodel.create_knowledge_base(data)
        self.assertEqual(kb.name, 'Test KB')
        self.assertEqual(kb.created_by, self.user)
    
    def test_get_knowledge_base(self):
        """测试获取知识库"""
        kb = KnowledgeBase.objects.create(
            name='Test KB',
            description='Test Description',
            created_by=self.user,
            permission='private',
            parser_config={},
            embed_id='test_embed'
        )
        
        result = self.viewmodel.get_knowledge_base(str(kb.knowledge_base_id))
        self.assertEqual(result, kb)
    
    def test_get_knowledge_base_no_permission(self):
        """测试获取无权限的知识库"""
        kb = KnowledgeBase.objects.create(
            name='Test KB',
            description='Test Description',
            created_by=self.superuser,
            permission='private',
            parser_config={},
            embed_id='test_embed'
        )
        
        with self.assertRaises(Exception):
            self.viewmodel.get_knowledge_base(str(kb.knowledge_base_id))


class FileUploadViewModelTest(TestCase):
    """文件上传视图模型测试"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.knowledge_base = KnowledgeBase.objects.create(
            name='Test KB',
            description='Test Description',
            created_by=self.user,
            permission='private',
            parser_config={},
            embed_id='test_embed'
        )
        self.viewmodel = FileUploadViewModel(self.user)
    
    @patch('rag_app.viewmodels.RAGComponentFactory')
    def test_validate_upload_request(self, mock_factory):
        """测试验证上传请求"""
        # 模拟文件列表
        files = [MagicMock() for _ in range(5)]
        
        # 测试正常情况
        result = self.viewmodel.validate_upload_request(files, str(self.knowledge_base.knowledge_base_id))
        self.assertEqual(result, self.knowledge_base)
    
    def test_validate_upload_request_too_many_files(self):
        """测试文件数量超限"""
        files = [MagicMock() for _ in range(25)]
        
        with self.assertRaises(Exception):
            self.viewmodel.validate_upload_request(files, str(self.knowledge_base.knowledge_base_id))
    
    def test_validate_upload_request_no_kb_id(self):
        """测试缺少知识库ID"""
        files = [MagicMock()]
        
        with self.assertRaises(Exception):
            self.viewmodel.validate_upload_request(files, '')
    
    def test_validate_file_size(self):
        """测试文件大小验证"""
        # 创建一个小文件
        small_file = MagicMock()
        small_file.size = 1024 * 1024  # 1MB
        small_file.name = 'small.txt'
        
        # 应该通过验证
        self.viewmodel.validate_file_size(small_file)
        
        # 创建一个大文件
        large_file = MagicMock()
        large_file.size = 25 * 1024 * 1024  # 25MB
        large_file.name = 'large.txt'
        
        # 应该抛出异常
        with self.assertRaises(Exception):
            self.viewmodel.validate_file_size(large_file)


class DocumentViewModelTest(TestCase):
    """文档视图模型测试"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.knowledge_base = KnowledgeBase.objects.create(
            name='Test KB',
            description='Test Description',
            created_by=self.user,
            permission='private',
            parser_config={},
            embed_id='test_embed'
        )
        self.document = Document.objects.create(
            knowledge_base=self.knowledge_base,
            document_name='test_doc.pdf',
            document_location='test/location',
            created_by=self.user,
            parser_config={},
            parser_id='test_parser',
            source_type='local'
        )
        self.viewmodel = DocumentViewModel(self.user)
    
    def test_get_documents_by_knowledge_base(self):
        """测试获取知识库下的文档列表"""
        documents = self.viewmodel.get_documents_by_knowledge_base(str(self.knowledge_base.knowledge_base_id))
        self.assertEqual(documents.count(), 1)
        self.assertEqual(documents.first(), self.document)
    
    def test_get_documents_by_knowledge_base_swagger_fake(self):
        """测试Swagger假视图模式"""
        documents = self.viewmodel.get_documents_by_knowledge_base(
            str(self.knowledge_base.knowledge_base_id), 
            is_swagger_fake_view=True
        )
        self.assertEqual(documents.count(), 0)
    
    def test_get_document(self):
        """测试获取文档"""
        document = self.viewmodel.get_document(str(self.document.document_id))
        self.assertEqual(document, self.document)
    
    def test_get_document_invalid_id(self):
        """测试获取无效ID的文档"""
        with self.assertRaises(Exception):
            self.viewmodel.get_document('invalid-uuid')
    
    def test_perform_document_action_start_parse(self):
        """测试开始解析文档"""
        result = self.viewmodel.perform_document_action(str(self.document.document_id), 'start_parse')
        self.assertEqual(result.status, 'processing')
        self.assertEqual(result.progress, '0')
        self.assertEqual(result.progress_msg, '开始解析文档')
    
    def test_perform_document_action_stop_parse(self):
        """测试停止解析文档"""
        result = self.viewmodel.perform_document_action(str(self.document.document_id), 'stop_parse')
        self.assertEqual(result.status, 'stopped')
        self.assertEqual(result.progress_msg, '解析已停止')
    
    def test_perform_document_action_refresh(self):
        """测试刷新文档"""
        result = self.viewmodel.perform_document_action(str(self.document.document_id), 'refresh')
        self.assertEqual(result.status, 'init')
        self.assertEqual(result.progress, '0')
        self.assertEqual(result.progress_msg, '文档已刷新')
    
    def test_perform_document_action_invalid_action(self):
        """测试无效操作"""
        with self.assertRaises(Exception):
            self.viewmodel.perform_document_action(str(self.document.document_id), 'invalid_action')


class ViewModelIntegrationTest(APITestCase):
    """视图模型集成测试"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
    
    def test_knowledge_base_viewmodel_integration(self):
        """测试知识库视图模型集成"""
        viewmodel = KnowledgeBaseViewModel(self.user)
        
        # 创建知识库
        data = {
            'name': 'Integration Test KB',
            'description': 'Integration Test Description',
            'permission': 'private',
            'parser_config': {},
            'embed_id': 'test_embed'
        }
        
        kb = viewmodel.create_knowledge_base(data)
        self.assertEqual(kb.name, 'Integration Test KB')
        
        # 获取知识库
        retrieved_kb = viewmodel.get_knowledge_base(str(kb.knowledge_base_id))
        self.assertEqual(retrieved_kb, kb)
        
        # 更新知识库
        update_data = {'description': 'Updated Description'}
        updated_kb = viewmodel.update_knowledge_base(str(kb.knowledge_base_id), update_data)
        self.assertEqual(updated_kb.description, 'Updated Description')
        
        # 删除知识库
        result = viewmodel.delete_knowledge_base(str(kb.knowledge_base_id))
        self.assertTrue(result)
        
        # 验证知识库已被删除
        with self.assertRaises(Exception):
            viewmodel.get_knowledge_base(str(kb.knowledge_base_id)) 