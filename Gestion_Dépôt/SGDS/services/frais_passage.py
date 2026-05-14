"""
Service Frais de Passage — document de facturation mensuel.
Regroupe les marketeurs par mode de règlement avec sous-totaux.
Générique sur les produits (aucun code produit en dur).
"""
from decimal import Decimal


_Q2 = Decimal('0.01')


def _D(x):
    if x is None:
        return Decimal('0')
    return Decimal(str(x)) if not isinstance(x, Decimal) else x


# Ordre d'affichage des modes de règlement
_ORDRE_MODES = ['ESP-IMMEDIAT', 'VIREMENT', 'CHEQUE', 'CREDIT']


def calculer_frais_passage(periode) -> dict:
    """
    Retourne {
        'periode', 'parametres', 'produits',
        'modes': [{mode, mode_libelle, lignes, sous_totaux}, ...],
        'total_general': {volumes_par_produit, volume_global, montant}
    }
    """
    from SGDS.models import Mouvement, ParametresCoulage, Produit

    params     = ParametresCoulage.en_vigueur(periode.date_debut)
    pu_global  = _D(params.prix_unitaire_passage) if params else Decimal('4.7554')
    motif      = params.motif_defaut if params else 'Chargement'

    produits = list(Produit.objects.filter(statut='ACTIF').order_by('nom'))

    # PU par produit : prix_passage du produit si renseigné, sinon tarif global
    pu_par_produit = {
        p.id: _D(p.prix_passage) if p.prix_passage is not None else pu_global
        for p in produits
    }

    sorties = (
        Mouvement.objects
        .filter(
            type_mouvement='SORTIE',
            date_mouvement__range=(periode.date_debut, periode.date_fin),
            volume_ambiant_sortie__isnull=False,
        )
        .exclude(volume_ambiant_sortie=0)
        .select_related('marketeur', 'produit')
    )

    # Regroupement (mode, marketeur_id) → {produit_id: vol}
    from collections import defaultdict
    groupes  = {}   # {(mode, mkt_id): {'mkt': Mkt, 'vols': {pid: Decimal}}}
    for s in sorties:
        mode = s.mode_reglement or 'NON_DEFINI'
        key  = (mode, s.marketeur_id)
        if key not in groupes:
            groupes[key] = {
                'mkt':  s.marketeur,
                'vols': {p.id: Decimal('0') for p in produits},
            }
        if s.produit_id in groupes[key]['vols']:
            groupes[key]['vols'][s.produit_id] += _D(s.volume_ambiant_sortie)

    MODE_LABELS = dict(Mouvement.MODE_REGLEMENT_CHOICES)
    MODE_LABELS['NON_DEFINI'] = 'Mode non défini'

    modes_presents = sorted(
        set(k[0] for k in groupes),
        key=lambda m: _ORDRE_MODES.index(m) if m in _ORDRE_MODES else 999,
    )

    modes_data    = []
    total_vols    = {p.id: Decimal('0') for p in produits}
    total_montant = Decimal('0')
    total_vol_global = Decimal('0')

    for mode in modes_presents:
        lignes    = []
        st_vols   = {p.id: Decimal('0') for p in produits}
        st_global = Decimal('0')
        st_montant = Decimal('0')

        # Tri par raison sociale dans chaque mode
        items_mode = sorted(
            ((k, v) for k, v in groupes.items() if k[0] == mode),
            key=lambda kv: kv[1]['mkt'].raison_sociale,
        )

        for (_, mkt_id), data in items_mode:
            vol_global = sum(data['vols'].values(), Decimal('0')).quantize(_Q2)
            # Montant = Σ (volume_produit × pu_produit) — tarif par produit
            montant = sum(
                (v * pu_par_produit.get(pid, pu_global) for pid, v in data['vols'].items()),
                Decimal('0'),
            ).quantize(_Q2)
            # PU moyen affiché (pour la colonne d'affichage)
            pu_moyen = (montant / vol_global).quantize(_Q2) if vol_global else pu_global
            lignes.append({
                'marketeur':           data['mkt'],
                'volumes_par_produit': dict(data['vols']),
                'volume_global':       vol_global,
                'motif':               motif,
                'pu':                  pu_moyen,
                'pu_par_produit':      {pid: pu_par_produit.get(pid, pu_global) for pid in data['vols']},
                'montant':             montant,
            })
            for pid, v in data['vols'].items():
                st_vols[pid] += v
            st_global  += vol_global
            st_montant += montant

        modes_data.append({
            'mode':         mode,
            'mode_libelle': MODE_LABELS.get(mode, mode),
            'lignes':       lignes,
            'sous_totaux': {
                'volumes_par_produit': st_vols,
                'volume_global':       st_global.quantize(_Q2),
                'montant':             st_montant.quantize(_Q2),
            },
        })

        for pid, v in st_vols.items():
            total_vols[pid] += v
        total_montant    += st_montant
        total_vol_global += st_global

    return {
        'periode':    periode,
        'parametres': {
            'prix_unitaire_global': pu_global,
            'pu_par_produit':       pu_par_produit,
            'motif':                motif,
        },
        'produits':   produits,
        'modes':      modes_data,
        'total_general': {
            'volumes_par_produit': total_vols,
            'volume_global':       total_vol_global.quantize(_Q2),
            'montant':             total_montant.quantize(_Q2),
        },
    }
