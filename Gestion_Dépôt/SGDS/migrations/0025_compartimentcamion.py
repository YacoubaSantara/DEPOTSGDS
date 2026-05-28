# Migration générée manuellement — 2026-05-18
# Crée le modèle CompartimentCamion pour stocker la capacité
# individuelle de chaque compartiment d'un camion citerne.

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('SGDS', '0024_ajout_champs_entree_sortie_cession'),
    ]

    operations = [
        migrations.CreateModel(
            name='CompartimentCamion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('numero', models.PositiveSmallIntegerField(verbose_name='N° compartiment')),
                ('capacite', models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Capacité (litres)')),
                ('camion', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='compartiments',
                    to='SGDS.camion',
                    verbose_name='Camion',
                )),
            ],
            options={
                'verbose_name': 'Compartiment',
                'verbose_name_plural': 'Compartiments',
                'ordering': ['camion', 'numero'],
                'unique_together': {('camion', 'numero')},
            },
        ),
    ]
