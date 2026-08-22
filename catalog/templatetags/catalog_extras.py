from decimal import Decimal, InvalidOperation

from django import template
from django.utils.safestring import mark_safe

register = template.Library()

ICON_SVG = {
    # interface
    "zap": '<polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>',
    "search": '<circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/>',
    "flame": '<path d="M8.5 14.5A2.5 2.5 0 0 0 11 12c0-1.38-.5-2-1-3-1.072-2.143-.224-4.054 2-6 .5 2.5 2 4.9 4 6.5 2 1.6 3 3.5 3 5.5a7 7 0 1 1-14 0c0-1.153.433-2.294 1-3a2.5 2.5 0 0 0 2.5 2.5z"/>',
    "bell": '<path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9"/><path d="M10.3 21a1.94 1.94 0 0 0 3.4 0"/>',
    "check-circle": '<path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><path d="m9 11 3 3L22 4"/>',
    "alert-triangle": '<path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/><path d="M12 9v4"/><path d="M12 17h.01"/>',
    "info": '<circle cx="12" cy="12" r="10"/><path d="M12 16v-4"/><path d="M12 8h.01"/>',
    "trophy": '<path d="M6 9H4.5a2.5 2.5 0 0 1 0-5H6"/><path d="M18 9h1.5a2.5 2.5 0 0 0 0-5H18"/><path d="M4 22h16"/><path d="M10 14.66V17c0 .55-.47.98-.97 1.21C7.85 18.75 7 20.24 7 22"/><path d="M14 14.66V17c0 .55.47.98.97 1.21C16.15 18.75 17 20.24 17 22"/><path d="M18 2H6v7a6 6 0 0 0 12 0V2Z"/>',
    "tag": '<path d="M12.586 2.586A2 2 0 0 0 11.172 2H4a2 2 0 0 0-2 2v7.172a2 2 0 0 0 .586 1.414l8.704 8.704a2.426 2.426 0 0 0 3.42 0l6.58-6.58a2.426 2.426 0 0 0 0-3.42z"/><circle cx="7.5" cy="7.5" r=".5" fill="currentColor"/>',
    "mail": '<rect width="20" height="16" x="2" y="4" rx="2"/><path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"/>',
    "arrow-right": '<path d="M5 12h14"/><path d="m12 5 7 7-7 7"/>',
    "chevron-left": '<path d="m15 18-6-6 6-6"/>',
    "chevron-right": '<path d="m9 18 6-6-6-6"/>',
    "external-link": '<path d="M15 3h6v6"/><path d="M10 14 21 3"/><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/>',
    # categorias
    "monitor": '<rect width="20" height="14" x="2" y="3" rx="2"/><line x1="8" x2="16" y1="21" y2="21"/><line x1="12" x2="12" y1="17" y2="21"/>',
    "gpu": '<rect x="2" y="7" width="17" height="10" rx="2"/><circle cx="10" cy="12" r="2.6"/><circle cx="15.2" cy="11.4" r=".01"/><path d="M19 10h3v5h-3"/><path d="M6 17v3"/><path d="M11 17v3"/>',
    "cpu": '<rect x="4" y="4" width="16" height="16" rx="2"/><rect x="9" y="9" width="6" height="6"/><path d="M15 2v2"/><path d="M15 20v2"/><path d="M2 15h2"/><path d="M2 9h2"/><path d="M20 15h2"/><path d="M20 9h2"/><path d="M9 2v2"/><path d="M9 20v2"/>',
    "ram": '<path d="M6 19v-3"/><path d="M10 19v-3"/><path d="M14 19v-3"/><path d="M18 19v-3"/><path d="M8 11V9"/><path d="M16 11V9"/><path d="M12 11V9"/><path d="M2 15h20"/><path d="M2 7a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a1 1 0 0 1-1 1H3a1 1 0 0 1-1-1Z"/>',
    "ssd": '<line x1="22" x2="2" y1="12" y2="12"/><path d="M5.45 5.11 2 12v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-6l-3.45-6.89A2 2 0 0 0 16.76 4H7.24a2 2 0 0 0-1.79 1.11z"/><path d="M6 16h.01"/><path d="M10 16h.01"/>',
    "psu": '<path d="M12 2v10"/><path d="M18.4 6.6a9 9 0 1 1-12.77.04"/>',
    "motherboard": '<rect x="3" y="3" width="18" height="18" rx="1.5"/><rect x="7" y="7" width="6" height="6"/><path d="M16 7v4"/><path d="M7 17h10"/><path d="M7 13.5h3"/>',
    "notebook": '<path d="M20 16V7a2 2 0 0 0-2-2H6a2 2 0 0 0-2 2v9m16 0H4m16 0 1.28 2.55a1 1 0 0 1-.9 1.45H3.62a1 1 0 0 1-.9-1.45L4 16"/>',
    "keyboard": '<rect x="2" y="6" width="20" height="12" rx="2"/><path d="M6 10h.01"/><path d="M10 10h.01"/><path d="M14 10h.01"/><path d="M18 10h.01"/><path d="M6 14h.01"/><path d="M18 14h.01"/><path d="M9 14h6"/>',
    "headset": '<path d="M3 14h3a2 2 0 0 1 2 2v3a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-7a9 9 0 0 1 18 0v7a2 2 0 0 1-2 2h-1a2 2 0 0 1-2-2v-3a2 2 0 0 1 2-2h3"/>',
    "fan": '<path d="M10.827 16.379a6.082 6.082 0 0 1-8.618-7.002l5.412 1.45a6.082 6.082 0 0 1 7.002-8.618l-1.45 5.412a6.082 6.082 0 0 1 8.618 7.002l-5.412-1.45a6.082 6.082 0 0 1-7.002 8.618l1.45-5.412Z"/><path d="M12 12v.01"/>',
    "case": '<rect x="6" y="2" width="12" height="20" rx="1.5"/><rect x="9" y="6" width="6" height="4"/><path d="M12 16h.01"/><path d="M15 16h.01"/>',
    "package": '<path d="M21 8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16Z"/><path d="m3.3 7 8.7 5 8.7-5"/><path d="M12 22V12"/>',
}

