from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.utils import timezone

@login_required
def user_sessions(request):

    sessions = [
        {
            "id": "current",
            "device": "Current Browser",
            "location": "Localhost",
            "last_active": timezone.now()
        }
    ]

    return JsonResponse(sessions, safe=False)