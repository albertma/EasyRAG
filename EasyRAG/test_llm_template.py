#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 LLM 模板创建功能
"""

import sys
import os
import json

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')
django.setup()

from EasyRAG.llm_app.models import LLMTemplate

def test_llm_template_creation():
    """测试 LLM 模板创建"""
    print("测试 LLM 模板创建...")
    
    # 测试数据
    template_data = {
        "template_name": "Siliconflow",
        "template_code": "siliconflow",
        "template_description": "SiliconFlow API",
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
    
    try:
        # 验证 JSON 格式
        json_str = json.dumps(template_data["llm_template_config"])
        print(f"✓ JSON 格式验证通过: {json_str}")
        
        # 创建模板
        template = LLMTemplate.objects.create(
            llm_template_id="test-siliconflow-001",
            template_name=template_data["template_name"],
            template_code="silicon",
            template_description=template_data["template_description"],
            llm_template_config=template_data["llm_template_config"],
            llm_status=template_data["llm_status"]
        )
        
        print(f"✓ LLM 模板创建成功: {template.template_name}")
        print(f"  模板ID: {template.llm_template_id}")
        print(f"  模板配置: {template.llm_template_config}")
        
        # 清理测试数据
        template.delete()
        print("✓ 测试数据清理完成")
        
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = test_llm_template_creation()
    if success:
        print("\n🎉 所有测试通过！")
    else:
        print("\n❌ 测试失败！") 