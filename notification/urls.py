from rest_framework.routers import DefaultRouter
from django.urls import path
from .views import NotificationViewSet, websocket_info, websocket_doc

router = DefaultRouter()
router.register(r'notifications', NotificationViewSet, basename='notification')

urlpatterns = router.urls + [
    path('ws-info/', websocket_info, name='websocket-info'),
    path('ws-doc/', websocket_doc, name='websocket-docs'),
]
