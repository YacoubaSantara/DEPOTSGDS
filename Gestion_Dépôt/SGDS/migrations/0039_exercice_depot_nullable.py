# Édité à la main : Exercice gagne une FK depot (oubliée en Phase B). Comme
# pour Cuve/JaugeageJour/Mouvement/PeriodeComptable/InventaireInitialMarketeur,
# 3 étapes : (1) champ nullable + retrait de l'unique=True global sur annee,
# (2) backfill PRINCIPAL, (3) champ requis + contrainte unique (depot, annee).

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('SGDS', '0038_depot_fk_required'),
    ]

    operations = [
        migrations.AddField(
            model_name='exercice',
            name='depot',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='exercices', to='SGDS.depot', verbose_name='Dépôt'),
        ),
        migrations.AlterField(
            model_name='exercice',
            name='annee',
            field=models.PositiveIntegerField(verbose_name='Année'),
        ),
        migrations.AlterField(
            model_name='exercice',
            name='slug',
            field=models.SlugField(blank=True, max_length=30, unique=True, verbose_name='Slug URL'),
        ),
    ]
