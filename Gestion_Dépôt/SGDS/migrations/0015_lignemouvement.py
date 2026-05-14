from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('SGDS', '0014_produit_prix_passage'),
    ]

    operations = [
        migrations.CreateModel(
            name='LigneMouvement',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('volume_ambiant', models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True, verbose_name='Volume ambiant (L)')),
                ('volume_15c', models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True, verbose_name='Volume @15°C (L)')),
                ('ordre', models.PositiveSmallIntegerField(default=1, verbose_name='Ordre')),
                ('cuve', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='lignes_mouvement', to='SGDS.cuve', verbose_name='Cuve')),
                ('mouvement', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='lignes', to='SGDS.mouvement', verbose_name='Mouvement')),
                ('produit', models.ForeignKey(help_text='Dénormalisé depuis mouvement.produit pour faciliter les agrégats par produit/cuve.', on_delete=django.db.models.deletion.PROTECT, to='SGDS.produit', verbose_name='Produit')),
            ],
            options={
                'verbose_name': 'Ligne mouvement',
                'verbose_name_plural': 'Lignes mouvement',
                'ordering': ['ordre'],
            },
        ),
    ]
