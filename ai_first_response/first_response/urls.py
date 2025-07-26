from django.urls import path
from .views import (first_response, dashboard, admin_dashboard, system_dashboard, voice_message, 
                   emergency_alerts, text_to_speech_api, agentic_system_status, 
                   agentic_memory_insights, disaster_feeds_cache_stats, clear_disaster_feeds_cache,
                   reset_agentic_metrics)

# API URLs (no language prefix)
api_urlpatterns = [
    path('first-response/emergency/', first_response, name='first_response'),
    path('first-response/voice/', voice_message, name='voice_message'),
    path('first-response/alerts/', emergency_alerts, name='emergency_alerts'),
    path('first-response/tts/', text_to_speech_api, name='text_to_speech_api'),
    path('first-response/agentic/status/', agentic_system_status, name='agentic_system_status'),
    path('first-response/agentic/memory/', agentic_memory_insights, name='agentic_memory_insights'),
    path('first-response/agentic/reset/', reset_agentic_metrics, name='reset_agentic_metrics'),
    path('first-response/cache/stats/', disaster_feeds_cache_stats, name='disaster_feeds_cache_stats'),
    path('first-response/cache/clear/', clear_disaster_feeds_cache, name='clear_disaster_feeds_cache'),
]

# Dashboard URLs (with language prefix) 
urlpatterns = [
    path('', dashboard, name='dashboard'),
    path('admin-dashboard/', admin_dashboard, name='admin_dashboard'),
    path('system-dashboard/', system_dashboard, name='system_dashboard'),
] + api_urlpatterns