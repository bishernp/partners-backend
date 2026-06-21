"""Public onboarding endpoints (token-gated, throttled, no auth)."""
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Invitation
from .services import create_submission


class SubmissionCreateView(APIView):
    """Accept an onboarding payload, validate against the active catalog, and
    store Partner + Submission + Answers. Returns the submission reference."""
    authentication_classes = []
    permission_classes = [permissions.AllowAny]
    throttle_scope = "onboarding_submit"

    def post(self, request):
        submission = create_submission(request.data)
        return Response(
            {"reference": submission.reference, "status": submission.status},
            status=status.HTTP_201_CREATED,
        )


class InvitationCheckView(APIView):
    """Validate an invitation token before the form loads. Lenient for now:
    unknown tokens are accepted (pilot), known tokens honour expiry/status."""
    authentication_classes = []
    permission_classes = [permissions.AllowAny]
    throttle_scope = "onboarding_check"

    def get(self, request, token):
        try:
            inv = Invitation.objects.get(token=token)
        except Invitation.DoesNotExist:
            return Response({"valid": True, "known": False})
        return Response({
            "valid": inv.is_open(),
            "known": True,
            "email": inv.email,
            "full_name": inv.full_name,
            "locale": inv.locale,
        })
