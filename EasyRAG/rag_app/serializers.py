from rest_framework import serializers
from .models import KnowledgeBase, Document

class KnowledgeBaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = KnowledgeBase
        fields = [
            'knowledge_base_id',
            'name',
            'description',
            'document_num',
            'chunk_num',
            'permission',
            'parser_config',
            'vector_similarity_weight',
            'embed_id',
            'language',
            'page_rank',
            'status',
            'created_at',
            'updated_at',
            'created_by'
        ]
        read_only_fields = ['knowledge_base_id', 'created_at', 'updated_at', 'created_by'] 

class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = [
            'document_id',
            'knowledge_base',
            'document_name',
            'document_location',
            'token_num',
            'chunk_num',
            'is_active',
            'parser_config',
            'parser_id',
            'source_type',
            'run_id',
            'status',
            'metadata',
            'progress',
            'progress_msg',
            'progress_begin_at',
            'progress_duration',
            'created_by',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['document_id', 'created_at', 'updated_at', 'created_by'] 