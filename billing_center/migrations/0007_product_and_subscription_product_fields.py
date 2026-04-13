# Generated manually for Product-aware architecture

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("billing_center", "0006_companyonboardingtransaction_payment_method"),
    ]

    operations = [
        migrations.CreateModel(
            name="Product",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=255, unique=True)),
                ("code", models.CharField(db_index=True, max_length=100, unique=True)),
                ("description", models.TextField(blank=True, null=True)),
                ("is_active", models.BooleanField(default=True)),
                ("sort_order", models.PositiveIntegerField(default=0)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "Product",
                "verbose_name_plural": "Products",
                "ordering": ["sort_order", "name"],
            },
        ),
        migrations.AddField(
            model_name="subscriptionplan",
            name="product",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="plans",
                to="billing_center.product",
            ),
        ),
        migrations.AddField(
            model_name="companysubscription",
            name="product",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="company_subscriptions",
                to="billing_center.product",
            ),
        ),
        migrations.AddIndex(
            model_name="subscriptionplan",
            index=models.Index(fields=["product", "is_active"], name="billing_cen_produc_5ef467_idx"),
        ),
        migrations.AddIndex(
            model_name="companysubscription",
            index=models.Index(fields=["company", "product", "status"], name="billing_cen_company_3e72b8_idx"),
        ),
        migrations.AddIndex(
            model_name="companysubscription",
            index=models.Index(fields=["company", "status"], name="billing_cen_company_7d4c0f_idx"),
        ),
    ]