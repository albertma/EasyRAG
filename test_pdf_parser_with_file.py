#!/usr/bin/env python3
"""
使用 test_document.pdf 测试 PDF 解析器
"""

import os
import sys
import json

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_pdf_parser_with_actual_file():
    """使用实际的 PDF 文件测试 PDF 解析器"""
    
    print("=== 使用 test_document.pdf 测试 PDF 解析器 ===")
    
    try:
        from EasyRAG.file_parser.pdf_parser import PDFParser
        
        # 创建 PDF 解析器
        parser = PDFParser()
        print("✓ PDF 解析器创建成功")
        
        # 读取测试 PDF 文件
        pdf_file_path = "EasyRAG/data/test_document.pdf"
        
        if not os.path.exists(pdf_file_path):
            print(f"✗ 测试文件不存在: {pdf_file_path}")
            return False
        
        print(f"✓ 找到测试文件: {pdf_file_path}")
        
        # 读取 PDF 文件内容
        with open(pdf_file_path, 'rb') as f:
            pdf_content = f.read()
        
        print(f"✓ PDF 文件大小: {len(pdf_content)} 字节")
        
        # 模拟文档信息
        doc_info = {
            'doc_id': 'test_doc_001',
            'name': '测试文档',
            'type': 'pdf'
        }
        
        # 模拟文件信息
        file_info = {
            'file_content': pdf_content
        }
        
        # 模拟知识库信息
        knowledge_base_info = {
            'kb_id': 'test_kb_001'
        }
        
        # 解析配置
        config = {
            'output_format': 'markdown',
            'enable_ocr': True,
            'enable_formula': True,
            'ocr_lang': 'ch',  # 中文
            'debug_mode': True
        }
        
        print("\n=== 开始解析 PDF ===")
        
        # 执行解析
        result = parser.parse(doc_info, file_info, knowledge_base_info, config)
        
        print("\n=== 解析结果 ===")
        print(f"成功: {result.get('success', False)}")
        
        if result.get('success'):
            print("✓ PDF 解析成功")
            
            # 显示元数据
            metadata = result.get('metadata', {})
            print(f"\n元数据:")
            print(f"  - 解析方法: {metadata.get('parse_method', 'unknown')}")
            print(f"  - OCR 启用: {metadata.get('ocr_enabled', False)}")
            print(f"  - 页数: {metadata.get('pages', 0)}")
            print(f"  - 输出格式: {metadata.get('format', 'unknown')}")
            
            # 显示解析内容（前500字符）
            content = result.get('content', '')
            if content:
                print(f"\n解析内容预览 (前500字符):")
                print("-" * 50)
                print(content[:500])
                if len(content) > 500:
                    print("...")
                print("-" * 50)
                print(f"总内容长度: {len(content)} 字符")
            else:
                print("⚠ 解析内容为空")
                
        else:
            print("✗ PDF 解析失败")
            error = result.get('error', '未知错误')
            print(f"错误信息: {error}")
            
        return result.get('success', False)
        
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("PDF 解析器实际文件测试")
    print("=" * 50)
    
    # 测试 PDF 解析器
    success = test_pdf_parser_with_actual_file()
    
    print("\n" + "=" * 50)
    print("测试结果:")
    print(f"  - PDF 解析器测试: {'✓ 成功' if success else '✗ 失败'}") 