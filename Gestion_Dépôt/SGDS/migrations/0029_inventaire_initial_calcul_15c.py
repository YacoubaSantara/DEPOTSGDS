"""
Migration 0029 — InventaireInitialMarketeur : autoriser les volumes négatifs
(soldes débiteurs marketeurs — suppression de MinValueValidator(0)).
"""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('SGDS', '0028_populate_slugs'),
    ]

    operations = [
        migrations.AlterField(
            model_name='inventaireinitialmarketeur',
            name='volume_15c',
            field=models.DecimalField(
                default=0, max_digits=14, decimal_places=2,
                verbose_name='Volume @15°C (L)',
                help_text='Peut être négatif (solde débiteur du marketeur)',
            ),
        ),
        migrations.AlterField(
            model_name='inventaireinitialmarketeur',
            name='volume_ambiant',
            field=models.DecimalField(
                default=0, max_digits=14, decimal_places=2,
                verbose_name='Volume ambiant (L)',
                help_text='Peut être négatif (solde débiteur du marketeur)',
            ),
        ),
    ]
