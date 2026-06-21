from django import template

register = template.Library()


@register.filter
def lookup(d, key):
    """Accède à un dict avec une clé dynamique (id de produit, etc.)."""
    if isinstance(d, dict):
        return d.get(key)
    return None


@register.filter
def lookup_id(d, obj):
    """Accède à un dict avec obj.id comme clé."""
    if isinstance(d, dict) and obj is not None:
        return d.get(obj.id)
    return None


@register.filter
def cycle_class(index, prefix):
    """Classe CSS cyclique 'prefix-0'..'prefix-5' à partir d'un index (forloop.counter0).
    Permet de colorer les groupes de colonnes par produit sans répéter un if/elif
    en cascade à chaque cellule, et cycle proprement au-delà de 6 produits."""
    try:
        idx = int(index) % 6
    except (TypeError, ValueError):
        idx = 0
    return f"{prefix}-{idx}"
