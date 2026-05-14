"""
Migration 0003 : Crée les permissions du référentiel, crée les 5 rôles
système avec leurs permissions, et migre tous les UserProfile.role_old → role.
"""
from django.db import migrations


PERMISSIONS_REGISTRY = {
    'mouvements': {
        'permissions': [
            ('voir_mouvement',      'Consulter les mouvements'),
            ('ajouter_mouvement',   'Créer un mouvement'),
            ('modifier_mouvement',  'Modifier un mouvement'),
            ('supprimer_mouvement', 'Supprimer un mouvement'),
            ('exporter_mouvement',  'Exporter les mouvements'),
        ],
    },
    'jaugeages': {
        'permissions': [
            ('voir_jaugeage',      'Consulter les jaugeages'),
            ('ajouter_jaugeage',   'Créer un jaugeage'),
            ('modifier_jaugeage',  'Modifier un jaugeage'),
            ('valider_jaugeage',   'Valider un jaugeage'),
            ('supprimer_jaugeage', 'Supprimer un jaugeage'),
        ],
    },
    'periodes': {
        'permissions': [
            ('voir_periode',     'Consulter les périodes'),
            ('ouvrir_periode',   'Ouvrir une nouvelle période'),
            ('cloturer_periode', 'Clôturer une période'),
        ],
    },
    'coulage': {
        'permissions': [
            ('voir_coulage',           'Consulter la répartition du coulage'),
            ('exporter_coulage',       'Exporter les rapports coulage'),
            ('voir_frais_passage',     'Consulter les frais de passage'),
            ('exporter_frais_passage', 'Exporter les frais de passage'),
            ('voir_suivi_evolution',   "Consulter le suivi d'évolution"),
        ],
    },
    'referentiels': {
        'permissions': [
            ('voir_marketeur',     'Consulter les marketeurs'),
            ('ajouter_marketeur',  'Créer un marketeur'),
            ('modifier_marketeur', 'Modifier un marketeur'),
            ('supprimer_marketeur','Supprimer un marketeur'),
            ('voir_cuve',          'Consulter les cuves'),
            ('modifier_cuve',      'Modifier une cuve'),
            ('voir_produit',       'Consulter les produits'),
            ('modifier_produit',   'Modifier un produit'),
            ('voir_camion',        'Consulter les camions'),
            ('modifier_camion',    'Modifier un camion'),
            ('voir_chauffeur',     'Consulter les chauffeurs'),
            ('modifier_chauffeur', 'Modifier un chauffeur'),
        ],
    },
    'administration': {
        'permissions': [
            ('voir_utilisateur',    'Consulter les utilisateurs'),
            ('gerer_utilisateur',   'Créer/modifier/désactiver les utilisateurs'),
            ('gerer_role',          'Gérer les rôles et permissions'),
            ('voir_audit',          "Consulter le journal d'audit"),
            ('modifier_parametres', 'Modifier les paramètres système'),
        ],
    },
}

