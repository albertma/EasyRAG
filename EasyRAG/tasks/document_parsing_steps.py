from typing import Dict, Any, List, Optional
import logging
import tempfile
import os
from datetime import datetime
from io import BytesIO

from .base_workflow import WorkflowStep
from EasyRAG.rag_service.rag_comp_factory import RAGComponentFactory
from EasyRAG.common.rag_tokenizer import RagTokenizer
from EasyRAG.common.utils import generate_uuid
from EasyRAG.common.redis_utils import get_redis_instance, set_cache, get_cache, delete_cache

logger = logging.getLogger(__name__)


class InitializeStep(WorkflowStep):
    """初始化步骤"""
    
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行初始化"""
        self.update_progress(10, "初始化解析环境")
        
        try:
            # 获取文档信息
            document_id = context.get("document_id")
            if not document_id:
                raise ValueError("document_id is required")
            
            # 延迟导入，避免循环依赖
            from EasyRAG.task_app.models import Document
            document = Document.objects.get(document_id=document_id)
            
            # 更新文档状态
            document.status = "PROCESSING"
            document.progress = "0"
            document.progress_msg = "开始解析文档"
            document.progress_begin_at = datetime.now()
            document.save()
            
            # 初始化组件
            self.update_progress(30, "初始化文件存储和向量数据库")
            file_storage = RAGComponentFactory.instance().get_default_file_storage()
            
            # 获取知识库信息
            kb_id = document.knowledge_base.knowledge_base_id
            index_name = f"easyrag_{kb_id}"
            vector_database = RAGComponentFactory.instance().get_default_vector_database(index_name=index_name)
            
            # 更新上下文
            context.update({
                "document": document,
                "file_storage": file_storage,
                "vector_database": vector_database,
                "kb_id": str(kb_id),
                "index_name": index_name,
                "temp_files": []
            })
            
            self.update_progress(50, "初始化完成")
            return context
            
        except Exception as e:
            logger.error(f"初始化失败: {e}")
            raise


class OCRStep(WorkflowStep):

    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行OCR"""
        logger.info(f"执行OCR: {context}")
        self.update_progress(10, "执行OCR")
        
        return context


class GetFileContentStep(WorkflowStep):
    """获取文件内容步骤"""
    
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """获取文件内容"""
        self.update_progress(10, "获取文件内容")
        
        try:
            document = context.get("document")
            file_storage = context.get("file_storage")
            
            if not document or not file_storage:
                raise ValueError("document and file_storage are required")
            
            # 从文件存储获取文件内容
            file_location = document.document_location
            bucket_name = str(document.knowledge_base.knowledge_base_id)
            
            self.update_progress(30, f"从存储获取文件: {file_location}")
            file_content = file_storage.get_file_content(
                bucket_name=bucket_name,
                file_path=file_location
            )
            
            if not file_content:
                raise ValueError(f"无法获取文件内容: {file_location}")
            
            # 缓存文件内容
            cache_key = f"file_content_{document.document_id}"
            set_cache(cache_key, file_content, expire=3600)  # 1小时过期
            
            self.update_progress(80, "文件内容获取完成")
            
            context["file_content"] = file_content
            return context
            
        except Exception as e:
            logger.error(f"获取文件内容失败: {e}")
            raise


