import json
from typing import Any, Dict

from pydantic import BaseModel

 #define valid model types
LLM_CHAT_MODEL_TYPE = 'CHAT'
LLM_EMBEDDING_MODEL_TYPE = 'EMBEDDING'
LLM_RERANK_MODEL_TYPE = 'RERANK'
LLM_IMG_TO_TEXT_MODEL_TYPE = 'IMG_TO_TEXT'
LLM_SPEECH_TO_TEXT_MODEL_TYPE = 'SPEECH_TO_TEXT'  
 
class ChunkConfig(BaseModel):
    def __init__(self, max_chunk_size: int, max_chunk_overlap: int, split_by: str):
        self.max_chunk_size = max_chunk_size
        self.max_chunk_overlap = max_chunk_overlap
        self.split_by = split_by
    def to_dict(self) -> Dict[str, Any]:
        return {
            "max_chunk_size": self.max_chunk_size,
            "max_chunk_overlap": self.max_chunk_overlap,
            "split_by": self.split_by,
        }

class LLMModelConfig(BaseModel):
    def __init__(self, model_name: str, 
                 model_type: str, 
                 model_provider: str, 
                 model_provider_url: str,
                 api_key: str = None):
        self.model_name = model_name
        self.model_type = model_type
        self.model_provider = model_provider
        self.model_provider_url = model_provider_url
        self.api_key = api_key
    def to_dict(self) -> Dict[str, Any]:
        return {
            "model_name": self.model_name,
            "model_type": self.model_type,
            "model_provider": self.model_provider,
            "model_provider_url": self.model_provider_url,
            "api_key": self.api_key,
        }

class KeywordQuestionConfig(BaseModel):
    def __init__(self, each_trunk_keywords_number: int = 0, each_trunk_questions_number: int = 0):
        self.each_trunk_keywords_number = each_trunk_keywords_number
        self.each_trunk_questions_number = each_trunk_questions_number
        
    def to_dict(self) -> Dict[str, Any]:
        return {
            "each_trunk_keywords_number": self.each_trunk_keywords_number,
            "each_trunk_questions_number": self.each_trunk_questions_number,
        }

class ParserConfig:
    def __init__(self, chunk_config: ChunkConfig, llm_model_config: LLMModelConfig, 
                 embed_model_config: LLMModelConfig, image2text_model_config: LLMModelConfig,
                 speech2text_model_config: LLMModelConfig, reranker_model_config: LLMModelConfig,
                 keyword_question_config: KeywordQuestionConfig):
        self.chunk_config = chunk_config
        self.llm_model_config = llm_model_config
        self.embed_model_config = embed_model_config
        self.image2text_model_config = image2text_model_config
        self.speech2text_model_config = speech2text_model_config
        self.reranker_model_config = reranker_model_config
        self.keyword_question_config = keyword_question_config
    def to_dict(self) -> Dict[str, Any]:
        return {
            "chunk_config": self.chunk_config.to_dict(),
            "llm_model_config": self.llm_model_config.to_dict(),
            "embed_model_config": self.embed_model_config.to_dict(),
            "image2text_model_config": self.image2text_model_config.to_dict(),
            "speech2text_model_config": self.speech2text_model_config.to_dict(),
            "reranker_model_config": self.reranker_model_config.to_dict(),
            "keyword_question_config": self.keyword_question_config.to_dict(),
        }
    def to_json(self) -> str:
        return json.dumps(self.to_dict())
    
    def from_json(self, json_str: str) -> 'ParserConfig':
        return ParserConfig.from_dict(json.loads(json_str))
    
    def from_dict(self, data: Dict[str, Any]) -> 'ParserConfig':
        return ParserConfig(
            chunk_config=ChunkConfig.from_dict(data["chunk_config"]),
            llm_model_config=LLMModelConfig.from_dict(data["llm_model_config"]),
            embed_model_config=LLMModelConfig.from_dict(data["embed_model_config"]),
            image2text_model_config=LLMModelConfig.from_dict(data["image2text_model_config"]),
            speech2text_model_config=LLMModelConfig.from_dict(data["speech2text_model_config"]),
            reranker_model_config=LLMModelConfig.from_dict(data["reranker_model_config"]),
            keyword_question_config=KeywordQuestionConfig.from_dict(data["keyword_question_config"]),
        )
        
class UserDefaultLLMConfig(BaseModel):
    def __init__(self, chat_config: LLMModelConfig, 
                 embedding_config: LLMModelConfig,
                 image2text_config: LLMModelConfig = None, 
                 speech2text_config: LLMModelConfig = None, 
                 reranker_config: LLMModelConfig = None):
        self.chat_config = chat_config
        self.embedding_config = embedding_config
        self.image2text_config = image2text_config
        self.speech2text_config = speech2text_config
        self.reranker_config = reranker_config

    def to_dict(self) -> Dict[str, Any]:
        return {
            "chat_config": self.chat_config.to_dict(),
            "embedding_config": self.embedding_config.to_dict(),
            "image2text_config": self.image2text_config.to_dict() if self.image2text_config else None,
            "speech2text_config": self.speech2text_config.to_dict() if self.speech2text_config else None,
            "reranker_config": self.reranker_config.to_dict() if self.reranker_config else None,
        }
