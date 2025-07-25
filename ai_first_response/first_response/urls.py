from django.urls import path
from .views import first_response, dashboard, admin_dashboard, voice_message, emergency_alerts

# API URLs (no language prefix)
api_urlpatterns = [
    path('first-response/emergency/', first_response, name='first_response'),
    path('first-response/voice/', voice_message, name='voice_message'),
    path('first-response/alerts/', emergency_alerts, name='emergency_alerts'),
]

# Dashboard URLs (with language prefix) 
urlpatterns = [
    path('', dashboard, name='dashboard'),
    path('admin-dashboard/', admin_dashboard, name='admin_dashboard'),
] + api_urlpatterns