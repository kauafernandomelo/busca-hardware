from django import forms

from .models import Category, PriceAlert, PromoSubscription

INPUT_CLASSES = (
    "w-full rounded-lg border border-slate-300 bg-white px-4 py-2.5 text-sm "
    "text-slate-800 placeholder:text-slate-400 focus:border-blue-500 focus:outline-none"
)
SELECT_CLASSES = (
    "w-full rounded-lg border border-slate-300 bg-white px-4 py-2.5 text-sm "
    "text-slate-800 focus:border-blue-500 focus:outline-none"
)


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
                attrs={"class": INPUT_CLASSES, "placeholder": "voce@email.com"}
            ),
            "target_price": forms.NumberInput(
                attrs={
                    "class": INPUT_CLASSES,
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
                attrs={"class": INPUT_CLASSES, "placeholder": "seu@email.com"}
            ),
            "category": forms.Select(attrs={"class": SELECT_CLASSES}),
            "product": forms.HiddenInput(),
            "min_discount": forms.Select(
                choices=[(10, "a partir de 10%"), (20, "a partir de 20%"), (30, "a partir de 30%"), (50, "a partir de 50%")],
                attrs={"class": SELECT_CLASSES},
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
