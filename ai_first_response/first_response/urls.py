from django.urls import path
from .views import first_response, dashboard, admin_dashboard

# API URLs (no language prefix)
api_urlpatterns = [
    path('first-response/emergency/', first_response, name='first_response'),
]

# Dashboard URLs (with language prefix) 
urlpatterns = [
    path('', dashboard, name='dashboard'),
    path('admin-dashboard/', admin_dashboard, name='admin_dashboard'),
] + api_urlpatterns