from django.db import models

from EasyRAG.user_app.models import User
default_template_config = """[
       {
         "key": "supplier",
         "type": "string",
         "description": "The supplier to use",
         "required": true
       },
       {
         "key": "url",
         "type": "string",
         "description": "The url to use",
         "required": true
       },
       {
         "key": "api_key",
         "type": "string",
         "description": "The api key to use",
         "required": false
       }
     ]"""



# Create your models here.
class LLMTemplate(models.Model):
    llm_template_id = models.CharField(max_length=128, primary_key=True)
    template_name = models.CharField(max_length=128, null=False)
    template_code = models.CharField(max_length=20, null=False, unique=True, default='')
    template_logo = models.ImageField(upload_to='llm_templates/', null=True, blank=True)
    template_description = models.TextField(default='', blank=True, null=True)
    llm_template_config = models.JSONField(default=default_template_config) # 模型配置
    llm_status = models.CharField(max_length=50) 
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        db_table = 'llm_templates'
        verbose_name = 'LLM Template'
        verbose_name_plural = 'LLM Templates'

class LLMInstance(models.Model):
    llm_instance_id = models.CharField(max_length=128, primary_key=True)
    llm_template = models.ForeignKey(LLMTemplate, on_delete=models.CASCADE)
    llm_config = models.JSONField() # 模型配置
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    llm_status = models.CharField(max_length=50, default='ACTIVE') 
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'llm_instances'
        verbose_name = 'LLM Instance'
        verbose_name_plural = 'LLM Instances'
        unique_together = ('llm_template', 'created_by')
        
class LLMInstanceLLMModel(models.Model):
    llm_instance_llm_model_id = models.CharField(max_length=128, primary_key=True)
    llm_instance = models.ForeignKey(LLMInstance, on_delete=models.CASCADE)
    llm_model_id = models.CharField(max_length=128, null=False)
    llm_object_id = models.CharField(max_length=128, null=False)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    model_status = models.CharField(max_length=50, default='ACTIVE')
    instance_config = models.JSONField(null=False, blank=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'llm_instance_llm_models'
        verbose_name = 'LLM Instance LLM Model'
        verbose_name_plural = 'LLM Instance LLM Models'
        unique_together = ('llm_instance', 'llm_model_id')
        
class LLMModelUserConfig(models.Model):
    llm_model_user_config_id = models.CharField(max_length=128, primary_key=True)
    llm_instance_llm_model = models.ForeignKey(LLMInstanceLLMModel, on_delete=models.CASCADE)
    config_type = models.CharField(max_length=128, null=False)
    config_value = models.CharField(max_length=128, null=False)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'llm_model_user_configs'
        verbose_name = 'LLM Model User Config'
        verbose_name_plural = 'LLM Model User Configs'
        unique_together = ('config_type', 'owner')
        