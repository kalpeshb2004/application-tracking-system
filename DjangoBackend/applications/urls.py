from rest_framework.routers import DefaultRouter

from .views import ApplicationViewSet, FollowUpViewSet

router = DefaultRouter()
router.register("applications", ApplicationViewSet, basename="application")
router.register("followups", FollowUpViewSet, basename="followup")

urlpatterns = router.urls