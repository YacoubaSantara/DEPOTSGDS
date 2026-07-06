from django.db import migrations


def backfill_depot_principal(apps, schema_editor):
    """Rattache les Exercice existants (créés avant le multi-dépôt) au
    dépôt PRINCIPAL créé par la migration 0035."""
    Depot = apps.get_model('SGDS', 'Depot')
    Exercice = apps.get_model('SGDS', 'Exercice')

    principal = Depot.objects.filter(code='PRINCIPAL').first()
    if principal is None:
        return

    Exercice.objects.filter(depot__isnull=True).update(depot=principal)


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('SGDS', '0039_exercice_depot_nullable'),
    ]

    operations = [
        migrations.RunPython(backfill_depot_principal, noop),
    ]
