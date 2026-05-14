"""
Migration de données : recalcule Produit.stock_actuel pour tous les produits
en tenant compte des InventaireInitialMarketeur déjà saisis.
Nécessaire pour que les stocks initiaux saisis AVANT l'installation du signal
soient correctement reflétés dans stock_actuel.
"""
from django.db import migrations
from django.db.models import Sum
from decimal import Decimal
from django.utils import timezone


def recalculer_stocks_produits(apps, schema_editor):
    Produit = apps.get_model('SGDS', 'Produit')
    Cuve    = apps.get_model('SGDS', 'Cuve')
    InventaireInitialMarketeur = apps.get_model('SGDS', 'InventaireInitialMarketeur')

    now = timezone.now()

    for produit in Produit.objects.all():
        # 1. Stock des cuves (jaugeages physiques)
        total_cuves = (
            Cuve.objects
            .filter(produit=produit)
            .aggregate(s=Sum('niveau_actuel'))['s']
        ) or Decimal('0')

        if Decimal(str(total_cuves)) == Decimal('0'):
            # 2. Pas de jaugeage → utiliser la somme des inventaires initiaux
            #    (SD + AC, toutes cuves confondues)
            total_inv = (
                InventaireInitialMarketeur.objects
                .filter(produit=produit)
                .aggregate(s=Sum('volume_ambiant'))['s']
            ) or Decimal('0')
            stock = Decimal(str(total_inv))
        else:
            stock = Decimal(str(total_cuves))

        if stock != Decimal('0'):
            Produit.objects.filter(pk=produit.pk).update(
                stock_actuel=stock,
                date_maj_stock=now,
            )


class Migration(migrations.Migration):

    dependencies = [
        ('SGDS', '0019_inventaire_cuves'),
    ]

    operations = [
        migrations.RunPython(
            recalculer_stocks_produits,
            migrations.RunPython.noop,
        ),
    ]
