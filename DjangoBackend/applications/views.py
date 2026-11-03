from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from .models import Application
from .serializers import ApplicationSerializer, ApplicationStatusSerializer


class ApplicationViewSet(viewsets.ModelViewSet):
    """
    One class = 6 APIs:
      list    GET    /api/applications/
      create  POST   /api/applications/
      get     GET    /api/applications/{id}/
      update  PUT    /api/applications/{id}/        (PATCH = partial)
      delete  DELETE /api/applications/{id}/
      status  PATCH  /api/applications/{id}/status/ (custom action)
    """

    serializer_class = ApplicationSerializer     # default permission: IsAuthenticated

    def get_queryset(self):
        # ONLY my rows. Other user's id → automatic 404. This is the ownership rule.
        qs = Application.objects.filter(user=self.request.user)

        if self.action == "list":
            status = self.request.query_params.get("status")
            search = self.request.query_params.get("search")
            if status:
                if status not in Application.Status.values:
                    raise ValidationError({"status": "Invalid stage"})
                qs = qs.filter(status=status)
            if search:
                qs = qs.filter(company__icontains=search)
        return qs

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)   # user from token, not from client

    @action(detail=True, methods=["patch"], url_path="status")
    def set_status(self, request, pk=None):
        application = self.get_object()           # 404 if not mine
        serializer = ApplicationStatusSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        application.status = serializer.validated_data["status"]
        application.save(update_fields=["status"])
        return Response(ApplicationSerializer(application).data)