#!/usr/bin/env python3
"""
简单测试分组功能
"""
import os
import sys
import django

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'EasyRAG.settings')
django.setup()

from EasyRAG.llm_app.models import LLMTemplate, LLMInstance, LLMInstanceLLMModel
from EasyRAG.user_app.models import User
from EasyRAG.common.utils import generate_uuid
from rest_framework.test import APIRequestFactory
from EasyRAG.llm_app.views import LLMInstanceLLMModelViewSet

def test_grouping_function():
    """测试分组功能"""
    print("测试分组功能...")
    
    # 获取或创建测试用户
    user, created = User.objects.get_or_create(
        username='testuser_grouping',
        defaults={'email': 'test_grouping@example.com'}
    )
    if created:
        print(f"✅ 创建测试用户: {user.username}")
    else:
        print(f"✅ 使用现有测试用户: {user.username}")
    
    # 获取现有模板
    template = LLMTemplate.objects.filter(llm_template_id__isnull=False).exclude(llm_template_id='').first()
    if not template:
        print("❌ 没有找到有效模板")
        return False
    
    print(f"✅ 使用模板: {template.template_name}")
    
    # 创建测试实例和模型
    instance = LLMInstance.objects.create(
        llm_instance_id=generate_uuid(),
        llm_template=template,
        llm_config={'url': 'https://api.test.com', 'api_key': 'test_key'},
        created_by=user,
        llm_status='ACTIVE'
    )
    print(f"✅ 创建测试实例: {instance.llm_instance_id}")
    
    # 创建多个模型
    models = []
    for i in range(3):
        model = LLMInstanceLLMModel.objects.create(
            llm_instance_llm_model_id=generate_uuid(),
            llm_instance=instance,
            llm_model_id=f'test_model_{i}',
            llm_object_id='model',
            owner=user,
            model_status='ACTIVE',
            instance_config=instance.llm_config
        )
        models.append(model)
        print(f"✅ 创建模型 {i+1}: {model.llm_model_id}")
    
    # 测试ViewSet
    factory = APIRequestFactory()
    viewset = LLMInstanceLLMModelViewSet()
    
    # 测试分组功能
    print("\n测试分组功能:")
    request = factory.get('/api/llm/llm-instance-llm-models/?group_by_instance=true')
    request.user = user
    viewset.request = request
    viewset.format_kwarg = None
    
    # 设置query_params
    from django.http import QueryDict
    request.query_params = QueryDict('group_by_instance=true')
    
    response = viewset.list(request)
    print(f"状态码: {response.status_code}")
    
    if response.status_code == 200:
        data = response.data
        print(f"用户ID: {data.get('user_id')}")
        print(f"用户名: {data.get('username')}")
        print(f"实例数量: {data.get('total_instances')}")
        print(f"模型总数: {data.get('total_models')}")
        print(f"分组数据: {data.get('data')}")
        
        # 验证分组结果
        if data.get('total_instances') == 1 and data.get('total_models') == 3:
            print("✅ 分组功能正常")
            success = True
        else:
            print("❌ 分组结果不符合预期")
            success = False
    else:
        print(f"❌ 请求失败: {response.data}")
        success = False
    
    # 清理测试数据
    print("\n清理测试数据...")
    for model in models:
        model.delete()
    instance.delete()
    print("✅ 测试数据清理完成")
    
    return success

if __name__ == "__main__":
    success = test_grouping_function()
    if success:
        print("\n🎉 分组功能测试通过！")
    else:
        print("\n⚠️ 分组功能测试失败") 