"""
Commande de gestion Django pour recalculer tous les stocks cuves et produits.

Usage :
    python manage.py recalcul_stocks
    python manage.py recalcul_stocks --produit Super
    python manage.py recalcul_stocks --verbeux
"""
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Recalcule Cuve.niveau_actuel et Produit.stock_actuel pour tous les produits"

    def add_arguments(self, parser):
        parser.add_argument(
            '--produit',
            type=str,
            default=None,
            help="Nom ou code du produit a recalculer (ex: Super). "
                 "Si absent, recalcule TOUS les produits.",
        )
        parser.add_argument(
            '--verbeux',
            action='store_true',
            default=False,
            help="Affiche le detail cuve par cuve.",
        )

    def handle(self, *args, **options):
        from SGDS.models import Cuve, Produit
        from SGDS.services.recalcul_stock import (
            recalculer_stock_cuve,
            recalculer_stock_produit,
        )

        nom_filtre = options.get('produit')
        verbeux    = options.get('verbeux')

        if nom_filtre:
            produits = (
                Produit.objects.filter(nom__icontains=nom_filtre) |
                Produit.objects.filter(code__icontains=nom_filtre)
            ).distinct()
            if not produits.exists():
                self.stderr.write(self.style.ERROR(
                    f"Aucun produit trouve pour '{nom_filtre}'"
                ))
                return
        else:
            produits = Produit.objects.all()

        self.stdout.write(self.style.MIGRATE_HEADING(
            f"\n{'='*60}\n Recalcul stocks -- {produits.count()} produit(s)\n{'='*60}"
        ))

        for produit in produits.order_by('nom'):
            avant = produit.stock_actuel
            cuves = Cuve.objects.filter(produit=produit).select_related('parametre_jaugeage')

            for cuve in cuves:
                niveau_avant = cuve.niveau_actuel
                recalculer_stock_cuve(cuve)
                cuve.refresh_from_db()
                if verbeux:
                    self.stdout.write(
                        f"  Cuve {cuve.numero}: {niveau_avant} -> {cuve.niveau_actuel} L"
                    )

            recalculer_stock_produit(produit)
            produit.refresh_from_db()
            apres = produit.stock_actuel
            delta = apres - avant

            signe = '+' if delta >= 0 else ''
            style = self.style.SUCCESS if delta >= 0 else self.style.WARNING
            self.stdout.write(style(
                f"  >> {produit.nom} ({produit.code}) : "
                f"{avant:,.2f} -> {apres:,.2f} L  ({signe}{delta:,.2f} L)"
            ))

        self.stdout.write(self.style.SUCCESS("\nRecalcul termine avec succes.\n"))
