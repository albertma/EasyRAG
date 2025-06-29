#!/usr/bin/env python3
"""
测试按instance_id分组获取用户数据的功能
"""
import os
import sys
import django
import requests
import json

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'EasyRAG.settings')
django.setup()

from EasyRAG.llm_app.models import LLMTemplate, LLMInstance, LLMInstanceLLMModel
from EasyRAG.user_app.models import User
from EasyRAG.common.utils import generate_uuid

def create_test_data():
    """创建测试数据"""
    print("创建测试数据...")
    
    # 创建测试用户
    user, created = User.objects.get_or_create(
        username='testuser_grouping',
        defaults={'email': 'test_grouping@example.com'}
    )
    if created:
        print(f"✅ 创建测试用户: {user.username}")
    else:
        print(f"✅ 使用现有测试用户: {user.username}")
    
    # 创建测试模板
    template, created = LLMTemplate.objects.get_or_create(
        template_code='test_grouping',
        defaults={
            'template_name': 'Test Grouping Template',
            'llm_status': 'ACTIVE',
            'llm_template_config': [
                {"key": "url", "type": "string", "description": "API URL", "required": "true"},
                {"key": "api_key", "type": "string", "description": "API Key", "required": "true"}
            ]
        }
    )
    if created:
        print(f"✅ 创建测试模板: {template.template_name}")
    else:
        print(f"✅ 使用现有测试模板: {template.template_name}")
    
    # 创建多个LLM实例
    instances = []
    for i in range(3):
        instance = LLMInstance.objects.create(
            llm_instance_id=generate_uuid(),
            llm_template=template,
            llm_config={'url': f'https://api{i}.test.com', 'api_key': f'key{i}'},
            created_by=user,
            llm_status='ACTIVE'
        )
        instances.append(instance)
        print(f"✅ 创建LLM实例 {i+1}: {instance.llm_instance_id}")
    
    # 为每个实例创建多个LLM模型
    for i, instance in enumerate(instances):
        for j in range(2):  # 每个实例创建2个模型
            model = LLMInstanceLLMModel.objects.create(
                llm_instance_llm_model_id=generate_uuid(),
                llm_instance=instance,
                llm_model_id=f'model_{i}_{j}',
                llm_object_id='model',
                owner=user,
                model_status='ACTIVE',
                instance_config=instance.llm_config
            )
            print(f"✅ 为实例 {i+1} 创建模型 {j+1}: {model.llm_model_id}")
    
    return user, instances

def test_api_endpoint():
    """测试API端点"""
    print("\n测试API端点...")
    
    # 测试获取当前用户数据（分组）
    print("1. 测试获取当前用户数据（分组）:")
    response = requests.get('http://localhost:8000/api/llm/llm-instance-llm-models/?group_by_instance=true')
    print(f"状态码: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"用户ID: {data.get('user_id')}")
        print(f"用户名: {data.get('username')}")
        print(f"实例数量: {data.get('total_instances')}")
        print(f"模型总数: {data.get('total_models')}")
        print(f"分组数据: {json.dumps(data.get('data', [])[:2], indent=2, ensure_ascii=False)}")  # 只显示前2个
    else:
        print(f"错误: {response.text}")
    
    # 测试获取当前用户数据（不分组）
    print("\n2. 测试获取当前用户数据（不分组）:")
    response = requests.get('http://localhost:8000/api/llm/llm-instance-llm-models/?group_by_instance=false')
    print(f"状态码: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"用户ID: {data.get('user_id')}")
        print(f"用户名: {data.get('username')}")
        print(f"模型总数: {data.get('total_models')}")
        print(f"数据示例: {json.dumps(data.get('data', [])[:2], indent=2, ensure_ascii=False)}")  # 只显示前2个
    else:
        print(f"错误: {response.text}")

def cleanup_test_data(user, instances):
    """清理测试数据"""
    print("\n清理测试数据...")
    
    # 删除LLM模型
    LLMInstanceLLMModel.objects.filter(owner=user).delete()
    print("✅ 删除LLM模型")
    
    # 删除LLM实例
    for instance in instances:
        instance.delete()
    print("✅ 删除LLM实例")
    
    # 删除用户
    user.delete()
    print("✅ 删除测试用户")

if __name__ == "__main__":
    try:
        # 创建测试数据
        user, instances = create_test_data()
        
        # 测试API端点
        test_api_endpoint()
        
        # 清理测试数据
        cleanup_test_data(user, instances)
        
        print("\n🎉 测试完成！")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc() 