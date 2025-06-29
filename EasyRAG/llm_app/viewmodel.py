from typing import List
import openai
import logging
from rest_framework import serializers
from rest_framework.exceptions import ValidationError as DRFValidationError
from django.db import transaction
import openai.cli

from EasyRAG.llm_app.models import LLMInstance, LLMInstanceLLMModel, LLMModelUserConfig, LLMTemplate
from EasyRAG.user_app.models import User
from EasyRAG.common.utils import generate_uuid

logger = logging.getLogger(__name__)
#define valid model types
LLM_CHAT_MODEL_TYPE = 'CHAT'
LLM_EMBEDDING_MODEL_TYPE = 'EMBEDDING'
LLM_RERANK_MODEL_TYPE = 'RERANK'
LLM_IMG_TO_TEXT_MODEL_TYPE = 'IMG_TO_TEXT'
LLM_SPEECH_TO_TEXT_MODEL_TYPE = 'SPEECH_TO_TEXT'

class LLMInstanceViewModel:
    """LLM实例视图模型"""

    def perform_create(self, serializer):
        """执行实例创建逻辑"""
        logger.info(f"In viewmodel perform_create, serializer: {serializer.validated_data}")
        
        # 先进行验证，不保存到数据库
        validated_data = serializer.validated_data
        
        # 处理 llm_template_id 获取模板
        llm_template_id = validated_data.get('llm_template_id')
        if not llm_template_id:
            logger.error("LLM template ID not found in validated_data")
            raise serializers.ValidationError("LLM template ID is required")
        
        try:
            llm_template = LLMTemplate.objects.get(llm_template_id=llm_template_id)
        except LLMTemplate.DoesNotExist:
            logger.error(f"LLM template not found: {llm_template_id}")
            raise serializers.ValidationError(f"LLM template not found: {llm_template_id}")
        
        logger.info(f"In viewmodel perform_create, llm_template: {llm_template.template_name}")
        
        # 验证配置格式
        llm_template_config = llm_template.llm_template_config
        user_config = validated_data.get('llm_config', {})
        
        for template_config in llm_template_config:
            if not self._check_config(template_config['key'], template_config['type'], template_config['required'], user_config):
                logger.error(f"Invalid config: {template_config}, config: {user_config}")
                raise serializers.ValidationError(f"Invalid config: {template_config['key']}")
        
        try:
            llm_models = self._get_llm_models(user_config, llm_template.template_name)
            if not llm_models:
                logger.error(f"Connection verification failed for config: {user_config}")
                raise serializers.ValidationError(f"Connection verification failed for the provided configuration")
            with transaction.atomic():
                instance = serializer.save()
                logger.info(f"In viewmodel perform_create, llm instance: {instance.llm_instance_id}")
                if not self._save_llm_model(llm_models, instance):
                    logger.error(f"LLM instance creation failed: {instance.llm_instance_id}")
                    raise DRFValidationError(f"LLM instance creation failed: {instance.llm_instance_id}")
                return instance 
        except Exception as e:
            logger.error(f"LLM instance creation failed: {e}")
            raise DRFValidationError(f"LLM instance creation failed: {e}")
    
   
            

    def _check_config(self, key, type_name, required, config):
        """检查配置字段"""
        logger.info(f"In _check_config, key: {key}, type: {type_name}, required: {required}, config: {config}")
        key_exist = key in config.keys()
        
        # 如果字段不存在
        if not key_exist:
            # 非必填字段不存在是允许的
            if required == "false":
                return True
            # 必填字段不存在是不允许的
            return False
        
        # 字段存在，检查值
        key_value = config[key]
        
        # 必填字段必须有值且不能为None或空字符串
        if required == "true" and (key_value is None or key_value == ""):
            return False
        elif required == "false" and (key_value is None or key_value == ""):
            return True
        
        # 类型校验
        if type_name == 'string' and not isinstance(key_value, str):
            return False
        if type_name == 'number' and not isinstance(key_value, int):
            return False
        if type_name == 'boolean' and not isinstance(key_value, bool):
            return False
        
        return True
        
    def _get_llm_models(self, llm_config:dict, template_name:str)->List[dict]:
        """验证实例是否可以连接"""
        logger.info(f"In verify_instance_by_try_connect, template_name: {template_name}")
        if template_name.lower() == "siliconflow":
            url = llm_config["url"]
            api_key = llm_config["api_key"]
            if url is None or api_key is None:
                return []
            llm_models = self._openai_compatible_get_models(url, api_key)
            return llm_models
        else:
            return []
            
    def _openai_compatible_get_models(self, url:str, api_key:str)->List[str]:
        logger.info(f"API Key compatible connect, url: {url}, api_key: {api_key}")
        client = openai.OpenAI(api_key=api_key, base_url=url)
        try:
            llm_models = client.models.list()
            # use set to remove duplicate llm_model_id
            llm_models_list = list(set([llm_model.id for llm_model in llm_models]))
            logger.info(f"API Key compatible connect, llm_models: {llm_models}")
            
            return llm_models_list
        except Exception as e:
            logger.error(f"API Key compatible connect, error: {e}")
            return None
    
    def _save_llm_model(self, llm_models:List[str], llm_instance:LLMInstance)->bool:
        """保存模型"""
        logger.info(f"In _save_llm_model, llm_models: {llm_models}")
        for llm_model in llm_models:
            instance_llm_model = LLMInstanceLLMModel.objects.create(
                llm_instance_llm_model_id=generate_uuid(),
                llm_instance=llm_instance,
                llm_model_id=llm_model,
                llm_object_id="model",
                owner=llm_instance.created_by,
                instance_config=llm_instance.llm_config,
                model_status='ACTIVE'
            )
            instance_llm_model.save()
        
        return True
    

