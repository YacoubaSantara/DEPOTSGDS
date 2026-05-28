from django import template

register = template.Library()

NNBSP = " "  # narrow no-break space U+202F


@register.filter(name="frnum")
def frnum(value):
    """Formate un nombre à la française : 32500 → '32 500' (espace fine insécable)."""
    if value is None or value == "":
        return "—"
    try:
        n = float(value)
    except (TypeError, ValueError):
        return value
    if n == int(n):
        s = f"{int(n):,}".replace(",", NNBSP)
    else:
        s = f"{n:,.2f}".replace(",", NNBSP).replace(".", ",")
    return s
