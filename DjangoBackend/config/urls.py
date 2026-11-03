from django.db import connection
from django.http import JsonResponse
from django.urls import include, path
from django.contrib import admin


def health(request):
    connection.ensure_connection()
    return JsonResponse({"status": "ok", "database": "connected"})


urlpatterns = [
    path("", health),                              # http://127.0.0.1:8000/
    path("admin/", admin.site.urls),
    path("api/auth/", include("accounts.urls")),
    path("api/", include("applications.urls")),
    path("api/auth/", include("accounts.urls")),
    path("api/dashboard/", include("dashboard.urls")),
    path("api/", include("applications.urls")),
]

