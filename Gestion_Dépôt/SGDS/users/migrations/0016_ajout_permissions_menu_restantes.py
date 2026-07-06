"""
Migration 0016 : Ajoute au référentiel les permissions manquantes pour les
derniers liens de menu encore pilotés par un rôle en dur dans le code
(Société, Configuration email, Paramètres jaugeage, Gestion des dépôts,
Stock ouverture/fermeture mensuel) — voir_societe et modifier_societe
existaient déjà mais n'étaient pas réellement utilisés par les vues.

Les assignations par rôle préservent exactement l'accès actuel (ex:
gerer_depot va uniquement à SUPERADMIN, comme @superadmin_required
aujourd'hui) — rien ne change pour les utilisateurs existants tant que
personne ne modifie les permissions via l'écran Rôles.
"""
from django.db import migrations


NOUVELLES_PERMISSIONS = [
    ('voir_parametre_jaugeage',        'Consulter les paramètres de jaugeage'),
    ('gerer_depot',                    'Gérer la liste des dépôts'),
    ('voir_stock_ouverture_fermeture', 'Consulter le stock ouverture/fermeture mensuel'),
]

# Préserve l'accès actuel : voir_parametre_jaugeage suit voir_cuve (déjà
# accordé à ces 3 rôles), voir_stock_ouverture_fermeture suit
# @chef_depot_required (CHEF_DEPOT seulement, SUPERADMIN via le garde-fou),
# gerer_depot suit @superadmin_required (aucun rôle non-SUPERADMIN ici).
ROLES_A_COMPLETER = {
    'CHEF_DEPOT': ['voir_parametre_jaugeage', 'voir_stock_ouverture_fermeture'],
    'OPERATEUR':  ['voir_parametre_jaugeage'],
    'COMPTABLE':  ['voir_parametre_jaugeage'],
}


def ajouter_permissions(apps, schema_editor):
    UserProfile = apps.get_model('users', 'UserProfile')
    Role        = apps.get_model('users', 'Role')
    Permission  = apps.get_model('auth', 'Permission')
    ContentType = apps.get_model('contenttypes', 'ContentType')

    ct = ContentType.objects.get_for_model(UserProfile)

    perms_par_code = {}
    for codename, libelle in NOUVELLES_PERMISSIONS:
        perm, _ = Permission.objects.get_or_create(
            codename=codename,
            content_type=ct,
            defaults={'name': libelle},
        )
        perms_par_code[codename] = perm

    for code, codenames in ROLES_A_COMPLETER.items():
        role = Role.objects.filter(code=code).first()
        if not role:
            continue
        role.permissions.add(*[perms_par_code[c] for c in codenames])

    superadmin = Role.objects.filter(code='SUPERADMIN').first()
    if superadmin:
        superadmin.permissions.add(*perms_par_code.values())


def retirer_permissions(apps, schema_editor):
    Role       = apps.get_model('users', 'Role')
    Permission = apps.get_model('auth', 'Permission')

    codes = [c for c, _ in NOUVELLES_PERMISSIONS]
    perms = Permission.objects.filter(codename__in=codes)
    for role in Role.objects.all():
        role.permissions.remove(*perms)
    perms.delete()


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0015_backfill_role_manquant'),
    ]

    operations = [
        migrations.RunPython(ajouter_permissions, retirer_permissions),
    ]
