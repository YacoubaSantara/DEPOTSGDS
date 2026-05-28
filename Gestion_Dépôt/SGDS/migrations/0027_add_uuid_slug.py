"""
Migration 0027 — Ajout des champs uuid et slug sur tous les modèles principaux.

Stratégie en 3 étapes pour éviter la violation d'unicité sur les lignes existantes :
  1. AddField : uuid nullable, sans contrainte unique, sans default PostgreSQL
  2. RunPython : générer un UUID unique pour chaque ligne existante
  3. AlterField : rendre le champ NOT NULL + UNIQUE

Modèles avec uuid + slug :
  Marketeur, Camion, Chauffeur, Famille, Produit, Cuve,
  ParametreJaugeageCuve, JaugeageJour, Mouvement, PeriodeComptable

Modèles avec uuid seulement :
  MouvementDocument, Notification, InventaireInitialMarketeur
"""

import uuid as uuid_module

from django.db import migrations, models


# ── Helpers ──────────────────────────────────────────────────────────────────

def _fill_uuids(model_name):
    """Retourne une fonction RunPython qui remplit uuid sur toutes les lignes."""
    def _runner(apps, schema_editor):
        Model = apps.get_model('SGDS', model_name)
        for obj in Model.objects.filter(uuid__isnull=True):
            obj.uuid = uuid_module.uuid4()
            obj.save(update_fields=['uuid'])
    _runner.__name__ = f'fill_uuids_{model_name.lower()}'
    return _runner


# ── Modèles concernés ────────────────────────────────────────────────────────

MODELS_UUID_SLUG = [
    'Marketeur',
    'Camion',
    'Chauffeur',
    'Famille',
    'Produit',
    'Cuve',
    'ParametreJaugeageCuve',
    'JaugeageJour',
    'Mouvement',
    'PeriodeComptable',
]

MODELS_UUID_ONLY = [
    'MouvementDocument',
    'Notification',
    'InventaireInitialMarketeur',
]

ALL_MODELS = MODELS_UUID_SLUG + MODELS_UUID_ONLY