class ParseFileStep(WorkflowStep):
    """解析文件步骤"""
    
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """解析文件内容"""
        self.update_progress(10, "开始解析文件")
        
        try:
            document = context.get("document")
            file_content = context.get("file_content")
            
            if not document or not file_content:
                raise ValueError("document and file_content are required")
            
            file_type = document.parser_config.get("file_type", "pdf").lower()
            
            self.update_progress(20, f"使用解析器处理文件类型: {file_type}")
            
            # 根据文件类型选择解析方法
            if file_type.endswith("pdf"):
                result = self._parse_pdf(document, context, file_content)
            elif file_type.endswith(("word", "ppt", "txt", "md", "html")):
                result = self._parse_office_document(document, context, file_content)
            elif file_type.endswith("excel"):
                result = self._parse_excel(context, file_content)
            elif file_type.endswith("visual"):
                result = self._parse_visual(document, context, file_content)
            else:
                raise NotImplementedError(f"不支持的文件类型: {file_type}")
            
            # 缓存解析结果
            cache_key = f"parse_result_{document.document_id}"
            set_cache(cache_key, result, expire=7200)  # 2小时过期
            
            self.update_progress(80, "文件解析完成")
            
            context.update(result)
            return context
            
        except Exception as e:
            logger.error(f"解析文件失败: {e}")
            raise
    
    def _parse_pdf(self, document, file_content: bytes) -> Dict[str, Any]:
        """解析PDF文件"""
        from magic_pdf.data.data_reader_writer import FileBasedDataReader, FileBasedDataWriter
        from magic_pdf.data.dataset import PymuDocDataset
        from magic_pdf.model.doc_analyze_by_custom_model import doc_analyze
        from magic_pdf.config.enums import SupportedPdfParseMethod
        
        # 创建临时PDF文件
        temp_dir = tempfile.gettempdir()
        temp_pdf_path = os.path.join(temp_dir, f"{document.document_id}.pdf")
        context["temp_files"].append(temp_pdf_path)
        
        with open(temp_pdf_path, "wb") as f:
            f.write(file_content)
        
        # 使用MinerU处理
        reader = FileBasedDataReader("")
        pdf_bytes = reader.read_pdf(temp_pdf_path)
        ds = PymuDocDataset(pdf_bytes)
        
        # 判断是否需要OCR
        is_ocr = ds.classify() == SupportedPdfParseMethod.OCR
        mode_msg = "OCR模式" if is_ocr else "文本模式"
        
        infer_result = ds.apply(doc_analyze, ocr=is_ocr)
        
        # 设置临时输出目录
        temp_image_dir = os.path.join(temp_dir, f"images_{document.document_id}")
        os.makedirs(temp_image_dir, exist_ok=True)
        context["temp_files"].append(temp_image_dir)
        
        image_writer = FileBasedDataWriter(temp_image_dir)
        
        # 处理结果
        pipe_result = infer_result.pipe_ocr_mode(image_writer) if is_ocr else infer_result.pipe_text_mode(image_writer)
        
        # 提取内容
        content_list = pipe_result.get_content_list(os.path.basename(temp_pdf_path))
        middle_content = pipe_result.get_middle_json()
        middle_json_content = infer_result.to_json(temp_dir, f"{document.document_id}.json")
        
        return {
            "content_list": content_list,
            "middle_content": middle_content,
            "middle_json_content": middle_json_content,
            "image_info_list": []
        }
    
    def _parse_office_document(self, document, file_content: bytes) -> Dict[str, Any]:
        """解析Office文档"""
        from magic_pdf.data.read_api import read_local_office
        from magic_pdf.model.doc_analyze_by_custom_model import doc_analyze
        from magic_pdf.data.data_reader_writer import FileBasedDataWriter
        
        # 创建临时文件
        temp_dir = tempfile.gettempdir()
        file_extension = os.path.splitext(document.document_location)[1]
        temp_file_path = os.path.join(temp_dir, f"{document.document_id}{file_extension}")
        context["temp_files"].append(temp_file_path)
        
        with open(temp_file_path, "wb") as f:
            f.write(file_content)
        
        # 使用MinerU处理
        ds = read_local_office(temp_file_path)[0]
        infer_result = ds.apply(doc_analyze, ocr=True)
        
        # 设置临时输出目录
        temp_image_dir = os.path.join(temp_dir, f"images_{document.document_id}")
        os.makedirs(temp_image_dir, exist_ok=True)
        context["temp_files"].append(temp_image_dir)
        
        image_writer = FileBasedDataWriter(temp_image_dir)
        
        # 处理结果
        pipe_result = infer_result.pipe_text_mode(image_writer)
        
        # 提取内容
        content_list = pipe_result.get_content_list(os.path.basename(temp_file_path))
        middle_content = pipe_result.get_middle_json()
        middle_json_content = infer_result.to_json(temp_dir, f"{document.document_id}.json")
        
        return {
            "content_list": content_list,
            "middle_content": middle_content,
            "middle_json_content": middle_json_content,
            "image_info_list": []
        }
    
    def _parse_excel(self, file_content: bytes) -> Dict[str, Any]:
        """解析Excel文件"""
        from EasyRAG.file_parser import excel_parser
        
        # 创建临时文件
        temp_dir = tempfile.gettempdir()
        temp_excel_path = os.path.join(temp_dir, f"temp_excel_{generate_uuid()}.xlsx")
        context["temp_files"].append(temp_excel_path)
        
        with open(temp_excel_path, "wb") as f:
            f.write(file_content)
        
        # 使用excel_parser解析
        content_list = excel_parser.parse_excel(temp_excel_path)
        
        return {
            "content_list": content_list,
            "middle_content": "",
            "middle_json_content": {},
            "image_info_list": []
        }
    
    def _parse_visual(self, document, file_content: bytes) -> Dict[str, Any]:
        """解析视觉文件"""
        from magic_pdf.data.read_api import read_local_images
        from magic_pdf.model.doc_analyze_by_custom_model import doc_analyze
        from magic_pdf.data.data_reader_writer import FileBasedDataWriter
        
        # 创建临时文件
        temp_dir = tempfile.gettempdir()
        file_extension = os.path.splitext(document.document_location)[1]
        temp_image_path = os.path.join(temp_dir, f"{document.document_id}{file_extension}")
        context["temp_files"].append(temp_image_path)
        
        with open(temp_image_path, "wb") as f:
            f.write(file_content)
        
        # 使用MinerU处理
        ds = read_local_images(temp_image_path)[0]
        infer_result = ds.apply(doc_analyze, ocr=True)
        
        # 判断是否需要OCR
        from magic_pdf.config.enums import SupportedPdfParseMethod
        is_ocr = ds.classify() == SupportedPdfParseMethod.OCR
        
        # 设置临时输出目录
        temp_image_dir = os.path.join(temp_dir, f"images_{document.document_id}")
        os.makedirs(temp_image_dir, exist_ok=True)
        context["temp_files"].append(temp_image_dir)
        
        image_writer = FileBasedDataWriter(temp_image_dir)
        
        # 处理结果
        pipe_result = infer_result.pipe_ocr_mode(image_writer) if is_ocr else infer_result.pipe_txt_mode(image_writer)
        
        # 提取内容
        content_list = pipe_result.get_content_list(os.path.basename(temp_image_path))
        middle_content = pipe_result.get_middle_json()
        middle_json_content = json.loads(middle_content)
        
        return {
            "content_list": content_list,
            "middle_content": middle_content,
            "middle_json_content": middle_json_content,
            "image_info_list": []
        }


