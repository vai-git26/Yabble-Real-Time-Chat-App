from django.urls import path
from .consumers import *
from django.urls import re_path
from . import consumers

# from a_rtchat import consumers

websocket_urlpatterns = [
    re_path(r'ws/chatroom/(?P<chatroom_name>[^/]+)/?$', ChatroomConsumer.as_asgi()),
    path("ws/online-status/", OnlineStatusConsumer.as_asgi()),
    re_path(r"ws/call/(?P<room_name>[^/]+)/$", consumers.CallConsumer.as_asgi()),
]
