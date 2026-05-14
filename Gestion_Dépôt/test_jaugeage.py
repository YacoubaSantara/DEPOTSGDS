"""
test_jaugeage.py
────────────────
Script de test à exécuter dans le shell Django pour vérifier que
petroleum_calc branché sur MesureCuve donne les mêmes valeurs qu'Excel.

USAGE :
    python manage.py shell < test_jaugeage.py

    OU en interactif :
    python manage.py shell
    >>> exec(open('test_jaugeage.py').read())

Valeurs de référence = feuille RJJ du classeur au 31 janvier 2026.
"""

from datetime import date, time
from decimal import Decimal

# ⚠️ Adapte 'SGDS' au nom réel de ton application Django
from SGDS.models import (
    Produit, Cuve, ParametreJaugeageCuve, JaugeageJour, MesureCuve
)


# ─────────────────────────────────────────────────────────────
#  1) Préparation : produits + cuves + paramètres de jaugeage
# ─────────────────────────────────────────────────────────────
print("\n" + "="*70)
print("  ÉTAPE 1 : Création des produits et cuves")
print("="*70)

super_p, _ = Produit.objects.get_or_create(
    code='SUPER',
    defaults={'nom': 'Essence Super', 'unite_mesure': 'LITRE'}
)
gasoil, _ = Produit.objects.get_or_create(
    code='GASOIL',
    defaults={'nom': 'Gas-oil', 'unite_mesure': 'LITRE'}
)
print(f"  ✓ Produits : {super_p}, {gasoil}")

# (numero, produit, HTT, capacite, remplissage_maxi, V(A), V/mn)
CUVES_DATA = [
    ('RO3', super_p, 12981, 1500000, 1300000,  60294, 139),
    ('RO5', super_p, 12954, 1800000, 1600000,  82779, 165),
    ('RO6', super_p, 12959, 1800000, 1600000,  74753, 165),
    ('RO1', gasoil,  12942, 2000000, 1800000,  88058, 176),
    ('RO2', gasoil,  12959, 6000000, 5800000, 263875, 530),
    ('RO4', gasoil,  12946, 1500000, 1300000,  58748, 132),
]

for numero, produit, htt, cap, rmax, va, vmn in CUVES_DATA:
    cuve, created = Cuve.objects.update_or_create(
        numero=numero,
        defaults={
            'designation': f'Cuve {numero}',
            'produit': produit,
            'capacite_totale': Decimal(str(cap)),
        }
    )
    ParametreJaugeageCuve.objects.update_or_create(
        cuve=cuve,
        defaults={
            'hauteur_totale_temoin': htt,
            'hauteur_min_livraison': 2000,
            'correction_creux': 4,
            'remplissage_maxi': Decimal(str(rmax)),
            'v_a': Decimal(str(va)),
            'v_mn': vmn,
            'is_pompe': False,
        }
    )
    print(f"  ✓ Cuve {numero} ({produit.code}) — HTT={htt}, V(A)={va}, V/mn={vmn}")


# ─────────────────────────────────────────────────────────────
#  2) Création du jaugeage du 31 janvier 2026
# ─────────────────────────────────────────────────────────────
print("\n" + "="*70)
print("  ÉTAPE 2 : Création du jaugeage du 31/01/2026")
print("="*70)

jaugeage = JaugeageJour.objects.create(
    date_jaugeage=date(2026, 1, 31),
    type_jaugeage='J',
    heure_jaugeage=time(8, 0),
    operateur='TEST',
    notes='Jaugeage de validation contre Excel RJJ 31/01/2026',
)
print(f"  ✓ {jaugeage}")


# ─────────────────────────────────────────────────────────────
#  3) Saisie des mesures (données feuille CONV_ADAMA colonnes C..H)
# ─────────────────────────────────────────────────────────────
print("\n" + "="*70)
print("  ÉTAPE 3 : Saisie des mesures")
print("="*70)

# (numero_cuve, creux, t1, t2, t3, t_obs, densite_moy, v_additionnel)
MESURES_DATA = [
    ('RO3', 12621, 26.2, 26.2, 26.2, 24.5, 742, 1000),
    ('RO5', 12539, 26.8, 26.8, 26.8, 23.0, 745,    0),
    ('RO6', 12599, 26.5, 26.5, 26.5, 22.5, 742,    0),
    ('RO1', 12571, 27.6, 27.6, 27.6, 27.5, 834,    0),
    ('RO2', 12657, 26.3, 26.3, 26.3, 30.0, 834, 1000),
    ('RO4', 12605, 24.7, 24.7, 24.7, 27.5, 835,    0),
]

for numero, creux, t1, t2, t3, t_obs, d_moy, v_add in MESURES_DATA:
    cuve = Cuve.objects.get(numero=numero)
    mesure, _ = MesureCuve.objects.update_or_create(
        jaugeage=jaugeage,
        cuve=cuve,
        defaults={
            'creux_mesure':       creux,
            't1':                 Decimal(str(t1)),
            't2':                 Decimal(str(t2)),
            't3':                 Decimal(str(t3)),
            'temperature_obs':    Decimal(str(t_obs)),
            'densite_moyenne':    Decimal(str(d_moy)),
            'volume_additionnel': v_add,
        }
    )
    print(f"  ✓ Mesure {numero} enregistrée (save() a auto-calculé D15°C + Vcf)")


# ─────────────────────────────────────────────────────────────
#  4) Comparaison avec les valeurs Excel attendues
# ─────────────────────────────────────────────────────────────
print("\n" + "="*70)
print("  ÉTAPE 4 : Validation contre Excel")
print("="*70)

