from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse
from django.conf import settings
from django.conf.urls.static import static

def health(request):
    return JsonResponse({"status": "ok", "service": "movie-service"})

urlpatterns = [
    path("admin/", admin.site.urls),
    path("health/", health),
    path("api/movies/", include("movies.urls")),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
