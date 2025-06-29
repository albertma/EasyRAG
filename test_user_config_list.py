#!/usr/bin/env python3
"""
测试新的List[Dict]格式的用户配置功能
"""
import os
import sys
import django

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'EasyRAG.settings')
django.setup()

from EasyRAG.llm_app.models import LLMTemplate, LLMInstance, LLMInstanceLLMModel, LLMModelUserConfig
from EasyRAG.user_app.models import User
from EasyRAG.common.utils import generate_uuid
from EasyRAG.llm_app.serializers import LLMModelUserConfigSerializer
from EasyRAG.llm_app.viewmodel import LLMModelUserConfigViewModel
from rest_framework.test import APIRequestFactory

def test_user_config_list():
    """测试List[Dict]格式的用户配置功能"""
    print("测试List[Dict]格式的用户配置功能...")
    
    # 获取或创建测试用户
    user, created = User.objects.get_or_create(
        username='testuser_config_list',
        defaults={'email': 'test_config_list@example.com'}
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
    
    # 清理该用户和模板下的所有实例
    LLMInstance.objects.filter(llm_template=template, created_by=user).delete()
    print("✅ 清理现有实例")
    
    # 创建测试实例
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
            model_status='ACTIVE'
        )
        models.append(model)
        print(f"✅ 创建模型 {i+1}: {model.llm_model_id}")
    
    # 准备测试数据
    configure_list = [
        {
            "llm_instance_id": instance.llm_instance_id,
            "llm_model_id": models[0].llm_model_id,
            "config_type": "CHAT",
            "config_value": "gpt-3.5-turbo"
        },
        {
            "llm_instance_id": instance.llm_instance_id,
            "llm_model_id": models[1].llm_model_id,
            "config_type": "EMBEDDING",
            "config_value": "BAAI/bge-m3"
        },
        {
            "llm_instance_id": instance.llm_instance_id,
            "llm_model_id": models[2].llm_model_id,
            "config_type": "RERANK",
            "config_value": "bge-reranker-v2-m3"
        }
    ]
    
    # 测试序列化器
    print("\n1. 测试序列化器:")
    factory = APIRequestFactory()
    request = factory.post('/api/llm/llm-model-user-configs/')
    request.user = user
    
    test_data = {
        'configure_list': configure_list
    }
    
    serializer = LLMModelUserConfigSerializer(data=test_data, context={'request': request})
    if serializer.is_valid():
        print("✅ 序列化器验证通过")
        print(f"配置列表: {serializer.validated_data.get('configure_list')}")
    else:
        print(f"❌ 序列化器验证失败: {serializer.errors}")
        return False
    
    # 测试viewmodel
    print("\n2. 测试viewmodel:")
    view_model = LLMModelUserConfigViewModel()
    
    try:
        result = view_model.perform_create_after_delete(configure_list, user)
        if result:
            print("✅ viewmodel处理成功")
            
            # 验证数据库中的配置
            user_configs = LLMModelUserConfig.objects.filter(owner=user)
            print(f"✅ 创建了 {user_configs.count()} 个用户配置")
            
            for config in user_configs:
                print(f"  - 配置ID: {config.llm_model_user_config_id}")
                print(f"    类型: {config.config_type}")
                print(f"    值: {config.config_value}")
            
            # 清理测试数据
            print("\n清理测试数据...")
            user_configs.delete()
            for model in models:
                model.delete()
            instance.delete()
            print("✅ 测试数据清理完成")
            
            return True
        else:
            print("❌ viewmodel处理失败")
            return False
    except Exception as e:
        print(f"❌ viewmodel处理异常: {e}")
        return False

if __name__ == "__main__":
    success = test_user_config_list()
    if success:
        print("\n🎉 List[Dict]格式用户配置测试通过！")
    else:
        print("\n⚠️ List[Dict]格式用户配置测试失败") 