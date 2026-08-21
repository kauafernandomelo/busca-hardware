from django import forms

from .models import Category, PriceAlert, PromoSubscription


class PriceAlertForm(forms.ModelForm):
    class Meta:
        model = PriceAlert
        fields = ["email", "target_price"]
        labels = {
            "email": "Seu e-mail",
            "target_price": "Preço alvo (R$)",
        }
        widgets = {
            "email": forms.EmailInput(
                attrs={
                    "class": "w-full rounded-lg border border-slate-700 bg-slate-800 px-4 py-2.5 text-sm placeholder:text-slate-500 focus:border-emerald-500 focus:outline-none",
                    "placeholder": "voce@email.com",
                }
            ),
            "target_price": forms.NumberInput(
                attrs={
                    "class": "w-full rounded-lg border border-slate-700 bg-slate-800 px-4 py-2.5 text-sm placeholder:text-slate-500 focus:border-emerald-500 focus:outline-none",
                    "min": "0.01",
                    "step": "0.01",
                    "placeholder": "Ex.: 2500,00",
                }
            ),
        }
        help_texts = {
            "target_price": "Avisaremos quando o menor preço ficar igual ou abaixo desse valor.",
        }

    def clean_target_price(self):
        value = self.cleaned_data["target_price"]
        if value <= 0:
            raise forms.ValidationError("Informe um valor maior que zero.")
        return value


class PromoSubscriptionForm(forms.ModelForm):
    class Meta:
        model = PromoSubscription
        fields = ["email", "category", "product", "min_discount"]
        widgets = {
            "email": forms.EmailInput(
                attrs={
                    "class": "w-full rounded-lg border border-slate-700 bg-slate-800 px-4 py-2.5 text-sm placeholder:text-slate-500 focus:border-emerald-500 focus:outline-none",
                    "placeholder": "seu@email.com",
                }
            ),
            "category": forms.Select(
                attrs={"class": "w-full rounded-lg border border-slate-700 bg-slate-800 px-4 py-2.5 text-sm focus:border-emerald-500 focus:outline-none"}
            ),
            "product": forms.HiddenInput(),
            "min_discount": forms.Select(
                choices=[(10, "a partir de 10%"), (20, "a partir de 20%"), (30, "a partir de 30%"), (50, "a partir de 50%")],
                attrs={"class": "w-full rounded-lg border border-slate-700 bg-slate-800 px-4 py-2.5 text-sm focus:border-emerald-500 focus:outline-none"},
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["category"].required = False
        self.fields["category"].empty_label = "Todas as categorias"
        self.fields["product"].required = False
        self.fields["min_discount"].required = False

    def clean(self):
        cleaned = super().clean()
        if not cleaned.get("min_discount"):
            cleaned["min_discount"] = 10
        if not cleaned.get("category") and not cleaned.get("product"):
            raise forms.ValidationError("Escolha uma categoria ou um produto.")
        return cleaned
