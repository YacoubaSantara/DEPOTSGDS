from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('SGDS', '0025_compartimentcamion'),
    ]

    operations = [
        # 6 nouveaux champs douaniers pour le type ACQUITTEMENT
        migrations.AddField(
            model_name='mouvement',
            name='acquittement_bureau_douane',
            field=models.CharField(blank=True, max_length=200, null=True, verbose_name='Bureau de douane'),
        ),
        migrations.AddField(
            model_name='mouvement',
            name='acquittement_code_bureau',
            field=models.CharField(blank=True, max_length=50, null=True, verbose_name='Code bureau'),
        ),
        migrations.AddField(
            model_name='mouvement',
            name='acquittement_numero_quittance',
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name='N° quittance'),
        ),
        migrations.AddField(
            model_name='mouvement',
            name='acquittement_date_paiement',
            field=models.DateField(blank=True, null=True, verbose_name='Date paiement'),
        ),
        migrations.AddField(
            model_name='mouvement',
            name='acquittement_commissionnaire',
            field=models.CharField(blank=True, max_length=200, null=True, verbose_name='Commissionnaire en douane'),
        ),
        migrations.AddField(
            model_name='mouvement',
            name='acquittement_agent_dedouaneur',
            field=models.CharField(blank=True, max_length=200, null=True, verbose_name='Agent dédouaneur'),
        ),
        # Mise à jour du help_text du champ acquittement_volume_15c (calculé auto)
        migrations.AlterField(
            model_name='mouvement',
            name='acquittement_volume_15c',
            field=models.DecimalField(
                blank=True, decimal_places=2, max_digits=12, null=True,
                verbose_name='Volume @15°C à acquitter (L)',
                help_text="Calculé automatiquement : Vol. ambiant × Vcf de l'entrée source",
            ),
        ),
    ]
