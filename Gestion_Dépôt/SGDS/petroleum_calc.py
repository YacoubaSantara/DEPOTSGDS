"""
petroleum_calc.py
─────────────────
Implémentation Python des algorithmes API/ASTM utilisés dans le classeur
Excel RJJ ETAT MENSUEL GESTION AMB 15°C.

Ce module remplace **exactement** les feuilles suivantes :
  - SRO3TRH_15, SRO5TRH_15, …  (Density → Density @ 15°C)
  - SRO3TVCF_15, SRO5TVCF_15, … (Volume Correction Factor → 15°C)
  - La logique combinée (CONV_ADAMA + RJJ) pour calculer volumes/stocks.

Référence : "Generalized products. Correction of observed density to density at
15°C" — Programme de calcul de la correction de masse volumique des produits
pétroliers (Octobre 1995) — J:\\OPS\\TRH_15.XLS / TVCF_15.XLS.

L'algorithme utilise une itération point-fixe (~7 itérations suffisent).
Les formules Excel ont été reproduites trait pour trait (ROUND, TRUNC, MOD...).
"""

from __future__ import annotations
from decimal import Decimal
import math


# ─────────────────────────────────────────────────────────────
#  HELPERS : reproductions exactes des fonctions Excel
# ─────────────────────────────────────────────────────────────
def _round(x: float, n: int) -> float:
    """Excel ROUND(x, n) — half away from zero."""
    if x == 0:
        return 0.0
    factor = 10 ** n
    return math.floor(abs(x) * factor + 0.5) / factor * (1 if x >= 0 else -1)


def _trunc(x: float, n: int = 0) -> float:
    """Excel TRUNC(x, n) — troncature vers zéro."""
    factor = 10 ** n
    return math.trunc(x * factor) / factor


# ─────────────────────────────────────────────────────────────
#  CONSTANTES API pour produits pétroliers généralisés
# ─────────────────────────────────────────────────────────────
# Plage <= 770 kg/m³ (essences légères)   : Ko=346.4228, K1=0.4388
# Plage 770 < ρ < 788 (zone ambiguë)       : itération spéciale I avec A/B
# Plage 788 <= ρ < 839 (gasoil / kérosène) : Ko=594.5418, K1=0
# Plage ρ >= 839 (fuels lourds)            : Ko=186.9696, K1=0.4862

K_SUPER  = (346.4228, 0.4388)   # colonne C : produit léger
K_MIDDLE = (594.5418, 0.0)      # colonne E : produit moyen (gasoil)
K_HEAVY  = (186.9696, 0.4862)   # colonne F : produit lourd
A_AMB, B_AMB = -0.00336312, 2680.3206   # colonne I : 770 < ρ < 788


# ─────────────────────────────────────────────────────────────
#  1) TRH_15 — densité observée → densité à 15 °C
# ─────────────────────────────────────────────────────────────
def density_at_15c(observed_density: float, observed_temperature: float) -> float:
    """
    Reproduit la feuille *TRH_15*.

    :param observed_density:     Densité moyenne mesurée (kg/m³), ex. 742
    :param observed_temperature: Température moyenne sur bac (°C), ex. 26.2
    :return: Densité corrigée à 15°C, arrondie à 1 décimale (kg/m³)
    """
    # Étape 1 — arrondis initiaux (C13, C14)
    rho = _round(observed_density / 5, 1) * 5       # C13
    t   = _round(observed_temperature * 2, 1) / 2   # C14
    delta15 = t - 15                                  # C15

    # Étape 3/4/5 — correction hydromètre + Rho15ini (C16..C18)
    hyc = 1 - _round(0.000023 * delta15, 9) - _round(0.00000002 * delta15 ** 2, 9)
    rho_t = _round(rho * hyc, 2)
    rho15_ini = _trunc(rho_t * 100) / 100   # C18

    # Trois colonnes d'itération calculées en parallèle :
    #   C = produit <=770     (Super)
    #   E = 788 <= Rho < 839  (Gasoil)
    #   F = Rho >= 839        (Lourd)
    #   I = 770 < Rho < 788   (zone ambiguë — démarre à 778.84)
    rho15_c  = _iterate_rho15(rho15_ini, delta15, *K_SUPER)
    rho15_e  = _iterate_rho15(rho15_ini, delta15, *K_MIDDLE)
    rho15_f  = _iterate_rho15(rho15_ini, delta15, *K_HEAVY)
    rho15_i  = _iterate_rho15_ambiguous(rho15_ini, delta15)

    # Formule finale C9 :
    # IF(AND(I48>770.5, I48<787.5), I48,
    #    IF(C48<=770, C48,
    #       IF(E48<839, E48, F48)))
    if 770.5 < rho15_i < 787.5:
        return _round(rho15_i, 1)
    if rho15_c <= 770:
        return _round(rho15_c, 1)
    if rho15_e < 839:
        return _round(rho15_e, 1)
    return _round(rho15_f, 1)


