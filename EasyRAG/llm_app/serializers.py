from rest_framework import serializers
from .models import LLMInstanceLLMModel, LLMTemplate, LLMInstance, LLMModelUserConfig
from EasyRAG.common.utils import generate_uuid
import logging
logger = logging.getLogger(__name__)

class LLMTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = LLMTemplate
        fields = '__all__'
        read_only_fields = ['llm_template_id', 'created_at', 'updated_at', 'llm_status']
        
    
    def create(self, validated_data):
        # 自动生成 llm_template_id
        validated_data['llm_template_id'] = generate_uuid()
        validated_data['llm_status'] = 'ACTIVE'
        return super().create(validated_data)

class LLMInstanceSerializer(serializers.ModelSerializer):
    llm_template_id = serializers.CharField( required=True)
    
    class Meta:
        model = LLMInstance
        fields = [
            'llm_instance_id',
            'llm_template_id',
            'llm_config',
            'created_by',
            'llm_status',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['llm_instance_id', 'created_at', 'updated_at', 'created_by', 'llm_status']
    
    def create(self, validated_data):
        logger.info(f"In Serializer create llm_instance, validated_data: {validated_data}")
        # 自动生成 llm_instance_id
        validated_data['llm_instance_id'] = generate_uuid()
        
        # 处理 llm_template_id
        llm_template_id = validated_data.pop('llm_template_id')
        logger.info(f"Try to get llm_template by llm_template_id: {llm_template_id}")
        try:
            llm_template = LLMTemplate.objects.get(llm_template_id=llm_template_id)
            validated_data['llm_template'] = llm_template
        except LLMTemplate.DoesNotExist:
            logger.error(f"Create llm_instance, LLM template not found: {llm_template_id}")
            raise serializers.ValidationError(f"LLM template not found: {llm_template_id}")
        
        validated_data['created_by'] = self.context['request'].user
        validated_data['llm_status'] = 'ACTIVE'
        logger.info(f"In Serializer create llm_instance, validated_data: {validated_data}")
        return super().create(validated_data) 
    
class LLMInstanceLLMModelSerializer(serializers.ModelSerializer):
   
    class Meta:
        model = LLMInstanceLLMModel
        fields = [
            'llm_instance_llm_model_id',
            'llm_instance',
            'llm_model_id',
            'owner'
        ]
        read_only_fields = ['llm_instance_llm_model_id','created_at', 'updated_at']

class LLMModelUserConfigSerializer(serializers.ModelSerializer):
    llm_instance_id = serializers.CharField(required=True)
    llm_model_id = serializers.CharField(required=True)
    
    class Meta:
        model = LLMModelUserConfig
        fields = [
            'llm_model_user_config_id',
            'llm_instance_id',
            'llm_model_id',
            'config_type',
            'config_value',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['llm_model_user_config_id', 'created_at', 'updated_at']
    
    def create(self, validated_data):
        logger.info(f"In Serializer create llm_model_user_config, validated_data: {validated_data}")
        # 这个序列化器主要用于接收数据，实际的创建逻辑在viewmodel中处理
        # 这里只设置基本字段
        validated_data['owner'] = self.context['request'].user
        validated_data['llm_model_user_config_id'] = generate_uuid()
        
        # 注意：这里不会真正创建对象，因为实际的创建逻辑在viewmodel中
        # 这里只是为了满足序列化器的要求
        return super().create(validated_data)