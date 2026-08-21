from __future__ import annotations

from datetime import timedelta

from django.core.mail import get_connection, send_mail
from django.core.management.base import BaseCommand
from django.utils import timezone

from catalog.models import Offer, PromoSubscription

COOLDOWN_HOURS = 24
MAX_ITEMS_PER_EMAIL = 10


class Command(BaseCommand):
    help = (
        "Casa assinaturas de promoção com ofertas em promoção recentes "
        "e envia um resumo por e-mail (máx. 1 por dia por assinatura)."
    )

    def handle(self, *args, **options):
        now = timezone.now()
        cooldown_limit = now - timedelta(hours=COOLDOWN_HOURS)
        subscriptions = PromoSubscription.objects.filter(is_active=True).select_related(
            "category", "product"
        )

        sent = skipped = no_news = 0
        for sub in subscriptions:
            if sub.last_notified_at and sub.last_notified_at > cooldown_limit:
                skipped += 1
                continue

            offers = self.matching_offers(sub)
            if not offers:
                no_news += 1
                continue

            self.send_digest(sub, offers[:MAX_ITEMS_PER_EMAIL])
            sub.last_notified_at = now
            sub.save(update_fields=["last_notified_at"])
            sent += 1
            self.stdout.write(
                self.style.SUCCESS(f"[PROMO] {sub.email}: {len(offers)} oferta(s) nova(s)")
            )

        self.stdout.write(
            f"Enviados: {sent} | Sem novidades: {no_news} | Em cooldown: {skipped}"
        )

    @staticmethod
    def matching_offers(sub: PromoSubscription):
        queryset = Offer.objects.filter(
            is_promo=True,
            is_available=True,
            current_price__isnull=False,
        ).select_related("product", "store")

        if sub.product:
            queryset = queryset.filter(product=sub.product)
        elif sub.category:
            queryset = queryset.filter(product__category=sub.category)

        if sub.min_discount:
            queryset = queryset.filter(discount_pct__gte=sub.min_discount)

        if sub.last_notified_at:
            queryset = queryset.filter(last_checked_at__gt=sub.last_notified_at)

        return list(queryset.order_by("-discount_pct", "current_price"))

    @staticmethod
    def send_digest(sub: PromoSubscription, offers) -> None:
        connection = get_connection()
        scope = sub.product or sub.category
        subject = f"🏷️ {len(offers)} promoção(ões) nova(s): {scope}"

        lines = []
        for offer in offers:
            price = f"R$ {offer.current_price:.2f}".replace(".", ",")
            original = (
                f" (antes R$ {offer.original_price:.2f})".replace(".", ",")
                if offer.original_price
                else ""
            )
            lines.append(
                f"• [{offer.discount_pct:.0f}% OFF] {offer.product.name}\n"
                f"  {price}{original} à vista na {offer.store.name}\n"
                f"  {offer.url}"
            )

        message = (
            f"Olá!\n\nNovas promoções que combinam com sua assinatura ({scope}):\n\n"
            + "\n\n".join(lines)
            + "\n\n— Busca Hardware\n"
            "Você recebe este e-mail no máximo 1 vez por dia por assinatura."
        )

        send_mail(
            subject=subject,
            message=message,
            from_email="promocoes@buscahardware.local",
            recipient_list=[sub.email],
            connection=connection,
        )
