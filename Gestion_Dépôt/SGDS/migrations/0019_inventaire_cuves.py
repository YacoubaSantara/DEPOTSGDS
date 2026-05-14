from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('SGDS', '0018_inventaire_initial_marketeur'),
    ]

    operations = [
        migrations.AddField(
            model_name='inventaireinitialmarketeur',
            name='cuves',
            field=models.ManyToManyField(
                blank=True,
                help_text='Cuves dans lesquelles ce stock est physiquement déposé (optionnel)',
                related_name='inventaires_initiaux',
                to='SGDS.cuve',
                verbose_name='Cuves associées',
            ),
        ),
    ]
