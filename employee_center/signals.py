# ===============================================================
# 📂 employee_center/signals.py
# 🧭 Employee Signals — AUTO USER CREATION (FINAL)
# ===============================================================

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.utils.crypto import get_random_string

from .models import Employee, EmploymentHistory


def generate_unique_username(base):
    User = get_user_model()
    username = base
    while User.objects.filter(username=username).exists():
        username = f"{base}_{get_random_string(4)}"
    return username


@receiver(post_save, sender=Employee)
def ensure_employee_has_user(sender, instance, created, **kwargs):
    """
    🔐 ضمان أن كل Employee لديه User
    """

    if not created:
        return

    if instance.user:
        return

    User = get_user_model()

    base_username = instance.national_id or f"emp_{instance.id}"
    username = generate_unique_username(base_username)
    raw_password = get_random_string(10)

    user = User.objects.create_user(
        username=username,
        password=raw_password,
        is_active=True,
    )

    instance.user = user
    instance.save(update_fields=["user"])

    EmploymentHistory.objects.create(
        employee=instance,
        action_type="hire",
        description=f"إنشاء مستخدم تلقائيًا ({username})"
    )
