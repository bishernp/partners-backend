from django.urls import path

from .views import (
    AnalyticsDistributionsView,
    AnalyticsOverviewView,
    SubmissionDetailView,
    SubmissionExportView,
    SubmissionListView,
)

urlpatterns = [
    path("submissions/", SubmissionListView.as_view(), name="dash-submissions"),
    path("submissions/export/", SubmissionExportView.as_view(), name="dash-export"),
    path("submissions/<int:pk>/", SubmissionDetailView.as_view(), name="dash-submission-detail"),
    path("analytics/overview/", AnalyticsOverviewView.as_view(), name="dash-overview"),
    path("analytics/distributions/", AnalyticsDistributionsView.as_view(), name="dash-distributions"),
]
