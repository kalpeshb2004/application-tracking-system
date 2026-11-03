from django.db.models import Count, Q
from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import User
from accounts.permissions import IsAdminRole
from applications.models import Application

from .serializers import (
    AdminApplicationSerializer,
    AdminUserSerializer,
    AdminUserStatusSerializer,
)


# ---------- API 1: GET /api/admin/stats/ ----------
# Totals across ALL users: users, active users, applications, count per stage
class AdminStatsView(APIView):
    permission_classes = [IsAdminRole]

    def get(self, request):
        users = User.objects.aggregate(                       # ONE query, two counts
            total=Count("id"),
            active=Count("id", filter=Q(is_active=True)),
        )
        # Start every stage at 0, so empty stages still show in the response
        per_stage = {stage: 0 for stage in Application.Status.values}
        rows = Application.objects.values("status").annotate(count=Count("id")).order_by()
        for row in rows:
            per_stage[row["status"]] = row["count"]

        return Response({
            "total_users": users["total"],
            "active_users": users["active"],
            "total_applications": sum(per_stage.values()),
            "applications_per_stage": per_stage,
        })


class AdminUserViewSet(
    mixins.ListModelMixin,        # API 2: list
    mixins.DestroyModelMixin,     # API 4: delete
    viewsets.GenericViewSet,
):
    """
    list          GET    /api/admin/users/
    destroy       DELETE /api/admin/users/{id}/
    set_status    PATCH  /api/admin/users/{id}/status/
    applications  GET    /api/admin/users/{id}/applications/
    """

    permission_classes = [IsAdminRole]     # guards EVERY action in this class
    serializer_class = AdminUserSerializer

    def get_queryset(self):
        # annotate = LEFT JOIN + COUNT per user, so users with 0 applications still show
        qs = User.objects.annotate(applications_count=Count("applications")).order_by("id")

        if self.action == "list":
            search = self.request.query_params.get("search")
            is_active = self.request.query_params.get("is_active")
            if search:
                qs = qs.filter(Q(name__icontains=search) | Q(email__icontains=search))
            if is_active is not None:
                if is_active.lower() not in ("true", "false"):
                    raise ValidationError({"is_active": "Must be true or false"})
                qs = qs.filter(is_active=(is_active.lower() == "true"))
        return qs

    # ---------- API 3: PATCH /api/admin/users/{id}/status/ ----------
    # Activate / deactivate. Admin cannot change own status (lockout guard)
    @action(detail=True, methods=["patch"], url_path="status")
    def set_status(self, request, pk=None):
        user = self.get_object()                          # 404 if the user does not exist
        if user.pk == request.user.pk:
            return Response({"detail": "You cannot change your own status"}, status=400)

        serializer = AdminUserStatusSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user.is_active = serializer.validated_data["is_active"]
        user.save(update_fields=["is_active"])
        return Response(AdminUserSerializer(user).data)

    # ---------- API 4: DELETE /api/admin/users/{id}/ ----------
    # Permanent. Cascade removes the user's applications and follow-ups
    def destroy(self, request, *args, **kwargs):
        user = self.get_object()
        if user.pk == request.user.pk:
            return Response({"detail": "You cannot delete yourself"}, status=400)
        if user.role == "admin":                          # demote first. Stops admin wipe
            return Response({"detail": "Cannot delete an admin account"}, status=400)
        user.delete()
        return Response(status=204)

    # ---------- API 5: GET /api/admin/users/{id}/applications/ ----------
    # Admin view of one user's applications. Summary fields only (privacy)
    @action(detail=True, methods=["get"], url_path="applications")
    def applications(self, request, pk=None):
        user = self.get_object()                          # 404 if the user does not exist
        qs = Application.objects.filter(user=user)

        stage = request.query_params.get("status")
        if stage:
            if stage not in Application.Status.values:
                raise ValidationError({"status": "Invalid stage"})
            qs = qs.filter(status=stage)

        page = self.paginate_queryset(qs)                 # same limit/offset as everywhere
        return self.get_paginated_response(AdminApplicationSerializer(page, many=True).data)