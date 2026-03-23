from django.http import JsonResponse


def csrf_failure(request, reason=""):
    return JsonResponse(
        {"detail": "CSRF token missing or invalid. Please refresh the page and try again."},
        status=403,
    )
