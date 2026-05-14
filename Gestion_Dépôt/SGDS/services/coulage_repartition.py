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
        ParametresCoulage,
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
            brut=Sum('volume_ambiant_recu'),
            coul=Sum('perte_gain_reception'),
        )
        brut  = _D(r['brut']).quantize(_Q2, ROUND_HALF_UP)
        coul  = _D(r['coul']).quantize(_Q2, ROUND_HALF_UP)
        nette = (brut + coul).quantize(_Q2, ROUND_HALF_UP)
        return brut, coul, nette

    def _agg_sortie_produit(produit_pk):
        r = qs_sorties.filter(produit_id=produit_pk).aggregate(s=Sum('volume_ambiant_sortie'))
        return _D(r['s']).quantize(_Q2, ROUND_HALF_UP)

    # ── Stock physique fin de mois (dernier jaugeage du mois) ─────
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

    for produit in produits:
        pk = produit.pk

        brut, coul, entree_nette = _agg_entree_produit(pk)
        sortie = _agg_sortie_produit(pk)

        so = StockOuverture.objects.filter(periode=periode, produit_id=pk).first()
        so_val = _D(so.volume_ambiant if so else None)

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
                brut=Sum('volume_ambiant_recu'),
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

    """
    Calcul pur (sans écriture DB) de la répartition du coulage.

    Retourne un dict avec : periode, coefficients, pertes_gains, cumuls,
    lignes (une par marketeur), totaux, parametres.
    """
    from django.db.models import Sum
    from SGDS.models import (
        Marketeur, Mouvement, JaugeageJour, StockOuverture,
        ParametresCoulage,
    )

    if marketeurs is None:
        marketeurs = Marketeur.objects.filter(statut='ACTIF').order_by('raison_sociale')

    date_debut = periode.date_debut
    date_fin   = periode.date_fin

    # ── Paramètres de coulage en vigueur ──────────────────────────
    params = ParametresCoulage.en_vigueur(date_fin)
    prix_unitaire = _D(params.prix_unitaire_passage) if params else Decimal('4.7554')
    motif_defaut  = params.motif_defaut if params else 'Chargement'

    # ── Stocks d'ouverture du mois ────────────────────────────────
    so_go = StockOuverture.objects.filter(
        periode=periode, produit__code=CODE_GASOIL
    ).first()
    so_super = StockOuverture.objects.filter(
        periode=periode, produit__code=CODE_SUPER
    ).first()
    so_go_val    = _D(so_go.volume_ambiant if so_go else None)
    so_super_val = _D(so_super.volume_ambiant if so_super else None)

    # ── Cumuls globaux (tous marketeurs) ──────────────────────────
    qs_entrees = Mouvement.objects.filter(
        type_mouvement='ENTREE',
        date_mouvement__range=(date_debut, date_fin),
    )
    qs_sorties = Mouvement.objects.filter(
        type_mouvement='SORTIE',
        date_mouvement__range=(date_debut, date_fin),
    )

    def _agg_entree(code):
        r = qs_entrees.filter(produit__code=code).aggregate(
            brut=Sum('volume_ambiant_recu'),
            coul=Sum('perte_gain_reception'),
        )
        brut = _D(r['brut'])
        coul = _D(r['coul'])
        nette = (brut + coul).quantize(_Q2, ROUND_HALF_UP)
        return brut.quantize(_Q2, ROUND_HALF_UP), coul.quantize(_Q2, ROUND_HALF_UP), nette

    def _agg_sortie(code):
        r = qs_sorties.filter(produit__code=code).aggregate(s=Sum('volume_ambiant_sortie'))
        return _D(r['s']).quantize(_Q2, ROUND_HALF_UP)

    brut_go,  coul_go,  entree_go    = _agg_entree(CODE_GASOIL)
    brut_sup, coul_sup, entree_super = _agg_entree(CODE_SUPER)
    sortie_go    = _agg_sortie(CODE_GASOIL)
    sortie_super = _agg_sortie(CODE_SUPER)

    cumuls = {
        'brut_entree_go':    brut_go,
        'coul_entree_go':    coul_go,
        'entree_go':         entree_go,
        'brut_entree_super': brut_sup,
        'coul_entree_super': coul_sup,
        'entree_super':      entree_super,
        'sortie_go':         sortie_go,
        'sortie_super':      sortie_super,
    }

    # ── Stock physique fin de mois (dernier jaugeage du mois) ─────
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

    if dernier_j:
        physique_go    = Decimal('0')
        physique_super = Decimal('0')
        for m in dernier_j.mesures.all():
            if m.cuve.produit is None:
                continue
            v = m.volume_ambiant_depot
            if v is None:
                continue
            if m.cuve.produit.code == CODE_GASOIL:
                physique_go += _D(v)
            elif m.cuve.produit.code == CODE_SUPER:
                physique_super += _D(v)
    else:
        physique_go    = Decimal('0')
        physique_super = Decimal('0')

    # ── Pertes/gains du mois ──────────────────────────────────────
    # stock_comptable = SO + Σentrees_nettes - Σsorties
    stock_comp_go    = so_go_val    + entree_go    - sortie_go
    stock_comp_super = so_super_val + entree_super - sortie_super

    perte_gain_go    = (physique_go    - stock_comp_go).quantize(_Q2, ROUND_HALF_UP)
    perte_gain_super = (physique_super - stock_comp_super).quantize(_Q2, ROUND_HALF_UP)

    pertes_gains = {'GO': perte_gain_go, 'SUPER': perte_gain_super}

    # ── Coefficients globaux ──────────────────────────────────────
    denom_go    = entree_go    + sortie_go
    denom_super = entree_super + sortie_super

    coef_go    = (perte_gain_go    / denom_go).quantize(_Q8, ROUND_HALF_UP) if denom_go else Decimal('0')
    coef_super = (perte_gain_super / denom_super).quantize(_Q8, ROUND_HALF_UP) if denom_super else Decimal('0')

    coefficients = {'GO': coef_go, 'SUPER': coef_super}

    # ── Calcul par marketeur ──────────────────────────────────────
    lignes = []
    for mkt in marketeurs:
        def _mkt_entree(code):
            r = qs_entrees.filter(marketeur=mkt, produit__code=code).aggregate(
                brut=Sum('volume_ambiant_recu'),
                coul=Sum('perte_gain_reception'),
            )
            b = _D(r['brut']).quantize(_Q2, ROUND_HALF_UP)
            c = _D(r['coul']).quantize(_Q2, ROUND_HALF_UP)
            n = (b + c).quantize(_Q2, ROUND_HALF_UP)
            return b, c, n

        def _mkt_sortie(code):
            r = qs_sorties.filter(marketeur=mkt, produit__code=code).aggregate(
                s=Sum('volume_ambiant_sortie')
            )
            return _D(r['s']).quantize(_Q2, ROUND_HALF_UP)

        m_brut_go,  m_coul_go,  m_nette_go    = _mkt_entree(CODE_GASOIL)
        m_brut_sup, m_coul_sup, m_nette_super  = _mkt_entree(CODE_SUPER)
        m_sortie_go    = _mkt_sortie(CODE_GASOIL)
        m_sortie_super = _mkt_sortie(CODE_SUPER)

        # Quote-part coulage GO
        m_base_go  = (m_nette_go + m_sortie_go).quantize(_Q2, ROUND_HALF_UP)
        m_qp_go    = (m_base_go * coef_go).quantize(_Q2, ROUND_HALF_UP)

        # Quote-part coulage SUPER
        m_base_sup = (m_nette_super + m_sortie_super).quantize(_Q2, ROUND_HALF_UP)
        m_qp_sup   = (m_base_sup * coef_super).quantize(_Q2, ROUND_HALF_UP)

        # Volume global sorti et montant
        vol_global  = (m_sortie_go + m_sortie_super).quantize(_Q2, ROUND_HALF_UP)
        montant     = (vol_global * prix_unitaire).quantize(_Q2, ROUND_HALF_UP)

        lignes.append({
            'marketeur':         mkt,
            'brut_entree_go':    m_brut_go,
            'coul_entree_go':    m_coul_go,
            'entree_nette_go':   m_nette_go,
            'brut_entree_super': m_brut_sup,
            'coul_entree_super': m_coul_sup,
            'entree_nette_super':m_nette_super,
            'sortie_go':         m_sortie_go,
            'sortie_super':      m_sortie_super,
            'base_qp_coul_go':   m_base_go,
            'coef_qp_coul_go':   coef_go,
            'qp_coul_go':        m_qp_go,
            'base_qp_coul_super':m_base_sup,
            'coef_qp_coul_super':coef_super,
            'qp_coul_super':     m_qp_sup,
            'volume_global_sorti': vol_global,
            'motif':             motif_defaut,
            'prix_unitaire':     prix_unitaire,
            'montant':           montant,
        })

    # ── Totaux ────────────────────────────────────────────────────
    def _sum_field(field):
        return sum((l[field] for l in lignes), Decimal('0')).quantize(_Q2, ROUND_HALF_UP)

    totaux = {
        'marketeur':         None,
        'brut_entree_go':    _sum_field('brut_entree_go'),
        'coul_entree_go':    _sum_field('coul_entree_go'),
        'entree_nette_go':   _sum_field('entree_nette_go'),
        'brut_entree_super': _sum_field('brut_entree_super'),
        'coul_entree_super': _sum_field('coul_entree_super'),
        'entree_nette_super':_sum_field('entree_nette_super'),
        'sortie_go':         _sum_field('sortie_go'),
        'sortie_super':      _sum_field('sortie_super'),
        'base_qp_coul_go':   _sum_field('base_qp_coul_go'),
        'coef_qp_coul_go':   coef_go,
        'qp_coul_go':        _sum_field('qp_coul_go'),
        'base_qp_coul_super':_sum_field('base_qp_coul_super'),
        'coef_qp_coul_super':coef_super,
        'qp_coul_super':     _sum_field('qp_coul_super'),
        'volume_global_sorti':_sum_field('volume_global_sorti'),
        'motif':             motif_defaut,
        'prix_unitaire':     prix_unitaire,
        'montant':           _sum_field('montant'),
    }

    return {
        'periode':      periode,
        'coefficients': coefficients,
        'pertes_gains': pertes_gains,
        'cumuls':       cumuls,
        'lignes':       lignes,
        'totaux':       totaux,
        'parametres':   {
            'prix_unitaire_passage': prix_unitaire,
            'motif':                 motif_defaut,
        },
    }

