from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .views import MeView, RegisterView

urlpatterns = [
    path("register/", RegisterView.as_view()),
    path("login/", TokenObtainPairView.as_view()),     # SimpleJWT gives login for free
    path("refresh/", TokenRefreshView.as_view()),
    path("me/", MeView.as_view()),
]