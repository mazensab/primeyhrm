from django import forms
from .models import (
    PerformanceTemplate,
    PerformanceCategory,
    PerformanceItem,
    PerformanceReview,
    PerformanceAnswer
)


# ================================================================
# 📌 1) TemplateForm — نموذج إنشاء/تعديل قالب التقييم
# ================================================================
class TemplateForm(forms.ModelForm):
    class Meta:
        model = PerformanceTemplate
        fields = ["name", "period", "description", "is_active"]

        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "period": forms.Select(attrs={"class": "form-select"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }


# ================================================================
# 📌 2) CategoryForm — نموذج إضافة/تعديل فئة تقييم
# ================================================================
class CategoryForm(forms.ModelForm):
    class Meta:
        model = PerformanceCategory
        fields = ["name", "weight"]

        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "weight": forms.NumberInput(attrs={"class": "form-control"}),
        }


# ================================================================
# 📌 3) ItemForm — نموذج إضافة/تعديل عنصر تقييم
# ================================================================
class ItemForm(forms.ModelForm):
    class Meta:
        model = PerformanceItem
        fields = ["question", "item_type", "max_score", "weight"]

        widgets = {
            "question": forms.TextInput(attrs={"class": "form-control"}),
            "item_type": forms.Select(attrs={"class": "form-select"}),
            "max_score": forms.NumberInput(attrs={"class": "form-control"}),
            "weight": forms.NumberInput(attrs={"class": "form-control"}),
        }


# ================================================================
# 📌 4) ReviewStartForm — بدء تقييم موظف
# ================================================================
class ReviewStartForm(forms.Form):
    period_label = forms.CharField(
        label="دورة التقييم",
        widget=forms.TextInput(attrs={"class": "form-control"})
    )


# ================================================================
# 📌 5) SelfEvaluationForm — نموذج التقييم الذاتي
# ================================================================
class SelfEvaluationForm(forms.Form):

    def __init__(self, *args, **kwargs):
        items = kwargs.pop("items")
        super().__init__(*args, **kwargs)

        """
        نولّد حقول ديناميكية بحسب عناصر التقييم
        مثال:
        item_1
        item_2
        item_3
        """
        for item in items:
            self.fields[f"item_{item.id}"] = forms.IntegerField(
                min_value=0,
                max_value=item.max_score,
                label=item.question,
                widget=forms.NumberInput(attrs={
                    "class": "form-control",
                    "placeholder": f"0 — {item.max_score}"
                })
            )


# ================================================================
# 📌 6) ManagerEvaluationForm — نموذج تقييم المدير
# ================================================================
class ManagerEvaluationForm(forms.Form):

    def __init__(self, *args, **kwargs):
        items = kwargs.pop("items")
        super().__init__(*args, **kwargs)

        for item in items:
            self.fields[f"item_{item.id}"] = forms.IntegerField(
                min_value=0,
                max_value=item.max_score,
                label=item.question,
                widget=forms.NumberInput(attrs={
                    "class": "form-control",
                })
            )


# ================================================================
# 📌 7) HREvaluationForm — نموذج تقييم HR
# ================================================================
class HREvaluationForm(forms.Form):

    def __init__(self, *args, **kwargs):
        items = kwargs.pop("items")
        super().__init__(*args, **kwargs)

        for item in items:
            self.fields[f"item_{item.id}"] = forms.IntegerField(
                min_value=0,
                max_value=item.max_score,
                label=item.question,
                widget=forms.NumberInput(attrs={
                    "class": "form-control",
                })
            )


# ================================================================
# 📌 8) FinalDecisionForm — قرار HR النهائي
# ================================================================
class FinalDecisionForm(forms.ModelForm):
    class Meta:
        model = PerformanceReview
        fields = ["final_decision"]

        widgets = {
            "final_decision": forms.Select(attrs={"class": "form-select"}),
        }
