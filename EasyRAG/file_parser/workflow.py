from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Tuple, Callable
import logging
import tempfile
import os
import json
from datetime import datetime
from io import BytesIO
from enum import Enum

from EasyRAG.common.rag_comp_factory import RAGComponentFactory
from EasyRAG.common.redis_utils import delete_cache, get_cache, set_cache
from EasyRAG.common.utils import generate_uuid
from EasyRAG.common.rag_tokenizer import RagTokenizer
from EasyRAG.file_parser import excel_parser



class StepStatus(Enum):
    """步骤状态枚举"""
    PENDING = "PENDING"      # 待执行
    RUNNING = "RUNNING"      # 执行中
    COMPLETED = "COMPLETED"  # 已完成
    FAILED = "FAILED"        # 失败
    SKIPPED = "SKIPPED"      # 跳过


class WorkflowStep(Enum):
    """工作流步骤枚举"""
    INIT = "INIT"                    # 初始化
    GET_FILE_CONTENT = "GET_FILE_CONTENT"  # 获取文件内容
    PARSE_FILE = "PARSE_FILE"        # 解析文件
    EXTRACT_BLOCKS = "EXTRACT_BLOCKS"  # 提取块信息
    PROCESS_CHUNKS = "PROCESS_CHUNKS"  # 处理向量化和存储
    UPDATE_FINAL_STATUS = "UPDATE_FINAL_STATUS"  # 更新最终状态


class ParserWorkflow(ABC):
    """解析工作流抽象基类"""
    
    def __init__(self):
        self.tokenizer = RagTokenizer()
        self.file_storage = RAGComponentFactory.instance().get_default_file_storage()
        self.vector_database = None
        
    @abstractmethod
    def execute(self, doc_id: str, doc_info: Dict[str, Any], 
                file_info: Dict[str, Any], embedding_config: Dict[str, Any],
                kb_info: Dict[str, Any], callback: Optional[Callable] = None,
                resume_from: Optional[str] = None) -> Dict[str, Any]:
        """执行解析工作流"""
        pass
    
    @abstractmethod
    def get_step_status(self, doc_id: str, step: str) -> Dict[str, Any]:
        """获取步骤状态"""
        pass


