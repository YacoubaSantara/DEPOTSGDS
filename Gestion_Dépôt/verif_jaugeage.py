"""
verif_jaugeage.py
─────────────────
Vérifie les 6 cuves déjà saisies contre les valeurs Excel.
À lancer APRÈS test_jaugeage.py (les mesures doivent déjà exister).

USAGE :
    python manage.py shell < verif_jaugeage.py
"""

from datetime import date
# ⚠️ Adapte 'monapp' au nom réel de ton application
from SGDS.models import Cuve, MesureCuve, JaugeageJour

EXCEL_ATTENDU = {
    'RO3': {'d15': 751.9, 'vcf': 0.9886, 'v_amb':  61850, 'v_15c':  61144.91},
    'RO5': {'d15': 755.4, 'vcf': 0.9905, 'v_amb':  84264, 'v_15c':  83463.49},
    'RO6': {'d15': 752.2, 'vcf': 0.9910, 'v_amb':  75413, 'v_15c':  74734.28},
    'RO1': {'d15': 842.7, 'vcf': 0.9895, 'v_amb':  88938, 'v_15c':  88004.15},
    'RO2': {'d15': 841.8, 'vcf': 0.9873, 'v_amb': 268055, 'v_15c': 264650.70},
    'RO4': {'d15': 841.7, 'vcf': 0.9894, 'v_amb':  59408, 'v_15c':  58778.28},
}

jaugeage = JaugeageJour.objects.filter(date_jaugeage=date(2026, 1, 31)).first()
if jaugeage is None:
    print("❌ Pas de jaugeage du 31/01/2026 trouvé. Lance test_jaugeage.py d'abord.")
else:
    print(f"\nJaugeage : {jaugeage}\n")
    print(f"{'Cuve':<5} {'D15 calc':>9} {'D15 xls':>9} {'Vcf calc':>10} {'Vcf xls':>10} "
          f"{'Vamb calc':>12} {'Vamb xls':>12} {'V15 calc':>14} {'V15 xls':>14}  OK")
    print("-" * 115)

    total_ok = 0
    for numero in ['RO3', 'RO5', 'RO6', 'RO1', 'RO2', 'RO4']:
        try:
            cuve = Cuve.objects.get(numero=numero)
            m = MesureCuve.objects.get(jaugeage=jaugeage, cuve=cuve)
            att = EXCEL_ATTENDU[numero]

            # Conversion explicite en float pour éviter tout souci Decimal
            d15   = float(m.densite_15c)          if m.densite_15c          is not None else 0.0
            vcf   = float(m.facteur_vcf)           if m.facteur_vcf           is not None else 0.0
            v_amb = float(m.volume_ambiant_depot)  if m.volume_ambiant_depot  is not None else 0.0
            v_15c = float(m.volume_standard_15c_calcule) if m.volume_standard_15c_calcule is not None else 0.0

            ok_d15 = abs(d15   - att['d15'])   < 0.15
            ok_vcf = abs(vcf   - att['vcf'])   < 0.0002
            ok_amb = abs(v_amb - att['v_amb']) < 1.0
            ok_15  = abs(v_15c - att['v_15c']) < 2.0
            ok_all = ok_d15 and ok_vcf and ok_amb and ok_15
            mark = "✅" if ok_all else "❌"
            if ok_all:
                total_ok += 1

            print(f"{numero:<5} "
                  f"{d15:>9.1f} {att['d15']:>9.1f} "
                  f"{vcf:>10.4f} {att['vcf']:>10.4f} "
                  f"{v_amb:>12,.0f} {att['v_amb']:>12,.0f} "
                  f"{v_15c:>14,.2f} {att['v_15c']:>14,.2f}  {mark}")

            if not ok_all:
                if not ok_d15: print(f"       ⚠ D15°C écart = {d15 - att['d15']:+.3f}")
                if not ok_vcf: print(f"       ⚠ Vcf   écart = {vcf - att['vcf']:+.5f}")
                if not ok_amb: print(f"       ⚠ Vamb  écart = {v_amb - att['v_amb']:+.2f}")
                if not ok_15:  print(f"       ⚠ V15°C écart = {v_15c - att['v_15c']:+.2f}")

        except Exception as e:
            print(f"{numero:<5}  ❌ ERREUR : {type(e).__name__}: {e}")

    print("-" * 115)
    print(f"\n  RÉSULTAT : {total_ok}/6 cuves conformes à Excel\n")