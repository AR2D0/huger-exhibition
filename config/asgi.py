import os

from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

django_asgi_app = get_asgi_application()

try:
    from exhibition import routing as exhibition_routing
except Exception:  # pragma: no cover - during initial setup
    exhibition_routing = None

application = ProtocolTypeRouter(
    {
        "http": django_asgi_app,
        "websocket": AuthMiddlewareStack(
            URLRouter(exhibition_routing.websocket_urlpatterns if exhibition_routing else [])
        ),
    }
)

