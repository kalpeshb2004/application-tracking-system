from django.db.models import Count, Q
from django.db.models.functions import TruncMonth
from rest_framework.response import Response
from rest_framework.views import APIView

from applications.models import Application

# 5-step funnel. "Rejected" is not here but still shows up if the user has any.
STAGES = ["Applied", "Screening", "Interview", "Offer", "Accepted"]


def my_applications(request):
    """Only the logged-in user's rows. Same ownership rule as the CRUD API."""
    return Application.objects.filter(user=request.user)


# ---------- GET /api/dashboard/stats/ ----------
# Count of applications per status
class StatsView(APIView):                       # default permission: IsAuthenticated
    def get(self, request):
        rows = (
            my_applications(request)
            .values("status")                    # GROUP BY status
            .annotate(count=Count("id"))
            .order_by()                          # clear default ordering so GROUP BY stays clean
        )
        by_status = {stage: 0 for stage in STAGES}   # zero-fill so the chart never misses a stage
        for row in rows:
            by_status[row["status"]] = row["count"]  # "Rejected" also appears here
        return Response({"total": sum(by_status.values()), "by_status": by_status})


# ---------- GET /api/dashboard/response-rate/ ----------
# % of applications that moved past "Applied"
class ResponseRateView(APIView):
    def get(self, request):
        result = my_applications(request).aggregate(     # ONE query, two counts
            total=Count("id"),
            responded=Count("id", filter=~Q(status="Applied")),
        )
        total = result["total"]
        responded = result["responded"]
        rate = round(responded * 100 / total, 1) if total else 0.0   # no divide by zero
        return Response({"total": total, "responded": responded, "response_rate": rate})


# ---------- GET /api/dashboard/timeline/ ----------
# Applications per month, based on applied_date
class TimelineView(APIView):
    def get(self, request):
        rows = (
            my_applications(request)
            .exclude(applied_date__isnull=True)
            .annotate(month=TruncMonth("applied_date"))  # 2026-10-17 → 2026-10-01
            .values("month")
            .annotate(count=Count("id"))
            .order_by("month")
        )
        return Response(
            [{"month": r["month"].strftime("%Y-%m"), "count": r["count"]} for r in rows]
        )