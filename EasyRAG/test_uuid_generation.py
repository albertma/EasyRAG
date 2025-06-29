#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 UUID 自动生成功能
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
from EasyRAG.common.utils import generate_uuid

def test_uuid_generation():
    """测试 UUID 生成功能"""
    print("测试 UUID 生成功能...")
    
    # 测试 generate_uuid 函数
    uuid1 = generate_uuid()
    uuid2 = generate_uuid()
    print(f"✓ generate_uuid() 生成: {uuid1}")
    print(f"✓ generate_uuid() 生成: {uuid2}")
    print(f"✓ UUID 长度: {len(uuid1)} 字符")
    print(f"✓ UUID 唯一性: {uuid1 != uuid2}")
    
    return True

def test_llm_template_uuid():
    """测试 LLM 模板 UUID 自动生成"""
    print("\n测试 LLM 模板 UUID 自动生成...")
    
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
        # 使用序列化器创建模板
        serializer = LLMTemplateSerializer(data=template_data)
        if serializer.is_valid():
            template = serializer.save()
            print(f"✓ LLM 模板创建成功")
            print(f"  模板ID: {template.llm_template_id}")
            print(f"  模板名称: {template.template_name}")
            print(f"  UUID 长度: {len(template.llm_template_id)} 字符")
            
            # 清理测试数据
            template.delete()
            print("✓ 测试数据清理完成")
            return True
        else:
            print(f"✗ 序列化器验证失败: {serializer.errors}")
            return False
            
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        return False

def test_llm_instance_uuid():
    """测试 LLM 实例 UUID 自动生成"""
    print("\n测试 LLM 实例 UUID 自动生成...")
    
    try:
        # 首先创建一个模板
        template = LLMTemplate.objects.create(
            llm_template_id=generate_uuid(),
            template_name="Test Template for Instance",
            template_code="testinst2",
            template_description="Test Template for Instance",
            llm_template_config=[
                {
                   "key": "supplier",
                   "type": "string",
                   "description": "The supplier to use",
                   "required": "true",
                }
            ],
            llm_status="ACTIVE"
        )
        
        # 创建用户（如果不存在）
        user, created = User.objects.get_or_create(
            username="testuser",
            defaults={
                "email": "test@example.com",
                "is_staff": False,
                "is_active": True
            }
        )
        
        # 测试数据
        instance_data = {
            "llm_template_id": template.llm_template_id,
            "llm_config": {
                "supplier": "test_supplier"
            },
            "llm_status": "ACTIVE"
        }
        
        # 使用序列化器创建实例
        serializer = LLMInstanceSerializer(data=instance_data)
        if serializer.is_valid():
            instance = serializer.save(created_by=user)
            print(f"✓ LLM 实例创建成功")
            print(f"  实例ID: {instance.llm_instance_id}")
            print(f"  模板ID: {instance.llm_template.llm_template_id}")
            print(f"  UUID 长度: {len(instance.llm_instance_id)} 字符")
            
            # 清理测试数据
            instance.delete()
            template.delete()
            if created:
                user.delete()
            print("✓ 测试数据清理完成")
            return True
        else:
            print(f"✗ 序列化器验证失败: {serializer.errors}")
            return False
            
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        return False

if __name__ == "__main__":
    print("🧪 开始测试 UUID 自动生成功能...\n")
    
    success1 = test_uuid_generation()
    success2 = test_llm_template_uuid()
    success3 = test_llm_instance_uuid()
    
    if success1 and success2 and success3:
        print("\n🎉 所有测试通过！UUID 自动生成功能正常工作！")
    else:
        print("\n❌ 部分测试失败！") 