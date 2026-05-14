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
