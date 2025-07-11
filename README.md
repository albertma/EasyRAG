# EasyRAG - 企业级RAG应用开发框架

EasyRAG是一个基于Django的企业级RAG（Retrieval-Augmented Generation）应用开发框架，提供了完整的文档处理、向量存储、LLM集成和用户管理功能。

## 🚀 主要特性

- **📚 知识库管理**: 支持多用户知识库创建、管理和权限控制
- **📄 文档处理**: 支持PDF、Word、Excel等多种文档格式的解析和向量化
- **🔍 智能检索**: 基于Elasticsearch的高效向量检索
- **🤖 LLM集成**: 支持多种LLM模型和配置管理
- **👥 用户管理**: 完整的用户认证、权限管理和团队协作
- **🔄 工作流引擎**: 可配置的文档处理工作流
- **📊 实时监控**: 文档处理进度跟踪和状态管理
- **🔧 组件化架构**: 模块化设计，易于扩展和维护

## 📁 项目结构

```
EasyRAG/
├── EasyRAG/                    # Django项目主目录
│   ├── common/                 # 公共组件
│   │   ├── file_utils.py      # 文件工具类
│   │   ├── permissions.py     # 权限控制
│   │   ├── rag_comp_factory.py # RAG组件工厂
│   │   ├── rag_config_model.py # RAG配置模型
│   │   ├── rag_tokenizer.py   # 中文分词器
│   │   ├── rag_utils.py       # RAG工具函数
│   │   └── redis_utils.py     # Redis缓存工具
│   ├── file_parser/           # 文档解析模块
│   │   ├── document_parser.py # 文档解析基类
│   │   ├── excel_parser.py    # Excel解析器
│   │   ├── mineru_parser.py   # MinerU解析器
│   │   └── workflow.py        # 工作流引擎
│   ├── file_storage/          # 文件存储模块
│   │   ├── file_storage.py    # 存储基类
│   │   └── minio_storage.py   # MinIO存储实现
│   ├── llm_app/              # LLM管理应用
│   │   ├── models.py         # LLM相关模型
│   │   ├── serializers.py    # 序列化器
│   │   ├── views.py          # 视图
│   │   ├── viewmodel.py      # 视图模型
│   │   └── urls.py           # URL配置
│   ├── rag_app/              # RAG核心应用
│   │   ├── models.py         # 知识库、文档模型
│   │   ├── serializers.py    # 序列化器
│   │   ├── views.py          # 视图
│   │   ├── viewmodels.py     # 视图模型
│   │   └── urls.py           # URL配置
│   ├── user_app/             # 用户管理应用
│   │   ├── models.py         # 用户模型
│   │   ├── serializers.py    # 序列化器
│   │   ├── views.py          # 视图
│   │   └── urls.py           # URL配置
│   ├── task_app/             # 任务管理应用
│   │   └── models.py         # 任务模型
│   ├── vectors/              # 向量存储模块
│   │   └── vectors.py        # Elasticsearch向量实现
│   └── settings.py           # Django设置
├── data/                     # 测试数据
├── env/                      # 虚拟环境
├── requirements.txt          # 依赖包
└── manage.py                # Django管理脚本
```

## 🛠️ 技术栈

- **后端框架**: Django 4.2+
- **数据库**: MySQL/PostgreSQL
- **向量数据库**: Elasticsearch
- **文件存储**: MinIO
- **缓存**: Redis
- **文档解析**: MinerU
- **分词**: 自定义中文分词器
- **API文档**: drf-yasg (Swagger)
- **认证**: JWT

## 📦 安装部署

### 1. 环境要求

- Python 3.8+
- MySQL 8.0+ 或 PostgreSQL 12+
- Elasticsearch 7.x+
- Redis 6.0+
- MinIO

### 2. 安装依赖

```bash
# 克隆项目
git clone <repository-url>
cd EasyRAG

# 创建虚拟环境
python -m venv env
source env/bin/activate  # Linux/Mac
# 或
env\Scripts\activate     # Windows

# 安装依赖
pip install -r requirements.txt
```

### 3. 配置环境变量

创建 `.env` 文件并配置以下环境变量：

```bash
# 数据库配置
DATABASE_URL=mysql://user:password@localhost:3306/easyrag

# Elasticsearch配置
ELASTICSEARCH_HOSTS=localhost:9200
ELASTICSEARCH_VECTOR_SIZE=1536

# Redis配置
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=

# MinIO配置
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=your_access_key
MINIO_SECRET_KEY=your_secret_key

# Django配置
SECRET_KEY=your_secret_key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
```

### 4. 数据库迁移

```bash
# 执行数据库迁移
python manage.py makemigrations
python manage.py migrate

# 创建超级用户
python manage.py createsuperuser
```

