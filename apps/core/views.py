from django.http import JsonResponse
from django.views.generic import TemplateView


def csrf_failure(request, reason=""):
    return JsonResponse(
        {"detail": "CSRF token missing or invalid. Please refresh the page and try again."},
        status=403,
    )


class PrivacyPolicyView(TemplateView):
    template_name = "core/privacy_policy.html"
