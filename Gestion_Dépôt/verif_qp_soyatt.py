"""
Simulation QP Coulage — Marketeur SOYATT — Avril 2026

Exécuter depuis Gestion_Dépôt avec le venv activé :
    cd "E:\Projet Site\SANKE\SGDS\Gestion_Dépôt"
    ..\env\Scripts\activate
    python verif_qp_soyatt.py
"""
import os, sys
import django

sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Gestion_Dépôt.settings')
django.setup()

from decimal import Decimal, ROUND_HALF_UP
from django.db.models import Sum
from SGDS.models import (
    PeriodeComptable, Marketeur, Mouvement,
    StockOuverture, JaugeageJour, ParametresCoulage,
    InventaireInitialMarketeur,
)

_Q8 = Decimal('0.00000001')
_Q2 = Decimal('0.01')

def _D(x):
    return Decimal('0') if x is None else Decimal(str(x))

SEP  = "─" * 70
SEP2 = "═" * 70

# ── Période ──────────────────────────────────────────────────
periode = PeriodeComptable.objects.filter(mois=4, annee=2026).first()
assert periode, "Période Avril 2026 introuvable"
print(f"\n{SEP2}")
print(f"  SIMULATION QP COULAGE — Avril 2026")
print(f"  Du {periode.date_debut} au {periode.date_fin}  |  statut : {periode.statut}")
print(SEP2)

# ── Marketeur SOYATT ─────────────────────────────────────────
mkt = (
    Marketeur.objects.filter(raison_sociale__icontains='SOYATT').first()
    or Marketeur.objects.filter(sigle__icontains='SOYATT').first()
)
assert mkt, "Marketeur SOYATT introuvable"

# ── Mouvements de la période ─────────────────────────────────
qs_entrees = Mouvement.objects.filter(
    type_mouvement='ENTREE',
    date_mouvement__range=(periode.date_debut, periode.date_fin),
)
qs_sorties = Mouvement.objects.filter(
    type_mouvement='SORTIE',
    date_mouvement__range=(periode.date_debut, periode.date_fin),
)

# ── Produits concernés ────────────────────────────────────────
from django.db.models import Q
from SGDS.models import Produit
produits = list(
    Produit.objects.filter(
        Q(mouvements__date_mouvement__range=(periode.date_debut, periode.date_fin))
        | Q(cuves__statut='ACTIVE')
    ).distinct().order_by('nom')
)

# ── Stock physique fin (StockOuverture période suivante) ──────
physique_par_produit = {}
dernier_j = (
    JaugeageJour.objects
    .filter(date_jaugeage__gte=periode.date_debut, date_jaugeage__lte=periode.date_fin)
    .order_by('-date_jaugeage', '-heure_jaugeage', '-date_creation')
    .first()
)
source_physique = f"Dernier jaugeage : {dernier_j.date_jaugeage}" if dernier_j else "Aucun jaugeage trouvé"
if dernier_j:
    for m in dernier_j.mesures.all():
        if m.cuve.produit is None or m.volume_ambiant_depot is None:
            continue
        pk = m.cuve.produit_id
        physique_par_produit[pk] = physique_par_produit.get(pk, Decimal('0')) + _D(m.volume_ambiant_depot)

print(f"\n  Source stock physique fin : {source_physique}")

# ── Diagnostic StockOuverture ─────────────────────────────────
print(f"\n{SEP}")
print(f"  DIAGNOSTIC — StockOuverture en base (toutes périodes récentes)")
print(SEP)
for so in StockOuverture.objects.select_related('produit', 'periode').order_by('-periode__annee', '-periode__mois')[:20]:
    print(f"    [{so.periode}]  {so.produit.nom:<12}  {so.volume_ambiant:>15,.2f} L")

# ── Paramètres coulage ────────────────────────────────────────
params = ParametresCoulage.en_vigueur(periode.date_fin)
prix_unitaire = _D(params.prix_unitaire_passage) if params else Decimal('4.7554')

# ── Diagnostic mouvements Gasoil ─────────────────────────────
from SGDS.models import Produit as _Produit
gasoil = _Produit.objects.filter(nom__icontains='GASOIL').first()
if gasoil:
    print(f"\n{SEP}")
    print(f"  DIAGNOSTIC MOUVEMENTS GASOIL — Avril 2026")
    print(SEP)
    from django.db.models import Sum, Count
    mvts = Mouvement.objects.filter(
        produit=gasoil,
        date_mouvement__range=(periode.date_debut, periode.date_fin),
    )
    for t in ['ENTREE', 'SORTIE', 'CESSION']:
        qs = mvts.filter(type_mouvement=t)
        nb = qs.count()
        if t == 'ENTREE':
            agg = qs.aggregate(v=Sum('volume_ambiant_recu'))
        elif t == 'SORTIE':
            agg = qs.aggregate(v=Sum('volume_ambiant_sortie'))
            # Ventilation par régime
            for regime in ['ACQUITTE', 'SOUS_DOUANE']:
                r = qs.filter(regime_douanier=regime).aggregate(v=Sum('volume_ambiant_sortie'), n=Count('id'))
                print(f"    SORTIE {regime:<12} : {_D(r['v']):>14,.2f} L  ({r['n']} mvts)")
        else:
            agg = qs.aggregate(v=Sum('cession_volume_ambiant'))
        total = _D(agg['v'])
        print(f"    {t:<8} TOTAL        : {total:>14,.2f} L  ({nb} mvts)")

