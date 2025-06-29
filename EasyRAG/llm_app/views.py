from rest_framework import viewsets, permissions, serializers
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from .models import LLMInstanceLLMModel, LLMModelUserConfig, LLMTemplate, LLMInstance
from .serializers import LLMInstanceLLMModelSerializer, LLMModelUserConfigSerializer, LLMTemplateSerializer, LLMInstanceSerializer
from .viewmodel import LLMInstanceViewModel, LLMModelUserConfigViewModel, LLMInstanceLLMModelViewModel
import logging
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.contrib.auth.models import User

logger = logging.getLogger(__name__)

class LLMInstancePagination(PageNumberPagination):
    """LLM实例分页器"""
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100
    page_query_param = 'page'

class LLMTemplateViewSet(viewsets.ModelViewSet):
    queryset = LLMTemplate.objects.all()
    serializer_class = LLMTemplateSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ['get', 'post', 'delete']
    
    def perform_create(self, serializer):
        serializer.save()
    
    @swagger_auto_schema(
        operation_description="创建新的 LLM 模板",
        operation_summary="创建 LLM 模板",
        request_body=LLMTemplateSerializer,
        responses={201: LLMTemplateSerializer},
        tags=['LLM 模板管理']
    )
    def create(self, request, *args, **kwargs):
        if getattr(self, 'swagger_fake_view', False):
            return Response({}, status=201)
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="获取 LLM 模板列表",
        operation_summary="获取 LLM 模板列表",
        responses={200: LLMTemplateSerializer(many=True)},
        tags=['LLM 模板管理']
    )
    def list(self, request, *args, **kwargs):
        if getattr(self, 'swagger_fake_view', False):
            return Response([], status=200)
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="获取单个 LLM 模板详情",
        operation_summary="获取 LLM 模板详情",
        responses={200: LLMTemplateSerializer},
        tags=['LLM 模板管理']
    )
    def retrieve(self, request, *args, **kwargs):
        if getattr(self, 'swagger_fake_view', False):
            return Response({}, status=200)
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="删除 LLM 模板",
        operation_summary="删除 LLM 模板",
        tags=['LLM 模板管理']
    )
    def destroy(self, request, *args, **kwargs):
        if getattr(self, 'swagger_fake_view', False):
            return Response({}, status=204)
        return super().destroy(request, *args, **kwargs)

