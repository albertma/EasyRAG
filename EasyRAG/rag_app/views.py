from rest_framework import viewsets, permissions, generics, filters
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from EasyRAG.common.permissions import KnowledgeBasePermission, FileStoragePermission, DocumentPermission
from .models import KnowledgeBase, Document
from .serializers import KnowledgeBaseSerializer, DocumentSerializer
from rest_framework.views import APIView
import logging
from .viewmodels import KnowledgeBaseViewModel, FileUploadViewModel, DocumentViewModel

logger = logging.getLogger(__name__)

class KnowledgeBaseViewSet(viewsets.ModelViewSet):
    """
    知识库管理 API
    
    提供知识库的创建、读取、更新和删除操作。
    """
    queryset = KnowledgeBase.objects.all()
    serializer_class = KnowledgeBaseSerializer
    permission_classes = [permissions.IsAuthenticated, KnowledgeBasePermission]

    def get_viewmodel(self):
        """获取视图模型实例"""
        return KnowledgeBaseViewModel(self.request.user)

    @swagger_auto_schema(
        operation_description="获取知识库列表",
        operation_summary="获取知识库列表",
        responses={
            200: KnowledgeBaseSerializer(many=True),
            401: "未认证",
            403: "权限不足"
        },
        tags=['知识库管理']
    )
    def list(self, request, *args, **kwargs):
        # 检查是否是Swagger schema生成
        if getattr(self, 'swagger_fake_view', False):
            return Response([], status=200)
            
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="创建新的知识库",
        operation_summary="创建知识库",
        request_body=KnowledgeBaseSerializer,
        responses={
            201: KnowledgeBaseSerializer,
            400: "请求数据无效",
            401: "未认证",
            403: "权限不足"
        },
        tags=['知识库管理']
    )
    def create(self, request, *args, **kwargs):
        # 检查是否是Swagger schema生成
        if getattr(self, 'swagger_fake_view', False):
            return Response({'message': 'Swagger schema generation'}, status=201)
            
        viewmodel = self.get_viewmodel()
        try:
            knowledge_base = viewmodel.create_knowledge_base(request.data)
            serializer = self.get_serializer(knowledge_base)
            return Response(serializer.data, status=201)
        except Exception as e:
            return Response({'error': str(e)}, status=400)

    @swagger_auto_schema(
        operation_description="获取指定知识库详情",
        operation_summary="获取知识库详情",
        responses={
            200: KnowledgeBaseSerializer,
            404: "知识库不存在",
            401: "未认证",
            403: "权限不足"
        },
        tags=['知识库管理']
    )
    def retrieve(self, request, *args, **kwargs):
        # 检查是否是Swagger schema生成
        if getattr(self, 'swagger_fake_view', False):
            return Response({'message': 'Swagger schema generation'}, status=200)
            
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="更新知识库",
        operation_summary="更新知识库",
        request_body=KnowledgeBaseSerializer,
        responses={
            200: KnowledgeBaseSerializer,
            400: "请求数据无效",
            401: "未认证",
            403: "权限不足",
            404: "知识库不存在"
        },
        tags=['知识库管理']
    )
    def update(self, request, *args, **kwargs):
        # 检查是否是Swagger schema生成
        if getattr(self, 'swagger_fake_view', False):
            return Response({'message': 'Swagger schema generation'}, status=200)
            
        viewmodel = self.get_viewmodel()
        try:
            knowledge_base = viewmodel.update_knowledge_base(kwargs['pk'], request.data)
            serializer = self.get_serializer(knowledge_base)
            return Response(serializer.data, status=200)
        except Exception as e:
            return Response({'error': str(e)}, status=400)

    @swagger_auto_schema(
        operation_description="删除知识库",
        operation_summary="删除知识库",
        responses={
            204: "删除成功",
            401: "未认证",
            403: "权限不足",
            404: "知识库不存在"
        },
        tags=['知识库管理']
    )
    def destroy(self, request, *args, **kwargs):
        # 检查是否是Swagger schema生成
        if getattr(self, 'swagger_fake_view', False):
            return Response(status=204)
            
        viewmodel = self.get_viewmodel()
        try:
            success = viewmodel.delete_knowledge_base(kwargs['pk'])
            if success:
                return Response(status=204)
            else:
                return Response({'error': '删除失败'}, status=400)
        except Exception as e:
            return Response({'error': str(e)}, status=400)

    def get_queryset(self):
        """根据用户权限过滤知识库"""
        viewmodel = self.get_viewmodel()
        return viewmodel.get_queryset(getattr(self, 'swagger_fake_view', False))