def _iterate_rho15(rho15_ini: float, delta15: float, k0: float, k1: float,
                   n_iter: int = 7) -> float:
    """Itération point-fixe standard (colonnes C/E/F de la feuille)."""
    rho_prev = rho15_ini
    alpha = _round(k0 / rho_prev ** 2 + k1 / rho_prev, 7)
    vcf   = _round(math.exp(-alpha * delta15 - _round(0.8 * (alpha * delta15) ** 2, 9)), 6)
    rho   = _trunc(rho15_ini / vcf * 1000) / 1000
    rho   = _round(rho, 2)

    for _ in range(n_iter - 1):
        if abs(rho_prev - rho) > 0.05:
            alpha = _round(k0 / rho ** 2 + k1 / rho, 7)
        # sinon alpha conservé
        vcf = _round(math.exp(-alpha * delta15 - _round(0.8 * (alpha * delta15) ** 2, 9)), 6)
        rho_prev = rho
        rho = _trunc(rho15_ini / vcf * 1000) / 1000
        rho = _round(rho, 2)
    return rho


def _iterate_rho15_ambiguous(rho15_ini: float, delta15: float,
                              n_iter: int = 7) -> float:
    """Itération pour la zone 770<ρ<788 (colonne I, démarrage à 778.84)."""
    rho = 778.84
    alpha = _round(A_AMB + B_AMB / rho ** 2, 7)
    vcf   = _round(math.exp(-alpha * delta15 - _round(0.8 * (alpha * delta15) ** 2, 9)), 6)
    rho   = _trunc(rho15_ini / vcf * 1000) / 1000
    rho   = _round(rho, 2)

    for _ in range(n_iter - 1):
        alpha = _round(A_AMB + B_AMB / rho ** 2, 7)
        vcf   = _round(math.exp(-alpha * delta15 - _round(0.8 * (alpha * delta15) ** 2, 9)), 6)
        rho   = _trunc(rho15_ini / vcf * 1000) / 1000
        rho   = _round(rho, 2)
    return rho


# ─────────────────────────────────────────────────────────────
#  2) TVCF_15 — Volume Correction Factor vers 15 °C
# ─────────────────────────────────────────────────────────────
def vcf_to_15c(density_at_15c_val: float, observed_temperature: float) -> float:
    """
    Reproduit la feuille *TVCF_15*.

    :param density_at_15c_val:   ρ15 calculée (sortie de density_at_15c)
    :param observed_temperature: Température ambiante observée (°C)
    :return: Vcf arrondi à 4 décimales
    """
    rho15 = _round(density_at_15c_val / 5, 1) * 5         # C12
    t     = _round(observed_temperature * 2, 1) / 2       # C13
    delta15 = t - 15

    # Sélection Ko/K1 selon rho15 (C15..F15 dans Excel)
    if density_at_15c_val > 788:
        if density_at_15c_val > 839:
            k0, k1 = K_HEAVY
        else:
            k0, k1 = K_MIDDLE
    else:
        k0, k1 = K_SUPER

    alpha = _round(k0 / rho15 ** 2 + k1 / rho15, 7)
    vcf   = _round(math.exp(-alpha * delta15 - _round(0.8 * (alpha * delta15) ** 2, 9)), 6)
    return _round(vcf, 4)


