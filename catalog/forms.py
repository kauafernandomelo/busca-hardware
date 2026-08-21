from django import forms

from .models import PriceAlert


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
