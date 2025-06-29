from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import numpy as np
from elasticsearch import Elasticsearch
import logging

class Vectors(ABC):
    """向量存储的抽象基类"""
    
    @abstractmethod
    def add_vector(self, vector: List[float], metadata: Dict[str, Any] = None) -> str:
        """
        添加单个向量
        
        Args:
            vector: 向量数据
            metadata: 向量相关的元数据
            
        Returns:
            str: 向量ID
        """
        pass

    @abstractmethod
    def add_vectors(self, vectors: List[List[float]], metadatas: List[Dict[str, Any]] = None) -> List[str]:
        """
        批量添加向量
        
        Args:
            vectors: 向量数据列表
            metadatas: 向量相关的元数据列表
            
        Returns:
            List[str]: 向量ID列表
        """
        pass

    @abstractmethod
    def search(self, query_vector: List[float], top_k: int = 5) -> List[Dict[str, Any]]:
        """
        搜索最相似的向量
        
        Args:
            query_vector: 查询向量
            top_k: 返回结果数量
            
        Returns:
            List[Dict]: 包含相似度和元数据的字典列表
        """
        pass
    
    @abstractmethod
    def get_vector(self, vector_id: str) -> Optional[List[float]]:
        """
        获取指定ID的向量
        
        Args:
            vector_id: 向量ID
            
        Returns:
            Optional[List[float]]: 向量数据，如果不存在则返回None
        """
        pass
    
    @abstractmethod
    def delete_vector(self, vector_id: str) -> bool:
        """
        删除指定ID的向量
        
        Args:
            vector_id: 向量ID
            
        Returns:
            bool: 是否删除成功
        """
        pass
    
    @abstractmethod
    def get_vector_count(self) -> int:
        """
        获取向量总数
        
        Returns:
            int: 向量数量
        """
        pass
    
    @abstractmethod
    def get_vector_size(self) -> int:
        """
        获取向量维度
        
        Returns:
            int: 向量维度
        """
        pass

    @abstractmethod
    def index(self, index_name: str, id: str, document: Dict[str, Any]):
        """索引文档"""
        pass

class ElasticsearchVectors(Vectors):
    """Elasticsearch向量存储实现"""
    
    def __init__(self, 
                 es_hosts: List[str], 
                 vector_size: int = 1536,
                 similarity: str = "cosine"):
        """
        初始化Elasticsearch向量存储
        
        Args:
            es_hosts: Elasticsearch服务器地址列表
            vector_size: 向量维度
            similarity: 相似度计算方法，支持 "cosine", "l2_norm", "dot_product"
        """
        self.es = Elasticsearch(es_hosts)
        self.vector_size = vector_size
        self.similarity = similarity
        
    
    def create_index(self, index_name: str, body: Dict[str, Any]):
        """创建Elasticsearch索引"""
        if not self.es.indices.exists(index=index_name):
            self.es.indices.create(index=index_name, body=body)
            logging.info(f"创建向量索引: {index_name}")
        else:
            logging.info(f"向量索引已存在: {index_name}")
    
    def add_vector(self, vector: List[float], metadata: Dict[str, Any] = None) -> str:
        """添加单个向量"""
        if len(vector) != self.vector_size:
            raise ValueError(f"Vector dimension mismatch. Expected {self.vector_size}, got {len(vector)}")
        
        doc = {
            "vector": vector,
            "metadata": metadata or {}
        }
        
        response = self.es.index(index=self.index_name, body=doc)
        return response["_id"]
    
    def add_vectors(self, vectors: List[List[float]], metadatas: List[Dict[str, Any]] = None) -> List[str]:
        """批量添加向量"""
        if metadatas is None:
            metadatas = [{}] * len(vectors)
            
        if len(vectors) != len(metadatas):
            raise ValueError("Number of vectors and metadatas must match")
            
        actions = []
        for vector, metadata in zip(vectors, metadatas):
            if len(vector) != self.vector_size:
                raise ValueError(f"Vector dimension mismatch. Expected {self.vector_size}, got {len(vector)}")
            
            action = {
                "_index": self.index_name,
                "_source": {
                    "vector": vector,
                    "metadata": metadata
                }
            }
            actions.append(action)
        
        response = self.es.bulk(body=actions)
        if response.get("errors"):
            raise Exception("Error during bulk indexing")
            
        return [item["_id"] for item in response["items"]]
    
    def search(self, query_vector: List[float], top_k: int = 5) -> List[Dict[str, Any]]:
        """搜索最相似的向量"""
        if len(query_vector) != self.vector_size:
            raise ValueError(f"Query vector dimension mismatch. Expected {self.vector_size}, got {len(query_vector)}")
        
        query = {
            "query": {
                "script_score": {
                    "query": {"match_all": {}},
                    "script": {
                        "source": f"cosineSimilarity(params.query_vector, 'vector') + 1.0",
                        "params": {"query_vector": query_vector}
                    }
                }
            },
            "size": top_k
        }
        
        response = self.es.search(index=self.index_name, body=query)
        
        results = []
        for hit in response["hits"]["hits"]:
            results.append({
                "id": hit["_id"],
                "score": hit["_score"],
                "metadata": hit["_source"]["metadata"]
            })
            
        return results
    
    def get_vector(self, vector_id: str) -> Optional[List[float]]:
        """获取指定ID的向量"""
        try:
            response = self.es.get(index=self.index_name, id=vector_id)
            return response["_source"]["vector"]
        except:
            return None
    
    def delete_vector(self, vector_id: str) -> bool:
        """删除指定ID的向量"""
        try:
            self.es.delete(index=self.index_name, id=vector_id)
            return True
        except:
            return False
    
    def get_vector_count(self) -> int:
        """获取向量总数"""
        response = self.es.count(index=self.index_name)
        return response["count"]
    
    def get_vector_size(self) -> int:
        """获取向量维度"""
        return self.vector_size
    
    def index(self, index_name: str, id: str, document: Dict[str, Any]):
        """索引文档"""
        return self.es.index(index=index_name, id=id, document=document)