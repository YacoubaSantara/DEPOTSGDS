from django.db import migrations


def backfill_depot_principal(apps, schema_editor):
    """Rattache toutes les lignes existantes (créées avant le multi-dépôt)
    au dépôt PRINCIPAL créé par la migration 0035."""
    Depot = apps.get_model('SGDS', 'Depot')
    Cuve = apps.get_model('SGDS', 'Cuve')
    JaugeageJour = apps.get_model('SGDS', 'JaugeageJour')
    Mouvement = apps.get_model('SGDS', 'Mouvement')
    PeriodeComptable = apps.get_model('SGDS', 'PeriodeComptable')
    InventaireInitialMarketeur = apps.get_model('SGDS', 'InventaireInitialMarketeur')

    principal = Depot.objects.filter(code='PRINCIPAL').first()
    if principal is None:
        return

    Cuve.objects.filter(depot__isnull=True).update(depot=principal)
    JaugeageJour.objects.filter(depot__isnull=True).update(depot=principal)
    Mouvement.objects.filter(depot__isnull=True).update(depot=principal)
    PeriodeComptable.objects.filter(depot__isnull=True).update(depot=principal)
    InventaireInitialMarketeur.objects.filter(depot__isnull=True).update(depot=principal)


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('SGDS', '0036_depot_fk_nullable_metier'),
    ]

    operations = [
        migrations.RunPython(backfill_depot_principal, noop),
    ]