# ── Inventaires initiaux (fallback SO) ───────────────────────
inv_initiaux = {}
for inv in InventaireInitialMarketeur.objects.filter(
    date_inventaire__lte=periode.date_fin,
).select_related('produit'):
    pid = inv.produit_id
    inv_initiaux[pid] = inv_initiaux.get(pid, _D(0)) + _D(inv.volume_ambiant)

# ── Calcul global par produit ─────────────────────────────────
coefficients = {}
pertes_gains = {}

print(f"\n{SEP}")
print(f"  CALCUL GLOBAL PAR PRODUIT")
print(SEP)

for produit in produits:
    pk = produit.pk

    r_e = qs_entrees.filter(produit_id=pk).aggregate(
        brut=Sum('volume_ambiant_recu'),
        coul=Sum('perte_gain_reception'),
    )
    brut   = _D(r_e['brut']).quantize(_Q2, ROUND_HALF_UP)
    coul   = _D(r_e['coul']).quantize(_Q2, ROUND_HALF_UP)
    entree = (brut + coul).quantize(_Q2, ROUND_HALF_UP)

    r_s = qs_sorties.filter(produit_id=pk).aggregate(s=Sum('volume_ambiant_sortie'))
    sortie = _D(r_s['s']).quantize(_Q2, ROUND_HALF_UP)

    so = StockOuverture.objects.filter(periode=periode, produit_id=pk).first()
    if so:
        so_val = _D(so.volume_ambiant)
        so_source = "StockOuverture"
    else:
        so_val = inv_initiaux.get(pk, Decimal('0'))
        so_source = "Inventaire initial (fallback)"

    physique  = physique_par_produit.get(pk, Decimal('0'))
    stock_comp = (so_val + entree - sortie).quantize(_Q2, ROUND_HALF_UP)
    perte_gain = (physique - stock_comp).quantize(_Q2, ROUND_HALF_UP)

    denom = (entree + sortie).quantize(_Q2, ROUND_HALF_UP)
    coef  = (perte_gain / denom).quantize(_Q8, ROUND_HALF_UP) if denom else Decimal('0')

    coefficients[pk] = coef
    pertes_gains[pk] = perte_gain

    signe = "GAIN" if perte_gain >= 0 else "PERTE"
    print(f"\n  ▶ {produit.nom}")
    print(f"    Stock ouverture       : {so_val:>15,.2f} L  [{so_source}]")
    print(f"    Entrées brutes        : {brut:>15,.2f} L")
    print(f"    Coulage réception     : {coul:>15,.2f} L")
    print(f"    Entrées nettes        : {entree:>15,.2f} L")
    print(f"    Sorties               : {sortie:>15,.2f} L")
    print(f"    Stock comptable       : {stock_comp:>15,.2f} L")
    print(f"    Stock physique fin    : {physique:>15,.2f} L")
    print(f"    Perte/Gain ({signe:5s})  : {perte_gain:>15,.2f} L")
    print(f"    Dénominateur          : {denom:>15,.2f} L  (entrées nettes + sorties)")
    print(f"  ► Coefficient QP       : {coef:>15.8f}")

# ── QP par marketeur SOYATT ───────────────────────────────────
print(f"\n{SEP}")
print(f"  QP COULAGE — {mkt.raison_sociale} ({mkt.sigle})")
print(SEP)

vol_global = Decimal('0')
for produit in produits:
    pk = produit.pk

    r_e = qs_entrees.filter(marketeur=mkt, produit_id=pk).aggregate(
        brut=Sum('volume_ambiant_recu'),
        coul=Sum('perte_gain_reception'),
    )
    m_brut  = _D(r_e['brut']).quantize(_Q2, ROUND_HALF_UP)
    m_coul  = _D(r_e['coul']).quantize(_Q2, ROUND_HALF_UP)
    m_nette = (m_brut + m_coul).quantize(_Q2, ROUND_HALF_UP)

    r_s = qs_sorties.filter(marketeur=mkt, produit_id=pk).aggregate(s=Sum('volume_ambiant_sortie'))
    m_sortie = _D(r_s['s']).quantize(_Q2, ROUND_HALF_UP)

    m_base = (m_nette + m_sortie).quantize(_Q2, ROUND_HALF_UP)
    m_qp   = (m_base * coefficients[pk]).quantize(_Q2, ROUND_HALF_UP)

    vol_global += m_sortie

    print(f"\n  ▶ {produit.nom}")
    print(f"    Entrée nette mkt      : {m_nette:>15,.2f} L")
    print(f"    Sortie mkt            : {m_sortie:>15,.2f} L")
    print(f"    Base QP               : {m_base:>15,.2f} L  (entrée nette + sortie)")
    print(f"    Coefficient           : {coefficients[pk]:>15.8f}")
    print(f"  ► QP Coulage           : {m_qp:>15,.2f} L")

vol_global = vol_global.quantize(_Q2, ROUND_HALF_UP)
montant    = (vol_global * prix_unitaire).quantize(_Q2, ROUND_HALF_UP)

print(f"\n{SEP2}")
print(f"  Volume global sorti       : {vol_global:>15,.2f} L")
print(f"  Prix unitaire passage     : {prix_unitaire:>15,.4f} FCFA/L")
print(f"  Montant coulage           : {montant:>15,.2f} FCFA")
print(SEP2)