# ─────────────────────────────────────────────────────────────
#  3) Calculs CONV_ADAMA / RJJ (volumes bruts et corrigés)
# ─────────────────────────────────────────────────────────────
def calcul_volumes_cuve(
    htt: int,
    creux_mesure: int,
    correction_creux: int,
    v_a: float,
    v_mn: float,
    volume_tuyauterie: float = 0,
    volume_eau: float = 0,
    volume_additionnel: float = 0,
) -> dict:
    """
    Reproduit les formules CONV_ADAMA C38..C50 et RJJ E25..E31.

    :return: dict avec toutes les étapes intermédiaires :
        creux_corrige, hauteur_produit, hauteur_decimal, surplus,
        volume_ambiant_bac, volume_physique, volume_ambiant_depot
    """
    creux_corrige = creux_mesure - correction_creux         # C8/C39
    h_produit     = htt - creux_corrige                      # C40
    h_decimal     = h_produit - (h_produit % 10)             # C41
    surplus       = h_produit - h_decimal                    # C43  (= h_produit % 10)
    v_ambiant_bac = v_a + v_mn * surplus                     # C47

    # RJJ
    v_physique        = v_ambiant_bac + volume_tuyauterie - volume_eau  # E28
    v_ambiant_depot   = v_ambiant_bac + volume_additionnel              # E31 / C50

    return {
        "creux_corrige":       creux_corrige,
        "hauteur_produit":     h_produit,
        "hauteur_decimal":     h_decimal,
        "surplus":             surplus,
        "volume_ambiant_bac":  v_ambiant_bac,
        "volume_physique":     v_physique,
        "volume_ambiant_depot": v_ambiant_depot,
    }


def volume_standard_15c(volume_ambiant_depot: float, vcf: float) -> float:
    """RJJ E41 = volume_ambiant_depot × Vcf."""
    return volume_ambiant_depot * vcf


# ─────────────────────────────────────────────────────────────
#  DEMO / SELF-TEST avec les données du classeur (31 janvier 2026)
# ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    # Cuve RO3 (Super) - valeurs de CONV_ADAMA colonne C
    print("─── Cuve RO3 (SUPER) ───")
    d15 = density_at_15c(observed_density=742, observed_temperature=26.2)
    print(f"  ρ15         = {d15}  kg/m³   (attendu ≈ 737.8)")
    vcf = vcf_to_15c(d15, observed_temperature=24.5)
    print(f"  Vcf         = {vcf}          (attendu ≈ 0.9915)")
    vols = calcul_volumes_cuve(
        htt=12981, creux_mesure=12621, correction_creux=4,
        v_a=60294, v_mn=139, volume_additionnel=1000,
    )
    print(f"  volumes     = {vols}")
    print(f"  V@15°C      = {volume_standard_15c(vols['volume_ambiant_depot'], vcf):,.2f} L")

    # Cuve RO1 (Gasoil)
    print("\n─── Cuve RO1 (GASOIL) ───")
    d15 = density_at_15c(observed_density=834, observed_temperature=27.6)
    print(f"  ρ15         = {d15}")
    vcf = vcf_to_15c(d15, observed_temperature=27.5)
    print(f"  Vcf         = {vcf}")
    vols = calcul_volumes_cuve(
        htt=12942, creux_mesure=12571, correction_creux=4,
        v_a=88058, v_mn=176, volume_additionnel=0,
    )
    print(f"  volumes     = {vols}")
    print(f"  V@15°C      = {volume_standard_15c(vols['volume_ambiant_depot'], vcf):,.2f} L")