class MultiFileUploadView(APIView):
    permission_classes = [permissions.IsAuthenticated, FileStoragePermission]

    def get_viewmodel(self):
        """获取视图模型实例"""
        return FileUploadViewModel(self.request.user)

    @swagger_auto_schema(
        operation_description="批量上传文件到知识库",
        operation_summary="批量上传文件",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'files': openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(type=openapi.TYPE_FILE),
                    description="要上传的文件列表（最多20个文件，每个文件最大20MB）"
                ),
                'knowledge_base_id': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    format=openapi.FORMAT_UUID,
                    description="目标知识库ID"
                ),
            },
            required=['files', 'knowledge_base_id']
        ),
        responses={
            201: openapi.Response(
                description="所有文件上传成功",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'documents': openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    'document_id': openapi.Schema(type=openapi.TYPE_STRING),
                                    'document_name': openapi.Schema(type=openapi.TYPE_STRING),
                                    'document_location': openapi.Schema(type=openapi.TYPE_STRING),
                                }
                            )
                        ),
                        'total_files': openapi.Schema(type=openapi.TYPE_INTEGER, description="总文件数"),
                        'successful_uploads': openapi.Schema(type=openapi.TYPE_INTEGER, description="成功上传数"),
                        'failed_uploads': openapi.Schema(type=openapi.TYPE_INTEGER, description="失败上传数")
                    }
                )
            ),
            207: openapi.Response(
                description="部分文件上传成功",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'documents': openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    'document_id': openapi.Schema(type=openapi.TYPE_STRING),
                                    'document_name': openapi.Schema(type=openapi.TYPE_STRING),
                                    'document_location': openapi.Schema(type=openapi.TYPE_STRING),
                                }
                            )
                        ),
                        'total_files': openapi.Schema(type=openapi.TYPE_INTEGER, description="总文件数"),
                        'successful_uploads': openapi.Schema(type=openapi.TYPE_INTEGER, description="成功上传数"),
                        'failed_uploads': openapi.Schema(type=openapi.TYPE_INTEGER, description="失败上传数"),
                        'failed_files': openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    'file_name': openapi.Schema(type=openapi.TYPE_STRING),
                                    'error': openapi.Schema(type=openapi.TYPE_STRING)
                                }
                            ),
                            description="失败的文件列表"
                        )
                    }
                )
            ),
            400: "请求参数错误或文件过大",
            401: "未认证",
            403: "权限不足",
            404: "知识库不存在"
        },
        tags=['文件管理']
    )
    def post(self, request, *args, **kwargs):
        # 检查是否是Swagger schema生成
        if getattr(self, 'swagger_fake_view', False):
            return Response({'documents': []}, status=201)
            
        files = request.FILES.getlist('files')
        knowledge_base_id = request.data.get('knowledge_base_id')
        
        viewmodel = self.get_viewmodel()
        try:
            result = viewmodel.process_batch_upload(files, knowledge_base_id)
            
            # 根据是否有失败的文件决定返回状态码
            if result.get('failed_files'):
                return Response(result, status=207)  # Multi-Status
            else:
                return Response(result, status=201)  # Created
                
        except Exception as e:
            return Response({'error': str(e)}, status=400)

