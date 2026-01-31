from django.urls import path
from . import views

app_name = "scheduler_center"

urlpatterns = [
    path("dashboard/", views.scheduler_dashboard, name="scheduler_dashboard"),
]
