from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DocumentActionView, KnowledgeBaseViewSet, MultiFileUploadView, DocumentListByKnowledgeBaseView

router = DefaultRouter()
router.register(r'knowledge-bases', KnowledgeBaseViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('kb-files-upload/', MultiFileUploadView.as_view(), name='kb-files-upload'),
    path('documents/by-kb/<str:knowledge_base_id>/', DocumentListByKnowledgeBaseView.as_view(), name='document-list-by-kb'),
    path('documents/<str:document_id>/', DocumentActionView.as_view(), name='document-action'),
] 