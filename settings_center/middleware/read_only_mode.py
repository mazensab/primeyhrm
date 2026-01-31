from django.http import JsonResponse

class ReadOnlyModeMiddleware:
    """
    ============================================================
    🔒 Read-Only Mode Middleware — API SAFE
    ============================================================
    """

    API_PREFIXES = (
        "/api/",
    )

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):

        # API لا يُعاد توجيهه
        if request.path.startswith(self.API_PREFIXES):
            return self.get_response(request)

        # (بقية منطق القراءة فقط كما هو لديك)
        return self.get_response(request)
