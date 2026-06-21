from django.urls import path

from .views import InvitationCheckView, SubmissionCreateView

urlpatterns = [
    path("submissions/", SubmissionCreateView.as_view(), name="submission-create"),
    path("invitation/<str:token>/", InvitationCheckView.as_view(), name="invitation-check"),
]
