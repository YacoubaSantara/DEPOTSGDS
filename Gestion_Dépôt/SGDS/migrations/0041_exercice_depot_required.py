import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('SGDS', '0040_backfill_exercice_depot_principal'),
    ]

    operations = [
        migrations.AlterField(
            model_name='exercice',
            name='depot',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='exercices', to='SGDS.depot', verbose_name='Dépôt'),
        ),
        migrations.AddConstraint(
            model_name='exercice',
            constraint=models.UniqueConstraint(fields=('depot', 'annee'), name='unique_exercice_depot_annee'),
        ),
    ]
