"""
ASGI config for globalconceptBE project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/asgi/
"""

import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack

# ✅ Step 1: Set up Django environment first
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'globalconceptBE.settings')

# ✅ Step 2: Initialize Django (loads apps, models, etc.)
django_asgi_app = get_asgi_application()

# ✅ Step 3: Import routing *after* Django is ready
import notification.routing
import chat.routing
from app import routings as app_routings  # import the module, not directly the list

# ✅ Step 4: Combine all websocket patterns safely
application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AuthMiddlewareStack(
        URLRouter(
            notification.routing.websocket_urlpatterns +
            chat.routing.websocket_urlpatterns +
            app_routings.websocket_urlpatterns
        )
    ),
})
