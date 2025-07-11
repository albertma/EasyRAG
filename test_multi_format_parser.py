#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试多格式文档解析器
"""

import os
import tempfile
import json
from EasyRAG.file_parser.ppt_word_txt_md_html_parser import PPTWordTxtMDHTMLParser


def create_test_files():
    """创建测试文件"""
    test_files = {}
    
    # 创建测试文本文件
    temp_dir = tempfile.gettempdir()
    
    # 1. 创建测试TXT文件
    txt_content = """这是一个测试文本文件。
包含中文和English混合内容。
支持多行文本和特殊字符：@#$%^&*()
"""
    txt_path = os.path.join(temp_dir, "test_document.txt")
    with open(txt_path, 'w', encoding='utf-8') as f:
        f.write(txt_content)
    
    with open(txt_path, 'rb') as f:
        test_files['txt'] = {
            'file_name': 'test_document.txt',
            'file_content': f.read()
        }
    
    # 2. 创建测试Markdown文件
    md_content = """# 测试Markdown文档

这是一个**测试**的Markdown文件。

## 功能特性

- 支持标题
- 支持列表
- 支持**粗体**和*斜体*

### 代码示例

```python
def hello_world():
    print("Hello, World!")
```

> 这是一个引用块
"""
    md_path = os.path.join(temp_dir, "test_document.md")
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(md_content)
    
    with open(md_path, 'rb') as f:
        test_files['md'] = {
            'file_name': 'test_document.md',
            'file_content': f.read()
        }
    
    # 3. 创建测试HTML文件
    html_content = """<!DOCTYPE html>
<html>
<head>
    <title>测试HTML文档</title>
</head>
<body>
    <h1>测试HTML文档</h1>
    <p>这是一个测试的HTML文件。</p>
    <p>包含<strong>粗体</strong>和<em>斜体</em>文本。</p>
    <img src="test.jpg" alt="测试图片" />
    <ul>
        <li>列表项1</li>
        <li>列表项2</li>
    </ul>
</body>
</html>
"""
    html_path = os.path.join(temp_dir, "test_document.html")
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    with open(html_path, 'rb') as f:
        test_files['html'] = {
            'file_name': 'test_document.html',
            'file_content': f.read()
        }
    
    return test_files


def test_parser():
    """测试解析器"""
    print("开始测试多格式文档解析器...")
    
    # 创建解析器实例
    parser = PPTWordTxtMDHTMLParser()
    
    # 创建测试文件
    test_files = create_test_files()
    
    # 测试配置
    config = {
        'output_format': 'markdown',
        'enable_ocr': True,
        'enable_formula': True,
        'ocr_lang': 'ch',
        'debug_mode': False
    }
    
    # 测试每种文件类型
    for file_type, file_info in test_files.items():
        print(f"\n=== 测试 {file_type.upper()} 文件解析 ===")
        
        # 模拟文档信息
        doc_info = {
            'doc_id': f'test_{file_type}_doc',
            'file_name': file_info['file_name']
        }
        
        # 模拟知识库信息
        knowledge_base_info = {
            'kb_id': 'test_kb',
            'kb_name': '测试知识库'
        }
        
        try:
            # 执行解析
            result = parser.parse(doc_info, file_info, knowledge_base_info, config)
            
            # 输出结果
            print(f"解析成功: {result['success']}")
            if result['success']:
                print(f"内容长度: {len(result['content'])} 字符")
                print(f"元数据: {json.dumps(result['metadata'], ensure_ascii=False, indent=2)}")
                print("内容预览:")
                print(result['content'][:200] + "..." if len(result['content']) > 200 else result['content'])
            else:
                print(f"解析失败: {result['error']}")
                
        except Exception as e:
            print(f"测试过程中出现异常: {e}")
    
    print("\n=== 测试完成 ===")


def test_magic_pdf_integration():
    """测试magic_pdf集成"""
    print("\n=== 测试magic_pdf集成 ===")
    
    try:
        # 检查magic_pdf是否可用
        from magic_pdf.pdf_parse_union_core_v2 import pdf_parse_union
        from magic_pdf.data.data_reader_writer import FileBasedDataReader, FileBasedDataWriter
        from magic_pdf.data.dataset import PymuDocDataset
        from magic_pdf.config.enums import SupportedPdfParseMethod
        
        print("✓ magic_pdf模块导入成功")
        
        # 测试文件类型检测
        temp_dir = tempfile.gettempdir()
        test_file = os.path.join(temp_dir, "test_magic_pdf.txt")
        
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write("测试magic_pdf集成")
        
        try:
            reader = FileBasedDataReader("")
            file_bytes = reader.read(test_file)
            ds = PymuDocDataset(file_bytes)
            parse_method = ds.classify()
            
            print(f"✓ 文件类型检测成功: {parse_method.value}")
            
        except Exception as e:
            print(f"✗ 文件类型检测失败: {e}")
        
        # 清理测试文件
        try:
            os.remove(test_file)
        except:
            pass
            
    except ImportError as e:
        print(f"✗ magic_pdf模块不可用: {e}")
        print("请安装magic_pdf: pip install magic-pdf")


if __name__ == "__main__":
    # 运行基本测试
    test_parser()
    
    # 运行magic_pdf集成测试
    test_magic_pdf_integration() 