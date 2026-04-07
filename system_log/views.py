from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.http import JsonResponse
from company_manager.models import Company
from .models import SystemLog

# ================================================================
# 📘 System Log Views — V1 (Mham Cloud)
# (تم الاحتفاظ بها كما هي)
# ================================================================

@login_required
def log_dashboard(request, company_id):
    company = get_object_or_404(Company, id=company_id)
    logs = SystemLog.objects.filter(company=company)
    stats = logs.values("severity").annotate(total=Count("id"))

    context = {
        "company": company,
        "stats": stats,
        "total_logs": logs.count(),
        "page_title": "سجلات النظام — Dashboard",
    }
    return render(request, "system_log/log_dashboard.html", context)


@login_required
def log_list(request, company_id):
    company = get_object_or_404(Company, id=company_id)
    logs = SystemLog.objects.filter(company=company).order_by("-created_at")

    context = {
        "company": company,
        "logs": logs,
        "page_title": "سجلات النظام — Log List",
    }
    return render(request, "system_log/log_list.html", context)


@login_required
def log_detail(request, log_id):
    log_item = get_object_or_404(SystemLog, id=log_id)

    context = {
        "log": log_item,
        "company": log_item.company,
        "page_title": "تفاصيل السجل",
    }
    return render(request, "system_log/log_detail.html", context)


# ===================================================================
# 🚀 V2 — AJAX API: Sorting + Filtering + Search + Pagination
# ===================================================================
@login_required
def api_filter_logs(request, company_id):
    """
    🔥 API Ultra Pro للتصفية والفرز والبحث + pagination
    ترجع JSON فقط بدون أي HTML.
    """

    company = get_object_or_404(Company, id=company_id)
    logs = SystemLog.objects.filter(company=company)

    # ----------------------------
    # 🔍 1) البحث (search)
    # ----------------------------
    search_query = request.GET.get("search", "").strip()
    if search_query:
        logs = logs.filter(
            Q(module__icontains=search_query) |
            Q(action__icontains=search_query) |
            Q(message__icontains=search_query)
        )

    # ----------------------------
    # 🟦 2) التصفية حسب الوحدة (module)
    # ----------------------------
    module_filter = request.GET.get("module")
    if module_filter and module_filter != "all":
        logs = logs.filter(module=module_filter)

    # ----------------------------
    # 🟧 3) التصفية حسب الإجراء (action)
    # ----------------------------
    action_filter = request.GET.get("action")
    if action_filter and action_filter != "all":
        logs = logs.filter(action=action_filter)

    # ----------------------------
    # 🟥 4) التصفية حسب مستوى الخطورة (severity)
    # ----------------------------
    severity_filter = request.GET.get("severity")
    if severity_filter and severity_filter != "all":
        logs = logs.filter(severity=severity_filter)

    # ----------------------------
    # 🔽 5) الفرز (sorting)
    # ----------------------------
    sort_by = request.GET.get("sort", "-created_at")
    logs = logs.order_by(sort_by)

    # ----------------------------
    # 📄 6) Pagination (صفحات AJAX)
    # ----------------------------
    page = int(request.GET.get("page", 1))
    page_size = 20  # عدد العناصر لكل صفحة
    start = (page - 1) * page_size
    end = start + page_size

    total = logs.count()
    logs = logs[start:end]

    # ----------------------------
    # 📤 7) تجهيز JSON Response
    # ----------------------------
    log_list = []
    for log in logs:
        log_list.append({
            "id": log.id,
            "module": log.module,
            "action": log.action,
            "user": log.user.get_full_name() if log.user else "—",
            "severity": log.severity,
            "message": log.message[:80] + ("..." if len(log.message) > 80 else ""),
            "created_at": log.created_at.strftime("%Y-%m-%d %H:%M"),
        })

    return JsonResponse({
        "logs": log_list,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total // page_size) + (1 if total % page_size else 0)
    })

# ================================================================
# 📤 V3 — Export Excel
# ================================================================
import pandas as pd
from django.http import HttpResponse

@login_required
def export_logs_excel(request, company_id):
    company = get_object_or_404(Company, id=company_id)
    logs = SystemLog.objects.filter(company=company).order_by("-created_at")

    data = []
    for log in logs:
        data.append({
            "الوحدة": log.module,
            "الإجراء": log.action,
            "المستخدم": log.user.get_full_name() if log.user else "—",
            "الخطورة": log.severity,
            "الرسالة": log.message,
            "التاريخ": log.created_at.strftime("%Y-%m-%d %H:%M"),
        })

    df = pd.DataFrame(data)
    response = HttpResponse(content_type="application/vnd.ms-excel")
    response["Content-Disposition"] = f'attachment; filename="system_logs_{company.id}.xlsx"'
    df.to_excel(response, index=False)

    return response


# ================================================================
# 📄 V3 — Export PDF (ReportLab)
# ================================================================
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4

@login_required
def export_logs_pdf(request, company_id):
    company = get_object_or_404(Company, id=company_id)
    logs = SystemLog.objects.filter(company=company).order_by("-created_at")

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="system_logs_{company.id}.pdf"'

    p = canvas.Canvas(response, pagesize=A4)
    y = 800

    p.setFont("Helvetica-Bold", 14)
    p.drawString(50, y, f"System Logs — Company #{company.id}")
    y -= 40

    p.setFont("Helvetica", 10)

    for log in logs:
        p.drawString(50, y, f"{log.created_at}: {log.module} — {log.action} — {log.severity}")
        y -= 20

        if y < 50:
            p.showPage()
            y = 800

    p.showPage()
    p.save()
    return response


# ================================================================
# 🗑️ V3 — Clear Logs
# ================================================================
@login_required
def clear_logs(request, company_id):
    company = get_object_or_404(Company, id=company_id)

    # مستقبلاً: حماية RBAC — requires: system_log.delete_all_logs
    SystemLog.objects.filter(company=company).delete()

    return JsonResponse({"status": "success"})

# ================================================================
# 🛰️ V4 — Live Logs WebSocket Page
# ================================================================
from django.contrib.auth.decorators import login_required

@login_required
def log_live_view(request, company_id):
    """
    🛰️ صفحة البث اللحظي للسجلات (WebSocket Live Stream)
    """
    company = get_object_or_404(Company, id=company_id)

    context = {
        "company": company,
        "page_title": "البث اللحظي — System Log Live",
    }

    return render(request, "system_log/log_live.html", context)
