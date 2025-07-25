"""
URL configuration for ai_first_response project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect
from django.conf.urls.i18n import i18n_patterns
from django.utils.translation import get_language
from first_response.urls import api_urlpatterns

def home_redirect(request):
    # Redirect to dashboard (will be automatically prefixed with language)
    return redirect('dashboard')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('i18n/', include('django.conf.urls.i18n')),
    # API endpoints outside i18n patterns (no language prefix)
    path('api/', include(api_urlpatterns)),
]

urlpatterns += i18n_patterns(
    path('', home_redirect, name='home'),
    path('dashboard/', include('first_response.urls')),
    prefix_default_language=True
)
