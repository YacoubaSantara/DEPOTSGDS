"""
Migration 0018 : éclate la permission générique 'voir_etat' (côté admin) en
permissions distinctes par écran — Carte de stock, Stock global, Global
dépôt, RJJ, Stock à 15°, Stock Ambiant — pour que chacune soit activable
séparément par rôle depuis l'écran Rôles. Ajoute aussi
'voir_parametre_metrologique' (écran laissé ouvert à tous jusqu'ici).

'voir_etat' reste utilisée telle quelle côté espace marketeur (carte_stock,
stock_global_marketeur, écrans mensuels marketeur) — non touchée ici, le
MARKETEUR n'a pas demandé cette granularité.

Assignation = exactement l'accès actuel (CHEF_DEPOT/OPERATEUR/COMPTABLE
avaient tous 'voir_etat' → ils reçoivent les 6 permissions équivalentes ;
'voir_parametre_metrologique' était ouvert à tous les rôles non-marketeur →
même chose ici). 'voir_etat' est retiré de ces 3 rôles côté admin puisque
plus aucune vue admin ne la teste.
"""
from django.db import migrations


NOUVELLES_PERMISSIONS = [
    ('voir_parametre_metrologique', 'Consulter les paramètres métrologiques'),
    ('voir_carte_stock',            'Consulter la carte de stock'),
    ('voir_stock_global',           'Consulter le stock global'),
    ('voir_etat_global_depot',      "Consulter l'état global dépôt mensuel"),
    ('voir_etat_rjj',                "Consulter l'état RJJ mensuel"),
    ('voir_etat_stock_15',           'Consulter le stock à 15° mensuel'),
    ('voir_etat_stock_ambiant',      'Consulter le stock ambiant mensuel'),
]

ROLES_A_COMPLETER = ['CHEF_DEPOT', 'OPERATEUR', 'COMPTABLE']


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

    voir_etat = Permission.objects.filter(codename='voir_etat').first()

    for code in ROLES_A_COMPLETER:
        role = Role.objects.filter(code=code).first()
        if not role:
            continue
        role.permissions.add(*perms_par_code.values())
        if voir_etat:
            role.permissions.remove(voir_etat)

    superadmin = Role.objects.filter(code='SUPERADMIN').first()
    if superadmin:
        superadmin.permissions.add(*perms_par_code.values())


def revenir(apps, schema_editor):
    Role        = apps.get_model('users', 'Role')
    Permission  = apps.get_model('auth', 'Permission')

    codes = [c for c, _ in NOUVELLES_PERMISSIONS]
    perms = Permission.objects.filter(codename__in=codes)
    voir_etat = Permission.objects.filter(codename='voir_etat').first()

    for code in ROLES_A_COMPLETER:
        role = Role.objects.filter(code=code).first()
        if not role:
            continue
        role.permissions.remove(*perms)
        if voir_etat:
            role.permissions.add(voir_etat)

    perms.delete()


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0017_voir_societe_chef_depot'),
    ]

    operations = [
        migrations.RunPython(migrer, revenir),
    ]
