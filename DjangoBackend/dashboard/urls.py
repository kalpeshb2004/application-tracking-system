from django.urls import path

from .views import ResponseRateView, StatsView, TimelineView

urlpatterns = [
    path("stats/", StatsView.as_view()),
    path("response-rate/", ResponseRateView.as_view()),
    path("timeline/", TimelineView.as_view()),
]