class LLMInstanceViewSet(viewsets.ModelViewSet):
    serializer_class = LLMInstanceSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = LLMInstancePagination
    http_method_names = ['get', 'post', 'delete']
    llm_instance_view_model = LLMInstanceViewModel()

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return LLMInstance.objects.none()
        
        # 超级用户可以查看所有实例
        if self.request.user.is_superuser:
            return LLMInstance.objects.all()
        
        # 普通用户只能查看自己的实例
        return LLMInstance.objects.filter(created_by=self.request.user)

    def perform_create(self, serializer):
        """执行实例创建，委托给viewmodel处理"""
        logger.info(f"In view perform_create, delegating to viewmodel")
        return self.llm_instance_view_model.perform_create(serializer)

    @swagger_auto_schema(
        operation_description="创建新的 LLM 实例",
        operation_summary="创建 LLM 实例",
        request_body=LLMInstanceSerializer,
        responses={201: LLMInstanceSerializer},
        tags=['LLM 实例管理']
    )
    def create(self, request, *args, **kwargs):
        if getattr(self, 'swagger_fake_view', False):
            return Response({}, status=201)
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="获取 LLM 实例列表（分页显示，超级用户可查看所有，普通用户只能查看自己的）",
        operation_summary="获取 LLM 实例列表",
        manual_parameters=[
            openapi.Parameter(
                'page',
                openapi.IN_QUERY,
                description='页码（默认1）',
                required=False,
                type=openapi.TYPE_INTEGER
            ),
            openapi.Parameter(
                'page_size',
                openapi.IN_QUERY,
                description='每页数量（默认10，最大100）',
                required=False,
                type=openapi.TYPE_INTEGER
            ),
            openapi.Parameter(
                'created_by',
                openapi.IN_QUERY,
                description='按创建者过滤（用户ID，仅超级用户可用）',
                required=False,
                type=openapi.TYPE_INTEGER
            ),
            openapi.Parameter(
                'llm_status',
                openapi.IN_QUERY,
                description='按状态过滤',
                required=False,
                type=openapi.TYPE_STRING
            ),
            openapi.Parameter(
                'template_id',
                openapi.IN_QUERY,
                description='按模板ID过滤',
                required=False,
                type=openapi.TYPE_STRING
            )
        ],
        responses={200: LLMInstanceSerializer(many=True)},
        tags=['LLM 实例管理']
    )
    def list(self, request, *args, **kwargs):
        if getattr(self, 'swagger_fake_view', False):
            return Response([], status=200)
        
        # 获取查询参数
        created_by = request.query_params.get('created_by')
        llm_status = request.query_params.get('llm_status')
        template_id = request.query_params.get('template_id')
        
        # 构建查询集
        queryset = self.get_queryset()
        
        # 权限验证：只有超级用户可以使用created_by参数
        if created_by and not request.user.is_superuser:
            return Response(
                {'error': 'Only superusers can filter by created_by'}, 
                status=403
            )
        
        # 如果指定了created_by参数且是超级用户，则按该参数过滤
        if created_by and request.user.is_superuser:
            try:
                created_by_id = int(created_by)
                queryset = LLMInstance.objects.filter(created_by_id=created_by_id)
            except ValueError:
                return Response({'error': 'created_by must be a valid integer'}, status=400)
        
        # 按状态过滤
        if llm_status:
            queryset = queryset.filter(llm_status=llm_status)
        
        # 按模板ID过滤
        if template_id:
            queryset = queryset.filter(llm_template__llm_template_id=template_id)
        
        # 分页
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        # 如果没有分页，直接返回
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_description="获取单个 LLM 实例详情（权限验证：超级用户可查看所有，普通用户只能查看自己的）",
        operation_summary="获取 LLM 实例详情",
        responses={200: LLMInstanceSerializer},
        tags=['LLM 实例管理']
    )
    def retrieve(self, request, *args, **kwargs):
        if getattr(self, 'swagger_fake_view', False):
            return Response({}, status=200)
        
        instance = self.get_object()
        
        # 权限验证：普通用户只能查看自己的实例
        if not request.user.is_superuser and instance.created_by != request.user:
            return Response({'error': 'You do not have permission to view this instance'}, status=403)
        
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="删除 LLM 实例（权限验证：超级用户可删除所有，普通用户只能删除自己的）",
        operation_summary="删除 LLM 实例",
        tags=['LLM 实例管理']
    )
    def destroy(self, request, *args, **kwargs):
        if getattr(self, 'swagger_fake_view', False):
            return Response({}, status=204)
        
        instance = self.get_object()
        
        # 权限验证：普通用户只能删除自己的实例
        if not request.user.is_superuser and instance.created_by != request.user:
            return Response({'error': 'You do not have permission to delete this instance'}, status=403)
        
        return super().destroy(request, *args, **kwargs)

class LLMInstanceLLMModelViewSet(viewsets.ModelViewSet):
    serializer_class = LLMInstanceLLMModelSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ['get']
    pagination_class = None  # 禁用分页
    llm_instance_llm_model_view_model = LLMInstanceLLMModelViewModel()
    
    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return LLMInstanceLLMModel.objects.none()
        return LLMInstanceLLMModel.objects.filter(owner=self.request.user)
    
    @swagger_auto_schema(
        operation_description="获取用户的所有LLM模型数据，按instance_id分类",
        operation_summary="获取用户LLM模型数据",
        manual_parameters=[
            openapi.Parameter(
                'user_id',
                openapi.IN_QUERY,
                description='用户ID（仅超级用户可用，不传则获取当前用户数据）',
                required=False,
                type=openapi.TYPE_INTEGER
            ),
            openapi.Parameter(
                'group_by_instance',
                openapi.IN_QUERY,
                description='是否按instance_id分组（默认true）',
                required=False,
                type=openapi.TYPE_BOOLEAN
            )
        ],
        tags=['LLM 模型管理'],
        responses={200: LLMInstanceLLMModelSerializer(many=True)}
    )
    def list(self, request, *args, **kwargs):
        if getattr(self, 'swagger_fake_view', False):
            return Response([], status=200)
        
        # 获取查询参数
        user_id = request.query_params.get('user_id')
        group_by_instance = request.query_params.get('group_by_instance', 'true').lower() == 'true'
        
        # 确定要查询的用户
        target_user = None
        if user_id:
            # 只有超级用户可以查询其他用户的数据
            if not request.user.is_superuser:
                return Response(
                    {'error': 'Only superusers can query other users data'}, 
                    status=403
                )
            try:
                target_user = User.objects.get(id=int(user_id))
            except (ValueError, User.DoesNotExist):
                return Response({'error': 'Invalid user_id'}, status=400)
        
        # 委托给viewmodel处理
        result = self.llm_instance_llm_model_view_model.get_user_llm_models(
            user=request.user,
            target_user=target_user,
            group_by_instance=group_by_instance
        )
        
        return Response(result)

