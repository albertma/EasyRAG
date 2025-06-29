"""
URL configuration for EasyRAG project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path, include, re_path
from rest_framework.documentation import include_docs_urls
from rest_framework.schemas import get_schema_view
from rest_framework_simplejwt.views import TokenRefreshView
from EasyRAG.user_app.views import CustomTokenObtainPairView
from drf_yasg.views import get_schema_view as get_swagger_schema_view
from drf_yasg import openapi
from rest_framework import permissions

# Swagger UI schema view
schema_view = get_swagger_schema_view(
    openapi.Info(
        title="EasyRAG API",
        default_version='v1',
        description="""
        # EasyRAG 知识库管理系统 API 文档
        
        ## 认证方式
        
        ### JWT Token 认证（推荐）
        1. 获取 Token：POST `/api/token/`
        2. 在请求头中添加：`Authorization: Bearer <access_token>`
        
        ### 基本认证
        使用用户名和密码进行基本认证
        
        ## 主要功能
        
        - **知识库管理**：创建、查询、更新、删除知识库
        - **文档管理**：上传、解析、管理文档
        - **LLM管理**：创建、查询、更新、删除LLM模板和实例
        - **用户管理**：用户创建和管理
        - **文件存储**：支持多种文件格式的存储和解析
        
        ## 快速开始
        
        1. 创建用户（需要超级用户权限）
        2. 获取 JWT Token
        3. 创建知识库
        4. 上传文档
        5. 查询和管理文档
        """,
        terms_of_service="https://www.com/terms/",
        contact=openapi.Contact(email="contact@com"),
        license=openapi.License(name="MIT License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
    patterns=[
        path("api/", include("EasyRAG.rag_app.urls")),
        path("api/user/", include("EasyRAG.user_app.urls")),
        path("api/llm/", include("EasyRAG.llm_app.urls")),
        path('api/token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
        path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    ],
)

# 原有的schema view（保持向后兼容）
#old_schema_view = get_schema_view(title='EasyRAG API')

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("EasyRAG.rag_app.urls")),
    path("api/user/", include("EasyRAG.user_app.urls")),
    path("api/llm/", include("EasyRAG.llm_app.urls")),
    #path("api/task/", include("EasyRAG.task_app.urls")),
    path("api-auth/", include("rest_framework.urls")),
    
    # Swagger UI URLs
    re_path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    re_path(r'^swagger/$', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    re_path(r'^redoc/$', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    
    # 原有的文档URLs（保持向后兼容）
    # path("docs/", include_docs_urls(title="EasyRAG API")),
    # path("schema/", old_schema_view),
    
    # JWT 认证
    path('api/token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
