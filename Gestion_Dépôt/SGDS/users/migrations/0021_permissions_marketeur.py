"""
Migration 0021 : Aligne les permissions DB du rôle MARKETEUR sur le
référentiel ROLES_SYSTEME_PERMISSIONS (permissions_registry.py).

Le rôle MARKETEUR avait été créé sans permission RBAC (migration 0005,
l'accès étant alors géré par le rôle légataire is_marketeur_role), puis
seul voir_etat lui a été accordé (0014). Or l'API mobile
(api/v1/permissions.py — permission_codename='voir_mouvement',
MOBILE_FLOTTE_PERMISSIONS) et l'espace client web
(@voir_required('voir_mouvement'), views/client.py) vérifient désormais
ces permissions via le backend RBAC : sur une base fraîchement migrée,
un marketeur recevait 403 sur ses propres mouvements et la flotte.
"""
from django.db import migrations


PERMISSIONS_MARKETEUR = [
    ('voir_mouvement',        'Consulter les mouvements'),
    ('voir_detail_mouvement', 'Consulter le détail des mouvements'),
    ('exporter_mouvement',    'Exporter les mouvements'),
    ('voir_camion',           'Consulter les camions'),
    ('ajouter_camion',        'Ajouter un camion'),
    ('modifier_camion',       'Modifier un camion'),
    ('supprimer_camion',      'Supprimer un camion'),
    ('voir_chauffeur',        'Consulter les chauffeurs'),
    ('ajouter_chauffeur',     'Ajouter un chauffeur'),
    ('modifier_chauffeur',    'Modifier un chauffeur'),
    ('supprimer_chauffeur',   'Supprimer un chauffeur'),
    ('voir_coulage',          'Consulter la répartition du coulage'),
    ('voir_frais_passage',    'Consulter les frais de passage'),
    ('voir_etat',             'Consulter les états'),
]


def ajouter_permissions(apps, schema_editor):
    UserProfile = apps.get_model('users', 'UserProfile')
    Role        = apps.get_model('users', 'Role')
    Permission  = apps.get_model('auth', 'Permission')
    ContentType = apps.get_model('contenttypes', 'ContentType')

    marketeur = Role.objects.filter(code='MARKETEUR').first()
    if not marketeur:
        return

    ct = ContentType.objects.get_for_model(UserProfile)
    perms = []
    for codename, libelle in PERMISSIONS_MARKETEUR:
        perm, _ = Permission.objects.get_or_create(
            codename=codename,
            content_type=ct,
            defaults={'name': libelle},
        )
        perms.append(perm)
    marketeur.permissions.add(*perms)


def retirer_permissions(apps, schema_editor):
    UserProfile = apps.get_model('users', 'UserProfile')
    Role        = apps.get_model('users', 'Role')
    Permission  = apps.get_model('auth', 'Permission')
    ContentType = apps.get_model('contenttypes', 'ContentType')

    marketeur = Role.objects.filter(code='MARKETEUR').first()
    if not marketeur:
        return

    ct = ContentType.objects.get_for_model(UserProfile)
    codenames = [c for c, _ in PERMISSIONS_MARKETEUR if c != 'voir_etat']
    perms = Permission.objects.filter(codename__in=codenames, content_type=ct)
    marketeur.permissions.remove(*perms)


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0020_gabarit_email_mouvement'),
    ]

    operations = [
        migrations.RunPython(ajouter_permissions, retirer_permissions),
    ]
