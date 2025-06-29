from enum import StrEnum
from typing import Any, Dict

class ModelProvider(StrEnum):
    HUGGINGFACE = "huggingface"
    OPENAI = "openai"
    VLLM = "vllm"
    OLLAMA = "ollama"
    SILICONFLOW = "siliconflow"

class ModelType(StrEnum):
    TEXT_CHAT = "text-chat"
    TEXT_EMBEDDING = "text-embedding"
    TEXT_RERANK = "text-rerank"
    IMAGE_TO_TEXT = "image-to-text"
    
class ChunkConfigData:
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

class EmbeddingConfigData:
    def __init__(self, model_name: str, model_type: ModelType, model_provider: ModelProvider, model_provider_url: str):
        self.model_name = model_name
        self.model_type = model_type
        self.model_provider = model_provider
        self.model_provider_url = model_provider_url
    
    def to_dict(self) -> Dict[str, Any]:    
        return {
            "model_name": self.model_name,
            "model_type": self.model_type,
            "model_provider": self.model_provider,
            "model_provider_url": self.model_provider_url,
        }

class ModelConfigData:
    def __init__(self, model_name: str, model_type: ModelType, model_provider: ModelProvider, model_provider_url: str):
        self.model_name = model_name
        self.model_type = model_type
        self.model_provider = model_provider
        self.model_provider_url = model_provider_url
    def to_dict(self) -> Dict[str, Any]:
        return {
            "model_name": self.model_name,
            "model_type": self.model_type,
            "model_provider": self.model_provider,
            "model_provider_url": self.model_provider_url,
        }

class KeywordsConfigData:
    def __init__(self, each_trunk_keywords_number: int):
        self.each_trunk_keywords_number = each_trunk_keywords_number
    def to_dict(self) -> Dict[str, Any]:
        return {
            "each_trunk_keywords_number": self.each_trunk_keywords_number,
        }

class QuestionsConfigData:
    def __init__(self, each_trunk_questions_number: int):
        self.each_trunk_questions_number = each_trunk_questions_number
    def to_dict(self) -> Dict[str, Any]:
        return {
            "each_trunk_questions_number": self.each_trunk_questions_number,
        }

class RetrieverConfigData:
    def __init__(self, similarity_score_threshold: float, similarity_score_top_k: int):
        self.similarity_score_threshold = similarity_score_threshold
        self.similarity_score_top_k = similarity_score_top_k
    def to_dict(self) -> Dict[str, Any]:
        return {
            "similarity_score_threshold": self.similarity_score_threshold,
            "similarity_score_top_k": self.similarity_score_top_k,
        }

class ParserConfigData:
    def __init__(self, chunk_config: ChunkConfigData, llm_config: ModelConfigData, embedding_config: EmbeddingConfigData, keywords: KeywordsConfigData, questions: QuestionsConfigData):
        self.chunk_config = chunk_config
        self.llm_config = llm_config
        self.embedding_config = embedding_config
        self.keywords = keywords
        self.questions = questions
    def to_dict(self) -> Dict[str, Any]:
        return {
            "chunk_config": self.chunk_config.to_dict(),
            "llm_config": self.llm_config.to_dict(),
            "embedding_config": self.embedding_config.to_dict(),
            "keywords": self.keywords.to_dict(),
            "questions": self.questions.to_dict(),
        }

