"""
CrimeLink AI - Main URL Configuration
All app URLs are included here.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect

def home_redirect(request):
    """Redirect root URL to dashboard or login."""
    if request.user.is_authenticated:
        return redirect('dashboard:home')
    return redirect('accounts:login')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home_redirect, name='home'),
    path('accounts/', include('accounts.urls')),
    path('dashboard/', include('dashboard.urls')),
    path('cases/', include('cases.urls')),
    path('entities/', include('entities.urls')),
]

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
