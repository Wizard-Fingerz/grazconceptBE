from django.urls import re_path

from . import consumers

websocket_urlpatterns = [
    # WebSocket endpoint for a specific chat session (customer <-> agent)
    re_path(
        r"ws/chat/(?P<chat_id>[0-9a-f-]+)/(?P<user_id>[0-9]+)/$",
        consumers.ChatConsumer.as_asgi(),
    ),
    # WebSocket endpoint for managing/listing a user's chat sessions
    re_path(
        r"ws/chat_sessions/(?P<user_id>[0-9]+)/$",
        consumers.ChatSessionListConsumer.as_asgi(),
    ),
]
