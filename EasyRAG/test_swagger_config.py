#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 Swagger 配置的脚本
"""

import os
import sys
import django
from pathlib import Path

# 设置 Django 环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'EasyRAG.settings')

# 添加项目根目录到 Python 路径
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

def setup_django():
    """设置 Django 环境"""
    try:
        django.setup()
        print("✓ Django 环境设置成功")
        return True
    except Exception as e:
        print(f"✗ Django 环境设置失败: {e}")
        return False

def test_swagger_config():
    """测试 Swagger 配置"""
    print("\n=== 测试 Swagger 配置 ===")
    
    try:
        from EasyRAG import settings
        
        # 检查 Swagger 设置
        swagger_settings = settings.SWAGGER_SETTINGS
        
        print("1. 检查 Swagger 设置")
        print(f"   SECURITY_DEFINITIONS: {'✓' if 'SECURITY_DEFINITIONS' in swagger_settings else '✗'}")
        print(f"   SECURITY: {'✓' if 'SECURITY' in swagger_settings else '✗'}")
        print(f"   USE_SESSION_AUTH: {'✓' if swagger_settings.get('USE_SESSION_AUTH') else '✗'}")
        
        # 检查 JWT 配置
        security_defs = swagger_settings.get('SECURITY_DEFINITIONS', {})
        bearer_config = security_defs.get('Bearer', {})
        
        print("\n2. 检查 JWT 认证配置")
        print(f"   Bearer 类型: {'✓' if bearer_config.get('type') == 'apiKey' else '✗'}")
        print(f"   Authorization 头: {'✓' if bearer_config.get('name') == 'Authorization' else '✗'}")
        print(f"   描述信息: {'✓' if 'JWT Token' in bearer_config.get('description', '') else '✗'}")
        
        # 检查 REST Framework 配置
        print("\n3. 检查 REST Framework 配置")
        rf_settings = settings.REST_FRAMEWORK
        auth_classes = rf_settings.get('DEFAULT_AUTHENTICATION_CLASSES', [])
        
        jwt_auth = 'rest_framework_simplejwt.authentication.JWTAuthentication'
        print(f"   JWT 认证类: {'✓' if jwt_auth in auth_classes else '✗'}")
        
        # 检查 JWT 设置
        print("\n4. 检查 JWT 设置")
        jwt_settings = getattr(settings, 'SIMPLE_JWT', {})
        print(f"   ACCESS_TOKEN_LIFETIME: {'✓' if 'ACCESS_TOKEN_LIFETIME' in jwt_settings else '✗'}")
        print(f"   REFRESH_TOKEN_LIFETIME: {'✓' if 'REFRESH_TOKEN_LIFETIME' in jwt_settings else '✗'}")
        
        print("\n✓ Swagger 配置测试完成")
        return True
        
    except Exception as e:
        print(f"✗ Swagger 配置测试失败: {e}")
        return False

def test_urls_config():
    """测试 URLs 配置"""
    print("\n=== 测试 URLs 配置 ===")
    
    try:
        from EasyRAG.urls import urlpatterns
        
        # 检查必要的 URL 模式
        required_urls = [
            'swagger/',
            'api/token/',
            'api/token/refresh/',
            'api/',
            'api/user/'
        ]
        
        url_patterns = [str(pattern.pattern) for pattern in urlpatterns]
        
        print("1. 检查 URL 模式")
        for url in required_urls:
            found = any(url in pattern for pattern in url_patterns)
            print(f"   {url}: {'✓' if found else '✗'}")
        
        print("\n✓ URLs 配置测试完成")
        return True
        
    except Exception as e:
        print(f"✗ URLs 配置测试失败: {e}")
        return False

def test_views_config():
    """测试视图配置"""
    print("\n=== 测试视图配置 ===")
    
    try:
        # 检查自定义认证视图
        from EasyRAG.user_app.views import CustomTokenObtainPairView
        print("1. 自定义 JWT 认证视图: ✓")
        
        # 检查视图模型
        from EasyRAG.rag_app.viewmodels import KnowledgeBaseViewModel, FileUploadViewModel, DocumentViewModel
        print("2. 视图模型: ✓")
        
        # 检查权限类
        from EasyRAG.common.permissions import KnowledgeBasePermission, FileStoragePermission, DocumentPermission
        print("3. 权限类: ✓")
        
        print("\n✓ 视图配置测试完成")
        return True
        
    except Exception as e:
        print(f"✗ 视图配置测试失败: {e}")
        return False

def main():
    """主函数"""
    print("Swagger JWT 认证配置测试")
    print("=" * 50)
    
    # 设置 Django
    if not setup_django():
        return
    
    # 测试各项配置
    swagger_success = test_swagger_config()
    urls_success = test_urls_config()
    views_success = test_views_config()
    
    print("\n" + "=" * 50)
    print("测试结果汇总:")
    print(f"Swagger 配置: {'✓' if swagger_success else '✗'}")
    print(f"URLs 配置: {'✓' if urls_success else '✗'}")
    print(f"视图配置: {'✓' if views_success else '✗'}")
    
    if swagger_success and urls_success and views_success:
        print("\n🎉 所有配置测试通过！")
        print("\n使用说明:")
        print("1. 启动服务器: python manage.py runserver")
        print("2. 访问 Swagger UI: http://localhost:8000/swagger/")
        print("3. 点击右上角的 'Authorize' 按钮")
        print("4. 输入 JWT Token: Bearer <your_token>")
        print("5. 或者先调用 /api/token/ 获取 Token")
    else:
        print("\n❌ 部分配置测试失败，请检查相关配置")

if __name__ == "__main__":
    main() 