from __future__ import annotations

from decimal import Decimal

from django.conf import settings
from django.core.mail import get_connection, send_mail
from django.core.management.base import BaseCommand
from django.utils import timezone

from catalog.models import PriceAlert


class Command(BaseCommand):
    help = "Verifica alertas ativos e notifica por e-mail quando o preço alvo é atingido."

    def handle(self, *args, **options):
        alerts = PriceAlert.objects.filter(is_active=True).select_related("product")
        checked = notified = 0

        for alert in alerts:
            offer = alert.product.best_offer
            if offer is None or offer.current_price is None:
                continue
            checked += 1
            if offer.current_price > alert.target_price:
                continue

            self.send_alert_email(alert, offer)
            alert.notified_at = timezone.now()
            alert.is_active = False
            alert.save(update_fields=["notified_at", "is_active"])
            notified += 1
            self.stdout.write(
                self.style.SUCCESS(
                    f"[ALERTA] {alert.email} — {alert.product.name} "
                    f"(R$ {offer.current_price} <= R$ {alert.target_price})"
                )
            )

        self.stdout.write(
            f"Verificados: {checked} | Notificados: {notified}"
        )

    @staticmethod
    def send_alert_email(alert: PriceAlert, offer) -> None:
        connection = get_connection()
        subject = (
            f"Alerta de preço: {alert.product.name} por R$ {offer.current_price:.2f}"
        )
        message = (
            f"O produto que você acompanha atingiu seu preço alvo!\n\n"
            f"Produto: {alert.product.name}\n"
            f"Preço atual: R$ {offer.current_price:.2f} na loja {offer.store.name}\n"
            f"Seu preço alvo: R$ {alert.target_price:.2f}\n"
            f"Link da oferta: {offer.url}\n"
            f"Link do produto: {settings.SITE_URL}{alert.product.get_absolute_url()}\n\n"
            f"— Busca Hardware"
        )
        send_mail(
            subject=subject,
            message=message,
            from_email="alertas@buscahardware.local",
            recipient_list=[alert.email],
            connection=connection,
        )
