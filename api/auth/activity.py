from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.utils import timezone

@login_required
def user_activity(request):

    activities = [
        {
            "id": 1,
            "action": "Logged into the system",
            "created_at": timezone.now()
        }
    ]

    return JsonResponse(activities, safe=False)