# EasyRAG 视图模型使用指南

## 概述

视图模型（ViewModel）是一种设计模式，用于将视图中的业务逻辑提取到独立的类中，提高代码的可维护性、可测试性和可重用性。在EasyRAG项目中，我们使用视图模型来管理复杂的业务逻辑，使视图代码更加简洁。

## 架构设计

### 视图模型层次结构

```
Views (视图层)
    ↓
ViewModels (视图模型层)
    ↓
Models (模型层)
```

### 主要组件

1. **KnowledgeBaseViewModel**: 知识库相关业务逻辑
2. **FileUploadViewModel**: 文件上传相关业务逻辑
3. **DocumentViewModel**: 文档相关业务逻辑

## 视图模型详解

### 1. KnowledgeBaseViewModel

负责知识库的CRUD操作和权限管理。

#### 主要方法

```python
class KnowledgeBaseViewModel:
    def get_queryset(self, is_swagger_fake_view: bool = False):
        """根据用户权限过滤知识库"""
        
    def create_knowledge_base(self, data: Dict[str, Any]) -> KnowledgeBase:
        """创建知识库"""
        
    def get_knowledge_base(self, knowledge_base_id: str) -> KnowledgeBase:
        """获取知识库"""
        
    def update_knowledge_base(self, knowledge_base_id: str, data: Dict[str, Any]) -> KnowledgeBase:
        """更新知识库"""
        
    def delete_knowledge_base(self, knowledge_base_id: str) -> bool:
        """删除知识库"""
```

#### 使用示例

```python
# 在视图中使用
class KnowledgeBaseViewSet(viewsets.ModelViewSet):
    def get_viewmodel(self):
        return KnowledgeBaseViewModel(self.request.user)
    
    def create(self, request, *args, **kwargs):
        viewmodel = self.get_viewmodel()
        try:
            knowledge_base = viewmodel.create_knowledge_base(request.data)
            serializer = self.get_serializer(knowledge_base)
            return Response(serializer.data, status=201)
        except Exception as e:
            return Response({'error': str(e)}, status=400)
```

### 2. FileUploadViewModel

负责文件上传的验证、处理和批量操作。

#### 主要方法

```python
class FileUploadViewModel:
    def validate_upload_request(self, files: List, knowledge_base_id: str) -> KnowledgeBase:
        """验证上传请求"""
        
    def validate_file_size(self, file, max_size_mb: int = 20) -> None:
        """验证文件大小"""
        
    def process_single_file(self, file, knowledge_base: KnowledgeBase) -> Dict[str, Any]:
        """处理单个文件上传"""
        
    def process_batch_upload(self, files: List, knowledge_base_id: str) -> Dict[str, Any]:
        """处理批量文件上传"""
```

#### 使用示例

```python
# 在视图中使用
class MultiFileUploadView(APIView):
    def get_viewmodel(self):
        return FileUploadViewModel(self.request.user)
    
    def post(self, request, *args, **kwargs):
        files = request.FILES.getlist('files')
        knowledge_base_id = request.data.get('knowledge_base_id')
        
        viewmodel = self.get_viewmodel()
        try:
            result = viewmodel.process_batch_upload(files, knowledge_base_id)
            
            if result.get('failed_files'):
                return Response(result, status=207)  # Multi-Status
            else:
                return Response(result, status=201)  # Created
        except Exception as e:
            return Response({'error': str(e)}, status=400)
```

### 3. DocumentViewModel

负责文档的查询、操作和状态管理。

#### 主要方法

```python
class DocumentViewModel:
    def get_documents_by_knowledge_base(self, knowledge_base_id: str, is_swagger_fake_view: bool = False) -> List[Document]:
        """获取指定知识库下的文档列表"""
        
    def get_document(self, document_id: str) -> Document:
        """获取文档"""
        
    def perform_document_action(self, document_id: str, action: str) -> Optional[Document]:
        """执行文档操作"""
```

#### 使用示例

```python
# 在视图中使用
class DocumentActionView(APIView):
    def get_viewmodel(self):
        return DocumentViewModel(self.request.user)
    
    def put(self, request, *args, **kwargs):
        document_id = kwargs.get('document_id')
        action = request.data.get("action")
        
        viewmodel = self.get_viewmodel()
        try:
            result = viewmodel.perform_document_action(document_id, action)
            
            if action == "delete":
                return Response({'message': '文档删除成功'}, status=200)
            else:
                serializer = DocumentSerializer(result)
                return Response(serializer.data, status=200)
        except Exception as e:
            return Response({'error': str(e)}, status=400)
```

