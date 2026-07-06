"""
Migration 0017 : voir_societe et modifier_societe existaient déjà dans le
référentiel (et dans ROLES_SYSTEME_PERMISSIONS pour CHEF_DEPOT) mais
n'avaient jamais été réellement accordées au rôle CHEF_DEPOT en base — seul
le décorateur @chef_depot_required (rôle en dur) protégeait societe_detail/
configuration_email jusqu'ici. Maintenant que ces vues utilisent
voir_required('voir_societe')/('modifier_societe'), il faut les accorder
explicitement pour ne pas régresser l'accès de CHEF_DEPOT.
"""
from django.db import migrations

CODES = ['voir_societe', 'modifier_societe']


def ajouter_permissions(apps, schema_editor):
    Role       = apps.get_model('users', 'Role')
    Permission = apps.get_model('auth', 'Permission')

    perms = list(Permission.objects.filter(codename__in=CODES))
    chef_depot = Role.objects.filter(code='CHEF_DEPOT').first()
    if chef_depot:
        chef_depot.permissions.add(*perms)

    superadmin = Role.objects.filter(code='SUPERADMIN').first()
    if superadmin:
        superadmin.permissions.add(*perms)


def retirer_permissions(apps, schema_editor):
    Role       = apps.get_model('users', 'Role')
    Permission = apps.get_model('auth', 'Permission')

    perms = Permission.objects.filter(codename__in=CODES)
    chef_depot = Role.objects.filter(code='CHEF_DEPOT').first()
    if chef_depot:
        chef_depot.permissions.remove(*perms)


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0016_ajout_permissions_menu_restantes'),
    ]

    operations = [
        migrations.RunPython(ajouter_permissions, retirer_permissions),
    ]
