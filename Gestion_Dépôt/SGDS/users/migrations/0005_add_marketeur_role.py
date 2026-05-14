"""
Migration 0005 : Ajoute le rôle système MARKETEUR dans la table Role.
Ce rôle est réservé aux clients externes (sociétés marketeurs).
Il n'a aucune permission RBAC interne — l'accès est géré via
UtilisateurSGDS.role == 'MARKETEUR' et le lien UtilisateurSGDS.marketeur.
"""
from django.db import migrations


def ajouter_role_marketeur(apps, schema_editor):
    Role = apps.get_model('users', 'Role')
    Role.objects.get_or_create(
        code='MARKETEUR',
        defaults={
            'nom':         'Marketeur (Client)',
            'description': 'Accès à l\'espace client uniquement — consulte ses propres données (stock, mouvements, coulage)',
            'systeme':     True,
            'couleur':     'orange',
        },
    )


def supprimer_role_marketeur(apps, schema_editor):
    Role = apps.get_model('users', 'Role')
    Role.objects.filter(code='MARKETEUR', systeme=True).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0004_remove_role_old'),
    ]

    operations = [
        migrations.RunPython(ajouter_role_marketeur, supprimer_role_marketeur),
    ]
