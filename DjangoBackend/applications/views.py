from datetime import date, timedelta

from rest_framework import mixins, viewsets
from rest_framework import status as http_status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from .models import Application, FollowUp
from .serializers import (
    ApplicationSerializer,
    ApplicationStatusSerializer,
    FollowUpSerializer,
    UpcomingFollowUpSerializer,
)


class ApplicationViewSet(viewsets.ModelViewSet):
    """
    list    GET    /api/applications/
    create  POST   /api/applications/
    get     GET    /api/applications/{id}/
    update  PUT    /api/applications/{id}/        (PATCH = partial)
    delete  DELETE /api/applications/{id}/
    status  PATCH  /api/applications/{id}/status/
    followups GET/POST /api/applications/{id}/followups/
    """

    serializer_class = ApplicationSerializer     # default permission: IsAuthenticated

    def get_queryset(self):
        # ONLY my rows. Other user's id → automatic 404. This is the ownership rule.
        qs = Application.objects.filter(user=self.request.user)

        if self.action == "list":
            stage = self.request.query_params.get("status")
            search = self.request.query_params.get("search")
            if stage:
                if stage not in Application.Status.values:
                    raise ValidationError({"status": "Invalid stage"})
                qs = qs.filter(status=stage)
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

    # ---------- API 1 + 2: nested follow-ups of ONE application ----------
    @action(detail=True, methods=["get", "post"], url_path="followups")
    def followups(self, request, pk=None):
        application = self.get_object()           # 404 if application is not mine

        if request.method == "POST":
            serializer = FollowUpSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save(application=application)
            return Response(serializer.data, status=http_status.HTTP_201_CREATED)

        items = application.followups.order_by("followup_date", "id")
        return Response(FollowUpSerializer(items, many=True).data)   # plain list, no paging


class FollowUpViewSet(
    mixins.UpdateModelMixin,       # PUT / PATCH /api/followups/{id}/
    mixins.DestroyModelMixin,      # DELETE      /api/followups/{id}/
    viewsets.GenericViewSet,       # no list / create here, nested route does that
):
    serializer_class = FollowUpSerializer

    def get_queryset(self):
        # Follow-up has no user column. Ownership goes through its application.
        return FollowUp.objects.filter(application__user=self.request.user)

    def update(self, request, *args, **kwargs):
        kwargs["partial"] = True    # PUT acts like PATCH: send only changed fields (same as FastAPI)
        return super().update(request, *args, **kwargs)

    # ---------- API 3: GET /api/followups/upcoming/?days=7 ----------
    @action(detail=False, methods=["get"])
    def upcoming(self, request):
        try:
            days = int(request.query_params.get("days", 7))
        except ValueError:
            raise ValidationError({"days": "Must be a number"})
        if not 1 <= days <= 90:
            raise ValidationError({"days": "Must be between 1 and 90"})

        end = date.today() + timedelta(days=days)
        items = (
            self.get_queryset()
            .filter(is_done=False, followup_date__lte=end)   # overdue included on purpose
            .select_related("application")                   # one JOIN, no N+1 queries
            .order_by("followup_date", "id")
        )
        return Response(UpcomingFollowUpSerializer(items, many=True).data)