from django.urls import path
from .views import first_response, dashboard, admin_dashboard

urlpatterns = [
    path('api/first-response/emergency/', first_response, name='first_response'),
    path('dashboard/', dashboard, name='dashboard'),
    path('admin-dashboard/', admin_dashboard, name='admin_dashboard'),
]