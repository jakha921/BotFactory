"""
URLs for chat app.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.chat.views import (
    ChatSessionViewSet,
    ChatMessageViewSet,
    TranscriptionViewSet,
    FileProcessingViewSet,
    ChatGenerationView
)

app_name = 'chat'

router = DefaultRouter()
router.register(r'bots/(?P<bot_id>[^/.]+)/sessions', ChatSessionViewSet, basename='session')
router.register(r'sessions/(?P<session_id>[^/.]+)/messages', ChatMessageViewSet, basename='message')

# Separate router for chat utilities (transcription and file processing)
# Note: ViewSets with @action need to be registered, but we'll use direct paths instead
chat_router = DefaultRouter()
# Register for list/detail if needed, but we use direct paths for actions

urlpatterns = [
    path('', include(router.urls)),
    path('chat/', include(chat_router.urls)),
    # Direct paths for chat utilities endpoints
    path('chat/transcribe/', TranscriptionViewSet.as_view({'post': 'transcribe'}), name='chat-transcribe'),
    path('chat/process-file/', FileProcessingViewSet.as_view({'post': 'process_file'}), name='chat-process-file'),
    path('chat/generate/', ChatGenerationView.as_view(), name='chat-generate'),
]

