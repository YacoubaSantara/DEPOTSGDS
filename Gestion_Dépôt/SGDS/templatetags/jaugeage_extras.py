"""
Template tags et filtres pour le module jaugeage.
Usage dans les templates : {% load jaugeage_extras %}
"""
from django import template
from decimal import Decimal, InvalidOperation

register = template.Library()


# ─────────────────────────────────────────────────────────────
#  FILTRES DE FORMATAGE
# ─────────────────────────────────────────────────────────────

@register.filter(name='fmt_vol')
def fmt_vol(value, decimal_places=0):
    """
    Formate un volume (litres) avec séparateur milliers = espace insécable (\u202f).
    Ex : 1234567.89 → "1 234 568" (dec=0) ou "1 234 567,89" (dec=2)
    Retourne '—' si la valeur est None.
    """
    if value is None:
        return '—'
    try:
        v = float(value)
        dec = int(decimal_places)
        # Formater avec virgule comme séparateur de milliers (style Python)
        formatted = f"{v:,.{dec}f}"
        # Remplacer la virgule de milliers par espace insécable étroit
        formatted = formatted.replace(',', '\u202f')
        return formatted
    except (ValueError, TypeError):
        return str(value)


@register.filter(name='fmt_density')
def fmt_density(value):
    """Formate une densité avec 2 décimales. Ex : 726.45"""
    if value is None:
        return '—'
    try:
        return f"{float(value):.2f}"
    except (ValueError, TypeError):
        return str(value)


@register.filter(name='fmt_vcf')
def fmt_vcf(value):
    """Formate un facteur Vcf avec 4 décimales. Ex : 0.9978"""
    if value is None:
        return '—'
    try:
        return f"{float(value):.4f}"
    except (ValueError, TypeError):
        return str(value)


@register.filter(name='fmt_temp')
def fmt_temp(value):
    """Formate une température avec 2 décimales. Ex : 32.50"""
    if value is None:
        return '—'
    try:
        return f"{float(value):.2f}"
    except (ValueError, TypeError):
        return str(value)


@register.filter(name='or_tiret')
def or_tiret(value):
    """Retourne '—' si la valeur est None ou vide."""
    if value is None or value == '':
        return '—'
    return value


@register.filter(name='get_item')
def get_item(dictionary, key):
    """Accès à un dict par clé dynamique. Ex : {{ mon_dict|get_item:ma_cle }}"""
    if not isinstance(dictionary, dict):
        return None
    return dictionary.get(key)


@register.filter(name='fmt_mm')
def fmt_mm(value):
    """Formate une hauteur en mm (entier). Ex : 12 345"""
    if value is None:
        return '—'
    try:
        v = int(value)
        return f"{v:,}".replace(',', '\u202f')
    except (ValueError, TypeError):
        return str(value)


# ─────────────────────────────────────────────────────────────
#  TAGS SIMPLES
# ─────────────────────────────────────────────────────────────

@register.simple_tag
def jaugeage_total_v15(jaugeage):
    """
    Calcule le volume total standard @15°C du dépôt pour un jaugeage donné.
    Itère sur toutes les mesures et somme volume_standard_15c_calcule.
    Retourne None si aucune valeur disponible.
    """
    total = 0.0
    has_value = False
    for m in jaugeage.mesures.all():
        v = m.volume_standard_15c_calcule
        if v is not None:
            total += float(v)
            has_value = True
    return total if has_value else None


@register.simple_tag
def jaugeage_total_vad(jaugeage):
    """
    Calcule le volume total ambiant dépôt pour un jaugeage donné.
    Itère sur toutes les mesures et somme volume_ambiant_depot.
    Retourne None si aucune valeur disponible.
    """
    total = 0.0
    has_value = False
    for m in jaugeage.mesures.all():
        v = m.volume_ambiant_depot
        if v is not None:
            total += float(v)
            has_value = True
    return total if has_value else None