class DocumentListByKnowledgeBaseView(generics.ListAPIView):
    serializer_class = DocumentSerializer
    permission_classes = [permissions.IsAuthenticated, DocumentPermission]
    filter_backends = [filters.SearchFilter]
    search_fields = ['document_name']
    page_size = 10

    def get_viewmodel(self):
        """获取视图模型实例"""
        return DocumentViewModel(self.request.user)

    @swagger_auto_schema(
        operation_description="获取指定知识库下的文档列表",
        operation_summary="获取知识库文档列表",
        manual_parameters=[
            openapi.Parameter(
                'knowledge_base_id',
                openapi.IN_PATH,
                description="知识库ID",
                type=openapi.TYPE_STRING,
                format=openapi.FORMAT_UUID,
                required=True
            ),
            openapi.Parameter(
                'search',
                openapi.IN_QUERY,
                description="搜索文档名称",
                type=openapi.TYPE_STRING,
                required=False
            ),
            openapi.Parameter(
                'page',
                openapi.IN_QUERY,
                description="页码",
                type=openapi.TYPE_INTEGER,
                required=False
            ),
            openapi.Parameter(
                'page_size',
                openapi.IN_QUERY,
                description="每页数量",
                type=openapi.TYPE_INTEGER,
                required=False
            ),
        ],
        responses={
            200: DocumentSerializer(many=True),
            400: "知识库ID格式错误",
            401: "未认证",
            403: "权限不足",
            404: "知识库不存在"
        },
        tags=['文档管理']
    )
    def get(self, request, *args, **kwargs):
        # 检查是否是Swagger schema生成
        if getattr(self, 'swagger_fake_view', False):
            return Response([], status=200)
            
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        viewmodel = self.get_viewmodel()
        knowledge_base_id = self.kwargs.get('knowledge_base_id')
        
        try:
            return viewmodel.get_documents_by_knowledge_base(
                knowledge_base_id, 
                getattr(self, 'swagger_fake_view', False)
            )
        except Exception as e:
            # 如果获取失败，返回空查询集
            return Document.objects.none()

    def get_paginate_by(self, queryset):
        return self.request.query_params.get('page_size', 10)

class DocumentActionView(APIView):
    permission_classes = [permissions.IsAuthenticated, DocumentPermission]

    def get_viewmodel(self):
        """获取视图模型实例"""
        return DocumentViewModel(self.request.user)

    """
    文档操作API
    
    提供文档的解析、删除操作。
    """
    
    @swagger_auto_schema(
        operation_description="对文档执行操作（开始解析、停止解析、删除、继续解析）",
        operation_summary="文档操作",
        manual_parameters=[
            openapi.Parameter(
                'document_id',
                openapi.IN_PATH,
                description="文档ID",
                type=openapi.TYPE_STRING,
                required=True
            ),
        ],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'action': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="操作类型",
                    enum=['start_parse', 'stop_parse', 'delete', 'resume_parse']
                )
                
            },
            required=['action']
        ),
        responses={
            200: DocumentSerializer,
            400: "请求参数错误",
            401: "未认证",
            403: "权限不足",
            404: "文档不存在"
        },
        tags=['文档管理']
    )
    def put(self, request, *args, **kwargs):
        # 检查是否是Swagger schema生成
        if getattr(self, 'swagger_fake_view', False):
            return Response({}, status=200)
            
        document_id = kwargs.get('document_id')
        action = request.data.get("action")
        
        if not action:
            return Response({'error': 'action is required'}, status=400)
        
        action = action.lower()
        if action not in ["start_parse", "stop_parse", "delete", "refresh"]:
            return Response({'error': 'action is invalid'}, status=400)
        
        viewmodel = self.get_viewmodel()
        try:
            result = viewmodel.perform_document_action(document_id, action)
            
            if action == "delete":
                return Response({'message': '文档删除成功'}, status=200)
            else:
                serializer = DocumentSerializer(result)
                return Response(serializer.data, status=200)
                
        except Exception as e:
            return Response({'error': str(e)}, status=400)



