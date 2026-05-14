"""
Service de résolution des stocks d'ouverture.
Calcule automatiquement le SO d'une période à partir du dernier jaugeage
du mois précédent.
"""
from decimal import Decimal


def resoudre_stocks_ouverture(periode, *, forcer_recalcul=False) -> dict:
    """
    Calcule et persiste les stocks d'ouverture d'une période.

    1. Trouve periode.periode_precedente() → aucun si c'est la première
    2. Trouve le dernier JaugeageJour du mois précédent
    3. Pour chaque MesureCuve, crée/met à jour StockOuvertureCuve
       (respecte calcul_auto=False sauf si forcer_recalcul=True)
    4. Agrège par produit → crée/met à jour StockOuverture

    Retourne un dict avec stocks_produit, stocks_cuve, jaugeage_source, message.
    """
    from SGDS.models import (
        JaugeageJour, StockOuverture, StockOuvertureCuve
    )

    resultat = {
        'stocks_produit': [],
        'stocks_cuve': [],
        'jaugeage_source': None,
        'message': '',
    }

    # 1. Période précédente
    periode_prec = periode.periode_precedente()
    if periode_prec is None:
        resultat['message'] = (
            f"Aucune période précédente pour {periode} — stocks d'ouverture à saisir manuellement."
        )
        return resultat

    # 2. Dernier jaugeage du mois précédent
    dernier_j = (
        JaugeageJour.objects
        .filter(
            date_jaugeage__gte=periode_prec.date_debut,
            date_jaugeage__lte=periode_prec.date_fin,
        )
        .order_by('-date_jaugeage', '-heure_jaugeage', '-date_creation')
        .first()
    )
    if dernier_j is None:
        resultat['message'] = (
            f"Aucun jaugeage trouvé pour {periode_prec} — "
            "stocks d'ouverture à saisir manuellement."
        )
        return resultat

    resultat['jaugeage_source'] = dernier_j

    # 3. Créer/mettre à jour les stocks par cuve
    mesures = (
        dernier_j.mesures
        .select_related('cuve__produit', 'cuve__parametre_jaugeage')
        .all()
    )

    agregats_produit = {}  # {produit: {'volume_ambiant': Decimal, 'volume_15c': Decimal}}

    for mesure in mesures:
        cuve = mesure.cuve
        if cuve.produit is None:
            continue

        v_amb = mesure.volume_ambiant_depot
        v_15c = mesure.volume_standard_15c_calcule

        v_amb_dec = Decimal(str(v_amb)) if v_amb is not None else Decimal('0')
        v_15c_dec = Decimal(str(v_15c)) if v_15c is not None else Decimal('0')

        # Respecter les valeurs manuelles (calcul_auto=False)
        existing = StockOuvertureCuve.objects.filter(periode=periode, cuve=cuve).first()
        if existing and not existing.calcul_auto and not forcer_recalcul:
            # Garder la valeur manuelle, mais compter dans l'agrégat
            v_amb_dec = existing.volume_ambiant
            v_15c_dec = existing.volume_15c
        else:
            soc, _ = StockOuvertureCuve.objects.update_or_create(
                periode=periode,
                cuve=cuve,
                defaults={
                    'volume_ambiant': v_amb_dec,
                    'volume_15c': v_15c_dec,
                    'calcul_auto': True,
                    'source_mesure': mesure,
                },
            )
            resultat['stocks_cuve'].append(soc)

        produit = cuve.produit
        if produit not in agregats_produit:
            agregats_produit[produit] = {'volume_ambiant': Decimal('0'), 'volume_15c': Decimal('0')}
        agregats_produit[produit]['volume_ambiant'] += v_amb_dec
        agregats_produit[produit]['volume_15c'] += v_15c_dec

    # 4. Agréger par produit
    for produit, vals in agregats_produit.items():
        existing_so = StockOuverture.objects.filter(periode=periode, produit=produit).first()
        if existing_so and not existing_so.calcul_auto and not forcer_recalcul:
            resultat['stocks_produit'].append(existing_so)
            continue

        so, _ = StockOuverture.objects.update_or_create(
            periode=periode,
            produit=produit,
            defaults={
                'volume_ambiant': vals['volume_ambiant'],
                'volume_15c': vals['volume_15c'],
                'calcul_auto': True,
            },
        )
        resultat['stocks_produit'].append(so)

    resultat['message'] = (
        f"Stocks d'ouverture calculés depuis le jaugeage du {dernier_j.date_jaugeage} "
        f"({len(mesures)} mesures, {len(agregats_produit)} produits)."
    )
    return resultat
