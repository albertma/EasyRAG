from rest_framework.routers import DefaultRouter
from .views import LLMTemplateViewSet, LLMInstanceViewSet, LLMModelUserConfigViewSet, LLMInstanceLLMModelViewSet

router = DefaultRouter()
router.register(r'llm-templates', LLMTemplateViewSet, basename='llmtemplate')
router.register(r'llm-instances', LLMInstanceViewSet, basename='llminstance')
router.register(r'llm-model-user-configs', LLMModelUserConfigViewSet, basename='llmmodeluserconfig')
router.register(r'llm-instance-llm-models', LLMInstanceLLMModelViewSet, basename='llminstancellmmodel')

urlpatterns = router.urls