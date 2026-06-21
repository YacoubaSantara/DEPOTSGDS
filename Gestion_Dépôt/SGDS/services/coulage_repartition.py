"""
Service de calcul de la répartition du coulage par marketeur.
Reproduit la feuille COULA REPAR du Rapport Journalier de Jaugeage.

La logique est générique par produit : aucun code produit n'est codé en dur.
Les produits pris en compte sont ceux ayant des cuves actives OU des mouvements
sur la période.

Aucune écriture en DB dans calculer_repartition_coulage() (lecture pure).
figer_cloture_coulage() écrit en DB dans une transaction atomique.
"""
from decimal import Decimal, ROUND_HALF_UP

_Q8  = Decimal('0.00000001')  # précision coefficients
_Q2  = Decimal('0.01')        # précision volumes et montants


def _D(x):
    """None → Decimal('0'), sinon → Decimal(str(x))."""
    if x is None:
        return Decimal('0')
    return Decimal(str(x))


def _produits_concernes(date_debut, date_fin):
    """
    Retourne la liste ordonnée des Produit ayant des mouvements ou des cuves
    actives sur la période.
    """
    from django.db.models import Q
    from SGDS.models import Produit
    return list(
        Produit.objects
        .filter(
            Q(mouvements__date_mouvement__range=(date_debut, date_fin))
            | Q(cuves__statut='ACTIVE')
        )
        .distinct()
        .order_by('nom')
    )


