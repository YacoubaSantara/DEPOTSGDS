"""
Migration 0020 : ajoute la permission 'voir_gabarit_email_mouvement' pour le
nouvel écran d'édition du gabarit (sujet/corps) de l'email envoyé
immédiatement au marketeur à la création d'un mouvement.

Assignée à CHEF_DEPOT (qui a déjà les gabarits/écrans voisins) et SUPERADMIN
(déjà couvert par '__ALL__' mais explicite ici pour la cohérence avec le
pattern des migrations précédentes).
"""
from django.db import migrations


NOUVELLES_PERMISSIONS = [
    ('voir_gabarit_email_mouvement', "Consulter/modifier le gabarit d'email des mouvements"),
]

ROLES_A_COMPLETER = ['CHEF_DEPOT']


def migrer(apps, schema_editor):
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

    for code in ROLES_A_COMPLETER:
        role = Role.objects.filter(code=code).first()
        if role:
            role.permissions.add(*perms_par_code.values())

    superadmin = Role.objects.filter(code='SUPERADMIN').first()
    if superadmin:
        superadmin.permissions.add(*perms_par_code.values())


def revenir(apps, schema_editor):
    Role       = apps.get_model('users', 'Role')
    Permission = apps.get_model('auth', 'Permission')

    codes = [c for c, _ in NOUVELLES_PERMISSIONS]
    perms = Permission.objects.filter(codename__in=codes)

    for code in ROLES_A_COMPLETER + ['SUPERADMIN']:
        role = Role.objects.filter(code=code).first()
        if role:
            role.permissions.remove(*perms)

    perms.delete()


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0019_envoi_etats_mensuels'),
    ]

    operations = [
        migrations.RunPython(migrer, revenir),
    ]
