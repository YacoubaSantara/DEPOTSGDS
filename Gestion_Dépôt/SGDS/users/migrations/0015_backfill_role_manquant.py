"""
Migration 0015 : Corrige les UserProfile dont role est NULL en le déduisant
du CharField legacy accounts.UtilisateurSGDS.role (MARKETEUR/OPERATEUR).

Cause racine (corrigée en parallèle dans users/signals.py) : le signal de
création automatique de UserProfile assignait par défaut le rôle 'LECTEUR',
supprimé depuis la migration 0006_remove_lecteur_role — tout profil créé
depuis (notamment via Django admin, hors du formulaire CreerUtilisateurView)
se retrouvait avec role=NULL, invisible jusqu'à ce que les vues commencent à
vérifier les permissions RBAC plutôt que le seul rôle legacy.
"""
from django.db import migrations


MAPPING = {
    'MARKETEUR': 'MARKETEUR',
    'OPERATEUR': 'OPERATEUR',
}


def backfill_role(apps, schema_editor):
    UserProfile = apps.get_model('users', 'UserProfile')
    Role        = apps.get_model('users', 'Role')

    roles_par_code = {r.code: r for r in Role.objects.filter(code__in=MAPPING.values())}

    for profil in UserProfile.objects.filter(role__isnull=True).select_related('user'):
        code_legacy = getattr(profil.user, 'role', None)
        code_rbac = MAPPING.get(code_legacy)
        if code_rbac and code_rbac in roles_par_code:
            profil.role = roles_par_code[code_rbac]
            profil.save(update_fields=['role'])


def reverse_noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0014_voir_etat_marketeur'),
    ]

    operations = [
        migrations.RunPython(backfill_role, reverse_noop),
    ]