## 优势

### 1. 代码分离

- **视图层**: 只负责HTTP请求处理和响应
- **视图模型层**: 处理业务逻辑和数据处理
- **模型层**: 数据持久化和基础查询

### 2. 可测试性

视图模型可以独立测试，不依赖于HTTP请求和响应：

```python
def test_create_knowledge_base(self):
    viewmodel = KnowledgeBaseViewModel(self.user)
    data = {
        'name': 'Test KB',
        'description': 'Test Description',
        'permission': 'private',
        'parser_config': {},
        'embed_id': 'test_embed'
    }
    
    kb = viewmodel.create_knowledge_base(data)
    self.assertEqual(kb.name, 'Test KB')
    self.assertEqual(kb.created_by, self.user)
```

### 3. 可重用性

视图模型可以在不同的视图中重用：

```python
# 在API视图中使用
class KnowledgeBaseViewSet(viewsets.ModelViewSet):
    def get_viewmodel(self):
        return KnowledgeBaseViewModel(self.request.user)

# 在管理视图中使用
class KnowledgeBaseAdminView(APIView):
    def get_viewmodel(self):
        return KnowledgeBaseViewModel(self.request.user)
```

### 4. 错误处理

统一的错误处理机制：

```python
def create_knowledge_base(self, data: Dict[str, Any]) -> KnowledgeBase:
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
```

## 最佳实践

### 1. 依赖注入

视图模型通过构造函数接收依赖：

```python
def __init__(self, user):
    self.user = user
    self.file_storage = RAGComponentFactory.instance().get_default_file_storage()
```

### 2. 事务管理

在视图模型中使用事务确保数据一致性：

```python
def create_knowledge_base(self, data: Dict[str, Any]) -> KnowledgeBase:
    try:
        with transaction.atomic():
            # 业务逻辑
            pass
    except Exception as e:
        # 错误处理
        pass
```

### 3. 权限检查

在视图模型中统一处理权限检查：

```python
def get_knowledge_base(self, knowledge_base_id: str) -> KnowledgeBase:
    try:
        kb = KnowledgeBase.objects.get(pk=knowledge_base_id)
        if not self.user.can_access_knowledge_base(kb):
            raise DRFValidationError('您没有权限访问该知识库')
        return kb
    except KnowledgeBase.DoesNotExist:
        raise DRFValidationError('知识库不存在')
```

### 4. 日志记录

在视图模型中记录关键操作：

```python
def process_single_file(self, file, knowledge_base: KnowledgeBase) -> Dict[str, Any]:
    try:
        # 处理逻辑
        logger.info(f"Successfully processed file {file.name}")
    except Exception as e:
        logger.error(f"Failed to process file {file.name}: {e}")
        raise
```

## 测试

### 运行测试

```bash
# 运行所有视图模型测试
python manage.py test rag_app.tests_viewmodels

# 运行特定测试类
python manage.py test rag_app.tests_viewmodels.KnowledgeBaseViewModelTest

# 运行特定测试方法
python manage.py test rag_app.tests_viewmodels.KnowledgeBaseViewModelTest.test_create_knowledge_base
```

### 测试覆盖率

```bash
# 安装coverage
pip install coverage

# 运行测试并生成覆盖率报告
coverage run --source='.' manage.py test rag_app.tests_viewmodels
coverage report
coverage html
```

## 扩展指南

### 添加新的视图模型

1. 在 `viewmodels.py` 中创建新的视图模型类
2. 实现必要的业务逻辑方法
3. 在视图中使用新的视图模型
4. 编写相应的测试用例

### 示例：添加用户视图模型

```python
class UserViewModel:
    def __init__(self, user):
        self.user = user
    
    def get_user_profile(self, user_id: str) -> User:
        """获取用户资料"""
        pass
    
    def update_user_profile(self, user_id: str, data: Dict[str, Any]) -> User:
        """更新用户资料"""
        pass
```

## 总结

视图模型模式为EasyRAG项目提供了以下好处：

1. **代码组织**: 清晰的层次结构和职责分离
2. **可维护性**: 业务逻辑集中管理，易于修改和扩展
3. **可测试性**: 独立的业务逻辑便于单元测试
4. **可重用性**: 视图模型可以在多个视图中重用
5. **错误处理**: 统一的错误处理机制
6. **事务管理**: 集中的事务控制确保数据一致性

通过使用视图模型，我们实现了更好的代码架构，提高了开发效率和代码质量。 