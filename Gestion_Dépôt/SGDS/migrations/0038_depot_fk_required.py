import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('SGDS', '0037_backfill_depot_principal'),
    ]

    operations = [
        migrations.AlterField(
            model_name='cuve',
            name='depot',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='cuves', to='SGDS.depot', verbose_name='Dépôt'),
        ),
        migrations.AlterField(
            model_name='jaugeagejour',
            name='depot',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='jaugeages', to='SGDS.depot', verbose_name='Dépôt'),
        ),
        migrations.AlterField(
            model_name='mouvement',
            name='depot',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='mouvements', to='SGDS.depot', verbose_name='Dépôt'),
        ),
        migrations.AlterField(
            model_name='periodecomptable',
            name='depot',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='periodes_comptables', to='SGDS.depot', verbose_name='Dépôt'),
        ),
        migrations.AlterField(
            model_name='inventaireinitialmarketeur',
            name='depot',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='inventaires_initiaux', to='SGDS.depot', verbose_name='Dépôt'),
        ),
    ]
