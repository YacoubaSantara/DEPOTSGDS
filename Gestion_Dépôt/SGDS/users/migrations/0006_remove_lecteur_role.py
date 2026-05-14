"""
Migration 0006 : Supprime le rôle LECTEUR de la table Role.
- Rend d'abord role_id nullable (AlterField)
- Nullifie tous les UserProfile dont le rôle est LECTEUR
- Supprime ensuite l'entrée Role(code='LECTEUR')
"""
import django.db.models.deletion
from django.db import migrations, models


def supprimer_lecteur(apps, schema_editor):
    Role        = apps.get_model('users', 'Role')
    UserProfile = apps.get_model('users', 'UserProfile')

    lecteur_qs = Role.objects.filter(code='LECTEUR')
    if not lecteur_qs.exists():
        return  # Déjà absent, rien à faire

    lecteur = lecteur_qs.first()

    # 1. Mettre tous les profils avec rôle LECTEUR à NULL (colonne nullable après AlterField)
    UserProfile.objects.filter(role=lecteur).update(role=None)

    # 2. Supprimer via queryset (contourne le delete() personnalisé du modèle)
    lecteur_qs.delete()


def restaurer_lecteur(apps, schema_editor):
    """Rollback : recrée le rôle LECTEUR (sans réassigner les profils)."""
    Role = apps.get_model('users', 'Role')
    Role.objects.get_or_create(
        code='LECTEUR',
        defaults={
            'nom':         'Lecteur (Lecture seule)',
            'description': 'Accès en lecture seule — aucune action de modification.',
            'systeme':     True,
            'couleur':     'gray',
        },
    )


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0005_add_marketeur_role'),
    ]

    operations = [
        # Étape 1 : rendre role_id nullable en base avant de pouvoir y écrire NULL
        migrations.AlterField(
            model_name='userprofile',
            name='role',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='utilisateurs',
                to='users.role',
                verbose_name='Rôle',
            ),
        ),
        # Étape 2 : supprimer le rôle LECTEUR et nullifier les profils associés
        migrations.RunPython(supprimer_lecteur, restaurer_lecteur),
    ]