class LLMModelUserConfigViewSet(viewsets.ModelViewSet):
    serializer_class = LLMModelUserConfigSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ['get', 'post', 'delete']
    user_config_view_model = LLMModelUserConfigViewModel()

    
    
    @swagger_auto_schema(
        operation_description="获取 LLM 模型用户配置列表",
        operation_summary="获取 LLM 模型用户配置列表",
        tags=['LLM 模型用户配置管理'],
        responses={
            200: openapi.Response(
                description="用户配置列表",
                schema=openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            'llm_model_user_config_id': openapi.Schema(
                                type=openapi.TYPE_STRING,
                                description='配置ID'
                            ),
                            'config_type': openapi.Schema(
                                type=openapi.TYPE_STRING,
                                description='配置类型'
                            ),
                            'config_value': openapi.Schema(
                                type=openapi.TYPE_STRING,
                                description='配置值'
                            )
                           
                        }
                    )
                )
            )
        }
    )
    def list(self, request, *args, **kwargs):
        if getattr(self, 'swagger_fake_view', False):
            return Response([], status=200)
        llm_model_user_configs = LLMModelUserConfig.objects.filter(owner=self.request.user)
        configure_list = []
        for llm_model_user_config in llm_model_user_configs:
            configure_list.append({
                'llm_model_user_config_id': llm_model_user_config.llm_model_user_config_id,
                'config_type': llm_model_user_config.config_type,
                'config_value': llm_model_user_config.config_value,
                'instance_config': llm_model_user_config.instance_config
            })
        return Response(configure_list)
    
    @swagger_auto_schema(
        operation_description="创建新的 LLM 模型用户配置",
        operation_summary="创建 LLM 模型用户配置",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'configure_list': openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    description='配置列表',
                    items=openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            'llm_instance_id': openapi.Schema(
                                type=openapi.TYPE_STRING,
                                description='LLM实例ID'
                            ),
                            'llm_model_id': openapi.Schema(
                                type=openapi.TYPE_STRING,
                                description='LLM模型ID'
                            ),
                            'config_type': openapi.Schema(
                                type=openapi.TYPE_STRING,
                                description='配置类型（CHAT/EMBEDDING/RERANK/IMG_TO_TEXT/SPEECH_TO_TEXT）',
                                enum=['CHAT', 'EMBEDDING', 'RERANK', 'IMG_TO_TEXT', 'SPEECH_TO_TEXT']
                            ),
                            'config_value': openapi.Schema(
                                type=openapi.TYPE_STRING,
                                description='配置值（如模型名称）'
                            )
                        },
                        required=['llm_instance_id', 'llm_model_id', 'config_type', 'config_value']
                    )
                )
            },
            required=['configure_list']
        ),
        responses={201: LLMModelUserConfigSerializer},
        tags=['LLM 模型用户配置管理']
    )
    def create(self, request, *args, **kwargs):
        if getattr(self, 'swagger_fake_view', False):
            return Response({}, status=201)
        return super().create(request, *args, **kwargs)
    
    def perform_create(self, serializer):
        """执行用户配置创建，委托给viewmodel处理"""
        logger.info(f"In view perform_create, delegating to viewmodel")
        try:
            # 获取配置列表
            configure_list = serializer.validated_data.get('configure_list')
            
            # 委托给viewmodel处理
            return self.user_config_view_model.perform_create_after_delete(configure_list, self.request.user)
        except Exception as e:
            logger.error(f"Error in perform_create: {e}")
            raise serializers.ValidationError(f"Error in perform_create: {e}")

    @swagger_auto_schema(
        operation_description="删除 LLM 模型用户配置",
        operation_summary="删除 LLM 模型用户配置",
        tags=['LLM 模型用户配置管理']
    )
    def destroy(self, request, *args, **kwargs):
        if getattr(self, 'swagger_fake_view', False):
            return Response({}, status=204)
        
        instance = self.get_object()
        
        # 权限验证：用户只能删除自己的配置
        if instance.owner != request.user:
            return Response({'error': 'You do not have permission to delete this config'}, status=403)
        
        return self.user_config_view_model.delete_llm_model_user_config(instance.llm_model_user_config_id)