class LLMModelUserConfigViewModel:
    """LLM模型用户配置视图模型"""

    def perform_create_after_delete(self, llm_instance:LLMInstance, llm_model_id:str, user:User)->bool:
        """配置用户模型"""
        logger.info(f"In config_user_llm_model, llm_instance: {llm_instance}, llm_model_id: {llm_model_id}")
        
        # 验证配置类型和权限
        try:
            instance_llm_model = LLMInstanceLLMModel.objects.get(llm_instance=llm_instance, llm_model_id=llm_model_id)
            if instance_llm_model.owner != user:
                logger.error(f"instance_llm_model.owner: {instance_llm_model.owner}, user: {user}")
                raise serializers.ValidationError(f"You do not have permission to create user config for this instance")
        except LLMInstanceLLMModel.DoesNotExist:
            logger.error(f"LLM model not found: {llm_model_id}")
            raise serializers.ValidationError(f"LLM model not found: {llm_model_id}")

        try:
            with transaction.atomic():
                # 删除现有配置
                LLMModelUserConfig.objects.filter(owner=user).delete()
                
                # 创建新配置
                user_config = LLMModelUserConfig.objects.create(
                    llm_instance_llm_model=instance_llm_model,
                    config_type='CHAT',  # 默认配置类型
                    config_value=llm_model_id,
                    owner=user)
                user_config.save()
                return True
        except Exception as e:
            logger.error(f"LLM model user config creation failed: {e}")
            raise DRFValidationError(f"LLM model user config creation failed: {e}")
        
    def delete_llm_model_user_config(self, llm_model_user_config_id:str)->bool:
        """删除模型用户配置"""
        logger.info(f"In delete_llm_model_user_config(), llm_model_user_config_id: {llm_model_user_config_id}")
        try:
            llm_model_user_config = LLMModelUserConfig.objects.get(llm_model_user_config_id=llm_model_user_config_id)
            llm_model_user_config.delete()
            return True
        except LLMModelUserConfig.DoesNotExist:
            logger.error(f"LLM model user config not found: {llm_model_user_config_id}")
            raise DRFValidationError(f"LLM model user config not found: {llm_model_user_config_id}")