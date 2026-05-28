# Migration générée manuellement — 2026-05-18
# Ajoute les nouveaux champs aux mouvements : ENTREE (horaires),
# SORTIE (horaires, documents, densité observée), CESSION (autorisation,
# contrat, cuve, API MPMS).

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('SGDS', '0023_documents_justificatifs_et_notification_lien'),
    ]

    operations = [

        # ── Champs horaires ENTRÉE ─────────────────────────────
        migrations.AddField(
            model_name='mouvement',
            name='heure_arrivee',
            field=models.TimeField(blank=True, null=True, verbose_name="Heure d'arrivée"),
        ),
        migrations.AddField(
            model_name='mouvement',
            name='heure_depotage',
            field=models.TimeField(blank=True, null=True, verbose_name='Heure de dépotage'),
        ),
        migrations.AddField(
            model_name='mouvement',
            name='heure_fin',
            field=models.TimeField(blank=True, null=True, verbose_name='Heure de fin'),
        ),

        # ── Champs opérationnels SORTIE ───────────────────────
        # (les horaires heure_arrivee / heure_depotage / heure_fin
        #  sont partagés avec ENTREE — déjà ajoutés ci-dessus)
        migrations.AddField(
            model_name='mouvement',
            name='compartiments_charges',
            field=models.CharField(blank=True, max_length=300, null=True, verbose_name='Compartiments chargés'),
        ),
        migrations.AddField(
            model_name='mouvement',
            name='numero_autorisation_marketeur',
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name='N° autorisation Marketeur'),
        ),
        migrations.AddField(
            model_name='mouvement',
            name='numero_bon_enlevement',
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name="N° bon d'enlèvement"),
        ),
        migrations.AddField(
            model_name='mouvement',
            name='densite_observee_sortie',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=7, null=True, verbose_name='Densité observée sortie (kg/m³)'),
        ),

        # ── Champs complémentaires CESSION ────────────────────
        migrations.AddField(
            model_name='mouvement',
            name='cession_numero_autorisation_direction',
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name='N° autorisation Direction'),
        ),
        migrations.AddField(
            model_name='mouvement',
            name='cession_date_autorisation',
            field=models.DateField(blank=True, null=True, verbose_name='Date autorisation'),
        ),
        migrations.AddField(
            model_name='mouvement',
            name='cession_reference_contrat',
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name='Référence contrat'),
        ),
        migrations.AddField(
            model_name='mouvement',
            name='cession_periode_imputation',
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name="Période d'imputation"),
        ),
        migrations.AddField(
            model_name='mouvement',
            name='cession_visa_direction',
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name='Visa direction'),
        ),
        migrations.AddField(
            model_name='mouvement',
            name='cession_cuve',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='cessions',
                to='SGDS.cuve',
                verbose_name='Cuve (cession)',
            ),
        ),

        # ── Données labo CESSION pour API MPMS ────────────────
        migrations.AddField(
            model_name='mouvement',
            name='cession_densite_observee',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=7, null=True, verbose_name='Densité observée cession (kg/m³)'),
        ),
        migrations.AddField(
            model_name='mouvement',
            name='cession_temperature',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True, verbose_name='Température cession (°C)'),
        ),

        # ── Champs calculés auto CESSION ──────────────────────
        migrations.AddField(
            model_name='mouvement',
            name='cession_densite_15c',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=7, null=True, verbose_name='Densité @15°C cession (kg/m³)'),
        ),
        migrations.AddField(
            model_name='mouvement',
            name='cession_coefficient_vcf',
            field=models.DecimalField(blank=True, decimal_places=4, max_digits=8, null=True, verbose_name='Coefficient Vcf cession'),
        ),
    ]
