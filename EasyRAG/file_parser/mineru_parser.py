from typing import Dict, Any, List, Optional, Callable
import logging

from EasyRAG.rag_service.rag_comp_factory import RAGComponentFactory
from EasyRAG.common.rag_tokenizer import RagTokenizer
from EasyRAG.file_parser.document_parser import DocumentParser
from EasyRAG.file_parser.workflow import MinerUWorkflow

tknzr = RagTokenizer()

class MinerUDocumentParser(DocumentParser):
    def __init__(self):
        self.file_storage = RAGComponentFactory.instance().get_default_file_storage()
        
        

    def _tokenize_text(self, text: str) -> List[str]:
        """使用分词器进行文本分词"""
        return tknzr.tokenize(text)
    
    
    def _update_document_progress(self, 
                                doc_id, progress=None, 
                                message=None, status=None, 
                                run=None, chunk_count=None, 
                                process_duration=None):
        """更新数据库中文档的进度和状态"""
        try:
            # 延迟导入，避免循环依赖
            from EasyRAG.rag_app.models import Document
            
            update_fields = {}
            
            if progress is not None:
                update_fields['progress'] = str(float(progress))
            if message is not None:
                update_fields['progress_msg'] = message
            if status is not None:
                update_fields['status'] = status
            if run is not None:
                update_fields['run_id'] = run
            if chunk_count is not None:
                update_fields['chunk_num'] = chunk_count
            if process_duration is not None:
                update_fields['progress_duration'] = process_duration

            if not update_fields:
                return

            Document.objects.filter(document_id=doc_id).update(**update_fields)
            logging.info(f"[Parser-INFO] 成功更新文档 {doc_id} 进度")
            
        except Exception as e:
            logging.error(f"[Parser-ERROR] 更新文档 {doc_id} 进度失败: {e}")
            
    def _update_progress(self, doc_id, prog=None, msg=None):
        """更新文档进度的便捷方法"""
        self._update_document_progress(doc_id, progress=prog, message=msg)
        logging.info(f"[Parser-PROGRESS] Doc: {doc_id}, Progress: {prog}, Message: {msg}") 
              
    def parse(self, 
              doc_id: str, 
              doc_info: Dict[str, Any], 
              file_info: Dict[str, Any], 
              embedding_config: Dict[str, Any],
              kb_info: Dict[str, Any],
              callback: Optional[Callable] = None,
              resume_from: Optional[str] = None) -> Dict[str, Any]:
        """
        使用MinerU解析文件
        
        Args:
            doc_id: 文档ID
            doc_info (dict): 包含文档信息的字典 (name, location, type, kb_id, parser_config, created_by).
            file_info (dict): 包含文件信息的字典 (parent_id/bucket_name).
            embedding_config (dict): 包含嵌入信息的字典 (embedding_model_id, embedding_model_config).
            kb_info (dict): 包含知识库信息的字典 (created_by).
            callback (callable, optional): 状态更新回调函数，接收doc_id和update_fields参数
            resume_from (str, optional): 断点续传的起始步骤，支持的值：
                - "INIT": 初始化
                - "GET_FILE_CONTENT": 获取文件内容
                - "PARSE_FILE": 解析文件
                - "EXTRACT_BLOCKS": 提取块信息
                - "PROCESS_CHUNKS": 处理向量化和存储
                - "UPDATE_FINAL_STATUS": 更新最终状态
            
        Returns:
            Dict[str, Any]: 解析结果，包含文本内容和元数据
        """
        try:
            # 使用工作流执行解析
            result = self.workflow.execute(
                doc_id=doc_id,
                doc_info=doc_info,
                file_info=file_info,
                embedding_config=embedding_config,
                kb_info=kb_info,
                callback=callback,
                resume_from=resume_from
            )
            
            logging.info(f"[Parser-INFO] 文档 {doc_id} 解析完成，生成 {result.get('chunk_count', 0)} 个文本块")
            return result
            
        except Exception as e:
            logging.error(f"[Parser-ERROR] 文档 {doc_id} 解析失败: {e}")
            self._update_document_progress(doc_id, status="FAILED", message=str(e))
            raise
    
    def get_step_status(self, doc_id: str, step: str) -> Dict[str, Any]:
        """
        获取指定步骤的状态
        
        Args:
            doc_id: 文档ID
            step: 步骤名称
            
        Returns:
            Dict[str, Any]: 步骤状态信息
        """
        return self.workflow.get_step_status(doc_id, step) 