from typing import Any, Dict
from enum import StrEnum

from pydantic import BaseModel

from EasyRAG.common.rag_config_model import ChunkConfigData, EmbeddingConfigData, KeywordsConfigData, ModelConfigData, ParserConfigData, QuestionsConfigData

def default_parser_config() -> Dict[str, Any]:
    chunk_config = ChunkConfigData(max_chunk_size=1024, max_chunk_overlap=128, split_by="\n")
    embedding_config = EmbeddingConfigData(model_name="bge-m3", model_type="text-embedding", model_provider="huggingface", model_provider_url="https://huggingface.co/BAAI/bge-m3")
    llm_config = None # TODO: add llm config
    keywords = KeywordsConfigData(each_trunk_keywords_number=0)
    questions = QuestionsConfigData(each_trunk_questions_number=0)
    return ParserConfigData(chunk_config=chunk_config, llm_config=llm_config, embedding_config=embedding_config, keywords=keywords, questions=questions)