### 5. 启动服务

```bash
# 启动Django开发服务器
python manage.py runserver 8000

# 访问API文档
http://localhost:8000/swagger/
```

## 🔧 核心功能

### 1. 知识库管理

```python
# 创建知识库
POST /api/rag/knowledge-bases/
{
    "name": "技术文档库",
    "description": "存储技术相关文档",
    "permission": "private",
    "parser_config": {...},
    "embed_id": "bge-m3"
}

# 获取知识库列表
GET /api/rag/knowledge-bases/
```

### 2. 文档上传和处理

```python
# 批量上传文档
POST /api/rag/upload/
{
    "files": [file1, file2, ...],
    "knowledge_base_id": "kb-uuid"
}

# 文档操作
PUT /api/rag/documents/{document_id}/
{
    "action": "start_parse"  # start_parse, stop_parse, delete, refresh
}
```

### 3. LLM模型管理

```python
# 创建LLM模板
POST /api/llm/llm-templates/
{
    "template_name": "OpenAI GPT",
    "template_code": "openai",
    "llm_template_config": [...]
}

# 创建LLM实例
POST /api/llm/llm-instances/
{
    "llm_template_id": "template-uuid",
    "llm_config": {
        "url": "https://api.openai.com",
        "api_key": "your-api-key"
    }
}

# 配置用户模型
POST /api/llm/llm-model-user-configs/
{
    "configure_list": [
        {
            "llm_instance_id": "instance-uuid",
            "llm_model_id": "model-uuid",
            "config_type": "CHAT",
            "config_value": "gpt-3.5-turbo"
        }
    ]
}
```

### 4. 用户管理

```python
# 用户注册（仅超级用户）
POST /api/users/register/
{
    "username": "newuser",
    "email": "user@example.com",
    "password": "password123"
}

# 用户登录
POST /api/users/login/
{
    "username": "username",
    "password": "password"
}
```

## 🏗️ 架构设计

### 视图模型模式

EasyRAG采用视图模型（ViewModel）模式，将业务逻辑从视图中分离：

```python
class KnowledgeBaseViewModel:
    def __init__(self, user):
        self.user = user
    
    def create_knowledge_base(self, data: Dict[str, Any]) -> KnowledgeBase:
        """创建知识库的业务逻辑"""
        pass
    
    def get_queryset(self, is_swagger_fake_view: bool = False):
        """根据用户权限过滤查询集"""
        pass
```

### 组件工厂模式

使用工厂模式管理RAG组件：

```python
class RAGComponentFactory:
    def get_default_vector_database(self, index_name: str) -> ElasticsearchVectors:
        """获取向量数据库实例"""
        pass
    
    def get_default_file_storage(self) -> FileStorage:
        """获取文件存储实例"""
        pass
```

### 工作流引擎

支持可配置的文档处理工作流：

```python
class MinerUWorkflow(ParserWorkflow):
    def execute(self, doc_id: str, doc_info: Dict[str, Any], ...):
        """执行文档处理工作流"""
        # 1. 初始化
        # 2. 获取文件内容
        # 3. 解析文件
        # 4. 提取块信息
        # 5. 处理向量化
        # 6. 更新状态
        pass
```

## 🧪 测试

### 运行测试

```bash
# 运行所有测试
python manage.py test

# 运行特定应用测试
python manage.py test rag_app.tests_viewmodels

# 运行特定测试类
python manage.py test rag_app.tests_viewmodels.KnowledgeBaseViewModelTest
```

### 测试覆盖率

```bash
# 安装coverage
pip install coverage

# 运行测试并生成覆盖率报告
coverage run --source='.' manage.py test
coverage report
coverage html
```

## 📚 API文档

启动服务后访问以下地址查看API文档：

- **Swagger UI**: http://localhost:8000/swagger/
- **ReDoc**: http://localhost:8000/redoc/

## 🔒 权限控制

EasyRAG实现了细粒度的权限控制：

- **知识库权限**: 私有、团队、公开
- **文档权限**: 基于知识库权限继承
- **文件权限**: 基于用户和团队权限
- **LLM权限**: 基于实例所有者权限

## 🚀 性能优化

- **缓存策略**: Redis缓存热点数据
- **批量操作**: 支持批量文件上传和处理
- **异步处理**: 文档解析支持异步处理
- **连接池**: 数据库和Redis连接池管理

## 🤝 贡献指南

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 📞 联系方式

- 项目主页: [GitHub Repository]
- 问题反馈: [Issues]
- 邮箱: [your-email@example.com]

## 🙏 致谢

感谢所有为EasyRAG项目做出贡献的开发者和用户！
