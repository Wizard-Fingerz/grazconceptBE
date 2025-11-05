"""
ASGI config for globalconceptBE project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/asgi/
"""

import os
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application
from channels.auth import AuthMiddlewareStack

import notification.routing
import chat.routing  # Include chat websocket routing

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'globalconceptBE.settings')

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(
            notification.routing.websocket_urlpatterns +
            chat.routing.websocket_urlpatterns
        )
    ),
})
