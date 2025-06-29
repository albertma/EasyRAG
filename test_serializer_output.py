#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试序列化器返回数据是否包含 llm_template_id
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
from EasyRAG.user_app.models import User

def test_serializer_output():
    """测试序列化器返回数据"""
    print("测试序列化器返回数据...")
    
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
        "template_name": f"Test Template {timestamp}",
        "template_code": f"test_{timestamp}",
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
    
    template_serializer = LLMTemplateSerializer(data=template_data)
    if template_serializer.is_valid():
        template = template_serializer.save()
        print(f"✓ 模板创建成功: {template.template_name}")
        print(f"  模板ID: {template.llm_template_id}")
    else:
        print(f"✗ 模板创建失败: {template_serializer.errors}")
        return False
    
    # 创建测试实例
    instance_data = {
        "llm_template_id": template.llm_template_id,
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
    
    instance_serializer = LLMInstanceSerializer(data=instance_data, context={'request': DummyRequest(user)})
    if instance_serializer.is_valid():
        instance = instance_serializer.save()
        print(f"✓ 实例创建成功: {instance.llm_instance_id}")
        
        # 测试序列化器输出
        print("\n测试序列化器输出:")
        
        # 单个实例序列化
        single_serializer = LLMInstanceSerializer(instance)
        single_data = single_serializer.data
        print("单个实例序列化结果:")
        print(json.dumps(single_data, indent=2, ensure_ascii=False))
        
        # 检查是否包含 llm_template_id
        if 'llm_template_id_readonly' in single_data:
            print(f"\n✓ 返回数据包含 llm_template_id: {single_data['llm_template_id_readonly']}")
        else:
            print("\n✗ 返回数据不包含 llm_template_id")
            return False
        
        # 多个实例序列化
        instances = LLMInstance.objects.filter(created_by=user)
        many_serializer = LLMInstanceSerializer(instances, many=True)
        many_data = many_serializer.data
        print(f"\n多个实例序列化结果 (共{len(many_data)}个):")
        for i, data in enumerate(many_data):
            print(f"实例 {i+1}:")
            print(json.dumps(data, indent=2, ensure_ascii=False))
            if 'llm_template_id_readonly' in data:
                print(f"  ✓ 包含 llm_template_id: {data['llm_template_id_readonly']}")
            else:
                print("  ✗ 不包含 llm_template_id")
                return False
        
        # 清理测试数据
        instance.delete()
        template.delete()
        print("\n✓ 测试数据清理完成")
        
        return True
    else:
        print(f"✗ 实例创建失败: {instance_serializer.errors}")
        return False

if __name__ == "__main__":
    print("开始测试序列化器返回数据...\n")
    
    success = test_serializer_output()
    
    if success:
        print("\n🎉 测试通过！序列化器返回数据包含 llm_template_id")
    else:
        print("\n❌ 测试失败！") 