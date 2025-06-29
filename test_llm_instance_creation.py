#!/usr/bin/env python3
"""
测试LLM实例创建功能
"""
import os
import sys
import django

# 设置Django环境
sys.path.append('/Users/albertma/sourcecode/workspace/python/EasyRAG')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'EasyRAG.settings')
django.setup()

from EasyRAG.llm_app.models import LLMTemplate, LLMInstance, LLMInstanceLLMModel
from EasyRAG.user_app.models import User
from EasyRAG.llm_app.serializers import LLMInstanceSerializer
from EasyRAG.llm_app.viewmodel import LLMInstanceViewModel
from rest_framework.test import APIRequestFactory
from django.test import TestCase

def test_llm_instance_creation():
    """测试LLM实例创建"""
    print("开始测试LLM实例创建...")
    
    # 创建测试用户
    user, created = User.objects.get_or_create(
        username='testuser',
        defaults={'email': 'test@example.com'}
    )
    if created:
        print(f"✅ 创建测试用户: {user.username}")
    else:
        print(f"✅ 使用现有测试用户: {user.username}")
    
    # 创建测试模板
    template, created = LLMTemplate.objects.get_or_create(
        template_code='siliconflow',
        defaults={
            'template_name': 'SiliconFlow',
            'llm_status': 'ACTIVE',
            'llm_template_config': [
                {"key": "url", "type": "string", "description": "API URL", "required": "true"},
                {"key": "api_key", "type": "string", "description": "API Key", "required": "true"}
            ]
        }
    )
    if created:
        print(f"✅ 创建测试模板: {template.template_name} (ID: {template.llm_template_id})")
    else:
        print(f"✅ 使用现有测试模板: {template.template_name} (ID: {template.llm_template_id})")
    
    # 确保模板有ID
    if not template.llm_template_id:
        print("❌ 模板ID为空，跳过测试")
        return False
    
    # 创建请求工厂
    factory = APIRequestFactory()
    request = factory.post('/api/llm/llm-instances/')
    request.user = user
    
    # 准备测试数据
    test_data = {
        'llm_template_id': template.llm_template_id,
        'llm_config': {
            'supplier': 'test_supplier',
            'url': 'https://api.siliconflow.com/v1',
            'api_key': 'test_api_key_123'
        }
    }
    
    # 创建序列化器
    serializer = LLMInstanceSerializer(data=test_data, context={'request': request})
    
    if serializer.is_valid():
        print("✅ 序列化器验证通过")
        
        # 创建viewmodel并执行创建
        viewmodel = LLMInstanceViewModel()
        try:
            instance = viewmodel.perform_create(serializer)
            print(f"✅ LLM实例创建成功: {instance.llm_instance_id}")
            
            # 检查是否创建了LLM模型记录
            llm_models = LLMInstanceLLMModel.objects.filter(llm_instance=instance)
            print(f"✅ 创建了 {llm_models.count()} 个LLM模型记录")
            
            return True
        except Exception as e:
            print(f"❌ LLM实例创建失败: {e}")
            return False
    else:
        print(f"❌ 序列化器验证失败: {serializer.errors}")
        return False

if __name__ == "__main__":
    success = test_llm_instance_creation()
    if success:
        print("\n🎉 测试通过！LLM实例创建功能正常")
    else:
        print("\n⚠️ 测试失败，请检查修复") 