class ExtractBlocksStep(WorkflowStep):
    """提取块信息步骤"""
    
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """提取块信息"""
        self.update_progress(10, "提取块信息")
        
        try:
            middle_json_content = context.get("middle_json_content")
            if not middle_json_content:
                raise ValueError("middle_json_content is required")
            
            self.update_progress(30, "分析文档结构")
            block_info_list = self._extract_block_info(middle_json_content)
            
            self.update_progress(60, "生成块信息")
            
            # 缓存块信息
            document_id = context.get("document").document_id
            cache_key = f"block_info_{document_id}"
            set_cache(cache_key, block_info_list, expire=7200)  # 2小时过期
            
            self.update_progress(80, f"提取了{len(block_info_list)}个块信息")
            
            context["block_info_list"] = block_info_list
            return context
            
        except Exception as e:
            logger.error(f"提取块信息失败: {e}")
            raise
    
    def _extract_block_info(self, middle_json_content: Dict) -> List[Dict[str, Any]]:
        """从中间结果中提取块信息"""
        block_info_list = []
        
        # 这里实现具体的块信息提取逻辑
        # 根据middle_json_content的结构来提取页面、位置等信息
        
        return block_info_list


class ProcessChunksStep(WorkflowStep):
    """处理文本块步骤"""
    
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """处理文本块"""
        self.update_progress(10, "开始处理文本块")
        
        try:
            content_list = context.get("content_list", [])
            block_info_list = context.get("block_info_list", [])
            vector_database = context.get("vector_database")
            file_storage = context.get("file_storage")
            kb_id = context.get("kb_id")
            
            if not content_list:
                raise ValueError("content_list is required")
            
            self.update_progress(20, "创建向量索引")
            self._create_vector_index(vector_database, context.get("index_name"))
            
            chunk_count = 0
            chunk_ids_list = []
            image_info_list = []
            
            total_chunks = len(content_list)
            for chunk_idx, chunk_data in enumerate(content_list):
                self.update_progress(30 + (chunk_idx / total_chunks) * 60, 
                                   f"处理第{chunk_idx + 1}/{total_chunks}个块")
                
                try:
                    # 获取块信息
                    page_idx, bbox = self._get_chunk_info(chunk_idx, block_info_list)
                    
                    # 处理不同类型的块
                    if chunk_data["type"] in ["text", "table", "equation"]:
                        content = self._extract_text_content(chunk_data)
                        if content:
                            # 获取向量嵌入
                            vector = self._get_embedding(context, content)
                            
                            # 存储块
                            chunk_id = self._store_chunk(
                                context, kb_id, page_idx, bbox, content, vector
                            )
                            chunk_ids_list.append(chunk_id)
                            chunk_count += 1
                            
                    elif chunk_data["type"] == "image":
                        image_info = self._process_image_chunk(
                            chunk_data, file_storage, kb_id, chunk_count
                        )
                        if image_info:
                            image_info_list.append(image_info)
                            
                except Exception as e:
                    logger.error(f"处理块 {chunk_idx} 失败: {e}")
                    continue
            
            self.update_progress(90, f"处理完成，共生成{chunk_count}个文本块")
            
            # 缓存处理结果
            document_id = context.get("document").document_id
            cache_key = f"chunk_result_{document_id}"
            set_cache(cache_key, (chunk_count, chunk_ids_list), expire=7200)
            
            context.update({
                "chunk_count": chunk_count,
                "chunk_ids_list": chunk_ids_list,
                "image_info_list": image_info_list
            })
            
            return context
            
        except Exception as e:
            logger.error(f"处理文本块失败: {e}")
            raise
    
    def _create_vector_index(self, vector_database, index_name: str):
        """创建向量索引"""
        creator = context.get("document").created_by
        index_name = f"easyrag_{creator}"
        
        body = {
            "settings": {"number_of_replicas": 0},
            "mappings": {
                "properties": {
                    "doc_id": {"type": "keyword"},
                    "kb_id": {"type": "keyword"},
                    "content_with_weight": {"type": "text"},
                    "q_1024_vec": {"type": "dense_vector", "dims": 1024}
                }
            }
        }
        
        vector_database.create_index(index_name=index_name, body=body)
    
    def _get_chunk_info(self, chunk_idx: int, block_info_list: List[Dict]) -> tuple:
        """获取块信息"""
        page_idx = 0
        bbox = [0, 0, 0, 0]
        
        if chunk_idx < len(block_info_list):
            block_info = block_info_list[chunk_idx]
            page_idx = block_info.get("page_idx", 0)
            bbox = block_info.get("bbox", [0, 0, 0, 0])
            
        return page_idx, bbox
    
    def _extract_text_content(self, chunk_data: Dict) -> Optional[str]:
        """提取文本内容"""
        if chunk_data["type"] == "text":
            content = chunk_data.get("text", "").strip()
        elif chunk_data["type"] == "equation":
            content = chunk_data.get("text", "").strip()
        elif chunk_data["type"] == "table":
            caption_list = chunk_data.get("table_caption", [])
            table_body = chunk_data.get("table_body", "")
            
            if isinstance(caption_list, list):
                caption_str = " ".join(caption_list)
            elif isinstance(caption_list, str):
                caption_str = caption_list
            else:
                caption_str = ""
                
            content = caption_str + table_body
        else:
            return None
            
        return content if content else None
    
    def _get_embedding(self, context: Dict[str, Any], content: str) -> List[float]:
        """获取文本嵌入向量"""
        import requests
        
        # 从文档配置中获取嵌入模型配置
        parser_config = context.get("document").parser_config
        embedding_config = parser_config.get("embedding_config", {})
        
        embedding_model_name = embedding_config.get("llm_name", "bge-m3")
        if "___" in embedding_model_name:
            embedding_model_name = embedding_model_name.split("___")[0]
        
        embedding_api_base = embedding_config.get("api_base", "https://api.siliconflow.cn/v1/embeddings")
        embedding_api_key = embedding_config.get("api_key")
        
        # 构建API URL
        if not embedding_api_base.startswith(("http://", "https://")):
            embedding_api_base = "https://" + embedding_api_base
        
        normalized_base_url = embedding_api_base.rstrip("/")
        if normalized_base_url.endswith("/v1"):
            embedding_url = normalized_base_url + "/embeddings"
        elif normalized_base_url.endswith("/embeddings"):
            embedding_url = normalized_base_url
        else:
            embedding_url = normalized_base_url + "/v1/embeddings"
        
        # 发送请求
        headers = {"Content-Type": "application/json"}
        if embedding_api_key:
            headers["Authorization"] = f"Bearer {embedding_api_key}"
            
        data = {
            "model": embedding_model_name,
            "input": content
        }
        
        response = requests.post(embedding_url, headers=headers, json=data, timeout=15)
        response.raise_for_status()
        
        embedding_data = response.json()
        vector = embedding_data["data"][0]["embedding"]
        
        if len(vector) != 1024:
            raise ValueError(f"向量维度不正确: {len(vector)}, 期望1024")
            
        return vector
    
    def _store_chunk(self, context: Dict[str, Any], kb_id: str, page_idx: int, 
                    bbox: List[float], content: str, vector: List[float]) -> str:
        """存储文本块"""
        chunk_id = generate_uuid()
        file_storage = context.get("file_storage")
        vector_database = context.get("vector_database")
        document = context.get("document")
        
        # 存储到文件存储
        file_storage.fput_object(
            bucket_name=kb_id,
            object_name=chunk_id,
            data=BytesIO(content.encode("utf-8")),
            length=len(content.encode("utf-8"))
        )
        
        # 准备ES文档
        chunk_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        chunk_timestamp = datetime.now().timestamp()
        x1, y1, x2, y2 = bbox
        bbox_reordered = [x1, x2, y1, y2]
        
        # 使用分词器
        tokenizer = RagTokenizer()
        
        es_doc = {
            "doc_id": str(document.document_id),
            "kb_id": str(kb_id),
            "docnm_kwd": document.document_name,
            "title_tks": tokenizer.tokenize(document.document_name),
            "title_sm_tks": tokenizer.tokenize(document.document_name),
            "content_ltks": tokenizer.tokenize(content),
            "content_sm_ltks": tokenizer.tokenize(content),
            "page_num_int": [page_idx + 1],
            "position_int": [[page_idx + 1] + bbox_reordered],
            "top_int": [1],
            "create_time": chunk_time,
            "create_timestamp_flt": chunk_timestamp,
            "img_id": "",
            "q_1024_vec": vector,
        }
        
        # 存储到向量数据库
        creator = document.created_by
        index_name = f"easyrag_{creator}"
        vector_database.index(index_name=index_name, id=chunk_id, document=es_doc)
        
        return chunk_id
    
    def _process_image_chunk(self, chunk_data: Dict, file_storage, kb_id: str, 
                           chunk_count: int) -> Optional[Dict[str, Any]]:
        """处理图片块"""
        img_path_relative = chunk_data.get("img_path")
        if not img_path_relative:
            return None
        
        # 查找对应的临时图片文件
        temp_files = context.get("temp_files", [])
        temp_image_dir = None
        for temp_file in temp_files:
            if "images_" in temp_file and os.path.isdir(temp_file):
                temp_image_dir = temp_file
                break
        
        if not temp_image_dir:
            return None
        
        img_path_abs = os.path.join(temp_image_dir, img_path_relative)
        if not os.path.exists(img_path_abs):
            logger.warning(f"图片文件不存在: {img_path_abs}")
            return None
        
        # 上传图片
        img_id = generate_uuid()
        img_ext = os.path.splitext(img_path_abs)[1]
        img_key = f"images/{img_id}{img_ext}"
        content_type = f"image/{img_ext[1:].lower()}"
        if content_type == "image/jpeg":
            content_type = "image/jpg"
        
        try:
            file_storage.fput_object(
                bucket_name=kb_id,
                object_name=img_key,
                file_path=img_path_abs,
                content_type=content_type,
            )
            
            # 设置访问策略
            policy = {
                "Version": "2012-10-17",
                "Statement": [{
                    "Effect": "Allow",
                    "Principal": {"AWS": ["*"]},
                    "Action": ["s3:GetObject"],
                    "Resource": [f"arn:aws:s3:::{kb_id}/*"]
                }]
            }
            file_storage.set_bucket_policy(kb_id, json.dumps(policy))
            
            # 生成访问URL
            from EasyRAG import settings
            minio_endpoint = settings.MINIO_CONFIG.get("endpoint")
            use_ssl = settings.MINIO_CONFIG.get("secure", False)
            protocol = "https" if use_ssl else "http"
            img_url = f"{protocol}://{minio_endpoint}/{kb_id}/{img_key}"
            
            return {
                "url": img_url,
                "position": chunk_count
            }
            
        except Exception as e:
            logger.error(f"上传图片失败: {e}")
            return None


