"""
Service de résolution des stocks d'ouverture par marketeur.

Contrairement au stock d'ouverture du dépôt (StockOuverture, ancré sur le
jaugeage physique), le stock d'ouverture d'un marketeur n'a pas de référence
physique propre : c'est un report comptable du stock de fermeture du
marketeur à la période précédente (stock comptable + quote-part coulage
figée à la clôture), exactement comme une carte de compte.

Ce module persiste ce report dans StockOuvertureMarketeur, pour que
l'ouverture d'un mois soit garantie égale à la fermeture du mois précédent
— au lieu d'être recalculée à chaque affichage en rejouant tout
l'historique des mouvements (ce qui ignorait la quote-part de coulage et
faisait dériver les écrans d'un mois à l'autre).
"""
from decimal import Decimal


def _D(x):
    if x is None:
        return Decimal('0')
    return Decimal(str(x))


def _flux_periode_marketeur_produit(periode, marketeur, produit):
    """
    Calcule les entrées/sorties détaillées par régime douanier (SD/AC) d'un
    marketeur, pour un produit, sur la période donnée.

    Reproduit exactement la logique de
    SGDS.views.mensuel._calculer_stock_ouverture_fermeture_marketeur
    (lignes Entrées/Sorties détaillées), condensée aux seuls totaux par
    régime nécessaires au calcul du stock comptable.
    """
    from SGDS.models import Mouvement

    _Z = Decimal('0')

    mvts_p = list(
        Mouvement.objects.filter(
            depot=periode.depot, marketeur=marketeur, produit=produit,
            date_mouvement__range=(periode.date_debut, periode.date_fin),
        )
    )
    cessions_recues = list(
        Mouvement.objects.filter(
            depot=periode.depot, cession_marketeur_destinataire=marketeur, produit=produit,
            type_mouvement='CESSION',
            date_mouvement__range=(periode.date_debut, periode.date_fin),
        )
    )

    # ── Entrées ──
    rec_sd_amb = rec_sd_15c = rec_ac_amb = rec_ac_15c = _Z
    recl_sd_entree_amb = recl_sd_entree_15c = _Z  # Acquittée→SD
    recl_ac_entree_amb = recl_ac_entree_15c = _Z  # SD→Acquittée
    for m in mvts_p:
        if m.type_mouvement == 'ENTREE':
            v_amb = _D(m.volume_ambiant_recu)
            v_15c = _D(m.volume_15c_recu)
            if m.regime_douanier == 'SOUS_DOUANE':
                rec_sd_amb += v_amb; rec_sd_15c += v_15c
            else:
                rec_ac_amb += v_amb; rec_ac_15c += v_15c
        elif m.type_mouvement == 'RECLASSEMENT':
            v_amb = _D(m.volume_ambiant_recu) if m.volume_ambiant_recu else _Z
            v_15c = _D(m.volume_15c_recu)     if m.volume_15c_recu     else _Z
            if m.regime_douanier == 'SOUS_DOUANE':
                recl_ac_entree_amb += v_amb
                recl_ac_entree_15c += v_15c
            else:
                recl_sd_entree_amb += v_amb
                recl_sd_entree_15c += v_15c

    cess_recues_sd_amb = cess_recues_sd_15c = _Z
    cess_recues_ac_amb = cess_recues_ac_15c = _Z
    for m in cessions_recues:
        if m.regime_douanier == 'SOUS_DOUANE':
            cess_recues_sd_amb += _D(m.cession_volume_ambiant)
            cess_recues_sd_15c += _D(m.cession_volume_15c)
        else:
            cess_recues_ac_amb += _D(m.cession_volume_ambiant)
            cess_recues_ac_15c += _D(m.cession_volume_15c)

    total_entrees_sd_amb = rec_sd_amb + cess_recues_sd_amb + recl_sd_entree_amb
    total_entrees_sd_15c = rec_sd_15c + cess_recues_sd_15c + recl_sd_entree_15c
    total_entrees_ac_amb = rec_ac_amb + cess_recues_ac_amb + recl_ac_entree_amb
    total_entrees_ac_15c = rec_ac_15c + cess_recues_ac_15c + recl_ac_entree_15c

    # ── Sorties ──
    livr_ac_amb = livr_ac_15c = livr_sd_amb = livr_sd_15c = _Z
    recl_sd_sortie_amb = recl_sd_sortie_15c = _Z  # quitte SD
    recl_ac_sortie_amb = recl_ac_sortie_15c = _Z  # quitte Acquittée
    cess_emises_sd_amb = cess_emises_sd_15c = _Z
    cess_emises_ac_amb = cess_emises_ac_15c = _Z
    for m in mvts_p:
        if m.type_mouvement == 'SORTIE':
            v_amb = _D(m.volume_ambiant_sortie)
            v_15c = _D(m.volume_15c_sortie)
            if m.regime_douanier == 'ACQUITTE':
                livr_ac_amb += v_amb; livr_ac_15c += v_15c
            else:
                livr_sd_amb += v_amb; livr_sd_15c += v_15c
        elif m.type_mouvement == 'CESSION':
            if m.regime_douanier == 'SOUS_DOUANE':
                cess_emises_sd_amb += _D(m.cession_volume_ambiant)
                cess_emises_sd_15c += _D(m.cession_volume_15c)
            else:
                cess_emises_ac_amb += _D(m.cession_volume_ambiant)
                cess_emises_ac_15c += _D(m.cession_volume_15c)
        elif m.type_mouvement == 'RECLASSEMENT':
            v_amb = _D(m.volume_ambiant_recu) if m.volume_ambiant_recu else _Z
            v_15c = _D(m.volume_15c_recu)     if m.volume_15c_recu     else _Z
            if m.regime_douanier == 'SOUS_DOUANE':
                recl_sd_sortie_amb += v_amb
                recl_sd_sortie_15c += v_15c
            else:
                recl_ac_sortie_amb += v_amb
                recl_ac_sortie_15c += v_15c

    total_sorties_sd_amb = livr_sd_amb + cess_emises_sd_amb + recl_sd_sortie_amb
    total_sorties_sd_15c = livr_sd_15c + cess_emises_sd_15c + recl_sd_sortie_15c
    total_sorties_ac_amb = livr_ac_amb + cess_emises_ac_amb + recl_ac_sortie_amb
    total_sorties_ac_15c = livr_ac_15c + cess_emises_ac_15c + recl_ac_sortie_15c

    return {
        'entrees_sd_amb': total_entrees_sd_amb, 'entrees_sd_15c': total_entrees_sd_15c,
        'entrees_ac_amb': total_entrees_ac_amb, 'entrees_ac_15c': total_entrees_ac_15c,
        'sorties_sd_amb': total_sorties_sd_amb, 'sorties_sd_15c': total_sorties_sd_15c,
        'sorties_ac_amb': total_sorties_ac_amb, 'sorties_ac_15c': total_sorties_ac_15c,
    }


