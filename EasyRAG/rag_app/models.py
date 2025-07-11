import uuid
from django.db import models

from EasyRAG.user_app.models import User

# Create your models here.
class KnowledgeBase(models.Model):
    knowledge_base_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=128)
    description = models.TextField(null=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, null=False)
    document_num = models.IntegerField(null=False, default=0)
    chunk_num = models.IntegerField(null=False, default=0)
    permission = models.CharField(max_length=50, null=False)
    parser_config = models.JSONField(blank=False, null=False)
    vector_similarity_weight = models.FloatField(null=False, default=0.2)
    embed_id = models.CharField(max_length=100, null=False)
    language = models.CharField(max_length=50, null=False, default='Chinese')
    page_rank = models.FloatField(null=False, default=0)
    status = models.CharField(max_length=50, null=False, default='active')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'knowledge_bases'
        verbose_name = 'Knowledge Base'
        verbose_name_plural = 'Knowledge Bases'

class File(models.Model):
    file_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    file_name = models.CharField(max_length=255, null=False)
    file_location = models.CharField(max_length=255, null=False)
    file_source = models.CharField(max_length=255, null=True, default='local')
    file_size = models.IntegerField(null=False)
    file_type = models.CharField(max_length=255, null=False)
    file_status = models.CharField(max_length=255, null=False, default='active')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, null=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'files'
        verbose_name = 'File'
        verbose_name_plural = 'Files'

class Document(models.Model):
    document_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    knowledge_base = models.ForeignKey(KnowledgeBase, on_delete=models.CASCADE, null=False)
    document_name = models.CharField(max_length=255, null=True, blank=False)
    document_location = models.CharField(max_length=255, null=True)
    token_num = models.IntegerField(null=False, default=0)
    chunk_num = models.IntegerField(null=False, default=0)
    is_active = models.BooleanField(default=True)
    parser_config = models.JSONField(blank=False, null=False)
    parser_id = models.CharField(max_length=20, null=False)
    source_type = models.CharField(max_length=128, null=False)
    run_id = models.CharField(max_length=50, null=True)
    #INIT, PARSING, STOPPED, COMPLETED, FAILED
    status = models.CharField(max_length=50, null=True)
    metadata = models.JSONField(null=True)
    progress = models.CharField(max_length=50, null=False)
    progress_msg = models.TextField(null=True)
    progress_begin_at = models.DateTimeField(null=True)
    progress_duration = models.IntegerField(null=True, default=0)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'documents'
        verbose_name = 'Document'
        verbose_name_plural = 'Documents'

class File2Document(models.Model):
    file = models.ForeignKey(File, on_delete=models.CASCADE)
    document = models.ForeignKey(Document, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        db_table = 'file_2_documents'
        verbose_name = 'File2Document'
        verbose_name_plural = 'File2Documents'
        unique_together = ('file', 'document')
    
    
class DocumentChunk(models.Model):
    document_chunk_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    document = models.ForeignKey(Document, on_delete=models.CASCADE)
    chunk_location = models.CharField(max_length=255)
    config = models.JSONField(default=dict)
    status = models.CharField(max_length=255)
    metadata = models.JSONField()
    #INIT, , COMPLETED, FAILED
    progress = models.CharField(max_length=50, default="INIT")
    progress_msg = models.TextField(default='')
    progress_begin_at = models.DateTimeField(null=True)
    progress_duration = models.IntegerField(null=True, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'document_chunks'
        verbose_name = 'Document Chunk'
        verbose_name_plural = 'Document Chunks'
        
        