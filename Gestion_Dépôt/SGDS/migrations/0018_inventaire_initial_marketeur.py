from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('SGDS', '0017_societe'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='InventaireInitialMarketeur',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('regime_douanier', models.CharField(
                    choices=[('SOUS_DOUANE', 'Sous douane'), ('ACQUITTE', 'Acquitté')],
                    max_length=15,
                    verbose_name='Régime douanier',
                )),
                ('volume_15c', models.DecimalField(
                    decimal_places=2,
                    default=0,
                    max_digits=14,
                    validators=[MinValueValidator(0)],
                    verbose_name='Volume @15°C (L)',
                )),
                ('volume_ambiant', models.DecimalField(
                    decimal_places=2,
                    default=0,
                    max_digits=14,
                    validators=[MinValueValidator(0)],
                    verbose_name='Volume ambiant (L)',
                )),
                ('date_inventaire', models.DateField(
                    help_text='Date de référence du stock initial (avant tout mouvement)',
                    verbose_name="Date d'inventaire",
                )),
                ('notes', models.TextField(blank=True, verbose_name='Notes / observations')),
                ('date_creation', models.DateTimeField(auto_now_add=True)),
                ('date_modification', models.DateTimeField(auto_now=True)),
                ('marketeur', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='inventaires_initiaux',
                    to='SGDS.marketeur',
                    verbose_name='Marketeur',
                )),
                ('produit', models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name='inventaires_initiaux',
                    to='SGDS.produit',
                    verbose_name='Produit',
                )),
                ('saisi_par', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='inventaires_initiaux_saisis',
                    to=settings.AUTH_USER_MODEL,
                    verbose_name='Saisi par',
                )),
            ],
            options={
                'verbose_name': 'Inventaire initial marketeur',
                'verbose_name_plural': 'Inventaires initiaux marketeurs',
                'ordering': ['marketeur__raison_sociale', 'produit__nom', 'regime_douanier'],
            },
        ),
        migrations.AddConstraint(
            model_name='inventaireinitialmarketeur',
            constraint=models.UniqueConstraint(
                fields=['marketeur', 'produit', 'regime_douanier'],
                name='unique_inventaire_initial_mktr_prod_regime',
            ),
        ),
    ]
