from rest_framework import generics
from rest_framework.permissions import AllowAny
from django.utils import timezone
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from .resume import ResumeError, extract_pdf_text

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

def resume_status(user):
    if not user.resume_text:
        return {"has_resume": False}
    return {
        "has_resume": True,
        "name": user.resume_name,
        "characters": len(user.resume_text),
        "updated_at": user.resume_updated_at,
        "preview": user.resume_text[:300],      # short preview, never the full text
    }


# /api/resume/   (default permission: IsAuthenticated)
class ResumeView(APIView):
    parser_classes = [MultiPartParser, FormParser]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "resume"                    # 10 per minute, see settings

    def get(self, request):
        return Response(resume_status(request.user))

    def post(self, request):
        uploaded = request.FILES.get("file")
        if uploaded is None:
            return Response({"file": "No file uploaded. Send it in a field named 'file'."}, status=400)
        try:
            text = extract_pdf_text(uploaded)
        except ResumeError as exc:
            return Response({"file": str(exc)}, status=400)

        user = request.user
        user.resume_text = text
        user.resume_name = uploaded.name[:255]
        user.resume_updated_at = timezone.now()
        user.save(update_fields=["resume_text", "resume_name", "resume_updated_at"])
        return Response(resume_status(user), status=201)

    def delete(self, request):
        user = request.user
        user.resume_text = None
        user.resume_name = None
        user.resume_updated_at = None
        user.save(update_fields=["resume_text", "resume_name", "resume_updated_at"])
        return Response(status=204)