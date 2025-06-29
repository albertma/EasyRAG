# EasyRAG - 知识库管理系统

EasyRAG 是一个基于 Django 和 REST Framework 的知识库管理系统，支持文档上传、解析、向量化和检索功能。

## 功能特性

- 📚 知识库管理：创建、编辑、删除知识库
- 📄 文档管理：支持多种格式文档上传和解析
- 🔍 智能检索：基于向量相似度的文档检索
- 👥 用户管理：多用户权限控制
- 🔐 JWT 认证：安全的 API 认证机制
- 📖 API 文档：完整的 Swagger UI 文档

## 技术栈

- **后端框架**: Django 5.2 + Django REST Framework
- **数据库**: MySQL
- **文件存储**: MinIO
- **向量数据库**: Elasticsearch
- **文档解析**: MinerU
- **API 文档**: drf-yasg (Swagger UI)

## 快速开始

### 1. 环境准备

确保已安装以下服务：
- Python 3.8+
- MySQL 8.0+
- MinIO
- Elasticsearch 8.0+

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置数据库

在 `EasyRAG/settings.py` 中配置数据库连接：

```python
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": "easyrag",
        "USER": "your_username",
        "PASSWORD": "your_password",
        "HOST": "127.0.0.1",
        "PORT": "3306",
    }
}
```

### 4. 运行迁移

```bash
python manage.py migrate
```

### 5. 创建超级用户

```bash
python manage.py createsuperuser
```

### 6. 启动服务

```bash
python manage.py runserver
```

## API 文档

### Swagger UI

访问 Swagger UI 文档：
- **Swagger UI**: http://localhost:8000/swagger/
- **ReDoc**: http://localhost:8000/redoc/
- **JSON Schema**: http://localhost:8000/swagger.json
- **YAML Schema**: http://localhost:8000/swagger.yaml

### 认证

API 使用 JWT 认证，获取 token：

```bash
curl -X POST http://localhost:8000/api/token/ \
  -H "Content-Type: application/json" \
  -d '{"username": "your_username", "password": "your_password"}'
```

使用 token 访问 API：

```bash
curl -X GET http://localhost:8000/api/knowledge-bases/ \
  -H "Authorization: Bearer your_token_here"
```

## 主要 API 端点

### 知识库管理
- `GET /api/knowledge-bases/` - 获取知识库列表
- `POST /api/knowledge-bases/` - 创建知识库
- `GET /api/knowledge-bases/{id}/` - 获取知识库详情
- `PUT /api/knowledge-bases/{id}/` - 更新知识库
- `DELETE /api/knowledge-bases/{id}/` - 删除知识库

### 文档管理
- `POST /api/kb-files-upload/` - 批量上传文件
- `GET /api/documents/by-kb/{kb_id}/` - 获取知识库下的文档列表
- `PUT /api/documents/{doc_id}/` - 文档操作（解析、删除等）

### 用户管理
- `POST /api/user/create/` - 创建用户（仅超级用户）

## 配置说明

### MinIO 配置

```python
MINIO_CONFIG = {
    'endpoint': '127.0.0.1:9000',
    'access_key': 'your_access_key',
    'secret_key': 'your_secret_key',
    'secure': False,
}
```

### Elasticsearch 配置

```python
ELASTICSEARCH_CONFIG = {
    'hosts': ['http://localhost:9200'],
    'username': 'elastic',
    'password': 'your_password',
    'use_ssl': False,
    'vector_size': 1536,
    'similarity': 'cosine',
}
```

## 开发说明

### 项目结构

```
EasyRAG/
├── EasyRAG/                 # 主项目目录
│   ├── common/             # 公共组件
│   ├── file_parser/        # 文档解析模块
│   ├── file_storage/       # 文件存储模块
│   ├── rag_app/           # RAG 应用
│   ├── user_app/          # 用户管理
│   ├── task_app/          # 任务管理
│   ├── vectors/           # 向量存储
│   └── settings.py        # 项目配置
├── manage.py              # Django 管理脚本
└── README.md             # 项目说明
```

### 添加新的 API 端点

1. 在相应的 `views.py` 中添加视图
2. 使用 `@swagger_auto_schema` 装饰器添加文档
3. 在 `urls.py` 中注册 URL

示例：

```python
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

@swagger_auto_schema(
    operation_description="API 描述",
    operation_summary="API 摘要",
    responses={
        200: YourSerializer,
        400: "错误描述"
    }
)
def your_view(request):
    # 视图逻辑
    pass
```

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request！
