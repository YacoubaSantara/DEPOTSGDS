"""
Suivi d'évolution journalier du stock par produit.
1 appel = 1 produit × 1 période → tableau jour par jour avec détail par cuve.
Générique : s'adapte aux cuves du produit demandé.
"""
from decimal import Decimal
from datetime import timedelta


_Q2 = Decimal('0.01')


def _D(x):
    if x is None:
        return Decimal('0')
    return Decimal(str(x)) if not isinstance(x, Decimal) else x


def calculer_suivi_evolution(periode, produit) -> dict:
    """
    Retourne {
        'produit', 'periode', 'cuves',
        'jours': [{date, jour_semaine, stock_initial, entree_brute,
                   coulage_reception, sortie, stock_comptable,
                   stock_physique, stock_physique_cumul,
                   pg_par_bac, pg_cumul, a_jaugeage}, ...],
        'totaux': {entree_brute, coulage_reception, sortie, pg_total}
    }
    """
    from SGDS.models import Cuve, LigneMouvement, JaugeageJour, StockOuvertureCuve

    cuves = list(
        Cuve.objects.filter(produit=produit, statut='ACTIVE').order_by('numero')
    )

    # Stock d'ouverture par cuve (1er jour du mois)
    so_par_cuve = {}
    for cuve in cuves:
        so = StockOuvertureCuve.objects.filter(periode=periode, cuve=cuve).first()
        so_par_cuve[cuve.id] = _D(so.volume_ambiant) if so else Decimal('0')

    # Lignes de mouvement du mois indexées par date (via LigneMouvement multi-cuves)
    lignes = (
        LigneMouvement.objects
        .filter(
            mouvement__produit=produit,
            cuve__in=cuves,
            mouvement__date_mouvement__range=(periode.date_debut, periode.date_fin),
            mouvement__type_mouvement__in=('ENTREE', 'SORTIE'),
        )
        .select_related('cuve', 'mouvement')
    )
    from collections import defaultdict
    lignes_par_date = defaultdict(list)
    for l in lignes:
        lignes_par_date[l.mouvement.date_mouvement].append(l)

    # Jaugeages du mois indexés par date → dernière mesure par cuve
    jaugeages_qs = (
        JaugeageJour.objects
        .filter(date_jaugeage__range=(periode.date_debut, periode.date_fin))
        .prefetch_related('mesures__cuve__parametre_jaugeage')
        .order_by('date_jaugeage', 'heure_jaugeage', 'date_creation')
    )
    # On garde le dernier jaugeage par date
    dernier_jaugeage_par_date = {}
    for j in jaugeages_qs:
        dernier_jaugeage_par_date[j.date_jaugeage] = j

    JOURS_FR = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche']

    jours = []
    stock_courant = dict(so_par_cuve)
    physique_veille = dict(so_par_cuve)
    pg_cumul = Decimal('0')

    d = periode.date_debut
    while d <= periode.date_fin:
        # Mouvements du jour par cuve
        entree_brute     = {c.id: Decimal('0') for c in cuves}
        coulage_recept   = {c.id: Decimal('0') for c in cuves}
        sortie           = {c.id: Decimal('0') for c in cuves}

        for l in lignes_par_date.get(d, []):
            if l.cuve_id not in entree_brute:
                continue
            cid = l.cuve_id
            type_m = l.mouvement.type_mouvement
            if type_m == 'ENTREE':
                entree_brute[cid] += _D(l.volume_ambiant)
                # Coulage réception : perte = volume_ambiant expéditeur - volume ligne reçu
                v_expe = _D(l.mouvement.volume_ambiant_expediteur)
                if v_expe and l.volume_ambiant:
                    pg = _D(l.volume_ambiant) - v_expe
                    if pg < 0:
                        coulage_recept[cid] += abs(pg)
            elif type_m == 'SORTIE':
                sortie[cid] += _D(l.volume_ambiant)

        # Stock comptable = init + entrée - coulage - sortie
        stock_compta = {
            c.id: (
                stock_courant[c.id]
                + entree_brute[c.id]
                - coulage_recept[c.id]
                - sortie[c.id]
            ).quantize(_Q2)
            for c in cuves
        }

        # Stock physique depuis le dernier jaugeage du jour
        jaugeage_du_jour = dernier_jaugeage_par_date.get(d)
        stock_phys   = {c.id: None for c in cuves}
        pg_par_bac   = {c.id: None for c in cuves}
        pg_cumul_jour = pg_cumul

        if jaugeage_du_jour:
            mesures_idx = {m.cuve_id: m for m in jaugeage_du_jour.mesures.all()}
            pg_jour = Decimal('0')
            for c in cuves:
                m = mesures_idx.get(c.id)
                if m and m.volume_ambiant_depot is not None:
                    vphys = _D(m.volume_ambiant_depot)
                    stock_phys[c.id] = vphys
                    pg_par_bac[c.id] = (vphys - stock_compta[c.id]).quantize(_Q2)
                    pg_jour += pg_par_bac[c.id]
            pg_cumul_jour = (pg_cumul + pg_jour).quantize(_Q2)

        # Stock physique total du jour
        phys_vals = [v for v in stock_phys.values() if v is not None]
        stock_phys_cumul = sum(phys_vals, Decimal('0')).quantize(_Q2) if phys_vals else None

        jours.append({
            'date':              d,
            'jour_semaine':      JOURS_FR[d.weekday()],
            'stock_initial':     dict(stock_courant),
            'stock_initial_cumul': sum(stock_courant.values(), Decimal('0')).quantize(_Q2),
            'entree_brute':      entree_brute,
            'coulage_reception': coulage_recept,
            'sortie':            sortie,
            'stock_comptable':   stock_compta,
            'stock_physique':    stock_phys,
            'stock_physique_cumul': stock_phys_cumul,
            'pg_par_bac':        pg_par_bac,
            'pg_cumul':          pg_cumul_jour,
            'a_jaugeage':        bool(jaugeage_du_jour),
        })

        # Le comptable devient le stock du lendemain;
        # si jaugeage → le physique mesuré remplace
        stock_courant = dict(stock_compta)
        if jaugeage_du_jour:
            for c in cuves:
                if stock_phys[c.id] is not None:
                    stock_courant[c.id] = stock_phys[c.id]
            pg_cumul = pg_cumul_jour

        d += timedelta(days=1)

    totaux = {
        'entree_brute':      sum(
            (sum(j['entree_brute'].values(), Decimal('0')) for j in jours), Decimal('0')
        ).quantize(_Q2),
        'coulage_reception': sum(
            (sum(j['coulage_reception'].values(), Decimal('0')) for j in jours), Decimal('0')
        ).quantize(_Q2),
        'sortie':            sum(
            (sum(j['sortie'].values(), Decimal('0')) for j in jours), Decimal('0')
        ).quantize(_Q2),
        'pg_total':          pg_cumul,
    }

    return {
        'produit': produit,
        'periode': periode,
        'cuves':   cuves,
        'jours':   jours,
        'totaux':  totaux,
    }