class Migration(migrations.Migration):

    dependencies = [
        ('SGDS', '0026_acquittement_champs_douane'),
    ]

    operations = [

        # ── ÉTAPE 1 : Ajouter uuid nullable (sans unique) sur tous les modèles ──
        # Marketeur
        migrations.AddField(
            model_name='marketeur',
            name='uuid',
            field=models.UUIDField(null=True, blank=True, editable=False, verbose_name='UUID'),
        ),
        migrations.AddField(
            model_name='marketeur',
            name='slug',
            field=models.SlugField(blank=True, max_length=200, verbose_name='Slug URL'),
        ),

        # Camion
        migrations.AddField(
            model_name='camion',
            name='uuid',
            field=models.UUIDField(null=True, blank=True, editable=False, verbose_name='UUID'),
        ),
        migrations.AddField(
            model_name='camion',
            name='slug',
            field=models.SlugField(blank=True, max_length=200, verbose_name='Slug URL'),
        ),

        # Chauffeur
        migrations.AddField(
            model_name='chauffeur',
            name='uuid',
            field=models.UUIDField(null=True, blank=True, editable=False, verbose_name='UUID'),
        ),
        migrations.AddField(
            model_name='chauffeur',
            name='slug',
            field=models.SlugField(blank=True, max_length=200, verbose_name='Slug URL'),
        ),

        # Famille
        migrations.AddField(
            model_name='famille',
            name='uuid',
            field=models.UUIDField(null=True, blank=True, editable=False, verbose_name='UUID'),
        ),
        migrations.AddField(
            model_name='famille',
            name='slug',
            field=models.SlugField(blank=True, max_length=200, verbose_name='Slug URL'),
        ),

        # Produit
        migrations.AddField(
            model_name='produit',
            name='uuid',
            field=models.UUIDField(null=True, blank=True, editable=False, verbose_name='UUID'),
        ),
        migrations.AddField(
            model_name='produit',
            name='slug',
            field=models.SlugField(blank=True, max_length=200, verbose_name='Slug URL'),
        ),

        # Cuve
        migrations.AddField(
            model_name='cuve',
            name='uuid',
            field=models.UUIDField(null=True, blank=True, editable=False, verbose_name='UUID'),
        ),
        migrations.AddField(
            model_name='cuve',
            name='slug',
            field=models.SlugField(blank=True, max_length=200, verbose_name='Slug URL'),
        ),

        # ParametreJaugeageCuve
        migrations.AddField(
            model_name='parametrejaugeagecuve',
            name='uuid',
            field=models.UUIDField(null=True, blank=True, editable=False, verbose_name='UUID'),
        ),
        migrations.AddField(
            model_name='parametrejaugeagecuve',
            name='slug',
            field=models.SlugField(blank=True, max_length=200, verbose_name='Slug URL'),
        ),

        # JaugeageJour
        migrations.AddField(
            model_name='jaugeagejour',
            name='uuid',
            field=models.UUIDField(null=True, blank=True, editable=False, verbose_name='UUID'),
        ),
        migrations.AddField(
            model_name='jaugeagejour',
            name='slug',
            field=models.SlugField(blank=True, max_length=200, verbose_name='Slug URL'),
        ),

        # Mouvement
        migrations.AddField(
            model_name='mouvement',
            name='uuid',
            field=models.UUIDField(null=True, blank=True, editable=False, verbose_name='UUID'),
        ),
        migrations.AddField(
            model_name='mouvement',
            name='slug',
            field=models.SlugField(blank=True, max_length=200, verbose_name='Slug URL'),
        ),

        # MouvementDocument (uuid seulement)
        migrations.AddField(
            model_name='mouvementdocument',
            name='uuid',
            field=models.UUIDField(null=True, blank=True, editable=False, verbose_name='UUID'),
        ),

        # Notification (uuid seulement)
        migrations.AddField(
            model_name='notification',
            name='uuid',
            field=models.UUIDField(null=True, blank=True, editable=False, verbose_name='UUID'),
        ),

        # PeriodeComptable
        migrations.AddField(
            model_name='periodecomptable',
            name='uuid',
            field=models.UUIDField(null=True, blank=True, editable=False, verbose_name='UUID'),
        ),
        migrations.AddField(
            model_name='periodecomptable',
            name='slug',
            field=models.SlugField(blank=True, max_length=20, verbose_name='Slug URL'),
        ),

        # InventaireInitialMarketeur (uuid seulement)
        migrations.AddField(
            model_name='inventaireinitialmarketeur',
            name='uuid',
            field=models.UUIDField(null=True, blank=True, editable=False, verbose_name='UUID'),
        ),

        # ── ÉTAPE 2 : Remplir uuid sur chaque ligne existante ────────────────────
        migrations.RunPython(_fill_uuids('Marketeur'),               migrations.RunPython.noop),
        migrations.RunPython(_fill_uuids('Camion'),                  migrations.RunPython.noop),
        migrations.RunPython(_fill_uuids('Chauffeur'),               migrations.RunPython.noop),
        migrations.RunPython(_fill_uuids('Famille'),                 migrations.RunPython.noop),
        migrations.RunPython(_fill_uuids('Produit'),                 migrations.RunPython.noop),
        migrations.RunPython(_fill_uuids('Cuve'),                    migrations.RunPython.noop),
        migrations.RunPython(_fill_uuids('ParametreJaugeageCuve'),   migrations.RunPython.noop),
        migrations.RunPython(_fill_uuids('JaugeageJour'),            migrations.RunPython.noop),
        migrations.RunPython(_fill_uuids('Mouvement'),               migrations.RunPython.noop),
        migrations.RunPython(_fill_uuids('MouvementDocument'),       migrations.RunPython.noop),
        migrations.RunPython(_fill_uuids('Notification'),            migrations.RunPython.noop),
        migrations.RunPython(_fill_uuids('PeriodeComptable'),        migrations.RunPython.noop),
        migrations.RunPython(_fill_uuids('InventaireInitialMarketeur'), migrations.RunPython.noop),

        # ── ÉTAPE 3 : Ajouter NOT NULL + UNIQUE sur uuid ─────────────────────────
        migrations.AlterField(
            model_name='marketeur',
            name='uuid',
            field=models.UUIDField(default=uuid_module.uuid4, editable=False, unique=True, verbose_name='UUID'),
        ),
        migrations.AlterField(
            model_name='camion',
            name='uuid',
            field=models.UUIDField(default=uuid_module.uuid4, editable=False, unique=True, verbose_name='UUID'),
        ),
        migrations.AlterField(
            model_name='chauffeur',
            name='uuid',
            field=models.UUIDField(default=uuid_module.uuid4, editable=False, unique=True, verbose_name='UUID'),
        ),
        migrations.AlterField(
            model_name='famille',
            name='uuid',
            field=models.UUIDField(default=uuid_module.uuid4, editable=False, unique=True, verbose_name='UUID'),
        ),
        migrations.AlterField(
            model_name='produit',
            name='uuid',
            field=models.UUIDField(default=uuid_module.uuid4, editable=False, unique=True, verbose_name='UUID'),
        ),
        migrations.AlterField(
            model_name='cuve',
            name='uuid',
            field=models.UUIDField(default=uuid_module.uuid4, editable=False, unique=True, verbose_name='UUID'),
        ),
        migrations.AlterField(
            model_name='parametrejaugeagecuve',
            name='uuid',
            field=models.UUIDField(default=uuid_module.uuid4, editable=False, unique=True, verbose_name='UUID'),
        ),
        migrations.AlterField(
            model_name='jaugeagejour',
            name='uuid',
            field=models.UUIDField(default=uuid_module.uuid4, editable=False, unique=True, verbose_name='UUID'),
        ),
        migrations.AlterField(
            model_name='mouvement',
            name='uuid',
            field=models.UUIDField(default=uuid_module.uuid4, editable=False, unique=True, verbose_name='UUID'),
        ),
        migrations.AlterField(
            model_name='mouvementdocument',
            name='uuid',
            field=models.UUIDField(default=uuid_module.uuid4, editable=False, unique=True, verbose_name='UUID'),
        ),
        migrations.AlterField(
            model_name='notification',
            name='uuid',
            field=models.UUIDField(default=uuid_module.uuid4, editable=False, unique=True, verbose_name='UUID'),
        ),
        migrations.AlterField(
            model_name='periodecomptable',
            name='uuid',
            field=models.UUIDField(default=uuid_module.uuid4, editable=False, unique=True, verbose_name='UUID'),
        ),
        migrations.AlterField(
            model_name='inventaireinitialmarketeur',
            name='uuid',
            field=models.UUIDField(default=uuid_module.uuid4, editable=False, unique=True, verbose_name='UUID'),
        ),
    ]