def calculer_repartition_coulage(periode, *, marketeurs=None) -> dict:
    """
    Calcul pur (sans écriture DB) de la répartition du coulage.

    Retourne un dict avec :
      periode, produits, coefficients, pertes_gains, cumuls,
      lignes (une par marketeur), totaux, parametres.

    Clés de produit : produit.pk (int).
    """
    from django.db.models import Sum
    from SGDS.models import (
        Marketeur, Mouvement, JaugeageJour, StockOuverture,
        ParametresCoulage, InventaireInitialMarketeur,
    )

    if marketeurs is None:
        marketeurs = Marketeur.objects.filter(statut='ACTIF').order_by('raison_sociale')

    date_debut = periode.date_debut
    date_fin   = periode.date_fin

    # ── Paramètres de coulage en vigueur ─────────────────────────
    params = ParametresCoulage.en_vigueur(date_fin)
    prix_unitaire = _D(params.prix_unitaire_passage) if params else Decimal('4.7554')
    motif_defaut  = params.motif_defaut if params else 'Chargement'

    # ── Produits concernés ────────────────────────────────────────
    produits = _produits_concernes(date_debut, date_fin)

    # ── Cumuls globaux (tous marketeurs) ──────────────────────────
    qs_entrees = Mouvement.objects.filter(
        type_mouvement='ENTREE',
        date_mouvement__range=(date_debut, date_fin),
    )
    qs_sorties = Mouvement.objects.filter(
        type_mouvement='SORTIE',
        date_mouvement__range=(date_debut, date_fin),
    )

    def _agg_entree_produit(produit_pk):
        r = qs_entrees.filter(produit_id=produit_pk).aggregate(
            brut=Sum('volume_ambiant_expediteur'),
            coul=Sum('perte_gain_reception'),
        )
        brut  = _D(r['brut']).quantize(_Q2, ROUND_HALF_UP)
        coul  = _D(r['coul']).quantize(_Q2, ROUND_HALF_UP)
        nette = (brut + coul).quantize(_Q2, ROUND_HALF_UP)
        return brut, coul, nette

    def _agg_sortie_produit(produit_pk):
        r = qs_sorties.filter(produit_id=produit_pk).aggregate(s=Sum('volume_ambiant_sortie'))
        return _D(r['s']).quantize(_Q2, ROUND_HALF_UP)

    # ── Stock physique fin de mois (dernier jaugeage de la période) ──
    dernier_j = (
        JaugeageJour.objects
        .filter(
            date_jaugeage__gte=date_debut,
            date_jaugeage__lte=date_fin,
        )
        .prefetch_related('mesures__cuve__produit', 'mesures__cuve__parametre_jaugeage')
        .order_by('-date_jaugeage', '-heure_jaugeage', '-date_creation')
        .first()
    )

    physique_par_produit = {}   # {produit_pk: Decimal}
    if dernier_j:
        for m in dernier_j.mesures.all():
            if m.cuve.produit is None:
                continue
            v = m.volume_ambiant_depot
            if v is None:
                continue
            pk = m.cuve.produit_id
            physique_par_produit[pk] = physique_par_produit.get(pk, Decimal('0')) + _D(v)

    # ── Calcul par produit ────────────────────────────────────────
    cumuls      = {}   # {produit_pk: dict}
    pertes_gains = {}  # {produit_pk: Decimal}
    coefficients = {}  # {produit_pk: Decimal}

    # ── Inventaires initiaux (fallback si pas de StockOuverture) ─
    inv_initiaux = {}   # {produit_pk: Decimal}
    for inv in InventaireInitialMarketeur.objects.filter(
        date_inventaire__lte=date_fin,
    ).select_related('produit'):
        pid = inv.produit_id
        inv_initiaux[pid] = inv_initiaux.get(pid, Decimal('0')) + _D(inv.volume_ambiant)

    for produit in produits:
        pk = produit.pk

        brut, coul, entree_nette = _agg_entree_produit(pk)
        sortie = _agg_sortie_produit(pk)

        so = StockOuverture.objects.filter(periode=periode, produit_id=pk).first()
        if so:
            so_val = _D(so.volume_ambiant)
        else:
            # Fallback : somme des inventaires initiaux des marketeurs
            so_val = inv_initiaux.get(pk, Decimal('0'))

        physique = physique_par_produit.get(pk, Decimal('0'))

        stock_comp = so_val + entree_nette - sortie
        perte_gain = (physique - stock_comp).quantize(_Q2, ROUND_HALF_UP)

        denom = entree_nette + sortie
        coef  = (perte_gain / denom).quantize(_Q8, ROUND_HALF_UP) if denom else Decimal('0')

        cumuls[pk] = {
            'brut_entree': brut,
            'coul_entree': coul,
            'entree':      entree_nette,
            'sortie':      sortie,
        }
        pertes_gains[pk] = perte_gain
        coefficients[pk] = coef

    # ── Calcul par marketeur ──────────────────────────────────────
    lignes = []
    for mkt in marketeurs:
        par_produit = {}
        vol_global  = Decimal('0')
        montant     = Decimal('0')

        for produit in produits:
            pk = produit.pk

            r_e = qs_entrees.filter(marketeur=mkt, produit_id=pk).aggregate(
                brut=Sum('volume_ambiant_expediteur'),
                coul=Sum('perte_gain_reception'),
            )
            m_brut  = _D(r_e['brut']).quantize(_Q2, ROUND_HALF_UP)
            m_coul  = _D(r_e['coul']).quantize(_Q2, ROUND_HALF_UP)
            m_nette = (m_brut + m_coul).quantize(_Q2, ROUND_HALF_UP)

            r_s = qs_sorties.filter(marketeur=mkt, produit_id=pk).aggregate(
                s=Sum('volume_ambiant_sortie')
            )
            m_sortie = _D(r_s['s']).quantize(_Q2, ROUND_HALF_UP)

            m_base = (m_nette + m_sortie).quantize(_Q2, ROUND_HALF_UP)
            m_qp   = (m_base * coefficients[pk]).quantize(_Q2, ROUND_HALF_UP)

            par_produit[pk] = {
                'brut_entree':  m_brut,
                'coul_entree':  m_coul,
                'entree_nette': m_nette,
                'sortie':       m_sortie,
                'base_qp_coul': m_base,
                'coef_qp_coul': coefficients[pk],
                'qp_coul':      m_qp,
                'volume_sorti': m_sortie,
            }
            vol_global += m_sortie

        vol_global = vol_global.quantize(_Q2, ROUND_HALF_UP)
        montant    = (vol_global * prix_unitaire).quantize(_Q2, ROUND_HALF_UP)

        lignes.append({
            'marketeur':          mkt,
            'par_produit':        par_produit,
            'volume_global_sorti': vol_global,
            'motif':              motif_defaut,
            'prix_unitaire':      prix_unitaire,
            'montant':            montant,
        })

    # ── Totaux ────────────────────────────────────────────────────
    totaux_par_produit = {}
    for produit in produits:
        pk = produit.pk
        def _sum_pp(field):
            return sum(
                (l['par_produit'][pk][field] for l in lignes),
                Decimal('0')
            ).quantize(_Q2, ROUND_HALF_UP)
        totaux_par_produit[pk] = {
            'brut_entree':  _sum_pp('brut_entree'),
            'coul_entree':  _sum_pp('coul_entree'),
            'entree_nette': _sum_pp('entree_nette'),
            'sortie':       _sum_pp('sortie'),
            'base_qp_coul': _sum_pp('base_qp_coul'),
            'coef_qp_coul': coefficients[pk],
            'qp_coul':      _sum_pp('qp_coul'),
            'volume_sorti': _sum_pp('volume_sorti'),
        }

    totaux = {
        'par_produit':        totaux_par_produit,
        'volume_global_sorti': sum(
            (l['volume_global_sorti'] for l in lignes), Decimal('0')
        ).quantize(_Q2, ROUND_HALF_UP),
        'motif':        motif_defaut,
        'prix_unitaire': prix_unitaire,
        'montant': sum(
            (l['montant'] for l in lignes), Decimal('0')
        ).quantize(_Q2, ROUND_HALF_UP),
    }

    return {
        'periode':      periode,
        'produits':     produits,
        'coefficients': coefficients,
        'pertes_gains': pertes_gains,
        'cumuls':       cumuls,
        'lignes':       lignes,
        'totaux':       totaux,
        'parametres': {
            'prix_unitaire_passage': prix_unitaire,
            'motif':                 motif_defaut,
        },
    }