class MinerUWorkflow(ParserWorkflow):
    """MinerU解析工作流"""
    
    def __init__(self):
        super().__init__()
        self.temp_files = []
        self.image_info_list = []
        self.callback = None
        self.step_status = {}
        
    def execute(self, 
                doc_id: str, 
                doc_info: Dict[str, Any], 
                file_info: Dict[str, Any], 
                embedding_config: Dict[str, Any],
                kb_info: Dict[str, Any], 
                callback: Optional[Callable] = None,
                resume_from: Optional[str] = None,
                onStepCallback: Optional[Callable] = None) -> Dict[str, Any]:
        """执行MinerU解析工作流"""
        self.callback = callback
        self.doc_id = doc_id
        
        try:
            # 初始化步骤状态
            self._init_step_status(doc_id, resume_from)
            
            # 步骤1: 初始化
            if self._should_execute_step(WorkflowStep.INIT.value):
                self._execute_init_step(doc_id, doc_info, file_info, embedding_config, kb_info)
            
            # 步骤2: 获取文件内容
            if self._should_execute_step(WorkflowStep.GET_FILE_CONTENT.value):
                file_content = self._execute_get_file_content_step(doc_id, file_info, doc_info)
            else:
                # 从缓存或存储中获取文件内容
                file_content = self._get_cached_file_content(doc_id)
            
            # 步骤3: 解析文件
            if self._should_execute_step(WorkflowStep.PARSE_FILE.value):
                content_list, middle_content, middle_json_content = self._execute_parse_file_step(
                    doc_id, doc_info, file_content
                )
            else:
                # 从缓存或存储中获取解析结果
                content_list, middle_content, middle_json_content = self._get_cached_parse_result(doc_id)
            
            # 步骤4: 提取块信息
            if self._should_execute_step(WorkflowStep.EXTRACT_BLOCKS.value):
                block_info_list = self._execute_extract_blocks_step(middle_json_content)
            else:
                # 从缓存或存储中获取块信息
                block_info_list = self._get_cached_block_info(doc_id)
            
            # 步骤5: 处理向量化和存储
            if self._should_execute_step(WorkflowStep.PROCESS_CHUNKS.value):
                chunk_count, chunk_ids_list = self._execute_process_chunks_step(
                    doc_id, doc_info, kb_info, content_list, block_info_list, embedding_config
                )
            else:
                # 从缓存或存储中获取处理结果
                chunk_count, chunk_ids_list = self._get_cached_chunk_result(doc_id)
            
            
            # 步骤6: 更新文档状态
            if self._should_execute_step(WorkflowStep.UPDATE_FINAL_STATUS.value):
                self._execute_update_final_status_step(doc_id, chunk_count)
            else:
                # 从缓存或存储中获取文档状态
                self._get_cached_final_status(doc_id)
            
            return {
                "success": True,
                "chunk_count": chunk_count,
                "chunk_ids": chunk_ids_list,
                "image_info": self.image_info_list,
                "completed_steps": self._get_completed_steps()
            }
            
        except Exception as e:
            logging.error(f"[Workflow-ERROR] 解析工作流执行失败: {e}")
            self._update_document_progress(doc_id, status="FAILED", message=str(e))
            raise
        finally:
            self._cleanup_temp_files()
    
    def get_step_status(self, doc_id: str, step: str) -> Dict[str, Any]:
        """获取步骤状态"""
        step_key = f"{doc_id}_{step}"
        return self.step_status.get(step_key, {
            "status": StepStatus.PENDING.value,
            "progress": 0,
            "message": "步骤未开始",
            "start_time": None,
            "end_time": None,
            "error": None
        })
    
    def _init_step_status(self, doc_id: str, resume_from: Optional[str] = None):
        """初始化步骤状态"""
        steps = [step.value for step in WorkflowStep]
        
        if resume_from:
            # 断点续传：从指定步骤开始
            resume_index = -1
            for i, step in enumerate(steps):
                if step == resume_from:
                    resume_index = i
                    break
            
            if resume_index == -1:
                raise ValueError(f"无效的断点步骤: {resume_from}")
            
            # 设置之前步骤为已完成
            for i in range(resume_index):
                step_key = f"{doc_id}_{steps[i]}"
                self.step_status[step_key] = {
                    "status": StepStatus.COMPLETED.value,
                    "progress": 100,
                    "message": "步骤已完成",
                    "start_time": datetime.now(),
                    "end_time": datetime.now(),
                    "error": None
                }
            
            # 设置当前步骤为待执行
            step_key = f"{doc_id}_{steps[resume_index]}"
            self.step_status[step_key] = {
                "status": StepStatus.PENDING.value,
                "progress": 0,
                "message": "步骤待执行",
                "start_time": None,
                "end_time": None,
                "error": None
            }
            
            # 设置后续步骤为待执行
            for i in range(resume_index + 1, len(steps)):
                step_key = f"{doc_id}_{steps[i]}"
                self.step_status[step_key] = {
                    "status": StepStatus.PENDING.value,
                    "progress": 0,
                    "message": "步骤待执行",
                    "start_time": None,
                    "end_time": None,
                    "error": None
                }
        else:
            # 全新执行：所有步骤都设为待执行
            for step in steps:
                step_key = f"{doc_id}_{step}"
                self.step_status[step_key] = {
                    "status": StepStatus.PENDING.value,
                    "progress": 0,
                    "message": "步骤待执行",
                    "start_time": None,
                    "end_time": None,
                    "error": None
                }
    
    def _should_execute_step(self, step: str) -> bool:
        """判断是否应该执行步骤"""
        step_key = f"{self.doc_id}_{step}"
        status_info = self.step_status.get(step_key, {})
        return status_info.get("status") in [StepStatus.PENDING.value, StepStatus.FAILED.value]
    
    def _update_step_status(self, step: str, status: StepStatus, progress: int = 0, 
                          message: str = "", error: Optional[str] = None):
        """更新步骤状态"""
        step_key = f"{self.doc_id}_{step}"
        current_time = datetime.now()
        
        if step_key not in self.step_status:
            self.step_status[step_key] = {
                "start_time": current_time,
                "end_time": None,
                "error": None
            }
        
        self.step_status[step_key].update({
            "status": status.value,
            "progress": progress,
            "message": message,
            "error": error
        })
        
        if status in [StepStatus.COMPLETED, StepStatus.FAILED, StepStatus.SKIPPED]:
            self.step_status[step_key]["end_time"] = current_time
        
        # 调用callback函数
        if self.callback and callable(self.callback):
            try:
                self.callback(self.doc_id, {
                    "step": step,
                    "step_status": self.step_status[step_key]
                })
            except Exception as e:
                logging.warning(f"[Workflow-WARNING] 调用callback函数失败: {e}")
    
    def _get_completed_steps(self) -> List[str]:
        """获取已完成的步骤列表"""
        completed_steps = []
        for step_key, status_info in self.step_status.items():
            if step_key.startswith(f"{self.doc_id}_") and status_info.get("status") == StepStatus.COMPLETED.value:
                step_name = step_key.replace(f"{self.doc_id}_", "")
                completed_steps.append(step_name)
        return completed_steps
    
    def _execute_init_step(self, doc_id: str, doc_info: Dict[str, Any], 
                          file_info: Dict[str, Any], embedding_config: Dict[str, Any],
                          kb_info: Dict[str, Any]):
        """执行初始化步骤"""
        self._update_step_status(WorkflowStep.INIT.value, StepStatus.RUNNING, 0, "开始初始化工作流")
        
        try:
            self.doc_info = doc_info
            self.file_info = file_info
            self.embedding_config = embedding_config
            self.kb_info = kb_info
            
            # 初始化向量数据库
            kb_id = kb_info.get("kb_id")
            creator = doc_info.get("created_by")
            index_name = f"easyrag_{creator}"
            self.vector_database = RAGComponentFactory.instance().get_default_vector_database(index_name=index_name)
            
            self._update_document_progress(doc_id, progress=0, message="开始解析工作流")
            self._update_step_status(WorkflowStep.INIT.value, StepStatus.COMPLETED, 100, "初始化完成")
            
        except Exception as e:
            self._update_step_status(WorkflowStep.INIT.value, StepStatus.FAILED, 0, f"初始化失败: {e}", str(e))
            raise
    
    def _execute_get_file_content_step(self, doc_id: str, file_info: Dict[str, Any], 
                                     doc_info: Dict[str, Any]) -> bytes:
        """执行获取文件内容步骤"""
        self._update_step_status(WorkflowStep.GET_FILE_CONTENT.value, StepStatus.RUNNING, 0, "获取文件内容")
        
        try:
            self._update_document_progress(doc_id, progress=5, message="获取文件内容")
            
            file_location = doc_info.get("location")
            bucket_name = str(file_info.get("parent_id"))
            
            file_content = self.file_storage.get_file_content(
                bucket_name=bucket_name, 
                file_path=file_location
            )
            
            if not file_content:
                raise Exception(f"获取文件内容失败: {file_location}")
            
            # 缓存文件内容
            self._cache_file_content(doc_id, file_content)
            
            logging.info(f"[Workflow-INFO] 成功获取文件内容: {file_location}")
            self._update_step_status(WorkflowStep.GET_FILE_CONTENT.value, StepStatus.COMPLETED, 100, "文件内容获取完成")
            self._remove_file_content_cache(doc_id)
            return file_content
            
        except Exception as e:
            self._update_step_status(WorkflowStep.GET_FILE_CONTENT.value, StepStatus.FAILED, 0, f"获取文件内容失败: {e}", str(e))
            raise
    
    def _execute_parse_file_step(self, doc_id: str, doc_info: Dict[str, Any], 
                               file_content: bytes) -> Tuple[List[Dict], str, Dict]:
        """执行解析文件步骤"""
        self._update_step_status(WorkflowStep.PARSE_FILE.value, StepStatus.RUNNING, 0, "开始解析文件")
        
        try:
            self._update_document_progress(doc_id, progress=10, message="开始解析文件")
            
            file_type = doc_info.get("type").lower()
            file_location = doc_info.get("location")
            _, file_extension = os.path.splitext(file_location)
            
            if file_type.endswith("pdf"):
                result = self._parse_pdf(doc_id, file_content)
            elif file_type.endswith(("word", "ppt", "txt", "md", "html")):
                result = self._parse_office_document(doc_id, file_extension, file_content)
            elif file_type.endswith("excel"):
                result = self._parse_excel(file_content)
            elif file_type.endswith("visual"):
                result = self._parse_visual(doc_id, file_extension, file_content)
            else:
                raise NotImplementedError(f"不支持的文件类型: {file_type}")
            
            # 缓存解析结果
            self._remove_file_content_cache(doc_id)
            self._cache_parse_result(doc_id, result)
            
            self._update_step_status(WorkflowStep.PARSE_FILE.value, StepStatus.COMPLETED, 100, "文件解析完成")
            return result
            
        except Exception as e:
            self._update_step_status(WorkflowStep.PARSE_FILE.value, StepStatus.FAILED, 0, f"文件解析失败: {e}", str(e))
            raise
    
    def _execute_extract_blocks_step(self, middle_json_content: Dict) -> List[Dict[str, Any]]:
        """执行提取块信息步骤"""
        self._update_step_status(WorkflowStep.EXTRACT_BLOCKS.value, StepStatus.RUNNING, 0, "提取块信息")
        
        try:
            block_info_list = self._extract_block_info(middle_json_content)
            
            # 缓存块信息
            self._remove_parse_result_cache(self.doc_id, block_info_list)
            self._cache_block_info(self.doc_id, block_info_list)
            
            self._update_step_status(WorkflowStep.EXTRACT_BLOCKS.value, StepStatus.COMPLETED, 100, f"提取了{len(block_info_list)}个块信息")
            return block_info_list
            
        except Exception as e:
            self._update_step_status(WorkflowStep.EXTRACT_BLOCKS.value, StepStatus.FAILED, 0, f"提取块信息失败: {e}", str(e))
            raise
    
    def _execute_process_chunks_step(self, doc_id: str, doc_info: Dict[str, Any], kb_info: Dict[str, Any],
                                   content_list: List[Dict], block_info_list: List[Dict], 
                                   embedding_config: Dict[str, Any]) -> Tuple[int, List[str]]:
        """执行处理向量化和存储步骤"""
        self._update_step_status(WorkflowStep.PROCESS_CHUNKS.value, StepStatus.RUNNING, 0, "处理文本块")
        
        try:
            self._update_document_progress(doc_id, progress=50, message="处理文本块")
            
            kb_id = kb_info.get("kb_id")
            output_bucket = str(kb_id)
            chunk_count = 0
            chunk_ids_list = []
            
            # 创建向量索引
            self._create_vector_index()
            
            total_chunks = len(content_list)
            for chunk_idx, chunk_data in enumerate(content_list):
                try:
                    # 更新进度
                    progress = int(50 + (chunk_idx / total_chunks) * 40)
                    self._update_step_status(WorkflowStep.PROCESS_CHUNKS.value, StepStatus.RUNNING, progress, 
                                           f"处理第{chunk_idx + 1}/{total_chunks}个块")
                    
                    # 获取块信息
                    page_idx, bbox = self._get_chunk_info(chunk_idx, block_info_list)
                    
                    # 处理不同类型的块
                    if chunk_data["type"] in ["text", "table", "equation"]:
                        content = self._extract_text_content(chunk_data)
                        if content:
                            # 获取向量嵌入
                            vector = self._get_embedding(embedding_config, content)
                            
                            # 存储块
                            chunk_id = self._store_chunk(
                                doc_id, doc_info, kb_id, output_bucket, 
                                page_idx, bbox, content, vector
                            )
                            chunk_ids_list.append(chunk_id)
                            chunk_count += 1
                            
                    elif chunk_data["type"] == "image":
                        self._process_image_chunk(chunk_data, output_bucket, chunk_count)
                        
                except Exception as e:
                    logging.error(f"[Workflow-ERROR] 处理块 {chunk_idx} 失败: {e}")
                    continue
            
            # 缓存处理结果
            self._cache_chunk_result(doc_id, chunk_count, chunk_ids_list)
            
            self._update_step_status(WorkflowStep.PROCESS_CHUNKS.value, StepStatus.COMPLETED, 100, f"处理完成，共生成{chunk_count}个文本块")
            return chunk_count, chunk_ids_list
            
        except Exception as e:
            self._update_step_status(WorkflowStep.PROCESS_CHUNKS.value, StepStatus.FAILED, 0, f"处理文本块失败: {e}", str(e))
            raise
    
    def _execute_update_final_status_step(self, doc_id: str, chunk_count: int):
        """执行更新最终状态步骤"""
        self._update_step_status(WorkflowStep.UPDATE_FINAL_STATUS.value, StepStatus.RUNNING, 0, "更新最终状态")
        
        try:
            self._update_final_status(doc_id, chunk_count)
            self._update_step_status(WorkflowStep.UPDATE_FINAL_STATUS.value, StepStatus.COMPLETED, 100, "最终状态更新完成")
            
        except Exception as e:
            self._update_step_status(WorkflowStep.UPDATE_FINAL_STATUS.value, StepStatus.FAILED, 0, f"更新最终状态失败: {e}", str(e))
            raise
    
    # 缓存相关方法
    def _remove_file_content_cache(self, doc_id: str):
        """删除文件内容缓存"""
        cache_key = f"file_content_{doc_id}"
        delete_cache(cache_key)
        
    def _cache_file_content(self, doc_id: str, file_content: bytes):
        """缓存文件内容"""
        # 这里可以实现文件内容的缓存逻辑
        # 比如保存到临时文件或内存缓存
        cache_key = f"file_content_{doc_id}"
        set_cache(cache_key, file_content)
    
    def _get_cached_file_content(self, doc_id: str) -> bytes:
        """获取缓存的文件内容"""
        # 这里可以实现从缓存获取文件内容的逻辑
        cache_key = f"file_content_{doc_id}"
        return get_cache(cache_key)
    
    def _cache_parse_result(self, doc_id: str, result: Tuple[List[Dict], str, Dict]):
        """缓存解析结果"""
        # 这里可以实现解析结果的缓存逻辑
        cache_key = f"parse_result_{doc_id}"
        set_cache(cache_key, result)
    
    def _get_cached_parse_result(self, doc_id: str) -> Tuple[List[Dict], str, Dict]:
        """获取缓存的解析结果"""
        # 这里可以实现从缓存获取解析结果的逻辑
        cache_key = f"parse_result_{doc_id}"
        return get_cache(cache_key)
    
    def _remove_parse_result_cache(self, doc_id: str):
        """删除解析结果缓存"""
        cache_key = f"parse_result_{doc_id}"
        delete_cache(cache_key)
    
    def _cache_block_info(self, doc_id: str, block_info_list: List[Dict[str, Any]]):
        """缓存块信息"""
        # 这里可以实现块信息的缓存逻辑
        cache_key = f"block_info_{doc_id}"
        set_cache(cache_key, block_info_list)
    
    def _get_cached_block_info(self, doc_id: str) -> List[Dict[str, Any]]:
        """获取缓存的块信息"""
        # 这里可以实现从缓存获取块信息的逻辑
        cache_key = f"block_info_{doc_id}"
        return get_cache(cache_key)
    
    def _remove_block_info_cache(self, doc_id: str):
        """删除块信息缓存"""
        cache_key = f"block_info_{doc_id}"
        delete_cache(cache_key)
    
    def _cache_chunk_result(self, doc_id: str, chunk_count: int, chunk_ids_list: List[str]):
        """缓存处理结果"""
        # 这里可以实现处理结果的缓存逻辑
        cache_key = f"chunk_result_{doc_id}"
        set_cache(cache_key, (chunk_count, chunk_ids_list))
    
    def _get_cached_chunk_result(self, doc_id: str) -> Tuple[int, List[str]]:
        """获取缓存的处理结果"""
        # 这里可以实现从缓存获取处理结果的逻辑
        cache_key = f"chunk_result_{doc_id}"
        return get_cache(cache_key)
    
    def _remove_chunk_result_cache(self, doc_id: str):
        """删除处理结果缓存"""
        cache_key = f"chunk_result_{doc_id}"
        delete_cache(cache_key)
    
    # 原有的方法保持不变
    def _get_file_content(self, doc_id: str, file_info: Dict[str, Any], 
                         doc_info: Dict[str, Any]) -> bytes:
        """获取文件内容（保持向后兼容）"""
        return self._execute_get_file_content_step(doc_id, file_info, doc_info)
    
    def _parse_file(self, doc_id: str, doc_info: Dict[str, Any], 
                   file_content: bytes) -> Tuple[List[Dict], str, Dict]:
        """解析文件内容（保持向后兼容）"""
        return self._execute_parse_file_step(doc_id, doc_info, file_content)
    
    def _process_chunks(self, doc_id: str, doc_info: Dict[str, Any], kb_info: Dict[str, Any],
                       content_list: List[Dict], block_info_list: List[Dict], 
                       embedding_config: Dict[str, Any]) -> Tuple[int, List[str]]:
        """处理文本块（保持向后兼容）"""
        return self._execute_process_chunks_step(doc_id, doc_info, kb_info, content_list, block_info_list, embedding_config)
    
    def _init_workflow(self, doc_id: str, doc_info: Dict[str, Any], 
                      file_info: Dict[str, Any], embedding_config: Dict[str, Any],
                      kb_info: Dict[str, Any]):
        """初始化工作流（保持向后兼容）"""
        self._execute_init_step(doc_id, doc_info, file_info, embedding_config, kb_info)
    
    def _extract_block_info(self, middle_json_content: Dict, parse_config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """提取块信息（保持向后兼容）"""
        if parse_config.embedding_config.get("embedding_model_name") is not None \
            and parse_config.chunk_config.get("chunk_size") is not None:
            return self._execute_extract_blocks_step(middle_json_content, parse_config)
        else:
            return self._execute_extract_blocks_step(middle_json_content, parse_config)
    
    def _update_final_status(self, doc_id: str, chunk_count: int):
        """更新最终状态（保持向后兼容）"""
        self._execute_update_final_status_step(doc_id, chunk_count)
    
    # 其他原有方法保持不变...
    def _parse_pdf(self, doc_id: str, file_content: bytes) -> Tuple[List[Dict], str, Dict]:
        """解析PDF文件"""
        from magic_pdf.data.data_reader_writer import FileBasedDataReader, FileBasedDataWriter
        from magic_pdf.data.dataset import PymuDocDataset
        from magic_pdf.model.doc_analyze_by_custom_model import doc_analyze
        from magic_pdf.config.enums import SupportedPdfParseMethod
        
        self._update_document_progress(doc_id, progress=15, message="解析PDF文件")
        
        # 创建临时PDF文件
        temp_dir = tempfile.gettempdir()
        temp_pdf_path = os.path.join(temp_dir, f"{doc_id}.pdf")
        self.temp_files.append(temp_pdf_path)
        
        with open(temp_pdf_path, "wb") as f:
            f.write(file_content)
        
        # 使用MinerU处理
        reader = FileBasedDataReader("")
        pdf_bytes = reader.read_pdf(temp_pdf_path)
        ds = PymuDocDataset(pdf_bytes)
        
        # 判断是否需要OCR
        is_ocr = ds.classify() == SupportedPdfParseMethod.OCR
        mode_msg = "OCR模式" if is_ocr else "文本模式"
        self._update_document_progress(doc_id, progress=20, message=f"使用{mode_msg}处理PDF")
        
        infer_result = ds.apply(doc_analyze, ocr=is_ocr)
        
        # 设置临时输出目录
        temp_image_dir = os.path.join(temp_dir, f"images_{doc_id}")
        os.makedirs(temp_image_dir, exist_ok=True)
        self.temp_files.append(temp_image_dir)
        
        image_writer = FileBasedDataWriter(temp_image_dir)
        
        # 处理结果
        pipe_result = infer_result.pipe_ocr_mode(image_writer) if is_ocr else infer_result.pipe_text_mode(image_writer)
        
        # 提取内容
        content_list = pipe_result.get_content_list(os.path.basename(temp_pdf_path))
        middle_content = pipe_result.get_middle_json()
        middle_json_content = infer_result.to_json(temp_dir, f"{doc_id}.json")
        
        return content_list, middle_content, middle_json_content
    
    def _parse_office_document(self, doc_id: str, file_extension: str, 
                              file_content: bytes) -> Tuple[List[Dict], str, Dict]:
        """解析Office文档"""
        from magic_pdf.data.read_api import read_local_office
        from magic_pdf.model.doc_analyze_by_custom_model import doc_analyze
        from magic_pdf.data.data_reader_writer import FileBasedDataWriter
        
        self._update_document_progress(doc_id, progress=15, message="解析Office文档")
        
        # 创建临时文件
        temp_dir = tempfile.gettempdir()
        temp_file_path = os.path.join(temp_dir, f"{doc_id}{file_extension}")
        self.temp_files.append(temp_file_path)
        
        with open(temp_file_path, "wb") as f:
            f.write(file_content)
        
        # 使用MinerU处理
        ds = read_local_office(temp_file_path)[0]
        infer_result = ds.apply(doc_analyze, ocr=True)
        
        # 设置临时输出目录
        temp_image_dir = os.path.join(temp_dir, f"images_{doc_id}")
        os.makedirs(temp_image_dir, exist_ok=True)
        self.temp_files.append(temp_image_dir)
        
        image_writer = FileBasedDataWriter(temp_image_dir)
        
        # 处理结果
        pipe_result = infer_result.pipe_text_mode(image_writer)
        
        # 提取内容
        content_list = pipe_result.get_content_list(os.path.basename(temp_file_path))
        middle_content = pipe_result.get_middle_json()
        middle_json_content = infer_result.to_json(temp_dir, f"{doc_id}.json")
        
        return content_list, middle_content, middle_json_content
    
    def _parse_excel(self, file_content: bytes) -> Tuple[List[Dict], str, Dict]:
        """解析Excel文件"""
        # 创建临时文件
        temp_dir = tempfile.gettempdir()
        temp_excel_path = os.path.join(temp_dir, f"temp_excel.xlsx")
        self.temp_files.append(temp_excel_path)
        
        with open(temp_excel_path, "wb") as f:
            f.write(file_content)
        
        # 使用excel_parser解析
        content_list = excel_parser.parse_excel(temp_excel_path)
        
        return content_list, "", {}
    
    def _parse_visual(self, doc_id: str, file_extension: str, 
                     file_content: bytes) -> Tuple[List[Dict], str, Dict]:
        """解析视觉文件"""
        from magic_pdf.data.read_api import read_local_images
        from magic_pdf.model.doc_analyze_by_custom_model import doc_analyze
        from magic_pdf.data.data_reader_writer import FileBasedDataWriter
        
        self._update_document_progress(doc_id, progress=15, message="解析视觉文件")
        
        # 创建临时文件
        temp_dir = tempfile.gettempdir()
        temp_image_path = os.path.join(temp_dir, f"{doc_id}{file_extension}")
        self.temp_files.append(temp_image_path)
        
        with open(temp_image_path, "wb") as f:
            f.write(file_content)
        
        # 使用MinerU处理
        ds = read_local_images(temp_image_path)[0]
        infer_result = ds.apply(doc_analyze, ocr=True)
        
        # 判断是否需要OCR
        from magic_pdf.config.enums import SupportedPdfParseMethod
        is_ocr = ds.classify() == SupportedPdfParseMethod.OCR
        mode_msg = "OCR模式" if is_ocr else "文本模式"
        
        # 设置临时输出目录
        temp_image_dir = os.path.join(temp_dir, f"images_{doc_id}")
        os.makedirs(temp_image_dir, exist_ok=True)
        self.temp_files.append(temp_image_dir)
        
        image_writer = FileBasedDataWriter(temp_image_dir)
        
        # 处理结果
        pipe_result = infer_result.pipe_ocr_mode(image_writer) if is_ocr else infer_result.pipe_txt_mode(image_writer)
        
        # 提取内容
        content_list = pipe_result.get_content_list(os.path.basename(temp_image_path))
        middle_content = pipe_result.get_middle_json()
        middle_json_content = json.loads(middle_content)
        
        return content_list, middle_content, middle_json_content
    
    def _get_bbox_from_block(self, block: Dict) -> List[float]:
        """从块中提取bbox信息"""
        if isinstance(block, dict) and "bbox" in block:
            bbox = block.get("bbox")
            if isinstance(bbox, list) and len(bbox) == 4 and all(isinstance(n, (int, float)) for n in bbox):
                return bbox
        return [0, 0, 0, 0]
    
    def _get_chunk_info(self, chunk_idx: int, block_info_list: List[Dict]) -> Tuple[int, List[float]]:
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
    
    def _get_embedding(self, embedding_config: Dict[str, Any], content: str) -> List[float]:
        """获取文本嵌入向量"""
        import requests
        
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
    
    def _create_vector_index(self):
        """创建向量索引"""
        creator = self.doc_info.get("created_by")
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
        
        self.vector_database.create_index(index_name=index_name, body=body)
        logging.info(f"[Workflow-INFO] 创建向量索引: {index_name}")
    
    def _store_chunk(self, doc_id: str, doc_info: Dict[str, Any], kb_id: str, 
                    output_bucket: str, page_idx: int, bbox: List[float], 
                    content: str, vector: List[float]) -> str:
        """存储文本块"""
        chunk_id = generate_uuid()
        
        # 存储到文件存储
        self.file_storage.fput_object(
            bucket_name=output_bucket,
            object_name=chunk_id,
            data=BytesIO(content.encode("utf-8")),
            length=len(content.encode("utf-8"))
        )
        
        # 准备ES文档
        chunk_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        chunk_timestamp = datetime.now().timestamp()
        x1, y1, x2, y2 = bbox
        bbox_reordered = [x1, x2, y1, y2]
        
        es_doc = {
            "doc_id": doc_id,
            "kb_id": str(kb_id),
            "docnm_kwd": doc_info["name"],
            "title_tks": self.tokenizer.tokenize(doc_info["name"]),
            "title_sm_tks": self.tokenizer.tokenize(doc_info["name"]),
            "content_ltks": self.tokenizer.tokenize(content),
            "content_sm_ltks": self.tokenizer.tokenize(content),
            "page_num_int": [page_idx + 1],
            "position_int": [[page_idx + 1] + bbox_reordered],
            "top_int": [1],
            "create_time": chunk_time,
            "create_timestamp_flt": chunk_timestamp,
            "img_id": "",
            "q_1024_vec": vector,
        }
        
        # 存储到向量数据库
        creator = self.doc_info.get("created_by")
        index_name = f"easyrag_{creator}"
        self.vector_database.index(index_name=index_name, id=chunk_id, document=es_doc)
        
        logging.info(f"[Workflow-INFO] 存储块 {chunk_id}")
        return chunk_id
    
    def _process_image_chunk(self, chunk_data: Dict, output_bucket: str, chunk_count: int):
        """处理图片块"""
        img_path_relative = chunk_data.get("img_path")
        if not img_path_relative:
            return
        
        # 查找对应的临时图片文件
        temp_image_dir = None
        for temp_file in self.temp_files:
            if "images_" in temp_file and os.path.isdir(temp_file):
                temp_image_dir = temp_file
                break
        
        if not temp_image_dir:
            return
        
        img_path_abs = os.path.join(temp_image_dir, img_path_relative)
        if not os.path.exists(img_path_abs):
            logging.warning(f"[Workflow-WARNING] 图片文件不存在: {img_path_abs}")
            return
        
        # 上传图片
        img_id = generate_uuid()
        img_ext = os.path.splitext(img_path_abs)[1]
        img_key = f"images/{img_id}{img_ext}"
        content_type = f"image/{img_ext[1:].lower()}"
        if content_type == "image/jpeg":
            content_type = "image/jpg"
        
        try:
            self.file_storage.fput_object(
                bucket_name=output_bucket,
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
                    "Resource": [f"arn:aws:s3:::{output_bucket}/*"]
                }]
            }
            self.file_storage.set_bucket_policy(output_bucket, json.dumps(policy))
            
            # 生成访问URL
            from EasyRAG import settings
            minio_endpoint = settings.MINIO_CONFIG.get("endpoint")
            use_ssl = settings.MINIO_CONFIG.get("secure", False)
            protocol = "https" if use_ssl else "http"
            img_url = f"{protocol}://{minio_endpoint}/{output_bucket}/{img_key}"
            
            image_info = {
                "url": img_url,
                "position": chunk_count
            }
            self.image_info_list.append(image_info)
            
            logging.info(f"[Workflow-INFO] 成功上传图片: {img_key}")
            
        except Exception as e:
            logging.error(f"[Workflow-ERROR] 上传图片失败: {e}")
    
    def _update_document_progress(self, doc_id: str, progress: Optional[float] = None,
                                message: Optional[str] = None, status: Optional[str] = None,
                                chunk_count: Optional[int] = None):
        """更新文档进度"""
        # try:
        #     update_fields = {}
            
        #     if progress is not None:
        #         update_fields['progress'] = str(float(progress))
        #     if message is not None:
        #         update_fields['progress_msg'] = message
        #     if status is not None:
        #         update_fields['status'] = status
        #     if chunk_count is not None:
        #         update_fields['chunk_num'] = chunk_count

        #     if update_fields:
        #         Document.objects.filter(document_id=doc_id).update(**update_fields)
        #         logging.info(f"[Workflow-INFO] 更新文档 {doc_id} 进度: {progress}% - {message}")
                
        #         # 调用callback函数
        #         if self.callback and callable(self.callback):
        #             try:
        #                 self.callback(doc_id, update_fields)
        #             except Exception as e:
        #                 logging.warning(f"[Workflow-WARNING] 调用callback函数失败: {e}")
                
        # except Exception as e:
        #     logging.error(f"[Workflow-ERROR] 更新文档进度失败: {e}")
        pass
    
    def _cleanup_temp_files(self):
        """清理临时文件"""
        for temp_file in self.temp_files:
            try:
                if os.path.isfile(temp_file):
                    os.remove(temp_file)
                elif os.path.isdir(temp_file):
                    import shutil
                    shutil.rmtree(temp_file)
            except Exception as e:
                logging.warning(f"[Workflow-WARNING] 清理临时文件失败 {temp_file}: {e}")
        
        self.temp_files.clear() 
        
        
        
        
if __name__ == "__main__":
    workflow = MinerUWorkflow()
    with open("test.pdf", "rb") as f:
        file_content = f.read()
    content_list, middle_content, middle_json_content = workflow._parse_pdf("123", file_content)
    print(content_list)
    print(middle_content)
    print(middle_json_content)
    