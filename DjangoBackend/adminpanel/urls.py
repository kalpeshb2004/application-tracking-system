from django.urls import path
from rest_framework.routers import SimpleRouter

from .views import AdminStatsView, AdminUserViewSet

router = SimpleRouter()
router.register("users", AdminUserViewSet, basename="admin-user")

urlpatterns = [path("stats/", AdminStatsView.as_view())] + router.urls