def _ouverture_marketeur(periode, marketeur, produit):
    """
    Retourne {'SOUS_DOUANE': {'amb','15c'}, 'ACQUITTE': {'amb','15c'}} pour
    le stock d'ouverture déjà persisté de `periode` (marketeur, produit).
    """
    from SGDS.models import StockOuvertureMarketeur

    _Z = Decimal('0')
    out = {
        'SOUS_DOUANE': {'amb': _Z, '15c': _Z},
        'ACQUITTE':    {'amb': _Z, '15c': _Z},
    }
    for som in StockOuvertureMarketeur.objects.filter(periode=periode, marketeur=marketeur, produit=produit):
        out[som.regime_douanier] = {'amb': _D(som.volume_ambiant), '15c': _D(som.volume_15c)}
    return out


def _quote_part_coulage(periode_cloturee, marketeur, produit):
    """Quote-part de coulage (ambiant) figée à la clôture de `periode_cloturee`."""
    from SGDS.models import ClotureCoulageLigne

    cloture = getattr(periode_cloturee, 'cloture_coulage', None)
    if cloture is None:
        return Decimal('0')
    ligne = ClotureCoulageLigne.objects.filter(
        cloture=cloture, marketeur=marketeur, produit=produit,
    ).first()
    return _D(ligne.qp_coul) if ligne else Decimal('0')


