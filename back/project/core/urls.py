from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/users/', include('users.urls')),
    path('api/repairs/', include('repairs.urls')),
    path('api/academics/', include('academics.urls')),
    path('api/chat/', include('chat.urls')),
    path('api/resources/', include('resources.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)