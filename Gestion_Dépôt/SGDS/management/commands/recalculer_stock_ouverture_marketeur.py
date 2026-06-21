"""
Commande de rattrapage : résout et persiste le stock d'ouverture par
marketeur de toutes les périodes comptables, dans l'ordre chronologique.

Corrige rétroactivement le défaut historique où le stock d'ouverture d'un
marketeur était recalculé en rejouant tout l'historique des mouvements
(sans jamais reporter la quote-part de coulage de la clôture précédente),
au lieu de reporter le stock de fermeture du mois précédent.

Usage :
    python manage.py recalculer_stock_ouverture_marketeur
    python manage.py recalculer_stock_ouverture_marketeur --marketeur EST
"""
from decimal import Decimal

from django.core.management.base import BaseCommand

_Z = Decimal('0')
_EPS = Decimal('0.01')


def _D(x):
    if x is None:
        return Decimal('0')
    return Decimal(str(x))


def _ancien_stock_ouverture_combine(periode, marketeur, produit):
    """
    Reproduit l'ANCIENNE formule (avant correctif) de stock d'ouverture
    marketeur : inventaire initial (toutes dates) + rejeu de tous les
    mouvements ENTREE/SORTIE antérieurs au début de la période, par régime,
    puis combine SD + Acquittée. Utilisée uniquement pour le rapport
    avant/après affiché par cette commande — jamais persistée.
    """
    from SGDS.models import InventaireInitialMarketeur, Mouvement

    bucket = {'SOUS_DOUANE': _Z, 'ACQUITTE': _Z}
    for inv in InventaireInitialMarketeur.objects.filter(marketeur=marketeur, produit=produit):
        bucket[inv.regime_douanier] += _D(inv.volume_ambiant)

    for m in Mouvement.objects.filter(
        marketeur=marketeur, produit=produit,
        date_mouvement__lt=periode.date_debut,
    ):
        if m.type_mouvement == 'ENTREE':
            bucket[m.regime_douanier] += _D(m.volume_ambiant_recu)
        elif m.type_mouvement == 'SORTIE':
            bucket[m.regime_douanier] -= _D(m.volume_ambiant_sortie)

    return bucket['SOUS_DOUANE'] + bucket['ACQUITTE']


class Command(BaseCommand):
    help = (
        "Recalcule et persiste le stock d'ouverture par marketeur de toutes "
        "les périodes comptables (correctif report fermeture -> ouverture)."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--marketeur', type=str, default=None,
            help="Sigle ou raison sociale du marketeur à filtrer dans le rapport d'écarts "
                 "(le recalcul porte toujours sur tous les marketeurs).",
        )

    def handle(self, *args, **options):
        from SGDS.models import PeriodeComptable, Marketeur, Produit, StockOuvertureMarketeur
        from SGDS.services.stock_ouverture_marketeur import resoudre_stock_ouverture_marketeur

        filtre_mkt = options.get('marketeur')

        periodes = list(PeriodeComptable.objects.order_by('annee', 'mois'))
        if not periodes:
            self.stdout.write(self.style.WARNING("Aucune période comptable trouvée."))
            return

        produits   = list(Produit.objects.filter(statut='ACTIF'))
        marketeurs = list(Marketeur.objects.all())
        if filtre_mkt:
            marketeurs_affiches = [
                m for m in marketeurs
                if filtre_mkt.lower() in (m.sigle or '').lower()
                or filtre_mkt.lower() in (m.raison_sociale or '').lower()
            ]
        else:
            marketeurs_affiches = marketeurs

        self.stdout.write(self.style.MIGRATE_HEADING(
            f"\n{'='*70}\n Rattrapage stock d'ouverture marketeur — {len(periodes)} période(s)\n{'='*70}"
        ))

        nb_lignes_corrigees = 0

        for periode in periodes:
            # ── Ancien calcul (pour comparaison, avant écriture) ──
            anciennes_valeurs = {}
            for marketeur in marketeurs_affiches:
                for produit in produits:
                    anciennes_valeurs[(marketeur.pk, produit.pk)] = _ancien_stock_ouverture_combine(
                        periode, marketeur, produit
                    )

            # ── Nouveau calcul : persiste le report correct ──
            resoudre_stock_ouverture_marketeur(periode, forcer_recalcul=True)

            # ── Nouvelles valeurs persistées (combinées SD + Acquittée) ──
            nouvelles_valeurs = {}
            for som in StockOuvertureMarketeur.objects.filter(periode=periode).select_related('marketeur', 'produit'):
                key = (som.marketeur_id, som.produit_id)
                nouvelles_valeurs[key] = nouvelles_valeurs.get(key, _Z) + _D(som.volume_ambiant)

            self.stdout.write(f"\n-- {periode} --")
            nb_lignes_periode = 0
            for marketeur in marketeurs_affiches:
                for produit in produits:
                    key = (marketeur.pk, produit.pk)
                    avant  = anciennes_valeurs.get(key, _Z)
                    apres  = nouvelles_valeurs.get(key, _Z)
                    delta  = apres - avant
                    if abs(delta) <= _EPS:
                        continue
                    nb_lignes_periode += 1
                    nb_lignes_corrigees += 1
                    signe = '+' if delta >= 0 else ''
                    mkt_label = marketeur.sigle or marketeur.raison_sociale
                    self.stdout.write(
                        f"  {mkt_label} - {produit.nom} : "
                        f"{avant:,.2f} -> {apres:,.2f} L  (delta {signe}{delta:,.2f} L)"
                    )
            if nb_lignes_periode == 0:
                self.stdout.write("  (aucun écart)")

        self.stdout.write(self.style.SUCCESS(
            f"\nRattrapage terminé : {len(periodes)} période(s) traitée(s), "
            f"{nb_lignes_corrigees} ligne(s) marketeur/produit corrigée(s).\n"
        ))
