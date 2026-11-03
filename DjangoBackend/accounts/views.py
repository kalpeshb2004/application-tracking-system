from rest_framework import generics
from rest_framework.permissions import AllowAny

from .serializers import RegisterSerializer, UserSerializer


# POST /api/auth/register/
class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]       # public: no token needed
    authentication_classes = []           # ignore any old/bad token sent here


# GET /api/auth/me/
class MeView(generics.RetrieveAPIView):
    serializer_class = UserSerializer     # default permission = IsAuthenticated

    def get_object(self):
        return self.request.user