class UpdateFinalStatusStep(WorkflowStep):
    """更新最终状态步骤"""
    
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """更新最终状态"""
        self.update_progress(10, "更新文档状态")
        
        try:
            document = context.get("document")
            chunk_count = context.get("chunk_count", 0)
            
            if not document:
                raise ValueError("document is required")
            
            # 更新文档状态
            document.status = "COMPLETED"
            document.progress = "100"
            document.progress_msg = f"解析完成，共生成{chunk_count}个文本块"
            document.chunk_num = chunk_count
            document.save()
            
            # 更新知识库统计
            knowledge_base = document.knowledge_base
            knowledge_base.chunk_num += chunk_count
            knowledge_base.save()
            
            self.update_progress(50, "清理临时文件")
            
            # 清理临时文件
            temp_files = context.get("temp_files", [])
            for temp_file in temp_files:
                try:
                    if os.path.isfile(temp_file):
                        os.remove(temp_file)
                    elif os.path.isdir(temp_file):
                        import shutil
                        shutil.rmtree(temp_file)
                except Exception as e:
                    logger.warning(f"清理临时文件失败 {temp_file}: {e}")
            
            # 清理缓存
            document_id = document.document_id
            delete_cache(f"file_content_{document_id}")
            delete_cache(f"parse_result_{document_id}")
            delete_cache(f"block_info_{document_id}")
            delete_cache(f"chunk_result_{document_id}")
            
            self.update_progress(100, "文档解析完成")
            
            return context
            
        except Exception as e:
            logger.error(f"更新最终状态失败: {e}")
            raise