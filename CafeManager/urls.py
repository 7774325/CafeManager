from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # 1. Admin Site
    path('admin/', admin.site.urls),

    # 2. Main App (Dashboard, Inventory, etc.)
    path('', include('core.urls')),

    # 3. Karaoke App
    path('karaoke/', include('karaoke.urls')),

    # 4. Authentication (Login/Logout)
    path('accounts/', include('django.contrib.auth.urls')),
    
    # 5. Redirect after login (prevents the 'accounts/profile/' 404)
    path('accounts/profile/', lambda r: redirect('dashboard')),
]

# 6. Serving Media and Static Files
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)