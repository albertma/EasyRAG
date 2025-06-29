from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .serializers import UserCreateSerializer

# Create your views here.

class IsSuperUser(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_superuser

class CustomTokenObtainPairView(TokenObtainPairView):
    """
    自定义 JWT Token 获取视图
    为 Swagger 提供更好的文档支持
    """
    
    @swagger_auto_schema(
        operation_description="获取 JWT 访问令牌",
        operation_summary="获取访问令牌",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['username', 'password'],
            properties={
                'username': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="用户名"
                ),
                'password': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="密码",
                    format=openapi.FORMAT_PASSWORD
                ),
            }
        ),
        responses={
            200: openapi.Response(
                description="获取令牌成功",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'access': openapi.Schema(
                            type=openapi.TYPE_STRING,
                            description="访问令牌"
                        ),
                        'refresh': openapi.Schema(
                            type=openapi.TYPE_STRING,
                            description="刷新令牌"
                        ),
                    }
                )
            ),
            401: "用户名或密码错误",
            400: "请求数据无效"
        },
        tags=['认证']
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)

class UserCreateView(generics.CreateAPIView):
    serializer_class = UserCreateSerializer
    permission_classes = [IsSuperUser]

    @swagger_auto_schema(
        operation_description="创建新用户（仅超级用户可用）",
        operation_summary="创建用户",
        request_body=UserCreateSerializer,
        responses={
            201: UserCreateSerializer,
            400: "请求数据无效",
            401: "未认证",
            403: "权限不足（需要超级用户权限）"
        },
        tags=['用户管理']
    )
    def post(self, request, *args, **kwargs):
        # 检查是否是Swagger schema生成
        if getattr(self, 'swagger_fake_view', False):
            return Response({'message': 'Swagger schema generation'}, status=201)
            
        return super().post(request, *args, **kwargs)
