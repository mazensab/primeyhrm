from company_manager.models import Company, CompanyUser


# ============================================================
# 📦 1) Subscription Features
#    المصدر الموحد لميزات الاشتراك (Feature Flags)
# ============================================================
def subscription_features(request):
    """
    Injects subscription feature flags into templates.
    لاحقًا سيتم ربطها فعليًا بخطة الاشتراك.
    """
    return {
        "features": {
            "employees_enabled": True,
            "attendance_enabled": True,
            "leave_enabled": True,
            "payroll_enabled": True,
            "documents_enabled": True,
            "eosb_enabled": True,
            "termination_enabled": True,
        }
    }


# ============================================================
# 🏢 2) Current Company Context — FINAL
#
# أولوية التحديد:
# 1️⃣ Impersonation (Super Admin)
# 2️⃣ Company Owner / Employee
# 3️⃣ Super Admin بدون شركة (None)
#
# ❗ Super Admin لا يُحقن له Company افتراضية
# ============================================================
def current_company(request):
    """
    Resolves current company context safely.
    Used by:
    - Templates
    - Sidebars
    - Views
    - Permissions
    """

    company = None

    # --------------------------------------------------------
    # 1️⃣ Impersonation (أعلى أولوية)
    # --------------------------------------------------------
    company_id = request.session.get("impersonate_company_id")
    if company_id:
        company = Company.objects.filter(id=company_id).first()
        return {
            "current_company": company
        }

    # --------------------------------------------------------
    # 2️⃣ Company Owner / Employee
    # --------------------------------------------------------
    if request.user.is_authenticated:
        link = (
            CompanyUser.objects
            .select_related("company")
            .filter(user=request.user)
            .first()
        )
        if link:
            company = link.company

    # --------------------------------------------------------
    # 3️⃣ Super Admin → بدون شركة
    # --------------------------------------------------------
    return {
        "current_company": company
    }