def resoudre_stock_ouverture_marketeur(periode, *, forcer_recalcul=False) -> dict:
    """
    Calcule et persiste les stocks d'ouverture par marketeur de `periode`.

    - Si periode.periode_precedente() est None (1ère période) : seed depuis
      InventaireInitialMarketeur, par marketeur/produit/régime.
    - Sinon : pour chaque marketeur et produit actif, ouverture(periode) =
      fermeture(periode_precedente) = stock comptable de periode_precedente
      (calculé à partir de SON propre stock d'ouverture déjà persisté + ses
      mouvements) + quote-part coulage figée (ambiant, régime ACQUITTE
      uniquement).

    Respecte calcul_auto=False (valeur saisie manuellement) sauf si
    forcer_recalcul=True.

    Retourne {'lignes': [...StockOuvertureMarketeur...], 'message': str}.
    """
    from django.db.models import Sum
    from SGDS.models import Marketeur, Produit, StockOuvertureMarketeur, InventaireInitialMarketeur

    resultat = {'lignes': [], 'message': ''}

    produits   = list(Produit.objects.filter(statut='ACTIF'))
    marketeurs = list(Marketeur.objects.all())

    periode_prec = periode.periode_precedente()

    if periode_prec is None:
        for marketeur in marketeurs:
            for produit in produits:
                for regime in ('SOUS_DOUANE', 'ACQUITTE'):
                    existing = StockOuvertureMarketeur.objects.filter(
                        periode=periode, marketeur=marketeur, produit=produit, regime_douanier=regime,
                    ).first()
                    if existing and not existing.calcul_auto and not forcer_recalcul:
                        resultat['lignes'].append(existing)
                        continue

                    inv = InventaireInitialMarketeur.objects.filter(
                        depot=periode.depot,
                        marketeur=marketeur, produit=produit, regime_douanier=regime,
                        date_inventaire__lte=periode.date_fin,
                    ).aggregate(amb=Sum('volume_ambiant'), v15=Sum('volume_15c'))
                    amb = _D(inv['amb']); v15 = _D(inv['v15'])

                    som, _ = StockOuvertureMarketeur.objects.update_or_create(
                        periode=periode, marketeur=marketeur, produit=produit, regime_douanier=regime,
                        defaults={'volume_ambiant': amb, 'volume_15c': v15, 'calcul_auto': True},
                    )
                    resultat['lignes'].append(som)

        resultat['message'] = (
            f"Stocks d'ouverture marketeur de la première période calculés "
            f"depuis les inventaires initiaux ({len(marketeurs)} marketeur(s))."
        )
        return resultat

    for marketeur in marketeurs:
        for produit in produits:
            ouv_prec = _ouverture_marketeur(periode_prec, marketeur, produit)
            flux     = _flux_periode_marketeur_produit(periode_prec, marketeur, produit)

            stk_c_sd_amb = ouv_prec['SOUS_DOUANE']['amb'] + flux['entrees_sd_amb'] - flux['sorties_sd_amb']
            stk_c_sd_15c = ouv_prec['SOUS_DOUANE']['15c'] + flux['entrees_sd_15c'] - flux['sorties_sd_15c']
            stk_c_ac_amb = ouv_prec['ACQUITTE']['amb']    + flux['entrees_ac_amb'] - flux['sorties_ac_amb']
            stk_c_ac_15c = ouv_prec['ACQUITTE']['15c']    + flux['entrees_ac_15c'] - flux['sorties_ac_15c']

            qp_coul = _quote_part_coulage(periode_prec, marketeur, produit)

            fermeture = {
                'SOUS_DOUANE': {'amb': stk_c_sd_amb,            '15c': stk_c_sd_15c},
                'ACQUITTE':    {'amb': stk_c_ac_amb + qp_coul, '15c': stk_c_ac_15c},
            }

            for regime, vals in fermeture.items():
                existing = StockOuvertureMarketeur.objects.filter(
                    periode=periode, marketeur=marketeur, produit=produit, regime_douanier=regime,
                ).first()
                if existing and not existing.calcul_auto and not forcer_recalcul:
                    resultat['lignes'].append(existing)
                    continue

                som, _ = StockOuvertureMarketeur.objects.update_or_create(
                    periode=periode, marketeur=marketeur, produit=produit, regime_douanier=regime,
                    defaults={'volume_ambiant': vals['amb'], 'volume_15c': vals['15c'], 'calcul_auto': True},
                )
                resultat['lignes'].append(som)

    resultat['message'] = (
        f"Stocks d'ouverture marketeur de {periode} reportés depuis la "
        f"fermeture de {periode_prec} ({len(marketeurs)} marketeur(s), {len(produits)} produit(s))."
    )
    return resultat
