"""
Migration 0013 : Ajoute au référentiel les permissions nécessaires au filtrage
du menu (voir_famille, voir_inventaire, voir_etat) et les assigne aux rôles
système existants (CHEF_DEPOT, OPERATEUR, COMPTABLE, SUPERADMIN).

Le rôle LECTEUR a été supprimé en migration 0006 : on ignore silencieusement
son absence plutôt que d'échouer.
"""
from django.db import migrations


NOUVELLES_PERMISSIONS = [
    ('voir_famille',    'Consulter les familles'),
    ('voir_inventaire', "Consulter l'inventaire initial"),
    ('voir_etat',       'Consulter les états et rapports de stock'),
]

ROLES_A_COMPLETER = {
    'CHEF_DEPOT': ['voir_famille', 'voir_inventaire', 'voir_etat'],
    'OPERATEUR':  ['voir_famille', 'voir_inventaire', 'voir_etat'],
    'COMPTABLE':  ['voir_famille', 'voir_inventaire', 'voir_etat'],
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
        ('users', '0012_remove_userprofile_depot'),
    ]

    operations = [
        migrations.RunPython(ajouter_permissions, retirer_permissions),
    ]
