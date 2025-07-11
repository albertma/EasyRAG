import os
import tempfile
import json
from typing import Any, Dict
from EasyRAG.file_parser.document_parser import DocumentParser


class PDFParser(DocumentParser):
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
                # 创建默认配置，优化 OCR 支持
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
                    }
                }
                
                with open(config_file, 'w', encoding='utf-8') as f:
                    json.dump(default_config, f, indent=2, ensure_ascii=False)
                    
        except Exception as e:
            print(f"警告: 无法创建 magic_pdf 配置文件: {e}")
    
    def parse(self, doc_info: Dict[str, Any], file_info: Dict[str, Any],
              knowledge_base_info: Dict[str, Any], config: Dict[str, Any]):
        """
        解析 PDF 文件，支持自动检测 PDF 类型
        
        Args:
            doc_info: 文档信息
            file_info: 文件信息，包含 file_content
            knowledge_base_info: 知识库信息
            config: 解析配置
            
        Returns:
            解析结果
        """
        try:
            # 创建临时文件
            temp_dir = tempfile.gettempdir()
            temp_pdf_path = os.path.join(temp_dir, f"{doc_info.get('doc_id', 'temp')}.pdf")
            
            # 写入 PDF 内容
            with open(temp_pdf_path, "wb") as f:
                f.write(file_info['file_content'])
            
            # 自动检测 PDF 类型并选择合适的解析方法
            result = self._parse_with_auto_detection(temp_pdf_path, config)
            
            # 清理临时文件
            try:
                os.remove(temp_pdf_path)
            except:
                pass
            
            return result
            
        except Exception as e:
            print(f"PDF 解析失败: {e}")
            # 返回错误结果
            return {
                'success': False,
                'error': str(e),
                'content': '',
                'metadata': {}
            }
    
    def _parse_with_auto_detection(self, pdf_path: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        自动检测 PDF 类型并选择合适的解析方法
        
        Args:
            pdf_path: PDF 文件路径
            config: 解析配置
            
        Returns:
            解析结果
        """
        try:
            # 首先尝试使用 magic_pdf 的自动检测功能
            result = self._parse_with_magic_pdf_auto(pdf_path, config)
            
            if result['success']:
                return result
            else:
                # 如果 magic_pdf 失败，尝试使用备用方法
                print(f"magic_pdf 解析失败，尝试备用方法: {result['error']}")
                return self._parse_with_pymupdf(pdf_path, config)
                
        except Exception as e:
            print(f"自动检测解析失败: {e}")
            # 尝试使用备用解析方法
            return self._parse_with_pymupdf(pdf_path, config)
    
    def _parse_with_magic_pdf_auto(self, pdf_path: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        使用 magic_pdf 自动检测并解析 PDF
        
        Args:
            pdf_path: PDF 文件路径
            config: 解析配置
            
        Returns:
            解析结果
        """
        try:
            # 导入 magic_pdf 相关模块
            from magic_pdf.pdf_parse_union_core_v2 import pdf_parse_union
            from magic_pdf.data.data_reader_writer import FileBasedDataReader, FileBasedDataWriter
            from magic_pdf.data.dataset import PymuDocDataset
            from magic_pdf.config.enums import SupportedPdfParseMethod
            
            # 读取 PDF 文件
            reader = FileBasedDataReader("")
            pdf_bytes = reader.read(pdf_path)
            ds = PymuDocDataset(pdf_bytes)
            
            # 自动检测 PDF 类型
            parse_method = ds.classify()
            is_ocr_needed = parse_method == SupportedPdfParseMethod.OCR
            
            print(f"PDF 类型检测结果: {parse_method.value} ({'需要OCR' if is_ocr_needed else '文本模式'})")
            
            # 设置输出目录
            temp_dir = tempfile.gettempdir()
            output_dir = os.path.join(temp_dir, f"magic_pdf_output_{os.path.basename(pdf_path)}")
            os.makedirs(output_dir, exist_ok=True)
            
            # 创建图片写入器
            image_writer = FileBasedDataWriter(output_dir)
            
            # 调用 magic_pdf 解析
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
                content_list = result.get_content_list(os.path.basename(pdf_path))
            except Exception as e:
                print(f"获取内容列表失败: {e}")
                content_list = []
            
            try:
                middle_content = result.get_middle_json()
            except Exception as e:
                print(f"获取中间内容失败: {e}")
                middle_content = {}
            
            try:
                middle_json_content = result.to_json(temp_dir, f"{os.path.basename(pdf_path)}.json")
            except Exception as e:
                print(f"保存JSON失败: {e}")
                middle_json_content = {}
            
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
                    'equations_extracted': len([c for c in content_list if c.get('type') == 'equation']) if content_list else 0
                }
            }
            
        except Exception as e:
            print(f"magic_pdf 自动检测解析失败: {e}")
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
    
    def _parse_with_magic_pdf(self, pdf_path: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        使用 magic_pdf 解析 PDF 文件（保持向后兼容）
        
        Args:
            pdf_path: PDF 文件路径
            config: 解析配置
            
        Returns:
            解析结果
        """
        try:
            # 导入 magic_pdf 核心模块
            from magic_pdf.pdf_parse_union_core_v2 import pdf_parse_union
            
            # 调用 magic_pdf 解析
            result = pdf_parse_union(
                pdf_path=pdf_path,
                output_format=config.get('output_format', 'markdown'),
                enable_ocr=config.get('enable_ocr', True),
                enable_formula=config.get('enable_formula', True)
            )
            
            return {
                'success': True,
                'content': result.get('content', ''),
                'metadata': {
                    'pages': result.get('pages', 0),
                    'format': config.get('output_format', 'markdown'),
                    'ocr_enabled': config.get('enable_ocr', True),
                    'formula_enabled': config.get('enable_formula', True)
                }
            }
            
        except Exception as e:
            print(f"magic_pdf 解析失败: {e}")
            # 尝试使用备用解析方法
            return self._parse_with_pymupdf(pdf_path, config)
    
    def _parse_with_pymupdf(self, pdf_path: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        使用 PyMuPDF 作为备用解析方法
        
        Args:
            pdf_path: PDF 文件路径
            config: 解析配置
            
        Returns:
            解析结果
        """
        try:
            import fitz  # PyMuPDF
            
            doc = fitz.open(pdf_path)
            content = ""
            page_count = len(doc)
            
            for page_num in range(page_count):
                page = doc.load_page(page_num)
                text = page.get_text()
                content += f"\n--- 第 {page_num + 1} 页 ---\n{text}\n"
            
            # 在关闭文档前获取页数
            doc.close()
            
            return {
                'success': True,
                'content': content,
                'metadata': {
                    'pages': page_count,
                    'format': 'text',
                    'parser': 'pymupdf',
                    'ocr_enabled': False,
                    'formula_enabled': False
                }
            }
            
        except Exception as e:
            print(f"PyMuPDF 解析也失败: {e}")
            return {
                'success': False,
                'error': f"所有解析方法都失败: {e}",
                'content': '',
                'metadata': {}
            }
    
    def get_step_status(self, doc_id: str, step: str) -> Dict[str, Any]:
        """
        获取指定步骤的状态
        
        Args:
            doc_id: 文档ID
            step: 步骤名称
            
        Returns:
            Dict[str, Any]: 步骤状态信息
        """
        # 对于 PDF 解析器，我们简化步骤状态
        return {
            'doc_id': doc_id,
            'step': step,
            'status': 'completed',
            'message': 'PDF 解析步骤已完成'
        }