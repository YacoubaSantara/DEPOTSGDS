from django.conf import settings
from django.db.models.signals import post_save, post_delete, pre_save, m2m_changed
from django.dispatch import receiver
from django.contrib.auth.signals import (
    user_logged_in, user_logged_out, user_login_failed,
)

from .models import UserProfile, AuditLog, Role
from .middleware import get_current_request


MODELS_AUDITES = {
    'Mouvement', 'LigneMouvement', 'JaugeageJour', 'MesureCuve',
    'PeriodeComptable', 'StockOuverture', 'StockOuvertureCuve',
    'ParametresCoulage', 'ClotureCoulageMensuel',
    'Marketeur', 'Cuve', 'Produit', 'ParametreJaugeageCuve',
    'Camion', 'Chauffeur',
    'UserProfile', 'Role',
}

_pre_save_state: dict = {}


# ── Création automatique du UserProfile ────────────────────────────────────────
@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def creer_profil_utilisateur(sender, instance, created, **kwargs):
    if created:
        role_defaut = Role.objects.filter(code='LECTEUR').first()
        UserProfile.objects.get_or_create(
            user=instance,
            defaults={'role': role_defaut},
        )


# ── Helpers ────────────────────────────────────────────────────────────────────
def _get_client_ip(request):
    xff = request.META.get('HTTP_X_FORWARDED_FOR')
    if xff:
        return xff.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


def _log_action(instance, action, changements=None, description=''):
    request = get_current_request()
    user = getattr(request, 'user', None) if request else None
    if user and not user.is_authenticated:
        user = None

    ip = None
    user_agent = ''
    source = 'SYSTEM'
    if request:
        ip = _get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')[:300]
        source = 'ADMIN' if request.path.startswith('/admin/') else 'WEB'

    AuditLog.objects.create(
        user=user,
        user_username_snapshot=user.username if user else '',
        action=action,
        objet_type=instance.__class__.__name__,
        objet_id=instance.pk,
        objet_repr=str(instance)[:300],
        description=description,
        ip_address=ip,
        user_agent=user_agent,
        source=source,
        changements=changements,
    )


# ── Capture état avant modification ────────────────────────────────────────────
@receiver(pre_save)
def capturer_etat_avant(sender, instance, **kwargs):
    if sender.__name__ not in MODELS_AUDITES:
        return
    if instance.pk is None:
        return
    try:
        ancien = sender.objects.get(pk=instance.pk)
        _pre_save_state[(sender.__name__, instance.pk)] = {
            f.name: getattr(ancien, f.name)
            for f in sender._meta.fields
            if not f.is_relation or f.many_to_one
        }
    except sender.DoesNotExist:
        pass


# ── Audit CREATE / UPDATE ───────────────────────────────────────────────────────
@receiver(post_save)
def auditer_modification(sender, instance, created, **kwargs):
    if sender.__name__ not in MODELS_AUDITES:
        return

    action = AuditLog.Action.CREATE if created else AuditLog.Action.UPDATE
    changements = None

    if not created:
        ancien = _pre_save_state.pop((sender.__name__, instance.pk), None)
        if ancien:
            changements = {}
            for k, v_avant in ancien.items():
                v_apres = getattr(instance, k, None)
                if v_avant != v_apres:
                    changements[k] = {
                        'avant': str(v_avant) if v_avant is not None else None,
                        'apres': str(v_apres) if v_apres is not None else None,
                    }
            if not changements:
                return  # Aucun changement réel

    _log_action(instance, action, changements=changements)


# ── Audit DELETE ───────────────────────────────────────────────────────────────
@receiver(post_delete)
def auditer_suppression(sender, instance, **kwargs):
    if sender.__name__ not in MODELS_AUDITES:
        return
    _log_action(instance, AuditLog.Action.DELETE)


# ── Audit connexions ───────────────────────────────────────────────────────────
@receiver(user_logged_in)
def log_login(sender, request, user, **kwargs):
    AuditLog.objects.create(
        user=user,
        user_username_snapshot=user.username,
        action=AuditLog.Action.LOGIN,
        ip_address=_get_client_ip(request) if request else None,
        user_agent=(request.META.get('HTTP_USER_AGENT', '') if request else '')[:300],
        source='WEB',
    )
    profil = getattr(user, 'profile', None)
    if profil and request:
        profil.derniere_ip = _get_client_ip(request)
        profil.save(update_fields=['derniere_ip'])


@receiver(user_logged_out)
def log_logout(sender, request, user, **kwargs):
    if user and user.is_authenticated:
        AuditLog.objects.create(
            user=user,
            user_username_snapshot=user.username,
            action=AuditLog.Action.LOGOUT,
            ip_address=_get_client_ip(request) if request else None,
            source='WEB',
        )


@receiver(user_login_failed)
def log_login_failed(sender, credentials, request, **kwargs):
    AuditLog.objects.create(
        user=None,
        user_username_snapshot=credentials.get('username', '')[:150],
        action=AuditLog.Action.LOGIN_FAILED,
        ip_address=_get_client_ip(request) if request else None,
        description=f"Tentative échouée pour '{credentials.get('username', '')}'",
        source='WEB',
    )


# ── Audit des changements de permissions sur un rôle (M2M) ────────────────────
@receiver(m2m_changed, sender=Role.permissions.through)
def auditer_changement_permissions_role(sender, instance, action, pk_set, **kwargs):
    if action not in ('post_add', 'post_remove', 'post_clear'):
        return

    from django.contrib.auth.models import Permission
    libelles = []
    if pk_set:
        libelles = list(
            Permission.objects.filter(pk__in=pk_set)
                              .values_list('codename', flat=True)
        )

    verbe = {'post_add': 'ajoutées', 'post_remove': 'retirées', 'post_clear': 'effacées'}
    description = (
        f"Permissions {verbe.get(action, action)}: "
        f"{', '.join(libelles) or 'toutes'}"
    )
    _log_action(instance, AuditLog.Action.UPDATE, description=description)


# ── Garde-fou : SUPERADMIN garde toujours TOUTES les permissions ───────────────
@receiver(m2m_changed, sender=Role.permissions.through)
def empecher_retrait_permissions_superadmin(sender, instance, action, pk_set, **kwargs):
    if instance.code != 'SUPERADMIN':
        return
    if action not in ('post_remove', 'post_clear'):
        return

    from django.contrib.auth.models import Permission
    from .permissions_registry import PERMISSIONS_REGISTRY
    codes = []
    for cat in PERMISSIONS_REGISTRY.values():
        codes.extend(c for c, _ in cat['permissions'])
    toutes_perms = Permission.objects.filter(codename__in=codes)
    instance.permissions.set(toutes_perms)
