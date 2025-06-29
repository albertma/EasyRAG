#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试重构后的viewmodel功能
"""

import sys
import os
import json
import logging
import time

# 设置日志
logging.basicConfig(level=logging.INFO)

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(__file__))

import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'EasyRAG.settings')
django.setup()

from EasyRAG.llm_app.models import LLMTemplate, LLMInstance
from EasyRAG.llm_app.serializers import LLMTemplateSerializer, LLMInstanceSerializer
from EasyRAG.llm_app.viewmodel import LLMInstanceViewModel
from EasyRAG.user_app.models import User

def test_viewmodel_perform_create():
    """测试viewmodel的perform_create方法"""
    print("测试viewmodel的perform_create方法...")
    
    # 创建测试用户
    try:
        user = User.objects.get(username='testuser')
    except User.DoesNotExist:
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    # 创建测试模板
    timestamp = int(time.time())
    template_data = {
        "template_name": "Siliconflow",
        "template_code": f"silicon_{timestamp % 1000}",
        "template_description": "Test Description",
        "llm_template_config": [
            {
               "key": "supplier",
               "type": "string",
               "description": "The supplier to use",
               "required": "true",
            },
            {
               "key": "url",
               "type": "string",
               "description": "The url to use",
               "required": "true",
            },
            {
               "key": "api_key",
               "type": "string",
               "description": "The api key to use",
               "required": "false",
            }
        ],
        "llm_status": "ACTIVE"
    }
    
    template_serializer = LLMTemplateSerializer(data=template_data)
    if template_serializer.is_valid():
        template = template_serializer.save()
        print(f"✓ 模板创建成功: {template.template_name}")
        print(f"  模板ID: {template.llm_template_id}")
    else:
        print(f"✗ 模板创建失败: {template_serializer.errors}")
        return False
    
    # 创建viewmodel实例
    viewmodel = LLMInstanceViewModel()
    
    # 测试1: 无效的模板ID
    print("\n1. 测试无效的模板ID:")
    instance_data_invalid_template = {
        "llm_template_id": "invalid_template_id",
        "llm_config": {
            "supplier": "test_supplier",
            "url": "http://test.com",
            "api_key": "test_key"
        },
        "llm_status": "ACTIVE"
    }
    
    # 创建DummyRequest类
    class DummyRequest:
        def __init__(self, user):
            self.user = user
    
    instance_serializer = LLMInstanceSerializer(data=instance_data_invalid_template, context={'request': DummyRequest(user)})
    if instance_serializer.is_valid():
        try:
            instance = viewmodel.perform_create(instance_serializer, user)
            print("✗ 应该失败但成功了")
            instance.delete()
            return False
        except Exception as e:
            print(f"✓ 正确捕获错误: {e}")
    else:
        print(f"✓ 序列化器验证失败: {instance_serializer.errors}")
    
    # 检查数据库中是否有实例
    instances_count = LLMInstance.objects.filter(created_by=user).count()
    print(f"  数据库中实例数量: {instances_count}")
    if instances_count > 0:
        print("✗ 验证失败时仍有实例保存到数据库")
        return False
    
    # 测试2: 缺少必需字段
    print("\n2. 测试缺少必需字段:")
    instance_data_missing_field = {
        "llm_template_id": template.llm_template_id,
        "llm_config": {
            "supplier": "test_supplier"
            # 缺少 url 字段
        },
        "llm_status": "ACTIVE"
    }
    
    instance_serializer = LLMInstanceSerializer(data=instance_data_missing_field, context={'request': DummyRequest(user)})
    if instance_serializer.is_valid():
        try:
            instance = viewmodel.perform_create(instance_serializer, user)
            print("✗ 应该失败但成功了")
            instance.delete()
            return False
        except Exception as e:
            print(f"✓ 正确捕获错误: {e}")
    else:
        print(f"✓ 序列化器验证失败: {instance_serializer.errors}")
    
    # 检查数据库中是否有实例
    instances_count = LLMInstance.objects.filter(created_by=user).count()
    print(f"  数据库中实例数量: {instances_count}")
    if instances_count > 0:
        print("✗ 验证失败时仍有实例保存到数据库")
        return False
    
    # 测试3: 有效的配置
    print("\n3. 测试有效的配置:")
    instance_data_valid = {
        "llm_template_id": template.llm_template_id,
        "llm_config": {
            "supplier": "test_supplier",
            "url": "https://api.siliconflow.cn/v1",
            "api_key": "test_key"
        },
        "llm_status": "ACTIVE"
    }
    
    instance_serializer = LLMInstanceSerializer(data=instance_data_valid, context={'request': DummyRequest(user)})
    if instance_serializer.is_valid():
        try:
            instance = viewmodel.perform_create(instance_serializer, user)
            print(f"✓ 实例创建成功: {instance.llm_instance_id}")
            
            # 检查数据库中是否有实例
            instances_count = LLMInstance.objects.filter(created_by=user).count()
            print(f"  数据库中实例数量: {instances_count}")
            
            # 清理测试数据
            instance.delete()
            template.delete()
            print("✓ 测试数据清理完成")
            
            return True
        except Exception as e:
            print(f"✗ 创建失败: {e}")
            return False
    else:
        print(f"✗ 序列化器验证失败: {instance_serializer.errors}")
        return False

def test_viewmodel_check_config():
    """测试viewmodel的_check_config方法"""
    print("\n测试viewmodel的_check_config方法...")
    
    viewmodel = LLMInstanceViewModel()
    
    # 测试配置
    config = {
        "supplier": "test_supplier",
        "url": "http://test.com",
        "api_key": "test_key"
    }
    
    # 测试1: 必填字段存在
    result1 = viewmodel._check_config("supplier", "string", "true", config)
    print(f"1. 必填字段存在: {result1}")
    
    # 测试2: 必填字段不存在
    result2 = viewmodel._check_config("missing_field", "string", "true", config)
    print(f"2. 必填字段不存在: {result2}")
    
    # 测试3: 必填字段为空字符串
    config_empty = {"supplier": "", "url": "http://test.com"}
    result3 = viewmodel._check_config("supplier", "string", "true", config_empty)
    print(f"3. 必填字段为空字符串: {result3}")
    
    # 测试4: 非必填字段不存在
    result4 = viewmodel._check_config("optional_field", "string", "false", config)
    print(f"4. 非必填字段不存在: {result4}")
    
    # 测试5: 类型不匹配
    config_wrong_type = {"number_field": "not_a_number"}
    result5 = viewmodel._check_config("number_field", "number", "true", config_wrong_type)
    print(f"5. 类型不匹配: {result5}")
    
    return True

if __name__ == "__main__":
    print("开始测试重构后的viewmodel功能...\n")
    
    success1 = test_viewmodel_perform_create()
    success2 = test_viewmodel_check_config()
    
    if success1 and success2:
        print("\n🎉 所有测试通过！viewmodel重构成功")
    else:
        print("\n❌ 部分测试失败！") 