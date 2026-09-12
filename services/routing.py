from django.urls import path
from . import consumer

websocket_urlpatterns=[
    path('ws/aswc/<int:auction_id>/',consumer.myaswc.as_asgi()), 
]