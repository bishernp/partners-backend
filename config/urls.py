from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView


def healthz(_request):
    """Lightweight liveness probe for the Render health check."""
    return JsonResponse({"status": "ok"})


urlpatterns = [
    path("healthz", healthz),
    path("admin/", admin.site.urls),

    # Auth (JWT) for the dashboard
    path("api/auth/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),

    # Public onboarding intake
    path("api/onboarding/", include("onboarding.urls")),

    # Internal dashboard (staff-only)
    path("api/dashboard/", include("dashboard.urls")),

    # API docs
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="docs"),
]
