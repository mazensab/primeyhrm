from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("billing_center", "0008_seed_hr_product_and_backfill_existing_records"),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name="companysubscription",
            name="unique_active_subscription_per_company",
        ),
        migrations.AddConstraint(
            model_name="companysubscription",
            constraint=models.UniqueConstraint(
                fields=("company", "product"),
                condition=models.Q(("status", "ACTIVE")),
                name="unique_active_subscription_per_company_product",
            ),
        ),
    ]