CATEGORY_ICON_RULES = [
    ("gpu", ("placa-de-video", "placas-de-video", "gpu", "video")),
    ("cpu", ("processador", "processadores", "cpu")),
    ("ram", ("memoria", "memorias", "memoria-ram", "ram")),
    ("ssd", ("ssd", "hd", "armazenamento", "ssd-hd", "disco")),
    ("monitor", ("monitor", "monitores", "display")),
    ("psu", ("fonte", "fontes", "alimentacao")),
    ("motherboard", ("placa-mae", "placas-mae")),
    ("notebook", ("notebook", "notebooks", "computador", "computadores", "pc")),
    ("keyboard", ("teclado", "teclados", "mouse", "mouses", "periferico", "perifericos")),
    ("headset", ("headset", "headsets", "fone", "audio")),
    ("fan", ("cooler", "coolers", "water-cooler", "refrigeracao", "ventoinha")),
    ("case", ("gabinete", "gabinetes", "case")),
]

STORE_BADGE_CLASSES = {
    "kabum": "border-amber-500/40 bg-amber-500/10 text-amber-300",
    "pichau": "border-red-500/40 bg-red-500/10 text-red-300",
    "terabyte": "border-sky-500/40 bg-sky-500/10 text-sky-300",
}
DEFAULT_STORE_BADGE = "border-slate-600/60 bg-slate-700/30 text-slate-300"


@register.simple_tag
def icon(name, classes="h-5 w-5"):
    """Renderiza um ícone SVG inline no estilo Lucide (stroke consistente)."""
    paths = ICON_SVG.get(name, ICON_SVG["package"])
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" '
        f'stroke="currentColor" stroke-width="2" stroke-linecap="round" '
        f'stroke-linejoin="round" class="{classes}" aria-hidden="true">{paths}</svg>'
    )
    return mark_safe(svg)


@register.filter
def brl(value):
    """Formata um número como moeda pt-BR: R$ 4.979,90."""
    if value in (None, ""):
        return value
    try:
        amount = Decimal(str(value)).quantize(Decimal("0.01"))
    except (InvalidOperation, ValueError):
        return value
    formatted = f"{amount:,.2f}".replace(",", "@").replace(".", ",").replace("@", ".")
    return f"R$ {formatted}"


@register.filter
def category_icon(category):
    """Escolhe o ícone de acordo com o slug da categoria."""
    slug = getattr(category, "slug", "") or ""
    for icon_name, keywords in CATEGORY_ICON_RULES:
        if any(keyword in slug for keyword in keywords):
            return icon_name
    return "package"


@register.filter
def store_badge(store):
    """Classes Tailwind do badge da loja conforme a identidade visual dela."""
    slug = getattr(store, "slug", "") or ""
    return STORE_BADGE_CLASSES.get(slug, DEFAULT_STORE_BADGE)
