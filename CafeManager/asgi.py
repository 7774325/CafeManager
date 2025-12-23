import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import karaoke.routing

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'CafeManager.settings')

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(
            karaoke.routing.websocket_urlpatterns
        )
    ),
})