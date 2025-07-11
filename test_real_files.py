#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试实际文件的解析功能
"""

import os
import json
from EasyRAG.file_parser.ppt_word_txt_md_html_parser import PPTWordTxtMDHTMLParser


def test_real_files():
    """测试实际文件"""
    print("开始测试实际文件解析...")
    
    # 文件路径
    ppt_file = "/Users/albertma/sourcecode/workspace/python/EasyRAG/EasyRAG/data/唯链Toolchain架构介绍.pptx"
    docx_file = "/Users/albertma/sourcecode/workspace/python/EasyRAG/EasyRAG/data/16关于申请将外马路1190号办公楼（1—4层及地下室）房产划拨区国资总公司的函（15.12.15）.docx"
    
    # 创建解析器实例
    parser = PPTWordTxtMDHTMLParser()
    
    # 测试配置
    config = {
        'output_format': 'markdown',
        'enable_ocr': True,
        'enable_formula': True,
        'ocr_lang': 'ch',
        'debug_mode': False
    }
    
    # 测试文件列表
    test_files = [
        {
            'name': 'PPT文件',
            'path': ppt_file,
            'file_name': '唯链Toolchain架构介绍.pptx'
        },
        {
            'name': 'Word文档',
            'path': docx_file,
            'file_name': '16关于申请将外马路1190号办公楼（1—4层及地下室）房产划拨区国资总公司的函（15.12.15）.docx'
        }
    ]
    
    for test_file in test_files:
        print(f"\n=== 测试 {test_file['name']} ===")
        print(f"文件路径: {test_file['path']}")
        
        # 检查文件是否存在
        if not os.path.exists(test_file['path']):
            print(f"❌ 文件不存在: {test_file['path']}")
            continue
        
        try:
            # 读取文件内容
            with open(test_file['path'], 'rb') as f:
                file_content = f.read()
            
            print(f"✅ 文件读取成功，大小: {len(file_content)} 字节")
            
            # 准备文档信息
            doc_info = {
                'doc_id': f'test_{test_file["name"]}_doc',
                'file_name': test_file['file_name']
            }
            
            # 准备文件信息
            file_info = {
                'file_content': file_content
            }
            
            # 准备知识库信息
            knowledge_base_info = {
                'kb_id': 'test_kb',
                'kb_name': '测试知识库'
            }
            
            # 执行解析
            print("开始解析...")
            result = parser.parse(doc_info, file_info, knowledge_base_info, config)
            
            # 输出结果
            print(f"解析成功: {result['success']}")
            if result['success']:
                print(f"内容长度: {len(result['content'])} 字符")
                print(f"元数据: {json.dumps(result['metadata'], ensure_ascii=False, indent=2)}")
                
                # 保存解析结果到文件
                output_file = f"parsed_{test_file['name']}.txt"
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(result['content'])
                print(f"解析结果已保存到: {output_file}")
                
                # 显示内容预览
                print("\n内容预览:")
                preview = result['content'][:500] + "..." if len(result['content']) > 500 else result['content']
                print(preview)
                
            else:
                print(f"解析失败: {result['error']}")
                
        except Exception as e:
            print(f"❌ 测试过程中出现异常: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n=== 测试完成 ===")


def test_file_info():
    """显示文件信息"""
    print("=== 文件信息 ===")
    
    files = [
        ("PPT文件", "/Users/albertma/sourcecode/workspace/python/EasyRAG/EasyRAG/data/唯链Toolchain架构介绍.pptx"),
        ("Word文档", "/Users/albertma/sourcecode/workspace/python/EasyRAG/EasyRAG/data/16关于申请将外马路1190号办公楼（1—4层及地下室）房产划拨区国资总公司的函（15.12.15）.docx")
    ]
    
    for name, path in files:
        print(f"\n{name}:")
        if os.path.exists(path):
            size = os.path.getsize(path)
            print(f"  ✅ 存在")
            print(f"  📁 路径: {path}")
            print(f"  📊 大小: {size} 字节 ({size/1024:.1f} KB)")
            
            # 获取文件扩展名
            ext = os.path.splitext(path)[1].lower()
            print(f"  📄 类型: {ext}")
        else:
            print(f"  ❌ 文件不存在")


if __name__ == "__main__":
    # 显示文件信息
    test_file_info()
    
    # 测试实际文件解析
    test_real_files() 