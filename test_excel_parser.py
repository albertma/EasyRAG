#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试Excel解析器
"""

import os
import json
from EasyRAG.file_parser.excel_parser import ExcelParser


def test_excel_parser():
    """测试Excel解析器"""
    print("开始测试Excel解析器...")
    
    # 文件路径
    excel_file = "/Users/albertma/sourcecode/workspace/python/EasyRAG/EasyRAG/data/test_excel.xls"
    
    # 创建解析器实例
    parser = ExcelParser()
    
    # 测试配置
    config = {
        'output_format': 'markdown',
        'enable_ocr': True,
        'enable_formula': True,
        'ocr_lang': 'ch',
        'debug_mode': False
    }
    
    print(f"=== 测试Excel文件 ===")
    print(f"文件路径: {excel_file}")
    
    # 检查文件是否存在
    if not os.path.exists(excel_file):
        print(f"❌ 文件不存在: {excel_file}")
        return
    
    try:
        # 读取文件内容
        with open(excel_file, 'rb') as f:
            file_content = f.read()
        
        print(f"✅ 文件读取成功，大小: {len(file_content)} 字节")
        
        # 准备文档信息
        doc_info = {
            'doc_id': 'test_excel_doc',
            'file_name': 'test_excel.xls'
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
            output_file = "parsed_excel.txt"
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(result['content'])
            print(f"解析结果已保存到: {output_file}")
            
            # 显示内容预览
            print("\n内容预览:")
            preview = result['content'][:1000] + "..." if len(result['content']) > 1000 else result['content']
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
    
    excel_file = "/Users/albertma/sourcecode/workspace/python/EasyRAG/EasyRAG/data/test_excel.xls"
    
    print(f"Excel文件:")
    if os.path.exists(excel_file):
        size = os.path.getsize(excel_file)
        print(f"  ✅ 存在")
        print(f"  📁 路径: {excel_file}")
        print(f"  📊 大小: {size} 字节 ({size/1024:.1f} KB)")
        
        # 获取文件扩展名
        ext = os.path.splitext(excel_file)[1].lower()
        print(f"  📄 类型: {ext}")
        
        # 尝试使用pandas预览文件结构
        try:
            import pandas as pd
            excel_data = pd.read_excel(excel_file, sheet_name=None)
            print(f"  📋 工作表数量: {len(excel_data)}")
            for sheet_name, df in excel_data.items():
                print(f"    - {sheet_name}: {len(df)} 行 x {len(df.columns)} 列")
        except Exception as e:
            print(f"  ⚠️  无法预览文件结构: {e}")
    else:
        print(f"  ❌ 文件不存在")


def test_pandas_import():
    """测试pandas导入"""
    print("\n=== 测试pandas导入 ===")
    try:
        import pandas as pd
        print("✅ pandas导入成功")
        
        # 测试Excel读取
        excel_file = "/Users/albertma/sourcecode/workspace/python/EasyRAG/EasyRAG/data/test_excel.xls"
        if os.path.exists(excel_file):
            excel_data = pd.read_excel(excel_file, sheet_name=None)
            print(f"✅ Excel文件读取成功，共 {len(excel_data)} 个工作表")
            
            # 显示第一个工作表的前几行
            if excel_data:
                first_sheet_name = list(excel_data.keys())[0]
                first_df = excel_data[first_sheet_name]
                print(f"第一个工作表 '{first_sheet_name}' 的前3行:")
                print(first_df.head(3))
        else:
            print("❌ 测试文件不存在")
            
    except ImportError as e:
        print(f"❌ pandas导入失败: {e}")
        print("请安装pandas: pip install pandas openpyxl")


if __name__ == "__main__":
    # 显示文件信息
    test_file_info()
    
    # 测试pandas导入
    test_pandas_import()
    
    # 测试Excel解析器
    test_excel_parser() 