from django import template

register = template.Library()

ROLE_STYLES = {
    'SUPERADMIN': ('background:#fee2e2;color:#991b1b;border:1px solid #fca5a5',
                   'S.Admin'),
    'CHEF_DEPOT': ('background:#dbeafe;color:#1d4ed8;border:1px solid #93c5fd',
                   'Chef Dépôt'),
    'OPERATEUR':  ('background:#dcfce7;color:#166534;border:1px solid #86efac',
                   'Opérateur'),
    'COMPTABLE':  ('background:#fef9c3;color:#854d0e;border:1px solid #fde047',
                   'Comptable'),
    'LECTEUR':    ('background:#f1f5f9;color:#475569;border:1px solid #cbd5e1',
                   'Lecteur'),
}

ACTION_ICONS = {
    'CREATE':       '🟢',
    'UPDATE':       '🟡',
    'DELETE':       '🔴',
    'VIEW':         '👁',
    'LOGIN':        '🔐',
    'LOGOUT':       '🚪',
    'LOGIN_FAILED': '⚠️',
    'EXPORT':       '📊',
    'VALIDATE':     '✅',
    'CLOSE':        '🔒',
    'OPEN':         '🔓',
}

ACTION_COLORS = {
    'CREATE':       '#dcfce7;color:#166534',
    'UPDATE':       '#fef9c3;color:#854d0e',
    'DELETE':       '#fee2e2;color:#991b1b',
    'LOGIN':        '#dbeafe;color:#1d4ed8',
    'LOGOUT':       '#f1f5f9;color:#475569',
    'LOGIN_FAILED': '#fff7ed;color:#c2410c',
    'EXPORT':       '#f3e8ff;color:#7e22ce',
    'VALIDATE':     '#dcfce7;color:#166534',
    'CLOSE':        '#f1f5f9;color:#334155',
    'OPEN':         '#ccfbf1;color:#0f766e',
}


@register.inclusion_tag('users/partials/role_badge.html')
def role_badge(user):
    if not user or not user.is_authenticated:
        return {'style': '', 'libelle': ''}
    profil = getattr(user, 'profile', None)
    if not profil:
        return {'style': '', 'libelle': ''}
    code = profil.role.code if profil.role else ''
    style, libelle = ROLE_STYLES.get(
        code,
        ('background:#f1f5f9;color:#475569;border:1px solid #cbd5e1', profil.role.nom if profil.role else ''),
    )
    return {'style': style, 'libelle': libelle}


@register.filter
def action_icon(action):
    return ACTION_ICONS.get(action, '•')


@register.filter
def action_badge_style(action):
    colors = ACTION_COLORS.get(action, '#f1f5f9;color:#475569')
    return f"background:#{colors}" if not colors.startswith('#') else f"background:{colors}"


@register.simple_tag
def has_role(user, *roles):
    """Retourne True si user a l'un des rôles donnés."""
    if not user or not user.is_authenticated:
        return False
    profil = getattr(user, 'profile', None)
    if not profil or not profil.actif:
        return False
    role_code = profil.role.code if profil.role else ''
    return role_code in roles