def figer_cloture_coulage(periode, user=None, notes=None):
    """
    Idempotent. Calcule la répartition puis persiste en DB :
    1. update_or_create du ClotureCoulageMensuel
    2. Remplace les ClotureCoulageProduit
    3. Remplace les ClotureCoulageLigne

    Retourne l'instance ClotureCoulageMensuel.
    """
    from django.db import transaction
    from SGDS.models import (
        ClotureCoulageMensuel, ClotureCoulageProduit, ClotureCoulageLigne
    )

    rapport = calculer_repartition_coulage(periode)
    params  = rapport['parametres']

    with transaction.atomic():
        cloture, _ = ClotureCoulageMensuel.objects.update_or_create(
            periode=periode,
            defaults={
                'prix_unitaire_passage': params['prix_unitaire_passage'],
                'motif':                 params['motif'],
                'notes':                 notes,
                'cloture_par':           user,
            },
        )

        # ── Snapshot par produit ──────────────────────────────
        cloture.produits_coulage.all().delete()
        ClotureCoulageProduit.objects.bulk_create([
            ClotureCoulageProduit(
                cloture=cloture,
                produit=produit,
                coefficient=rapport['coefficients'][produit.pk],
                pertes_gains=rapport['pertes_gains'][produit.pk],
                cumul_entree=rapport['cumuls'][produit.pk]['entree'],
                cumul_sortie=rapport['cumuls'][produit.pk]['sortie'],
            )
            for produit in rapport['produits']
        ])

        # ── Lignes marketeur × produit ────────────────────────
        cloture.lignes.all().delete()
        nouvelles_lignes = []
        for l in rapport['lignes']:
            for produit in rapport['produits']:
                pp = l['par_produit'][produit.pk]
                nouvelles_lignes.append(
                    ClotureCoulageLigne(
                        cloture=cloture,
                        marketeur=l['marketeur'],
                        produit=produit,
                        brut_entree=pp['brut_entree'],
                        coul_entree=pp['coul_entree'],
                        entree_nette=pp['entree_nette'],
                        sortie=pp['sortie'],
                        base_qp_coul=pp['base_qp_coul'],
                        coef_qp_coul=pp['coef_qp_coul'],
                        qp_coul=pp['qp_coul'],
                        volume_sorti=pp['volume_sorti'],
                        motif=l['motif'],
                        prix_unitaire=l['prix_unitaire'],
                        montant=(pp['volume_sorti'] * l['prix_unitaire']).quantize(
                            _Q2, ROUND_HALF_UP
                        ),
                    )
                )
        ClotureCoulageLigne.objects.bulk_create(nouvelles_lignes)

    return cloture
