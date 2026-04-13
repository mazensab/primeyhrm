from django.db import migrations


def seed_hr_and_backfill(apps, schema_editor):
    Product = apps.get_model("billing_center", "Product")
    SubscriptionPlan = apps.get_model("billing_center", "SubscriptionPlan")
    CompanySubscription = apps.get_model("billing_center", "CompanySubscription")

    hr_product, _ = Product.objects.get_or_create(
        code="HR",
        defaults={
            "name": "HR",
            "description": "Primey HR core product",
            "is_active": True,
            "sort_order": 1,
        },
    )

    # ربط جميع الخطط الحالية بمنتج HR إذا لم تكن مرتبطة
    SubscriptionPlan.objects.filter(product__isnull=True).update(product=hr_product)

    # ربط جميع اشتراكات الشركات الحالية بمنتج HR إذا لم تكن مرتبطة
    CompanySubscription.objects.filter(product__isnull=True).update(product=hr_product)


def reverse_seed_hr_and_backfill(apps, schema_editor):
    Product = apps.get_model("billing_center", "Product")
    SubscriptionPlan = apps.get_model("billing_center", "SubscriptionPlan")
    CompanySubscription = apps.get_model("billing_center", "CompanySubscription")

    try:
        hr_product = Product.objects.get(code="HR")
    except Product.DoesNotExist:
        return

    SubscriptionPlan.objects.filter(product=hr_product).update(product=None)
    CompanySubscription.objects.filter(product=hr_product).update(product=None)

    # لا نحذف الـ Product في reverse حتى لا نمس أي بيانات مستقبلية مرتبطة به


class Migration(migrations.Migration):

    dependencies = [
        ("billing_center", "0007_product_and_subscription_product_fields"),
    ]

    operations = [
        migrations.RunPython(
            seed_hr_and_backfill,
            reverse_seed_hr_and_backfill,
        ),
    ]