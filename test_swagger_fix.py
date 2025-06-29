#!/usr/bin/env python3
"""
测试Swagger修复和API端点
"""
import requests
import json

def test_swagger_access():
    """测试Swagger页面访问"""
    try:
        response = requests.get('http://localhost:8000/swagger/')
        print(f"Swagger页面状态码: {response.status_code}")
        if response.status_code == 200:
            print("✅ Swagger页面访问成功")
            return True
        else:
            print("❌ Swagger页面访问失败")
            return False
    except Exception as e:
        print(f"❌ Swagger页面访问异常: {e}")
        return False

def test_api_endpoints():
    """测试API端点"""
    endpoints = [
        '/api/llm/llm-templates/',
        '/api/llm/llm-instances/',
        '/api/llm/llm-model-user-configs/',
    ]
    
    for endpoint in endpoints:
        try:
            response = requests.get(f'http://localhost:8000{endpoint}')
            print(f"{endpoint} 状态码: {response.status_code}")
            if response.status_code in [200, 401, 403]:  # 这些状态码表示端点存在
                print(f"✅ {endpoint} 端点正常")
            else:
                print(f"❌ {endpoint} 端点异常")
        except Exception as e:
            print(f"❌ {endpoint} 端点异常: {e}")

def test_swagger_schema():
    """测试Swagger schema生成"""
    try:
        response = requests.get('http://localhost:8000/swagger/?format=openapi')
        print(f"Swagger schema状态码: {response.status_code}")
        if response.status_code == 200:
            print("✅ Swagger schema生成成功")
            return True
        else:
            print("❌ Swagger schema生成失败")
            return False
    except Exception as e:
        print(f"❌ Swagger schema生成异常: {e}")
        return False

if __name__ == "__main__":
    print("开始测试Swagger修复...")
    print("=" * 50)
    
    # 测试Swagger页面访问
    swagger_ok = test_swagger_access()
    
    # 测试API端点
    print("\n测试API端点:")
    test_api_endpoints()
    
    # 测试Swagger schema
    print("\n测试Swagger schema:")
    schema_ok = test_swagger_schema()
    
    print("\n" + "=" * 50)
    if swagger_ok and schema_ok:
        print("🎉 所有测试通过！Swagger修复成功！")
    else:
        print("⚠️  部分测试失败，请检查修复") 