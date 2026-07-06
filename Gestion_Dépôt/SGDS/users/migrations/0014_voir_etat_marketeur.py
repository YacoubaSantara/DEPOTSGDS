"""
Migration 0014 : Assigne la permission voir_etat (créée en 0013) au rôle
MARKETEUR, pour que les écrans Carte de stock / Stock global / États mensuels
de l'espace marketeur soient eux aussi pilotés par le RBAC (pas seulement par
le rôle légataire @marketeur_required).
"""
from django.db import migrations


def ajouter_permission(apps, schema_editor):
    Role        = apps.get_model('users', 'Role')
    Permission  = apps.get_model('auth', 'Permission')

    marketeur = Role.objects.filter(code='MARKETEUR').first()
    perm = Permission.objects.filter(codename='voir_etat').first()
    if marketeur and perm:
        marketeur.permissions.add(perm)


def retirer_permission(apps, schema_editor):
    Role        = apps.get_model('users', 'Role')
    Permission  = apps.get_model('auth', 'Permission')

    marketeur = Role.objects.filter(code='MARKETEUR').first()
    perm = Permission.objects.filter(codename='voir_etat').first()
    if marketeur and perm:
        marketeur.permissions.remove(perm)


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0013_ajout_permissions_menu'),
    ]

    operations = [
        migrations.RunPython(ajouter_permission, retirer_permission),
    ]