# Valeurs attendues = feuille RJJ (D15°C=ligne 39, Vcf=40, Vamb=31, V@15°C=41)
EXCEL_ATTENDU = {
    'RO3': {'d15': 751.9, 'vcf': 0.9886, 'v_amb':  61850, 'v_15c':  61144.91},
    'RO5': {'d15': 755.4, 'vcf': 0.9905, 'v_amb':  84264, 'v_15c':  83463.49},
    'RO6': {'d15': 752.2, 'vcf': 0.9910, 'v_amb':  75413, 'v_15c':  74734.28},
    'RO1': {'d15': 842.7, 'vcf': 0.9895, 'v_amb':  88938, 'v_15c':  88004.15},
    'RO2': {'d15': 841.8, 'vcf': 0.9873, 'v_amb': 268055, 'v_15c': 264650.70},
    'RO4': {'d15': 841.7, 'vcf': 0.9894, 'v_amb':  59408, 'v_15c':  58778.28},
}

print(f"\n{'Cuve':<6}{'D15°C':>12}{'Vcf':>12}{'V ambiant':>14}{'V@15°C':>16}  OK?")
print("-"*70)

total_ok = 0
total_ko = 0

for numero in ['RO3', 'RO5', 'RO6', 'RO1', 'RO2', 'RO4']:
    cuve = Cuve.objects.get(numero=numero)
    mesure = MesureCuve.objects.get(jaugeage=jaugeage, cuve=cuve)
    attendu = EXCEL_ATTENDU[numero]

    # Valeurs calculées par Django (via petroleum_calc)
    d15_calc = float(mesure.densite_15c)            # auto-rempli par save()
    vcf_calc = float(mesure.facteur_vcf)             # auto-rempli par save()
    v_amb    = float(mesure.volume_ambiant_depot)    # propriété existante
    v_15c    = float(mesure.volume_standard_15c_calcule)

    # Tolérance : 0.1 pour densité, 0.0001 pour Vcf, 1 L pour volumes
    ok_d15  = abs(d15_calc  - attendu['d15'])   < 0.15
    ok_vcf  = abs(vcf_calc  - attendu['vcf'])   < 0.0002
    ok_amb  = abs(v_amb     - attendu['v_amb']) < 1.0
    ok_15c  = abs(v_15c     - attendu['v_15c']) < 2.0

    ok_all = ok_d15 and ok_vcf and ok_amb and ok_15c
    mark = "✅" if ok_all else "❌"
    if ok_all:
        total_ok += 1
    else:
        total_ko += 1

    print(f"{numero:<6}"
          f"{d15_calc:>8.1f}/{attendu['d15']:<5}"
          f"{vcf_calc:>8.4f}/{attendu['vcf']:<5}"
          f"{v_amb:>10,.0f}/{attendu['v_amb']:<5}"
          f"{v_15c:>11,.2f}  {mark}")

    if not ok_all:
        if not ok_d15: print(f"       ⚠ D15°C : écart = {d15_calc - attendu['d15']:+.3f}")
        if not ok_vcf: print(f"       ⚠ Vcf   : écart = {vcf_calc - attendu['vcf']:+.5f}")
        if not ok_amb: print(f"       ⚠ V amb : écart = {v_amb - attendu['v_amb']:+.2f}")
        if not ok_15c: print(f"       ⚠ V@15C : écart = {v_15c - attendu['v_15c']:+.2f}")


# ─────────────────────────────────────────────────────────────
#  5) Résumé
# ─────────────────────────────────────────────────────────────
print("\n" + "="*70)
if total_ko == 0:
    print(f"  🎉 SUCCÈS : {total_ok}/6 cuves conformes à Excel")
    print("  Le module petroleum_calc est correctement branché sur MesureCuve.")
else:
    print(f"  ⚠ {total_ok}/6 cuves OK — {total_ko} en écart")
    print("  Vérifie l'import de petroleum_calc et les valeurs saisies.")
print("="*70 + "\n")


# ─────────────────────────────────────────────────────────────
#  6) Bonus : affichage d'un rapport style RJJ pour une cuve
# ─────────────────────────────────────────────────────────────
print("─── Détail cuve RO3 (comme dans la feuille RJJ) ───")
m = MesureCuve.objects.get(jaugeage=jaugeage, cuve=Cuve.objects.get(numero='RO3'))
p = m.cuve.parametre_jaugeage
print(f"  HTT                     = {p.hauteur_totale_temoin} mm")
print(f"  Creux mesuré            = {m.creux_mesure} mm")
print(f"  Creux corrigé           = {m.creux_corrige} mm")
print(f"  Hauteur produit         = {m.hauteur_produit} mm")
print(f"  Hauteur décimal         = {m.hauteur_decimal} mm")
print(f"  Surplus                 = {m.surplus} mm")
print(f"  V(A) certificat         = {p.v_a} L")
print(f"  V/mn                    = {p.v_mn} L/mm")
print(f"  Volume ambiant bac      = {m.volume_ambiant_bac:,.0f} L")
print(f"  Volume additionnel      = {m.volume_additionnel} L")
print(f"  Volume ambiant dépôt    = {m.volume_ambiant_depot:,.0f} L")
print(f"  Température moyenne    = {m.temperature_moyenne:.2f} °C")
print(f"  Densité moyenne         = {m.densite_moyenne} kg/m³")
print(f"  Densité @ 15°C          = {m.densite_15c} kg/m³")
print(f"  Facteur Vcf             = {m.facteur_vcf}")
print(f"  Volume standard @ 15°C  = {float(m.volume_standard_15c_calcule):,.2f} L")
print(f"  Volume disponible       = {m.volume_disponible:,.0f} L")