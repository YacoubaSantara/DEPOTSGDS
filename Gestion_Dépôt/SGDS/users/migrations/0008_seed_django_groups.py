"""
Migration 0008 — Data migration : crée un auth.Group pour chaque Role
existant et synchronise les membres (user.groups) selon UserProfile.role.

Après cette migration, chaque Role a son django_group renseigné,
et chaque utilisateur appartient au groupe correspondant à son rôle.
"""
from django.db import migrations


def creer_groups_pour_roles(apps, schema_editor):
    """
    Pour chaque Role existant :
      - Crée (ou récupère) un auth.Group dont le name = role.code
      - Copie les permissions du Role vers le Group
      - Lie Role.django_group → Group
    """
    Role = apps.get_model('users', 'Role')
    Group = apps.get_model('auth', 'Group')

    for role in Role.objects.all():
        group, _ = Group.objects.get_or_create(name=role.code)
        # Copier les permissions existantes du rôle vers le groupe
        group.permissions.set(role.permissions.all())
        role.django_group = group
        role.save(update_fields=['django_group'])


def synchroniser_membres_groupes(apps, schema_editor):
    """
    Pour chaque UserProfile avec un rôle défini :
      - Ajoute l'utilisateur au auth.Group correspondant à son rôle
    """
    UserProfile = apps.get_model('users', 'UserProfile')

    for profil in UserProfile.objects.select_related('role', 'user').all():
        if profil.role and profil.role.django_group_id:
            Group = apps.get_model('auth', 'Group')
            groupe = Group.objects.filter(pk=profil.role.django_group_id).first()
            if groupe:
                profil.user.groups.add(groupe)


def annuler_groups(apps, schema_editor):
    """Reverse : détache les groups des rôles (ne les supprime pas)."""
    Role = apps.get_model('users', 'Role')
    Role.objects.update(django_group=None)


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0007_role_django_group'),
    ]

    operations = [
        migrations.RunPython(creer_groups_pour_roles, reverse_code=annuler_groups),
        migrations.RunPython(synchroniser_membres_groupes, reverse_code=migrations.RunPython.noop),
    ]
