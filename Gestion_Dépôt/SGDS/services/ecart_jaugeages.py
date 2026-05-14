"""
Service de calcul de l'écart physique/comptable entre deux jaugeages.

Le modèle Mouvement utilise une FK produit + des champs volume génériques
(volume_ambiant_recu / perte_gain_reception pour ENTREE,
 volume_ambiant_sortie pour SORTIE), ce qui rend le calcul nativement
générique sur tous les produits.
"""
from decimal import Decimal

from django.db.models import Sum


def calculer_ecart_jaugeages(jaugeage_actuel):
    """
    Compare jaugeage_actuel au jaugeage précédent.

    Formule par produit :
        écart = stock_phys_nouveau
                - stock_phys_precedent
                - Σ entrees_nettes(entre les 2 jaugeages)
                + Σ sorties(entre les 2 jaugeages)

    Négatif = perte, positif = gain.

    Retourne {} si pas de jaugeage précédent.
    Retourne {produit_instance: Decimal, ...} pour tous les produits actifs.
    """
    from SGDS.models import JaugeageJour, Produit

    precedent = (
        JaugeageJour.objects
        .filter(
            date_jaugeage__lt=jaugeage_actuel.date_jaugeage,
        )
        .exclude(pk=jaugeage_actuel.pk)
        .order_by('-date_jaugeage', '-heure_jaugeage', '-date_creation')
        .first()
    )

    if precedent is None:
        # Même date : prendre le jaugeage précédent de la même date si existe
        precedent = (
            JaugeageJour.objects
            .filter(date_jaugeage=jaugeage_actuel.date_jaugeage)
            .exclude(pk=jaugeage_actuel.pk)
            .order_by('-heure_jaugeage', '-date_creation')
            .first()
        )

    if precedent is None:
        return {}

    stocks_nouveau   = _stocks_physiques_par_produit(jaugeage_actuel)
    stocks_precedent = _stocks_physiques_par_produit(precedent)

    date_debut = precedent.date_jaugeage
    date_fin   = jaugeage_actuel.date_jaugeage
    mouvements = _mouvements_entre(date_debut, date_fin)

    ecarts = {}
    for produit in Produit.objects.all():
        s_new  = stocks_nouveau.get(produit,   Decimal('0'))
        s_prev = stocks_precedent.get(produit, Decimal('0'))
        m      = mouvements.get(produit, {'entree_nette': Decimal('0'), 'sortie': Decimal('0')})

        ecart = s_new - s_prev - m['entree_nette'] + m['sortie']
        ecarts[produit] = ecart.quantize(Decimal('0.01'))

    return ecarts


def _stocks_physiques_par_produit(jaugeage):
    """
    Retourne {produit_instance: Decimal_total_ambiant, ...}
    en sommant volume_ambiant_depot de toutes les MesureCuve du jaugeage,
    groupées par cuve.produit. Générique.
    """
    stocks = {}
    for mesure in jaugeage.mesures.select_related('cuve__produit', 'cuve__parametre_jaugeage').all():
        produit = mesure.cuve.produit if mesure.cuve else None
        if produit is None:
            continue
        v = mesure.volume_ambiant_depot  # @property
        if v is None:
            continue
        stocks[produit] = stocks.get(produit, Decimal('0')) + Decimal(str(v))
    return stocks


def _mouvements_entre(date_debut, date_fin):
    """
    Retourne {produit_instance: {'entree_nette': Decimal, 'sortie': Decimal}}
    pour tous les produits ayant des mouvements entre date_debut et date_fin.

    Modèle Mouvement : champs génériques volume_ambiant_recu /
    perte_gain_reception / volume_ambiant_sortie + FK produit.
    entree_nette = brut_recu + perte_gain_reception (perte < 0, gain > 0).
    """
    from SGDS.models import Mouvement

    entrees = (
        Mouvement.objects
        .filter(
            type_mouvement='ENTREE',
            date_mouvement__gte=date_debut,
            date_mouvement__lte=date_fin,
        )
        .values('produit')
        .annotate(
            brut=Sum('volume_ambiant_recu'),
            coul=Sum('perte_gain_reception'),
        )
    )

    sorties = (
        Mouvement.objects
        .filter(
            type_mouvement='SORTIE',
            date_mouvement__gte=date_debut,
            date_mouvement__lte=date_fin,
        )
        .values('produit')
        .annotate(vol=Sum('volume_ambiant_sortie'))
    )

    from SGDS.models import Produit
    produits_map = {p.pk: p for p in Produit.objects.all()}

    result = {}
    for row in entrees:
        p = produits_map.get(row['produit'])
        if p is None:
            continue
        brut = Decimal(str(row['brut'] or 0))
        coul = Decimal(str(row['coul'] or 0))
        d = result.setdefault(p, {'entree_nette': Decimal('0'), 'sortie': Decimal('0')})
        d['entree_nette'] += (brut + coul)

    for row in sorties:
        p = produits_map.get(row['produit'])
        if p is None:
            continue
        d = result.setdefault(p, {'entree_nette': Decimal('0'), 'sortie': Decimal('0')})
        d['sortie'] += Decimal(str(row['vol'] or 0))

    return result


def formatter_ecart_pour_affichage(ecarts):
    """
    Formate le dict {produit: Decimal} en liste utilisable dans un template.
    Retourne [{'produit_code', 'produit_nom', 'ecart', 'signe', 'classe_css'}, ...]
    """
    lignes = []
    for produit, ecart in ecarts.items():
        if ecart < 0:
            signe      = 'negatif'
            classe_css = 'coulage-perte'
        elif ecart > 0:
            signe      = 'positif'
            classe_css = 'coulage-gain'
        else:
            signe      = 'neutre'
            classe_css = ''
        lignes.append({
            'produit_code': produit.code,
            'produit_nom':  produit.nom,
            'ecart':        ecart,
            'signe':        signe,
            'classe_css':   classe_css,
        })
    # Trier par code produit pour un affichage stable
    lignes.sort(key=lambda x: x['produit_code'])
    return lignes
