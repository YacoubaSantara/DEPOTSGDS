# Migration manuelle : refactoring coulage par produit
# Supprime les champs _go/_super hardcodés, ajoute ClotureCoulageProduit
# et genericise ClotureCoulageLigne avec une FK produit.

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('SGDS', '0012_add_date_ouverture_periode'),
    ]

    operations = [
        # 1. Supprimer les anciens champs hardcodés de ClotureCoulageMensuel
        migrations.RemoveField(model_name='cloturecoulagemensuel', name='coefficient_go'),
        migrations.RemoveField(model_name='cloturecoulagemensuel', name='coefficient_super'),
        migrations.RemoveField(model_name='cloturecoulagemensuel', name='pertes_gains_go'),
        migrations.RemoveField(model_name='cloturecoulagemensuel', name='pertes_gains_super'),
        migrations.RemoveField(model_name='cloturecoulagemensuel', name='cumul_entree_go'),
        migrations.RemoveField(model_name='cloturecoulagemensuel', name='cumul_entree_super'),
        migrations.RemoveField(model_name='cloturecoulagemensuel', name='cumul_sortie_go'),
        migrations.RemoveField(model_name='cloturecoulagemensuel', name='cumul_sortie_super'),

        # 2. Créer le nouveau modèle ClotureCoulageProduit
        migrations.CreateModel(
            name='ClotureCoulageProduit',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('coefficient', models.DecimalField(decimal_places=8, default=0, max_digits=14)),
                ('pertes_gains', models.DecimalField(decimal_places=2, default=0, max_digits=14)),
                ('cumul_entree', models.DecimalField(decimal_places=2, default=0, max_digits=14)),
                ('cumul_sortie', models.DecimalField(decimal_places=2, default=0, max_digits=14)),
                ('cloture', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='produits_coulage',
                    to='SGDS.cloturecoulagemensuel',
                    verbose_name='Clôture',
                )),
                ('produit', models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    to='SGDS.produit',
                    verbose_name='Produit',
                )),
            ],
            options={
                'verbose_name': 'Coulage par produit',
                'verbose_name_plural': 'Coulage par produit',
            },
        ),
        migrations.AddConstraint(
            model_name='cloturecoulageproduit',
            constraint=models.UniqueConstraint(
                fields=('cloture', 'produit'), name='unique_cloture_produit'
            ),
        ),

        # 3. Supprimer l'ancienne contrainte unique sur ClotureCoulageLigne
        migrations.RemoveConstraint(
            model_name='cloturecoulageligne',
            name='unique_cloture_ligne_marketeur',
        ),

        # 4. Supprimer les anciens champs _go/_super de ClotureCoulageLigne
        migrations.RemoveField(model_name='cloturecoulageligne', name='brut_entree_go'),
        migrations.RemoveField(model_name='cloturecoulageligne', name='coul_entree_go'),
        migrations.RemoveField(model_name='cloturecoulageligne', name='entree_nette_go'),
        migrations.RemoveField(model_name='cloturecoulageligne', name='sortie_go'),
        migrations.RemoveField(model_name='cloturecoulageligne', name='base_qp_coul_go'),
        migrations.RemoveField(model_name='cloturecoulageligne', name='coef_qp_coul_go'),
        migrations.RemoveField(model_name='cloturecoulageligne', name='qp_coul_go'),
        migrations.RemoveField(model_name='cloturecoulageligne', name='brut_entree_super'),
        migrations.RemoveField(model_name='cloturecoulageligne', name='coul_entree_super'),
        migrations.RemoveField(model_name='cloturecoulageligne', name='entree_nette_super'),
        migrations.RemoveField(model_name='cloturecoulageligne', name='sortie_super'),
        migrations.RemoveField(model_name='cloturecoulageligne', name='base_qp_coul_super'),
        migrations.RemoveField(model_name='cloturecoulageligne', name='coef_qp_coul_super'),
        migrations.RemoveField(model_name='cloturecoulageligne', name='qp_coul_super'),
        migrations.RemoveField(model_name='cloturecoulageligne', name='volume_global_sorti'),

        # 5. Ajouter les nouveaux champs génériques sur ClotureCoulageLigne
        migrations.AddField(
            model_name='cloturecoulageligne',
            name='brut_entree',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=14),
        ),
        migrations.AddField(
            model_name='cloturecoulageligne',
            name='coul_entree',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=14),
        ),
        migrations.AddField(
            model_name='cloturecoulageligne',
            name='entree_nette',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=14),
        ),
        migrations.AddField(
            model_name='cloturecoulageligne',
            name='sortie',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=14),
        ),
        migrations.AddField(
            model_name='cloturecoulageligne',
            name='base_qp_coul',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=14),
        ),
        migrations.AddField(
            model_name='cloturecoulageligne',
            name='coef_qp_coul',
            field=models.DecimalField(decimal_places=8, default=0, max_digits=14),
        ),
        migrations.AddField(
            model_name='cloturecoulageligne',
            name='qp_coul',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=14),
        ),
        migrations.AddField(
            model_name='cloturecoulageligne',
            name='volume_sorti',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=14),
        ),
        # 6. Ajouter la FK produit (nullable pour permettre la migration)
        migrations.AddField(
            model_name='cloturecoulageligne',
            name='produit',
            field=models.ForeignKey(
                null=True,
                blank=True,
                on_delete=django.db.models.deletion.PROTECT,
                to='SGDS.produit',
                verbose_name='Produit',
            ),
        ),

        # 7. Ajouter la nouvelle contrainte unique sur ClotureCoulageLigne
        migrations.AddConstraint(
            model_name='cloturecoulageligne',
            constraint=models.UniqueConstraint(
                fields=('cloture', 'marketeur', 'produit'),
                name='unique_cloture_ligne_marketeur_produit',
            ),
        ),
    ]
