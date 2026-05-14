"""
Migration : ajout du champ entree_source sur Mouvement.

Ce champ FK (self, nullable) lie un mouvement d'ACQUITTEMENT au mouvement
d'ENTREE SOUS_DOUANE dont il est l'acquittement douanier.
Cela permet de :
  1. Tracer l'origine douanière de chaque acquittement.
  2. Sélectionner l'entrée via son N° BL Dépôt Chargeur dans l'interface.
"""
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('SGDS', '0020_recalcul_stocks_initiaux'),
    ]

    operations = [
        migrations.AddField(
            model_name='mouvement',
            name='entree_source',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='acquittements',
                to='SGDS.mouvement',
                verbose_name='Entrée source (Sous douane)',
                help_text=(
                    "Mouvement d'ENTREE SOUS_DOUANE dont ce mouvement est "
                    "l'acquittement douanier. "
                    "Sélectionner via le N° BL Dépôt Chargeur de l'entrée correspondante."
                ),
                limit_choices_to={
                    'type_mouvement': 'ENTREE',
                    'regime_douanier': 'SOUS_DOUANE',
                },
            ),
        ),
    ]
