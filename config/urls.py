from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse

def health(request):
    return JsonResponse({"status": "ok", "service": "user-service"})

urlpatterns = [
    path("admin/", admin.site.urls),
    path("health/", health),
    path("api/users/", include("users.urls")),
]