ROLES_SYSTEME_PERMISSIONS = {
    'SUPERADMIN': '__ALL__',

    'CHEF_DEPOT': [
        'voir_mouvement', 'ajouter_mouvement', 'modifier_mouvement',
        'supprimer_mouvement', 'exporter_mouvement',
        'voir_jaugeage', 'ajouter_jaugeage', 'modifier_jaugeage',
        'valider_jaugeage', 'supprimer_jaugeage',
        'voir_periode', 'ouvrir_periode', 'cloturer_periode',
        'voir_coulage', 'exporter_coulage',
        'voir_frais_passage', 'exporter_frais_passage',
        'voir_suivi_evolution',
        'voir_marketeur', 'ajouter_marketeur', 'modifier_marketeur',
        'voir_cuve', 'modifier_cuve',
        'voir_produit', 'modifier_produit',
        'voir_camion', 'modifier_camion',
        'voir_chauffeur', 'modifier_chauffeur',
        'voir_utilisateur', 'voir_audit',
    ],

    'OPERATEUR': [
        'voir_mouvement', 'ajouter_mouvement', 'modifier_mouvement',
        'voir_jaugeage', 'ajouter_jaugeage', 'modifier_jaugeage',
        'valider_jaugeage',
        'voir_periode',
        'voir_coulage', 'voir_frais_passage', 'voir_suivi_evolution',
        'voir_marketeur', 'voir_cuve', 'voir_produit',
        'voir_camion', 'voir_chauffeur',
    ],

    'COMPTABLE': [
        'voir_mouvement', 'exporter_mouvement',
        'voir_jaugeage',
        'voir_periode',
        'voir_coulage', 'exporter_coulage',
        'voir_frais_passage', 'exporter_frais_passage',
        'voir_suivi_evolution',
        'voir_marketeur', 'voir_cuve', 'voir_produit',
    ],

    'LECTEUR': [
        'voir_mouvement', 'voir_jaugeage', 'voir_periode',
        'voir_coulage', 'voir_frais_passage', 'voir_suivi_evolution',
        'voir_marketeur', 'voir_cuve', 'voir_produit',
        'voir_camion', 'voir_chauffeur',
    ],
}

ROLES_META = {
    'SUPERADMIN': ('Super Administrateur', 'red',
                   'Accès complet à toutes les fonctionnalités'),
    'CHEF_DEPOT': ('Chef de Dépôt', 'blue',
                   'Validation, clôture, gestion opérationnelle'),
    'OPERATEUR':  ('Opérateur de Saisie', 'green',
                   'Saisie quotidienne des mouvements et jaugeages'),
    'COMPTABLE':  ('Comptable', 'yellow',
                   'Consultation et export des rapports financiers'),
    'LECTEUR':    ('Lecteur', 'gray',
                   'Consultation seulement, aucune action possible'),
}


def creer_permissions_et_roles(apps, schema_editor):
    UserProfile = apps.get_model('users', 'UserProfile')
    Role        = apps.get_model('users', 'Role')
    Permission  = apps.get_model('auth', 'Permission')
    ContentType = apps.get_model('contenttypes', 'ContentType')

    ct = ContentType.objects.get_for_model(UserProfile)

    # 1. Créer toutes les permissions du référentiel
    perms_par_code = {}
    for groupe in PERMISSIONS_REGISTRY.values():
        for codename, libelle in groupe['permissions']:
            perm, _ = Permission.objects.get_or_create(
                codename=codename,
                content_type=ct,
                defaults={'name': libelle},
            )
            if perm.name != libelle:
                perm.name = libelle
                perm.save()
            perms_par_code[codename] = perm

    # 2. Créer les 5 rôles système
    roles_crees = {}
    for code, (nom, couleur, description) in ROLES_META.items():
        role, _ = Role.objects.get_or_create(
            code=code,
            defaults={
                'nom': nom,
                'description': description,
                'systeme': True,
                'couleur': couleur,
            },
        )
        if ROLES_SYSTEME_PERMISSIONS[code] == '__ALL__':
            role.permissions.set(list(perms_par_code.values()))
        else:
            perms = [perms_par_code[c]
                     for c in ROLES_SYSTEME_PERMISSIONS[code]
                     if c in perms_par_code]
            role.permissions.set(perms)
        roles_crees[code] = role

    # 3. Migrer UserProfile.role_old → UserProfile.role
    for profil in UserProfile.objects.all():
        ancien_code = profil.role_old or 'LECTEUR'
        nouveau_role = roles_crees.get(ancien_code, roles_crees['LECTEUR'])
        profil.role = nouveau_role
        profil.save()


def reverse_migration(apps, schema_editor):
    UserProfile = apps.get_model('users', 'UserProfile')
    for profil in UserProfile.objects.select_related('role').all():
        if profil.role:
            profil.role_old = profil.role.code
            profil.save()


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_role_model'),
        ('auth', '0012_alter_user_first_name_max_length'),
        ('contenttypes', '0002_remove_content_type_name'),
    ]

    operations = [
        migrations.RunPython(creer_permissions_et_roles, reverse_migration),
    ]
