# ============================================================
# 🇸🇦 National Address — URLs
# ============================================================

from django.urls import path
from .resolve import resolve_short_address

urlpatterns = [
    path(
        "resolve/",
        resolve_short_address,
        name="national_address-resolve",
    ),
]
