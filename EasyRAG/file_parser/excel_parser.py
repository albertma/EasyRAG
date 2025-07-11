import os
import tempfile
import json
from typing import Any, Dict, List
import pandas as pd
from EasyRAG.file_parser.document_parser import DocumentParser


class ExcelParser(DocumentParser):
    """
    解析Excel文件，支持多种格式和图片提取
    """
    def __init__(self):
        super().__init__()
        self._setup_magic_pdf_config()
    
    def _setup_magic_pdf_config(self):
        """设置 magic_pdf 配置文件"""
        try:
            # 创建 magic_pdf 配置文件
            config_dir = os.path.expanduser("~")
            config_file = os.path.join(config_dir, "magic-pdf.json")
            
            if not os.path.exists(config_file):
                # 创建默认配置，优化Excel文档支持
                default_config = {
                    "latex_delimiters": {
                        "inline": ["$", "$"],
                        "display": ["$$", "$$"]
                    },
                    "output_format": "markdown",
                    "enable_ocr": True,
                    "enable_formula": True,
                    "latex-delimiter-config": {
                        "inline": ["$", "$"],
                        "display": ["$$", "$$"]
                    },
                    # OCR 相关配置
                    "ocr_config": {
                        "lang": "ch",  # 中文优先
                        "detect_orientation": True,
                        "preprocessing": True,
                        "confidence_threshold": 0.5
                    },
                    # 图片处理配置
                    "image_config": {
                        "extract_images": True,
                        "image_quality": "high",
                        "image_format": "png"
                    },
                    # Excel特定配置
                    "excel_config": {
                        "extract_tables": True,
                        "extract_images": True,
                        "extract_charts": True,
                        "preserve_formatting": True,
                        "handle_merged_cells": True
                    }
                }
                
                with open(config_file, 'w', encoding='utf-8') as f:
                    json.dump(default_config, f, indent=2, ensure_ascii=False)
                    
        except Exception as e:
            print(f"警告: 无法创建 magic_pdf 配置文件: {e}")
    
    def parse(self, doc_info: Dict[str, Any], 
              file_info: Dict[str, Any], 
              knowledge_base_info: Dict[str, Any], 
              config: Dict[str, Any]):
        """
        解析Excel文件
        
        Args:
            doc_info: 文档信息
            file_info: 文件信息，包含 file_content
            knowledge_base_info: 知识库信息
            config: 解析配置
            
        Returns:
            解析结果
        """
        try:
            # 获取文件扩展名
            file_name = doc_info.get('file_name', 'unknown')
            file_extension = self._get_file_extension(file_name)
            
            # 创建临时文件
            temp_dir = tempfile.gettempdir()
            temp_file_path = os.path.join(temp_dir, f"{doc_info.get('doc_id', 'temp')}{file_extension}")
            
            # 写入文件内容
            with open(temp_file_path, "wb") as f:
                f.write(file_info['file_content'])
            
            # 根据文件类型选择合适的解析方法
            result = self._parse_by_file_type(temp_file_path, file_extension, config)
            
            # 清理临时文件
            try:
                os.remove(temp_file_path)
            except:
                pass
            
            return result
            
        except Exception as e:
            print(f"Excel解析失败: {e}")
            return {
                'success': False,
                'error': str(e),
                'content': '',
                'metadata': {}
            }
    
    def _get_file_extension(self, file_name: str) -> str:
        """获取文件扩展名"""
        if '.' in file_name:
            return '.' + file_name.split('.')[-1].lower()
        return ''
    
    def _parse_by_file_type(self, file_path: str, file_extension: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        根据文件类型选择合适的解析方法
        
        Args:
            file_path: 文件路径
            file_extension: 文件扩展名
            config: 解析配置
            
        Returns:
            解析结果
        """
        file_extension = file_extension.lower()
        
        if file_extension in ['.xls', '.xlsx', '.xlsm', '.xlsb']:
            return self._parse_excel_file(file_path, config)
        else:
            # 尝试使用通用方法
            return self._parse_with_magic_pdf_generic(file_path, config)
    
    def _parse_excel_file(self, file_path: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        解析Excel文件
        
        Args:
            file_path: Excel文件路径
            config: 解析配置
            
        Returns:
            解析结果
        """
        try:
            # 使用pandas解析Excel文件
            excel_data = pd.read_excel(file_path, sheet_name=None)
            
            content = ""
            total_sheets = len(excel_data)
            total_tables = 0
            total_images = 0
            
            for sheet_name, df in excel_data.items():
                content += f"\n=== 工作表: {sheet_name} ===\n"
                
                # 处理表格数据
                if not df.empty:
                    # 获取表头
                    headers = df.columns.tolist()
                    
                    # 添加表头
                    content += "表头: " + " | ".join(str(col) for col in headers) + "\n\n"
                    
                    # 添加数据行
                    for idx, row in df.iterrows():
                        row_data = []
                        for col in headers:
                            cell_value = row[col]
                            # 处理NaN值
                            if pd.isna(cell_value):
                                cell_value = ""
                            row_data.append(str(cell_value))
                        content += " | ".join(row_data) + "\n"
                    
                    total_tables += 1
                    content += f"\n(共 {len(df)} 行数据)\n\n"
                else:
                    content += "空工作表\n\n"
                
                # 尝试提取图片信息（如果有的话）
                try:
                    # 这里可以添加图片提取逻辑
                    # 由于pandas不直接支持图片提取，我们标记为需要进一步处理
                    total_images += 0  # 暂时设为0，后续可以通过其他方法提取
                except Exception as e:
                    print(f"图片提取失败: {e}")
            
            return {
                'success': True,
                'content': content,
                'metadata': {
                    'file_type': 'excel',
                    'sheets': total_sheets,
                    'tables': total_tables,
                    'images': total_images,
                    'format': 'text',
                    'parser': 'pandas'
                }
            }
            
        except Exception as e:
            print(f"Excel文件解析失败，尝试使用magic_pdf: {e}")
            return self._parse_with_magic_pdf_generic(file_path, config)
    
    def _parse_with_magic_pdf_generic(self, file_path: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        使用magic_pdf通用方法解析文件，支持图片和影印文本
        
        Args:
            file_path: 文件路径
            config: 解析配置
            
        Returns:
            解析结果
        """
        try:
            # 导入magic_pdf相关模块
            from magic_pdf.pdf_parse_union_core_v2 import pdf_parse_union
            from magic_pdf.data.data_reader_writer import FileBasedDataReader, FileBasedDataWriter
            from magic_pdf.data.dataset import PymuDocDataset
            from magic_pdf.config.enums import SupportedPdfParseMethod
            
            # 读取文件
            reader = FileBasedDataReader("")
            file_bytes = reader.read(file_path)
            ds = PymuDocDataset(file_bytes)
            
            # 自动检测文件类型
            parse_method = ds.classify()
            is_ocr_needed = parse_method == SupportedPdfParseMethod.OCR
            
            print(f"文件类型检测结果: {parse_method.value} ({'需要OCR' if is_ocr_needed else '文本模式'})")
            
            # 设置输出目录
            temp_dir = tempfile.gettempdir()
            output_dir = os.path.join(temp_dir, f"magic_pdf_output_{os.path.basename(file_path)}")
            os.makedirs(output_dir, exist_ok=True)
            
            # 创建图片写入器
            image_writer = FileBasedDataWriter(output_dir)
            
            # 调用magic_pdf解析
            result = pdf_parse_union(
                model_list=[],  # 使用默认模型
                dataset=ds,
                imageWriter=image_writer,
                parse_mode=parse_method.value,
                debug_mode=config.get('debug_mode', False),
                lang=config.get('ocr_lang', 'ch')  # 默认中文
            )
            
            # 提取解析结果
            try:
                content_list = result.get_content_list(os.path.basename(file_path))
            except Exception as e:
                print(f"获取内容列表失败: {e}")
                content_list = []
            
            # 处理内容列表
            extracted_text = self._extract_text_from_content_list(content_list)
            
            return {
                'success': True,
                'content': extracted_text,
                'metadata': {
                    'parse_method': parse_method.value,
                    'ocr_enabled': is_ocr_needed,
                    'pages': len(content_list) if content_list else 0,
                    'format': config.get('output_format', 'markdown'),
                    'images_extracted': len([c for c in content_list if c.get('type') == 'image']) if content_list else 0,
                    'tables_extracted': len([c for c in content_list if c.get('type') == 'table']) if content_list else 0,
                    'equations_extracted': len([c for c in content_list if c.get('type') == 'equation']) if content_list else 0,
                    'parser': 'magic_pdf'
                }
            }
            
        except Exception as e:
            print(f"magic_pdf通用解析失败: {e}")
            return {
                'success': False,
                'error': str(e),
                'content': '',
                'metadata': {}
            }
    
    def _extract_text_from_content_list(self, content_list: list) -> str:
        """
        从内容列表中提取文本
        
        Args:
            content_list: 内容列表
            
        Returns:
            提取的文本
        """
        if not content_list:
            return ""
        
        extracted_text = ""
        
        for item in content_list:
            item_type = item.get('type', '')
            
            if item_type == 'text':
                text = item.get('text', '').strip()
                if text:
                    extracted_text += text + "\n\n"
                    
            elif item_type == 'table':
                # 处理表格
                caption = item.get('table_caption', '')
                body = item.get('table_body', '')
                
                if caption:
                    extracted_text += f"表格标题: {caption}\n"
                if body:
                    extracted_text += f"表格内容:\n{body}\n\n"
                    
            elif item_type == 'equation':
                # 处理公式
                equation = item.get('text', '').strip()
                if equation:
                    extracted_text += f"公式: {equation}\n\n"
                    
            elif item_type == 'image':
                # 处理图片描述
                img_path = item.get('img_path', '')
                if img_path:
                    extracted_text += f"[图片: {img_path}]\n\n"
        
        return extracted_text.strip()
    
    def get_step_status(self, doc_id: str, step: str) -> Dict[str, Any]:
        """
        获取指定步骤的状态
        
        Args:
            doc_id: 文档ID
            step: 步骤名称
            
        Returns:
            Dict[str, Any]: 步骤状态信息
        """
        return {
            'doc_id': doc_id,
            'step': step,
            'status': 'completed',
            'message': 'Excel解析步骤已完成'
        }

