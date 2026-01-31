from django.shortcuts import render

def scheduler_dashboard(request):
    return render(request, "scheduler_center/dashboard.html")
