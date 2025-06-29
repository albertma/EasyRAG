#!/usr/bin/env python3
"""
测试完整的LLM实例创建和用户配置流程
"""
import os
import sys
import django
from django.conf import settings

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'EasyRAG.settings')
django.setup()

from rest_framework.test import APIRequestFactory
from rest_framework import serializers
from EasyRAG.llm_app.models import LLMTemplate, LLMInstance, LLMInstanceLLMModel, LLMModelUserConfig
from EasyRAG.user_app.models import User
from EasyRAG.llm_app.serializers import LLMInstanceSerializer, LLMModelUserConfigSerializer
from EasyRAG.llm_app.viewmodel import LLMInstanceViewModel, LLMModelUserConfigViewModel
import logging

logger = logging.getLogger(__name__)

def test_complete_flow():
    """测试完整的LLM实例创建和用户配置流程"""
    print("开始测试完整流程...")
    
    # 获取或创建测试用户
    user, created = User.objects.get_or_create(
        username='testuser',
        defaults={'email': 'test@example.com'}
    )
    if created:
        print(f"✅ 创建测试用户: {user.username}")
    else:
        print(f"✅ 使用现有测试用户: {user.username}")
    
    # 使用现有的有效模板
    template = LLMTemplate.objects.filter(llm_template_id__isnull=False).exclude(llm_template_id='').first()
    if not template:
        print("❌ 没有找到有效的模板，跳过测试")
        return False
    
    print(f"✅ 使用现有测试模板: {template.template_name} (ID: {template.llm_template_id})")
    
    # 创建请求工厂
    factory = APIRequestFactory()
    request = factory.post('/api/llm/llm-instances/')
    request.user = user
    
    # 准备测试数据
    test_data = {
        'llm_template_id': template.llm_template_id,
        'llm_config': {
            'url': 'https://api.test.com/v1',
            'api_key': 'test_api_key_123'
        }
    }
    
    # 测试序列化器验证
    serializer = LLMInstanceSerializer(data=test_data, context={'request': request})
    if not serializer.is_valid():
        print(f"❌ 序列化器验证失败: {serializer.errors}")
        return False
    print("✅ 序列化器验证通过")
    
    # 测试viewmodel（跳过连接验证）
    view_model = LLMInstanceViewModel()
    
    # 模拟连接验证成功
    def mock_get_llm_models(config, template_name):
        return [
            {'id': 'test-model-1', 'object': 'model'},
            {'id': 'test-model-2', 'object': 'model'}
        ]
    
    # 临时替换方法
    original_method = view_model._get_llm_models
    view_model._get_llm_models = mock_get_llm_models
    
    try:
        # 执行创建
        instance = view_model.perform_create(serializer)
        print(f"✅ LLM实例创建成功: {instance.llm_instance_id}")
        
        # 验证LLM模型是否保存
        llm_models = LLMInstanceLLMModel.objects.filter(llm_instance=instance)
        print(f"✅ 保存了 {llm_models.count()} 个LLM模型")
        
        # 测试用户配置创建
        user_config_data = {
            'llm_instance_id': instance.llm_instance_id,
            'llm_model_id': 'test-model-1'
        }
        
        user_config_serializer = LLMModelUserConfigSerializer(
            data=user_config_data, 
            context={'request': request}
        )
        
        if not user_config_serializer.is_valid():
            print(f"❌ 用户配置序列化器验证失败: {user_config_serializer.errors}")
            return False
        print("✅ 用户配置序列化器验证通过")
        
        # 测试用户配置viewmodel
        user_config_view_model = LLMModelUserConfigViewModel()
        result = user_config_view_model.perform_create_after_delete(
            instance, 'test-model-1', user
        )
        
        if result:
            print("✅ 用户配置创建成功")
            
            # 验证用户配置是否保存
            user_configs = LLMModelUserConfig.objects.filter(owner=user)
            print(f"✅ 保存了 {user_configs.count()} 个用户配置")
            
            # 清理测试数据
            user_configs.delete()
            llm_models.delete()
            instance.delete()
            print("✅ 测试数据清理完成")
            
            return True
        else:
            print("❌ 用户配置创建失败")
            return False
            
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")
        return False
    finally:
        # 恢复原始方法
        view_model._get_llm_models = original_method

if __name__ == "__main__":
    success = test_complete_flow()
    if success:
        print("\n🎉 完整流程测试通过！")
    else:
        print("\n⚠️ 完整流程测试失败") 