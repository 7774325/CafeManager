from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    # This correctly routes the WebSocket connection to your Consumer
    # Standard Django Channels method is .as_asgi()
    re_path(r'ws/karaoke/staff/(?P<outlet_id>\w+)/$', consumers.KaraokeStaffConsumer.as_asgi()),
]