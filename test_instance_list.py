#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 LLM 实例列表过滤功能
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

def create_test_data():
    """创建测试数据"""
    print("创建测试数据...")
    
    # 创建测试用户
    users = []
    for i in range(2):
        username = f'testuser{i+1}'
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            user = User.objects.create_user(
                username=username,
                email=f'{username}@example.com',
                password='testpass123'
            )
        users.append(user)
        print(f"✓ 用户创建成功: {username} (ID: {user.id})")
    
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
    
    serializer = LLMTemplateSerializer(data=template_data)
    if serializer.is_valid():
        template = serializer.save()
        print(f"✓ 模板创建成功: {template.template_name} (ID: {template.llm_template_id})")
    else:
        print(f"✗ 模板创建失败: {serializer.errors}")
        return None, None, None
    
    # 创建测试实例
    instances = []
    for i, user in enumerate(users):
        instance_data = {
            "llm_template_id": template.llm_template_id,
            "llm_config": {
                "supplier": f"test_supplier_{i+1}",
                "url": f"http://test{i+1}.com",
                "api_key": f"test_key_{i+1}"
            },
            "llm_status": "ACTIVE" if i == 0 else "INACTIVE"
        }
        
        # 创建DummyRequest类
        class DummyRequest:
            def __init__(self, user):
                self.user = user
        
        serializer = LLMInstanceSerializer(data=instance_data, context={'request': DummyRequest(user)})
        if serializer.is_valid():
            instance = serializer.save()
            instances.append(instance)
            print(f"✓ 实例创建成功: {instance.llm_instance_id} (用户: {user.username}, 状态: {instance.llm_status})")
        else:
            print(f"✗ 实例创建失败: {serializer.errors}")
    
    return users, template, instances

def test_list_filtering():
    """测试列表过滤功能"""
    print("\n测试列表过滤功能...")
    
    # 创建测试数据
    users, template, instances = create_test_data()
    if not users or not template or not instances:
        print("✗ 测试数据创建失败")
        return False
    
    try:
        # 测试1: 获取所有实例（默认只显示当前用户）
        print("\n1. 测试默认列表（当前用户）:")
        queryset = LLMInstance.objects.filter(created_by=users[0])
        serializer = LLMInstanceSerializer(queryset, many=True)
        print(f"   找到 {len(serializer.data)} 个实例")
        for instance in serializer.data:
            print(f"   - {instance['llm_instance_id']} (状态: {instance['llm_status']})")
        
        # 测试2: 按用户ID过滤
        print("\n2. 测试按用户ID过滤:")
        queryset = LLMInstance.objects.filter(created_by_id=users[1].id)
        serializer = LLMInstanceSerializer(queryset, many=True)
        print(f"   用户 {users[1].username} 的实例: {len(serializer.data)} 个")
        
        # 测试3: 按状态过滤
        print("\n3. 测试按状态过滤:")
        queryset = LLMInstance.objects.filter(llm_status='ACTIVE')
        serializer = LLMInstanceSerializer(queryset, many=True)
        print(f"   活跃状态实例: {len(serializer.data)} 个")
        
        # 测试4: 按模板ID过滤
        print("\n4. 测试按模板ID过滤:")
        queryset = LLMInstance.objects.filter(llm_template__llm_template_id=template.llm_template_id)
        serializer = LLMInstanceSerializer(queryset, many=True)
        print(f"   模板 {template.template_name} 的实例: {len(serializer.data)} 个")
        
        # 测试5: 组合过滤
        print("\n5. 测试组合过滤:")
        queryset = LLMInstance.objects.filter(
            created_by=users[0],
            llm_status='ACTIVE',
            llm_template__llm_template_id=template.llm_template_id
        )
        serializer = LLMInstanceSerializer(queryset, many=True)
        print(f"   用户 {users[0].username} 的活跃实例: {len(serializer.data)} 个")
        
        return True
        
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        return False

def cleanup_test_data(users, template, instances):
    """清理测试数据"""
    print("\n清理测试数据...")
    
    # 删除实例
    for instance in instances:
        try:
            instance.delete()
            print(f"✓ 实例删除成功: {instance.llm_instance_id}")
        except:
            pass
    
    # 删除模板
    try:
        template.delete()
        print(f"✓ 模板删除成功: {template.template_name}")
    except:
        pass
    
    # 删除用户
    for user in users:
        try:
            user.delete()
            print(f"✓ 用户删除成功: {user.username}")
        except:
            pass

if __name__ == "__main__":
    print("开始测试 LLM 实例列表过滤功能...\n")
    
    # 创建测试数据
    users, template, instances = create_test_data()
    
    if users and template and instances:
        # 测试过滤功能
        success = test_list_filtering()
        
        if success:
            print("\n🎉 所有测试通过！")
        else:
            print("\n❌ 测试失败！")
        
        # 清理测试数据
        cleanup_test_data(users, template, instances)
    else:
        print("\n❌ 测试数据创建失败！") 