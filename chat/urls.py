from rest_framework import routers
from .views import ChatSessionViewSet, MessageViewSet

router = routers.DefaultRouter()
router.register(r'chats', ChatSessionViewSet, basename='chatsession')
router.register(r'messages', MessageViewSet, basename='message')

urlpatterns = router.urls

