"""
Migration 0028 — Population des slugs sur les enregistrements existants.

Pour chaque modèle qui a un SlugField, on génère le slug depuis le champ
naturel (raison_sociale, immatriculation, etc.) en reproduisant la même
logique que le save() du modèle.

Cette migration est une data-migration : elle modifie les données, pas le schéma.
"""

from django.db import migrations
from django.utils.text import slugify


def _slug_unique_mig(apps, model_class, base_slug, exclude_pk=None, max_length=200):
    """Version autonome de _slug_unique pour les migrations (pas d'import du modèle réel)."""
    slug = base_slug[:max_length]
    qs = model_class.objects.filter(slug=slug)
    if exclude_pk:
        qs = qs.exclude(pk=exclude_pk)
    if not qs.exists():
        return slug
    counter = 2
    while True:
        suffix = f"-{counter}"
        candidate = base_slug[: max_length - len(suffix)] + suffix
        qs2 = model_class.objects.filter(slug=candidate)
        if exclude_pk:
            qs2 = qs2.exclude(pk=exclude_pk)
        if not qs2.exists():
            return candidate
        counter += 1


def populate_marketeur_slugs(apps, schema_editor):
    Marketeur = apps.get_model('SGDS', 'Marketeur')
    for obj in Marketeur.objects.filter(slug=''):
        obj.slug = _slug_unique_mig(apps, Marketeur, slugify(obj.raison_sociale), exclude_pk=obj.pk)
        obj.save(update_fields=['slug'])


def populate_camion_slugs(apps, schema_editor):
    Camion = apps.get_model('SGDS', 'Camion')
    for obj in Camion.objects.filter(slug=''):
        obj.slug = _slug_unique_mig(apps, Camion, slugify(obj.immatriculation), exclude_pk=obj.pk)
        obj.save(update_fields=['slug'])


def populate_chauffeur_slugs(apps, schema_editor):
    Chauffeur = apps.get_model('SGDS', 'Chauffeur')
    for obj in Chauffeur.objects.filter(slug=''):
        base = slugify(f"{obj.nom}-{obj.prenom}")
        obj.slug = _slug_unique_mig(apps, Chauffeur, base, exclude_pk=obj.pk)
        obj.save(update_fields=['slug'])


def populate_famille_slugs(apps, schema_editor):
    Famille = apps.get_model('SGDS', 'Famille')
    for obj in Famille.objects.filter(slug=''):
        obj.slug = _slug_unique_mig(apps, Famille, slugify(obj.nom), exclude_pk=obj.pk)
        obj.save(update_fields=['slug'])


def populate_produit_slugs(apps, schema_editor):
    Produit = apps.get_model('SGDS', 'Produit')
    for obj in Produit.objects.filter(slug=''):
        obj.slug = _slug_unique_mig(apps, Produit, slugify(obj.code), exclude_pk=obj.pk)
        obj.save(update_fields=['slug'])


def populate_cuve_slugs(apps, schema_editor):
    Cuve = apps.get_model('SGDS', 'Cuve')
    for obj in Cuve.objects.filter(slug=''):
        obj.slug = _slug_unique_mig(apps, Cuve, slugify(obj.numero), exclude_pk=obj.pk)
        obj.save(update_fields=['slug'])


def populate_parametre_slugs(apps, schema_editor):
    ParametreJaugeageCuve = apps.get_model('SGDS', 'ParametreJaugeageCuve')
    for obj in ParametreJaugeageCuve.objects.select_related('cuve').filter(slug=''):
        base = slugify(f"params-{obj.cuve.numero}")
        obj.slug = _slug_unique_mig(apps, ParametreJaugeageCuve, base, exclude_pk=obj.pk)
        obj.save(update_fields=['slug'])


def populate_jaugeage_slugs(apps, schema_editor):
    JaugeageJour = apps.get_model('SGDS', 'JaugeageJour')
    for obj in JaugeageJour.objects.filter(slug=''):
        heure_str = obj.heure_jaugeage.strftime('%H%M') if obj.heure_jaugeage else ''
        base = slugify(f"{obj.date_jaugeage}-{obj.type_jaugeage}-{heure_str}")
        obj.slug = _slug_unique_mig(apps, JaugeageJour, base, exclude_pk=obj.pk)
        obj.save(update_fields=['slug'])


def populate_mouvement_slugs(apps, schema_editor):
    Mouvement = apps.get_model('SGDS', 'Mouvement')
    for obj in Mouvement.objects.filter(slug=''):
        if obj.numero_enregistrement:
            base = slugify(obj.numero_enregistrement)
        else:
            base = slugify(f"mvt-{obj.pk}")
        obj.slug = _slug_unique_mig(apps, Mouvement, base, exclude_pk=obj.pk)
        obj.save(update_fields=['slug'])


def populate_periode_slugs(apps, schema_editor):
    PeriodeComptable = apps.get_model('SGDS', 'PeriodeComptable')
    for obj in PeriodeComptable.objects.filter(slug=''):
        obj.slug = f"{obj.annee}-{obj.mois:02d}"
        obj.save(update_fields=['slug'])


class Migration(migrations.Migration):

    dependencies = [
        ('SGDS', '0027_add_uuid_slug'),
    ]

    operations = [
        migrations.RunPython(populate_marketeur_slugs,  migrations.RunPython.noop),
        migrations.RunPython(populate_camion_slugs,     migrations.RunPython.noop),
        migrations.RunPython(populate_chauffeur_slugs,  migrations.RunPython.noop),
        migrations.RunPython(populate_famille_slugs,    migrations.RunPython.noop),
        migrations.RunPython(populate_produit_slugs,    migrations.RunPython.noop),
        migrations.RunPython(populate_cuve_slugs,       migrations.RunPython.noop),
        migrations.RunPython(populate_parametre_slugs,  migrations.RunPython.noop),
        migrations.RunPython(populate_jaugeage_slugs,   migrations.RunPython.noop),
        migrations.RunPython(populate_mouvement_slugs,  migrations.RunPython.noop),
        migrations.RunPython(populate_periode_slugs,    migrations.RunPython.noop),
    ]
