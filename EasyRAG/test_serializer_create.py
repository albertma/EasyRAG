#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试序列化器 create 方法是否被调用
"""

import sys
import os
import json

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')
django.setup()

from EasyRAG.llm_app.models import LLMTemplate, LLMInstance
from EasyRAG.llm_app.serializers import LLMTemplateSerializer, LLMInstanceSerializer
from EasyRAG.user_app.models import User

def test_llm_template_serializer_create():
    """测试 LLM 模板序列化器的 create 方法"""
    print("测试 LLM 模板序列化器的 create 方法...")
    
    # 测试数据
    template_data = {
        "template_name": "Test Template",
        "template_code": "test",
        "template_description": "Test Description",
        "llm_template_config": [
            {
               "key": "supplier",
               "type": "string",
               "description": "The supplier to use",
               "required": "true",
            }
        ],
        "llm_status": "ACTIVE"
    }
    
    try:
        # 使用序列化器创建
        serializer = LLMTemplateSerializer(data=template_data)
        if serializer.is_valid():
            template = serializer.save()
            print(f"✓ LLM 模板序列化器创建成功: {template.template_name}")
            print(f"  模板ID: {template.llm_template_id}")
            
            # 清理测试数据
            template.delete()
            print("✓ 测试数据清理完成")
            return template.llm_template_id
        else:
            print(f"✗ 序列化器验证失败: {serializer.errors}")
            return None
            
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        return None

def test_llm_instance_serializer_create(template_id):
    """测试 LLM 实例序列化器的 create 方法"""
    print("测试 LLM 实例序列化器的 create 方法...")
    
    # 获取或创建测试用户
    try:
        user = User.objects.get(username='testuser')
    except User.DoesNotExist:
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    # 测试数据
    instance_data = {
        "llm_template_id": template_id,
        "llm_config": {
            "supplier": "test_supplier",
            "url": "http://test.com",
            "api_key": "test_key"
        },
        "llm_status": "ACTIVE"
    }
    
    try:
        # 使用序列化器创建
        serializer = LLMInstanceSerializer(data=instance_data)
        if serializer.is_valid():
            instance = serializer.save()
            print(f"✓ LLM 实例序列化器创建成功: {instance.llm_instance_id}")
            print(f"  实例ID: {instance.llm_instance_id}")
            print(f"  模板: {instance.llm_template.template_name}")
            
            # 清理测试数据
            instance.delete()
            print("✓ 测试数据清理完成")
            return True
        else:
            print(f"✗ 序列化器验证失败: {serializer.errors}")
            return False
            
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        return False

if __name__ == "__main__":
    print("开始测试序列化器 create 方法...\n")
    
    # 测试模板序列化器
    template_id = test_llm_template_serializer_create()
    
    if template_id:
        print(f"\n模板创建成功，ID: {template_id}")
        
        # 测试实例序列化器
        success = test_llm_instance_serializer_create(template_id)
        
        if success:
            print("\n🎉 所有序列化器测试通过！")
        else:
            print("\n❌ LLM 实例序列化器测试失败！")
    else:
        print("\n❌ LLM 模板序列化器测试失败！") 