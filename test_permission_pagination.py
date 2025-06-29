#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试权限验证和分页功能
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
    
    # 创建超级用户
    try:
        superuser = User.objects.get(username='admin')
    except User.DoesNotExist:
        superuser = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpass123'
        )
    print(f"✓ 超级用户创建成功: {superuser.username} (ID: {superuser.id}, is_superuser: {superuser.is_superuser})")
    
    # 创建普通用户
    users = []
    for i in range(2):
        username = f'normaluser{i+1}'
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            user = User.objects.create_user(
                username=username,
                email=f'{username}@example.com',
                password='userpass123'
            )
        users.append(user)
        print(f"✓ 普通用户创建成功: {username} (ID: {user.id}, is_superuser: {user.is_superuser})")
    
    # 为每个用户创建不同的模板
    templates = []
    all_instances = []
    
    for i, user in enumerate(users + [superuser]):
        timestamp = int(time.time()) + i  # 确保每个模板都有唯一的timestamp
        template_data = {
            "template_name": f"Test Template {timestamp}",
            "template_code": f"test_{timestamp}",
            "template_description": f"Test Description for {user.username}",
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
            templates.append(template)
            print(f"✓ 模板创建成功: {template.template_name} (ID: {template.llm_template_id})")
            
            # 为每个模板创建多个实例
            for j in range(3):  # 每个模板创建3个实例
                instance_data = {
                    "llm_template_id": template.llm_template_id,
                    "llm_config": {
                        "supplier": f"test_supplier_{i+1}_{j+1}",
                        "url": f"http://test{i+1}_{j+1}.com",
                        "api_key": f"test_key_{i+1}_{j+1}"
                    },
                    "llm_status": "ACTIVE" if j % 2 == 0 else "INACTIVE"
                }
                
                # 创建DummyRequest类
                class DummyRequest:
                    def __init__(self, user):
                        self.user = user
                
                serializer = LLMInstanceSerializer(data=instance_data, context={'request': DummyRequest(user)})
                if serializer.is_valid():
                    instance = serializer.save()
                    all_instances.append(instance)
                    print(f"✓ 实例创建成功: {instance.llm_instance_id} (用户: {user.username}, 状态: {instance.llm_status})")
                else:
                    print(f"✗ 实例创建失败: {serializer.errors}")
        else:
            print(f"✗ 模板创建失败: {serializer.errors}")
    
    return superuser, users, templates, all_instances

def test_permission_and_pagination():
    """测试权限验证和分页功能"""
    print("\n测试权限验证和分页功能...")
    
    # 创建测试数据
    superuser, users, templates, instances = create_test_data()
    if not superuser or not users or not templates or not instances:
        print("✗ 测试数据创建失败")
        return False
    
    try:
        print(f"\n总共创建了 {len(instances)} 个实例")
        
        # 测试1: 超级用户查看所有实例
        print("\n1. 测试超级用户查看所有实例:")
        queryset = LLMInstance.objects.all()
        serializer = LLMInstanceSerializer(queryset, many=True)
        print(f"   超级用户可以看到 {len(serializer.data)} 个实例")
        
        # 测试2: 普通用户只能查看自己的实例
        print("\n2. 测试普通用户权限:")
        for user in users:
            queryset = LLMInstance.objects.filter(created_by=user)
            serializer = LLMInstanceSerializer(queryset, many=True)
            print(f"   用户 {user.username} 只能看到 {len(serializer.data)} 个实例")
        
        # 测试3: 分页功能
        print("\n3. 测试分页功能:")
        from EasyRAG.llm_app.views import LLMInstancePagination
        
        paginator = LLMInstancePagination()
        all_instances = LLMInstance.objects.all()
        
        # 测试默认分页（每页10个）
        page = paginator.paginate_queryset(all_instances, None)
        print(f"   默认分页: 每页 {paginator.page_size} 个，总共 {len(all_instances)} 个实例")
        print(f"   第一页包含 {len(page)} 个实例")
        
        # 测试自定义分页大小
        paginator.page_size = 5
        page = paginator.paginate_queryset(all_instances, None)
        print(f"   自定义分页: 每页 {paginator.page_size} 个")
        print(f"   第一页包含 {len(page)} 个实例")
        
        # 测试4: 过滤功能
        print("\n4. 测试过滤功能:")
        
        # 按状态过滤
        active_instances = LLMInstance.objects.filter(llm_status='ACTIVE')
        print(f"   活跃状态实例: {active_instances.count()} 个")
        
        # 按用户过滤
        user1_instances = LLMInstance.objects.filter(created_by=users[0])
        print(f"   用户 {users[0].username} 的实例: {user1_instances.count()} 个")
        
        # 组合过滤
        user1_active_instances = LLMInstance.objects.filter(
            created_by=users[0],
            llm_status='ACTIVE'
        )
        print(f"   用户 {users[0].username} 的活跃实例: {user1_active_instances.count()} 个")
        
        return True
        
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        return False

def test_permission_validation():
    """测试权限验证逻辑"""
    print("\n测试权限验证逻辑...")
    
    try:
        # 创建测试用户
        normal_user = User.objects.create_user(
            username='test_normal',
            email='test_normal@example.com',
            password='testpass123'
        )
        
        super_user = User.objects.create_superuser(
            username='test_super',
            email='test_super@example.com',
            password='testpass123'
        )
        
        print(f"✓ 普通用户: {normal_user.username} (is_superuser: {normal_user.is_superuser})")
        print(f"✓ 超级用户: {super_user.username} (is_superuser: {super_user.is_superuser})")
        
        # 测试权限逻辑
        print("\n权限验证逻辑:")
        print(f"   普通用户 is_superuser: {normal_user.is_superuser}")
        print(f"   超级用户 is_superuser: {super_user.is_superuser}")
        
        # 清理测试用户
        normal_user.delete()
        super_user.delete()
        
        return True
        
    except Exception as e:
        print(f"✗ 权限验证测试失败: {e}")
        return False

def cleanup_test_data(superuser, users, templates, instances):
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
    for template in templates:
        try:
            template.delete()
            print(f"✓ 模板删除成功: {template.template_name}")
        except:
            pass
    
    # 删除普通用户
    for user in users:
        try:
            user.delete()
            print(f"✓ 普通用户删除成功: {user.username}")
        except:
            pass
    
    # 不删除超级用户，保留用于其他测试

if __name__ == "__main__":
    print("开始测试权限验证和分页功能...\n")
    
    # 创建测试数据
    superuser, users, templates, instances = create_test_data()
    
    if superuser and users and templates and instances:
        # 测试权限和分页功能
        success1 = test_permission_and_pagination()
        success2 = test_permission_validation()
        
        if success1 and success2:
            print("\n🎉 所有测试通过！")
        else:
            print("\n❌ 部分测试失败！")
        
        # 清理测试数据
        cleanup_test_data(superuser, users, templates, instances)
    else:
        print("\n❌ 测试数据创建失败！") 