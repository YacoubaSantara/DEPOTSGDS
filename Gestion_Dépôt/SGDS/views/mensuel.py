"""
États mensuels :
  1. Stock Ouverture / Fermeture          → chef_depot_required
  2. Global Mensuel Dépôt                 → login_required (staff)
  3. Global Mensuel RJJ                   → login_required (staff)
  4. Coulage Répartition (admin)          → login_required (staff)
  4b. Coulage Répartition (marketeur)     → marketeur_required
  5. Stock Mensuel Format A (admin + mkt) → login_required / marketeur_required
  6. Stock Mensuel Format B (admin + mkt) → login_required / marketeur_required
  7. Frais de Passage (admin + mkt)       → login_required / marketeur_required
"""

from decimal import Decimal

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required

from SGDS.users.decorators import chef_depot_required
from .client import marketeur_required, _D


_Z  = Decimal('0')
_Q2 = Decimal('0.01')


# ─────────────────────────────────────────────────────────────
#  HELPERS COMMUNS
# ─────────────────────────────────────────────────────────────

def _periodes_disponibles():
    from SGDS.models import PeriodeComptable
    return PeriodeComptable.objects.order_by('-annee', '-mois')


def _get_periode(request):
    """Période sélectionnée via GET ?periode_id=, sinon la plus récente."""
    from SGDS.models import PeriodeComptable
    pid = request.GET.get('periode_id')
    if pid:
        try:
            return PeriodeComptable.objects.get(pk=int(pid))
        except (PeriodeComptable.DoesNotExist, ValueError):
            pass
    return PeriodeComptable.objects.order_by('-annee', '-mois').first()


def _get_marketeur_optionnel(request):
    """Retourne le Marketeur sélectionné via GET ?marketeur=, ou None."""
    from SGDS.models import Marketeur
    mkt_id = request.GET.get('marketeur')
    if mkt_id:
        try:
            return Marketeur.objects.get(pk=int(mkt_id))
        except (Marketeur.DoesNotExist, ValueError):
            pass
    return None


# ═════════════════════════════════════════════════════════════
#  ÉTAT 1 — STOCK OUVERTURE / FERMETURE  (format fichier 06)
# ═════════════════════════════════════════════════════════════

def _calculer_stock_ouverture_fermeture(periode):
    """
    Pour chaque produit actif :
      stock_debut / entrees (SD CC, AC CC, cessions reçues) /
      sorties (livraisons AC, livraisons SD, cessions émises, coulage) /
      stock_fin_comptable / stock_fin_physique (période suivante)
    """
    from SGDS.models import Produit, StockOuverture, Mouvement

    produits   = list(Produit.objects.filter(statut='ACTIF').order_by('nom'))
    mouvements = list(
        Mouvement.objects
        .filter(date_mouvement__range=(periode.date_debut, periode.date_fin))
        .select_related('produit', 'marketeur', 'cession_marketeur_destinataire')
    )

    # Pertes coulage (si clôture disponible)
    coulage_pertes = {}
    cloture = getattr(periode, 'cloture_coulage', None)
    if cloture:
        for cp in cloture.produits_coulage.select_related('produit'):
            coulage_pertes[cp.produit_id] = _D(cp.pertes_gains)

    # Stock fermeture physique = StockOuverture de la période suivante
    periode_suiv        = periode.periode_suivante()
    sf_physique         = {}
    if periode_suiv:
        for so in StockOuverture.objects.filter(periode=periode_suiv).select_related('produit'):
            sf_physique[so.produit_id] = {
                'amb': _D(so.volume_ambiant),
                '15c': _D(so.volume_15c),
            }

    lignes = []
    for produit in produits:
        mvts_p = [m for m in mouvements if m.produit_id == produit.pk]

        # ── Stock ouverture ──
        try:
            so = StockOuverture.objects.get(periode=periode, produit=produit)
            stock_debut_amb = _D(so.volume_ambiant)
            stock_debut_15c = _D(so.volume_15c)
        except StockOuverture.DoesNotExist:
            stock_debut_amb = stock_debut_15c = _Z

        # ── Entrées ──
        rec_sd_amb = rec_sd_15c = rec_ac_amb = rec_ac_15c = _Z
        for m in mvts_p:
            if m.type_mouvement == 'ENTREE':
                v_amb = _D(m.volume_ambiant_recu)
                v_15c = _D(m.volume_15c_recu)
                if m.regime_douanier == 'SOUS_DOUANE':
                    rec_sd_amb += v_amb
                    rec_sd_15c += v_15c
                else:
                    rec_ac_amb += v_amb
                    rec_ac_15c += v_15c

        # Cessions reçues de l'extérieur du dépôt (via QuerySet séparé sur le destinataire).
        # Dans un dépôt unique, les cessions sont des transferts INTERNES entre marketeurs :
        # elles ne modifient pas le stock global → cess_recues = 0 pour éviter le double comptage.
        # (Si votre dépôt reçoit des cessions d'un autre dépôt externe, ajustez ici.)
        cess_recues_amb = _Z
        cess_recues_15c = _Z

        # ── Sorties ──
        livr_ac_amb = livr_ac_15c = livr_sd_amb = livr_sd_15c = _Z
        for m in mvts_p:
            if m.type_mouvement == 'SORTIE':
                v_amb = _D(m.volume_ambiant_sortie)
                v_15c = _D(m.volume_15c_sortie)
                if m.regime_douanier == 'ACQUITTE':
                    livr_ac_amb += v_amb
                    livr_ac_15c += v_15c
                else:
                    livr_sd_amb += v_amb
                    livr_sd_15c += v_15c

        cess_emises_amb = sum(
            _D(m.cession_volume_ambiant) for m in mvts_p
            if m.type_mouvement == 'CESSION'
        )
        cess_emises_15c = sum(
            _D(m.cession_volume_15c) for m in mvts_p
            if m.type_mouvement == 'CESSION'
        )

        # Coulage installation = |perte| sur ce produit
        coul_pg = coulage_pertes.get(produit.pk, _Z)
        coul_install_amb = abs(coul_pg) if coul_pg < _Z else _Z

        # ── Totaux ──
        total_entrees_amb = rec_sd_amb + rec_ac_amb + cess_recues_amb
        total_entrees_15c = rec_sd_15c + rec_ac_15c + cess_recues_15c
        total_sorties_amb = livr_ac_amb + livr_sd_amb + cess_emises_amb + coul_install_amb
        total_sorties_15c = livr_ac_15c + livr_sd_15c + cess_emises_15c

        stock_fin_c_amb = stock_debut_amb + total_entrees_amb - total_sorties_amb
        stock_fin_c_15c = stock_debut_15c + total_entrees_15c - total_sorties_15c

        sf = sf_physique.get(produit.pk, {})
        sf_amb = sf.get('amb')
        sf_15c = sf.get('15c')
        pg_amb = (sf_amb - stock_fin_c_amb) if sf_amb is not None else None

        lignes.append({
            'produit':                 produit,
            'stock_debut_amb':         stock_debut_amb,
            'stock_debut_15c':         stock_debut_15c,
            'rec_sd_amb':              rec_sd_amb,
            'rec_sd_15c':              rec_sd_15c,
            'rec_ac_amb':              rec_ac_amb,
            'rec_ac_15c':              rec_ac_15c,
            'cess_recues_amb':         cess_recues_amb,
            'cess_recues_15c':         cess_recues_15c,
            'total_entrees_amb':       total_entrees_amb,
            'total_entrees_15c':       total_entrees_15c,
            'livr_ac_amb':             livr_ac_amb,
            'livr_ac_15c':             livr_ac_15c,
            'livr_sd_amb':             livr_sd_amb,
            'livr_sd_15c':             livr_sd_15c,
            'cess_emises_amb':         cess_emises_amb,
            'cess_emises_15c':         cess_emises_15c,
            'coul_install_amb':        coul_install_amb,
            'total_sorties_amb':       total_sorties_amb,
            'total_sorties_15c':       total_sorties_15c,
            'stock_fin_comptable_amb': stock_fin_c_amb,
            'stock_fin_comptable_15c': stock_fin_c_15c,
            'stock_fin_physique_amb':  sf_amb,
            'stock_fin_physique_15c':  sf_15c,
            'perte_gain_amb':          pg_amb,
        })

    return lignes


@chef_depot_required
def etat_stock_ouverture_fermeture(request):
    from SGDS.models import Societe, Produit
    periodes       = _periodes_disponibles()
    periode        = _get_periode(request)
    produits       = list(Produit.objects.filter(statut='ACTIF').order_by('nom'))
    produit_id     = request.GET.get('produit_id')
    produit_filtre = None
    if produit_id:
        try:
            produit_filtre = Produit.objects.get(pk=produit_id, statut='ACTIF')
        except Produit.DoesNotExist:
            pass
    lignes_all = _calculer_stock_ouverture_fermeture(periode) if periode else []
    lignes = [l for l in lignes_all
              if produit_filtre is None or l['produit'].pk == produit_filtre.pk]
    societe = Societe.get_instance()
    return render(request, 'Etat/mensuel/stock_ouverture.html', {
        'periodes':       periodes,
        'periode':        periode,
        'lignes':         lignes,
        'societe':        societe,
        'produits':       produits,
        'produit_filtre': produit_filtre,
    })


@chef_depot_required
def etat_stock_fermeture(request):
    from SGDS.models import Societe, Produit
    periodes       = _periodes_disponibles()
    periode        = _get_periode(request)
    produits       = list(Produit.objects.filter(statut='ACTIF').order_by('nom'))
    produit_id     = request.GET.get('produit_id')
    produit_filtre = None
    if produit_id:
        try:
            produit_filtre = Produit.objects.get(pk=produit_id, statut='ACTIF')
        except Produit.DoesNotExist:
            pass
    lignes_all = _calculer_stock_ouverture_fermeture(periode) if periode else []
    lignes = [l for l in lignes_all
              if produit_filtre is None or l['produit'].pk == produit_filtre.pk]
    societe = Societe.get_instance()
    return render(request, 'Etat/mensuel/stock_fermeture.html', {
        'periodes':       periodes,
        'periode':        periode,
        'lignes':         lignes,
        'societe':        societe,
        'produits':       produits,
        'produit_filtre': produit_filtre,
    })


@chef_depot_required
def etat_stock_fermeture_export(request):
    from SGDS.models import Societe
    from django.http import HttpResponse
    periode    = _get_periode(request)
    if not periode:
        messages.warning(request, "Aucune periode disponible.")
        return redirect('etat_mensuel_stock_fermeture')
    lignes_all = _calculer_stock_ouverture_fermeture(periode)
    lignes = [
        {
            'produit':           l['produit'],
            'stk_comptable_amb': l['stock_fin_comptable_amb'],
            'stk_comptable_15c': l['stock_fin_comptable_15c'],
            'stk_physique_amb':  l['stock_fin_physique_amb'],
            'stk_physique_15c':  l['stock_fin_physique_15c'],
            'perte_gain_amb':    l['perte_gain_amb'],
            'total_entrees_amb': l['total_entrees_amb'],
        }
        for l in lignes_all
    ]
    societe = Societe.get_instance()
    contenu = _xlsx_stock_fermeture(periode, lignes, societe)
    nom = f"stock_fermeture_{periode.mois:02d}_{periode.annee}.xlsx"
    response = HttpResponse(
        content=contenu,
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    )
    response['Content-Disposition'] = f'attachment; filename="{nom}"'
    return response


def _xlsx_stock_fermeture(periode, lignes, societe):
    import io, openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment
    wb  = openpyxl.Workbook()
    ws  = wb.active
    ws.title = "Stock Fermeture"
    navy  = PatternFill("solid", fgColor="1B3A6B")
    green = PatternFill("solid", fgColor="16A34A")
    red   = PatternFill("solid", fgColor="DC2626")
    bold  = Font(bold=True)
    white = Font(bold=True, color="FFFFFF")
    row = 1
    if societe:
        ws.cell(row, 1, societe.raison_sociale).font = bold; row += 1
    ws.cell(row, 1, f"Stock Fermeture — {periode}").font = bold; row += 2
    headers = ["Produit", "Stk Comptable AMB (L)", "Stk Comptable 15°C (L)",
               "Stk Physique AMB (L)", "Stk Physique 15°C (L)", "P/G AMB (L)"]
    for c, h in enumerate(headers, 1):
        cell = ws.cell(row, c, h)
        cell.fill = navy; cell.font = white; cell.alignment = Alignment(horizontal='center')
    row += 1
    for l in lignes:
        ws.cell(row, 1, l['produit'].nom)
        ws.cell(row, 2, float(l['stk_comptable_amb'] or 0))
        ws.cell(row, 3, float(l['stk_comptable_15c'] or 0))
        ws.cell(row, 4, float(l['stk_physique_amb']) if l['stk_physique_amb'] is not None else "")
        ws.cell(row, 5, float(l['stk_physique_15c']) if l['stk_physique_15c'] is not None else "")
        pg = l['perte_gain_amb']
        cell = ws.cell(row, 6, float(pg) if pg is not None else "")
        if pg is not None:
            cell.fill = green if pg >= 0 else red
            cell.font = Font(color="FFFFFF")
        row += 1
    buf = io.BytesIO(); wb.save(buf); buf.seek(0)
    return buf.read()


@chef_depot_required
def etat_stock_ouverture_fermeture_export(request):
    from SGDS.models import Societe
    from django.http import HttpResponse
    periode = _get_periode(request)
    if not periode:
        messages.warning(request, "Aucune période disponible.")
        return redirect('etat_mensuel_stock_ouverture')
    lignes  = _calculer_stock_ouverture_fermeture(periode)
    societe = Societe.get_instance()
    contenu = _xlsx_stock_ouverture(periode, lignes, societe)
    nom = f"stock_ouverture_{periode.mois:02d}_{periode.annee}.xlsx"
    response = HttpResponse(
        content=contenu,
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    )
    response['Content-Disposition'] = f'attachment; filename="{nom}"'
    return response


def _xlsx_stock_ouverture(periode, lignes, societe):
    import io
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment
    from openpyxl.utils import get_column_letter

    BLEU_ENT  = PatternFill(fill_type='solid', fgColor='1F4E79')
    BLEU_LG   = PatternFill(fill_type='solid', fgColor='DEEAF1')
    VERT_LG   = PatternFill(fill_type='solid', fgColor='E2EFDA')
    ROUGE_LG  = PatternFill(fill_type='solid', fgColor='FCE4D6')
    JAUNE_LG  = PatternFill(fill_type='solid', fgColor='FFF2CC')
    TITRE_LG  = PatternFill(fill_type='solid', fgColor='BDD7EE')

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = f"Stock {periode.mois:02d}-{periode.annee}"

    ws.merge_cells('A1:C1')
    ws['A1'] = societe.raison_sociale if societe else 'SGDS'
    ws['A1'].font = Font(bold=True, size=14)
    ws['A1'].alignment = Alignment(horizontal='center')

    ws.merge_cells('A2:C2')
    ws['A2'] = f"ÉTAT STOCK OUVERTURE / FERMETURE — {periode}"
    ws['A2'].font = Font(bold=True, size=12)
    ws['A2'].alignment = Alignment(horizontal='center')

    row = 4
    for ci, (h, w) in enumerate(
        [('DÉSIGNATION', 35), ('V AMB (L)', 15), ('V @15°C (L)', 15)], 1
    ):
        c = ws.cell(row=row, column=ci, value=h)
        c.font = Font(bold=True, color='FFFFFF')
        c.fill = BLEU_ENT
        c.alignment = Alignment(horizontal='center')
        ws.column_dimensions[get_column_letter(ci)].width = w
    row += 1

    def _r(label, v_amb, v_15c, fill=None, bold=False):
        nonlocal row
        for ci, val in enumerate([label, v_amb, v_15c], 1):
            c = ws.cell(row=row, column=ci,
                        value=float(val) if isinstance(val, Decimal) else val)
            if fill:
                c.fill = fill
            if bold:
                c.font = Font(bold=True)
            if ci > 1 and isinstance(val, Decimal):
                c.number_format = '#,##0.00'
                c.alignment = Alignment(horizontal='right')
        row += 1

    for ligne in lignes:
        ws.merge_cells(f'A{row}:C{row}')
        t = ws.cell(row=row, column=1, value=f"═══ {ligne['produit'].nom.upper()} ═══")
        t.font = Font(bold=True, size=11, color='1F4E79')
        t.fill = TITRE_LG
        row += 1

        _r('Stock de départ',        ligne['stock_debut_amb'],         ligne['stock_debut_15c'],         BLEU_LG, True)
        _r('  Réceptions SD CC',     ligne['rec_sd_amb'],              ligne['rec_sd_15c'])
        _r('  Réceptions AC CC',     ligne['rec_ac_amb'],              ligne['rec_ac_15c'])
        _r('  Cessions reçues',      ligne['cess_recues_amb'],         ligne['cess_recues_15c'])
        _r('▶ Total Entrées',        ligne['total_entrees_amb'],       ligne['total_entrees_15c'],        VERT_LG, True)
        _r('  Livraisons AC',        ligne['livr_ac_amb'],             ligne['livr_ac_15c'])
        _r('  Livraisons SD',        ligne['livr_sd_amb'],             ligne['livr_sd_15c'])
        _r('  Cessions émises',      ligne['cess_emises_amb'],         ligne['cess_emises_15c'])
        _r('  Coulage installation', ligne['coul_install_amb'],        _Z)
        _r('▶ Total Sorties',        ligne['total_sorties_amb'],       ligne['total_sorties_15c'],        ROUGE_LG, True)
        _r('▶ Stock comptable (fin)',ligne['stock_fin_comptable_amb'], ligne['stock_fin_comptable_15c'],  JAUNE_LG, True)

        if ligne['stock_fin_physique_amb'] is not None:
            _r('▶ Stock physique (jaugeage)', ligne['stock_fin_physique_amb'], ligne['stock_fin_physique_15c'], JAUNE_LG, True)
            pg = ligne['perte_gain_amb']
            _r('  Perte / Gain', pg, _Z,
               ROUGE_LG if (pg is not None and pg < _Z) else VERT_LG, True)
        row += 1

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf.read()


# ═════════════════════════════════════════════════════════════
#  ÉTAT 2 — GLOBAL MENSUEL DÉPÔT
# ═════════════════════════════════════════════════════════════

def _calculer_global_depot(periode, marketeur=None):
    from SGDS.models import Mouvement
    from collections import defaultdict

    qs = (
        Mouvement.objects
        .filter(date_mouvement__range=(periode.date_debut, periode.date_fin))
        .select_related('produit', 'marketeur', 'camion', 'cession_marketeur_destinataire')
        .order_by('type_mouvement', 'date_mouvement', 'pk')
    )
    if marketeur:
        qs = qs.filter(marketeur=marketeur)

    mouvements = list(qs)
    par_type   = defaultdict(list)
    for m in mouvements:
        par_type[m.type_mouvement].append(m)

    # Totaux globaux par produit
    totaux = defaultdict(lambda: {
        'entrees_amb': _Z, 'entrees_15c': _Z,
        'sorties_amb': _Z, 'sorties_15c': _Z,
        'cessions_amb': _Z, 'cessions_15c': _Z,
    })
    for m in mouvements:
        t = totaux[m.produit.nom]
        if m.type_mouvement == 'ENTREE':
            t['entrees_amb'] += _D(m.volume_ambiant_recu)
            t['entrees_15c'] += _D(m.volume_15c_recu)
        elif m.type_mouvement == 'SORTIE':
            t['sorties_amb'] += _D(m.volume_ambiant_sortie)
            t['sorties_15c'] += _D(m.volume_15c_sortie)
        elif m.type_mouvement == 'CESSION':
            t['cessions_amb'] += _D(m.cession_volume_ambiant)
            t['cessions_15c'] += _D(m.cession_volume_15c)

    return {
        'periode':    periode,
        'mouvements': mouvements,
        'par_type':   dict(par_type),
        'totaux':     dict(totaux),
    }


@login_required
def etat_global_mensuel_depot(request):
    from SGDS.models import Societe, Marketeur
    if request.user.is_marketeur_role:
        messages.error(request, "Accès non autorisé.")
        return redirect('client_dashboard')

    periodes    = _periodes_disponibles()
    periode     = _get_periode(request)
    marketeurs  = list(Marketeur.objects.filter(statut='ACTIF').order_by('raison_sociale'))
    marketeur   = _get_marketeur_optionnel(request)
    rapport     = _calculer_global_depot(periode, marketeur) if periode else {}
    societe     = Societe.get_instance()

    return render(request, 'Etat/mensuel/global_depot.html', {
        'periodes':      periodes,
        'periode':       periode,
        'rapport':       rapport,
        'marketeurs':    marketeurs,
        'marketeur_sel': marketeur,
        'societe':       societe,
    })


@login_required
def etat_global_mensuel_depot_export(request):
    from SGDS.models import Societe
    from django.http import HttpResponse
    if request.user.is_marketeur_role:
        return redirect('client_dashboard')

    periode  = _get_periode(request)
    if not periode:
        messages.warning(request, "Aucune période disponible.")
        return redirect('etat_mensuel_global_depot')

    marketeur = _get_marketeur_optionnel(request)
    rapport   = _calculer_global_depot(periode, marketeur)
    societe   = Societe.get_instance()
    contenu   = _xlsx_global_depot(rapport, societe)

    suffix = f"_{marketeur.sigle or 'mkt'}" if marketeur else "_TOUS"
    nom = f"global_depot_{periode.mois:02d}_{periode.annee}{suffix}.xlsx"
    response = HttpResponse(
        content=contenu,
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    )
    response['Content-Disposition'] = f'attachment; filename="{nom}"'
    return response


def _xlsx_global_depot(rapport, societe):
    import io, openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment
    from openpyxl.utils import get_column_letter

    periode = rapport.get('periode')
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Global Dépôt"

    ws.merge_cells('A1:J1')
    ws['A1'] = societe.raison_sociale if societe else 'SGDS'
    ws['A1'].font = Font(bold=True, size=14)
    ws['A1'].alignment = Alignment(horizontal='center')

    ws.merge_cells('A2:J2')
    ws['A2'] = f"ÉTAT GLOBAL MENSUEL DÉPÔT — {periode}"
    ws['A2'].font = Font(bold=True, size=12)
    ws['A2'].alignment = Alignment(horizontal='center')

    BLEU  = PatternFill(fill_type='solid', fgColor='1F4E79')
    BLEU2 = PatternFill(fill_type='solid', fgColor='2E75B6')
    COLS  = ['Date', 'N°Enreg.', 'Marketeur', 'Régime', 'Produit',
             'Libellé', 'V Amb (L)', 'V @15°C (L)', 'Mode règl.', 'Notes']
    WIDTHS = [12, 18, 22, 8, 14, 28, 14, 14, 14, 25]

    TYPES_LABELS = {
        'ENTREE': 'ENTRÉES',
        'SORTIE': 'SORTIES',
        'CESSION': 'CESSIONS',
        'ACQUITTEMENT': 'ACQUITTEMENTS',
    }

    row = 4
    par_type = rapport.get('par_type', {})

    for type_key, label in TYPES_LABELS.items():
        mvts = par_type.get(type_key, [])
        if not mvts:
            continue

        ws.merge_cells(f'A{row}:J{row}')
        c = ws.cell(row=row, column=1, value=f"── {label} ({len(mvts)}) ──")
        c.font = Font(bold=True, color='FFFFFF', size=11)
        c.fill = BLEU
        row += 1

        for ci, (h, w) in enumerate(zip(COLS, WIDTHS), 1):
            c = ws.cell(row=row, column=ci, value=h)
            c.font = Font(bold=True, color='FFFFFF')
            c.fill = BLEU2
            c.alignment = Alignment(horizontal='center')
            ws.column_dimensions[get_column_letter(ci)].width = w
        row += 1

        for i, m in enumerate(mvts):
            # Libellé
            if type_key == 'ENTREE':
                libelle = m.provenance or ''
            elif type_key == 'SORTIE':
                libelle = m.destination or m.code_destination or 'BON DE SORTIE'
            elif type_key == 'CESSION':
                dest = m.cession_marketeur_destinataire
                libelle = f"→ {dest.sigle or dest.raison_sociale}" if dest else ''
            else:
                libelle = 'Acquittement douanier'

            if type_key == 'ENTREE':
                v_amb, v_15c = m.volume_ambiant_recu, m.volume_15c_recu
            elif type_key == 'SORTIE':
                v_amb, v_15c = m.volume_ambiant_sortie, m.volume_15c_sortie
            elif type_key == 'CESSION':
                v_amb, v_15c = m.cession_volume_ambiant, m.cession_volume_15c
            else:
                v_amb, v_15c = None, None

            vals = [
                str(m.date_mouvement),
                m.numero_enregistrement or '',
                str(m.marketeur),
                'SD' if m.regime_douanier == 'SOUS_DOUANE' else 'AC',
                m.produit.nom,
                libelle,
                float(_D(v_amb)) if v_amb else '',
                float(_D(v_15c)) if v_15c else '',
                m.mode_reglement or '',
                m.notes or '',
            ]
            fill = PatternFill(fill_type='solid', fgColor='EBF3FB') if i % 2 == 0 else None
            for ci, v in enumerate(vals, 1):
                c = ws.cell(row=row, column=ci, value=v)
                if fill:
                    c.fill = fill
                if isinstance(v, float):
                    c.number_format = '#,##0.00'
                    c.alignment = Alignment(horizontal='right')
            row += 1

        row += 1

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf.read()


# ═════════════════════════════════════════════════════════════
#  ÉTAT 3 — GLOBAL MENSUEL RJJ
# ═════════════════════════════════════════════════════════════

def _calculer_rjj(periode, cuve_id=None):
    from SGDS.models import JaugeageJour, Cuve

    qs = (
        JaugeageJour.objects
        .filter(date_jaugeage__range=(periode.date_debut, periode.date_fin))
        .prefetch_related('mesures__cuve__parametre_jaugeage')
        .order_by('date_jaugeage', 'heure_jaugeage')
    )
    jaugeages = list(qs)
    cuves     = list(Cuve.objects.filter(parametre_jaugeage__isnull=False)
                     .select_related('produit', 'parametre_jaugeage')
                     .order_by('numero'))
    if cuve_id:
        cuves = [c for c in cuves if c.pk == int(cuve_id)]

    lignes = []
    for j in jaugeages:
        mesures_dict = {m.cuve_id: m for m in j.mesures.all()}
        for cuve in cuves:
            m = mesures_dict.get(cuve.pk)
            if not m:
                continue
            lignes.append({
                'jaugeage_pk':     j.pk,
                'date':            j.date_jaugeage,
                'type_jaugeage':   j.get_type_jaugeage_display(),
                'heure':           j.heure_jaugeage,
                'est_valide':      j.est_valide,
                'cuve_numero':     cuve.numero,
                'produit_nom':     cuve.produit.nom if cuve.produit else '—',
                'creux':           m.creux_mesure,
                'creux_corrige':   m.creux_corrige,
                'hauteur_produit': m.hauteur_produit,
                't1':              m.t1,
                't2':              m.t2,
                't3':              m.t3,
                'temp_moy':        m.temperature_moyenne,
                'temp_obs':        m.temperature_obs,
                'densite_moy':     m.densite_moyenne,
                'densite_15c':     m.densite_15c,
                'facteur_vcf':     m.facteur_vcf,
                'v_amb_bac':       m.volume_ambiant_bac,
                'v_amb_depot':     m.volume_ambiant_depot,
                'v_15c':           m.volume_standard_15c,
                'v_disponible':    m.volume_disponible,
            })
    return {
        'periode':   periode,
        'jaugeages': jaugeages,
        'cuves':     cuves,
        'lignes':    lignes,
    }


@login_required
def etat_global_mensuel_rjj(request):
    from SGDS.models import Societe, Cuve
    if request.user.is_marketeur_role:
        messages.error(request, "Accès non autorisé.")
        return redirect('client_dashboard')

    periodes  = _periodes_disponibles()
    periode   = _get_periode(request)
    cuves     = list(Cuve.objects.filter(parametre_jaugeage__isnull=False).order_by('numero'))
    cuve_id   = request.GET.get('cuve')
    rapport   = _calculer_rjj(periode, cuve_id) if periode else {'lignes': [], 'cuves': []}
    societe   = Societe.get_instance()

    return render(request, 'Etat/mensuel/rjj.html', {
        'periodes': periodes,
        'periode':  periode,
        'rapport':  rapport,
        'cuves':    cuves,
        'cuve_sel': cuve_id,
        'societe':  societe,
    })


@login_required
def etat_global_mensuel_rjj_export(request):
    from SGDS.models import Societe
    from django.http import HttpResponse
    if request.user.is_marketeur_role:
        return redirect('client_dashboard')

    periode = _get_periode(request)
    if not periode:
        messages.warning(request, "Aucune période disponible.")
        return redirect('etat_mensuel_rjj')

    cuve_id = request.GET.get('cuve')
    rapport = _calculer_rjj(periode, cuve_id)
    societe = Societe.get_instance()
    contenu = _xlsx_rjj(rapport, societe)

    nom = f"rjj_{periode.mois:02d}_{periode.annee}.xlsx"
    response = HttpResponse(
        content=contenu,
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    )
    response['Content-Disposition'] = f'attachment; filename="{nom}"'
    return response


def _xlsx_rjj(rapport, societe):
    import io, openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment
    from openpyxl.utils import get_column_letter

    periode = rapport.get('periode')
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "RJJ"

    COLS   = ['Date', 'Type', 'Cuve', 'Produit', 'Creux', 'Creux corr.',
              'H.Produit', 'T1', 'T2', 'T3', 'T°Moy', 'T°Obs',
              'D.Moy', 'D15°C', 'VCF',
              'V Amb Bac', 'V Amb Dépôt', 'V @15°C', 'V Dispo']
    WIDTHS = [12, 8, 8, 12, 9, 10, 10, 7, 7, 7, 8, 8, 8, 8, 8, 13, 14, 12, 12]

    ws.merge_cells(f'A1:{get_column_letter(len(COLS))}1')
    ws['A1'] = societe.raison_sociale if societe else 'SGDS'
    ws['A1'].font = Font(bold=True, size=14)
    ws['A1'].alignment = Alignment(horizontal='center')

    ws.merge_cells(f'A2:{get_column_letter(len(COLS))}2')
    ws['A2'] = f"RELEVÉ JOURNALIER DE JAUGEAGE (RJJ) — {periode}"
    ws['A2'].font = Font(bold=True, size=12)
    ws['A2'].alignment = Alignment(horizontal='center')

    BLEU = PatternFill(fill_type='solid', fgColor='1F4E79')
    row = 4
    for ci, (h, w) in enumerate(zip(COLS, WIDTHS), 1):
        c = ws.cell(row=row, column=ci, value=h)
        c.font = Font(bold=True, color='FFFFFF')
        c.fill = BLEU
        c.alignment = Alignment(horizontal='center', wrap_text=True)
        ws.column_dimensions[get_column_letter(ci)].width = w
    ws.row_dimensions[row].height = 28
    row += 1

    def _f(v):
        return float(v) if v is not None else ''

    for l in rapport.get('lignes', []):
        ws.cell(row=row, column=1,  value=str(l['date']))
        ws.cell(row=row, column=2,  value=l['type_jaugeage'])
        ws.cell(row=row, column=3,  value=l['cuve_numero'])
        ws.cell(row=row, column=4,  value=l['produit_nom'])
        ws.cell(row=row, column=5,  value=l['creux'])
        ws.cell(row=row, column=6,  value=l['creux_corrige'])
        ws.cell(row=row, column=7,  value=l['hauteur_produit'])
        ws.cell(row=row, column=8,  value=_f(l['t1']))
        ws.cell(row=row, column=9,  value=_f(l['t2']))
        ws.cell(row=row, column=10, value=_f(l['t3']))
        ws.cell(row=row, column=11, value=_f(l['temp_moy']))
        ws.cell(row=row, column=12, value=_f(l['temp_obs']))
        ws.cell(row=row, column=13, value=_f(l['densite_moy']))
        ws.cell(row=row, column=14, value=_f(l['densite_15c']))
        ws.cell(row=row, column=15, value=_f(l['facteur_vcf']))
        for ci, key in enumerate(['v_amb_bac', 'v_amb_depot', 'v_15c', 'v_disponible'], 16):
            c = ws.cell(row=row, column=ci, value=_f(l[key]))
            if isinstance(c.value, float):
                c.number_format = '#,##0.00'
                c.alignment = Alignment(horizontal='right')
        row += 1

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf.read()


# ═════════════════════════════════════════════════════════════
#  ÉTAT 4 — COULAGE RÉPARTITION  (admin + marketeur)
# ═════════════════════════════════════════════════════════════

def _rapport_coulage_pour_periode(periode):
    """Retourne (rapport_dict, source_str) — snapshot si clôturé, temps réel sinon."""
    from SGDS.services.coulage_repartition import calculer_repartition_coulage
    if periode.statut == 'CLOTUREE' and hasattr(periode, 'cloture_coulage'):
        from SGDS.views.coulage import RepartitionCoulageView
        vue = RepartitionCoulageView()
        return vue._rapport_depuis_snapshot(periode.cloture_coulage), 'SNAPSHOT'
    return calculer_repartition_coulage(periode), 'TEMPS_REEL'


@login_required
def etat_coulage_repartition(request):
    from SGDS.models import Societe
    if request.user.is_marketeur_role:
        messages.error(request, "Accès non autorisé.")
        return redirect('client_dashboard')

    periodes = _periodes_disponibles()
    periode  = _get_periode(request)
    societe  = Societe.get_instance()
    rapport  = source = erreur = None

    if periode:
        cloture_dispo = (periode.statut == 'CLOTUREE') or hasattr(periode, 'cloture_coulage')
        if cloture_dispo:
            rapport, source = _rapport_coulage_pour_periode(periode)
        else:
            erreur = "La période n'est pas encore clôturée — coulage répartition indisponible."

    return render(request, 'Etat/mensuel/coulage_repartition.html', {
        'periodes': periodes,
        'periode':  periode,
        'rapport':  rapport,
        'source':   source,
        'erreur':   erreur,
        'societe':  societe,
    })


@login_required
def etat_coulage_repartition_export(request):
    from SGDS.models import Societe
    from django.http import HttpResponse
    if request.user.is_marketeur_role:
        return redirect('client_dashboard')

    periode = _get_periode(request)
    if not periode:
        messages.warning(request, "Aucune période disponible.")
        return redirect('etat_mensuel_coulage_repartition')

    if not (periode.statut == 'CLOTUREE' or hasattr(periode, 'cloture_coulage')):
        messages.warning(request, "Période non clôturée.")
        return redirect('etat_mensuel_coulage_repartition')

    rapport, _ = _rapport_coulage_pour_periode(periode)
    societe = Societe.get_instance()
    contenu = _xlsx_coulage_repartition(rapport, societe)

    nom = f"coulage_repartition_{periode.mois:02d}_{periode.annee}.xlsx"
    response = HttpResponse(
        content=contenu,
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    )
    response['Content-Disposition'] = f'attachment; filename="{nom}"'
    return response


@marketeur_required
def etat_coulage_repartition_marketeur(request):
    from SGDS.models import Societe
    periodes = _periodes_disponibles()
    periode  = _get_periode(request)
    societe  = Societe.get_instance()
    mkt      = request.user.marketeur
    rapport  = source = erreur = None

    if periode:
        cloture_dispo = (periode.statut == 'CLOTUREE') or hasattr(periode, 'cloture_coulage')
        if cloture_dispo:
            rapport_complet, source = _rapport_coulage_pour_periode(periode)
            lignes_mkt = [
                l for l in rapport_complet.get('lignes', [])
                if l['marketeur'].pk == mkt.pk
            ]
            rapport = {**rapport_complet, 'lignes': lignes_mkt}
        else:
            erreur = "La période n'est pas encore clôturée — coulage répartition indisponible."

    return render(request, 'Espace_Marketeur/mensuel/coulage_repartition.html', {
        'periodes': periodes,
        'periode':  periode,
        'rapport':  rapport,
        'source':   source,
        'erreur':   erreur,
        'societe':  societe,
        'marketeur': mkt,
    })


@marketeur_required
def etat_coulage_repartition_marketeur_export(request):
    from SGDS.models import Societe
    from django.http import HttpResponse

    periode = _get_periode(request)
    if not periode:
        return redirect('client_mensuel_coulage_repartition')
    if not (periode.statut == 'CLOTUREE' or hasattr(periode, 'cloture_coulage')):
        messages.warning(request, "Période non clôturée.")
        return redirect('client_mensuel_coulage_repartition')

    mkt = request.user.marketeur
    rapport_complet, _ = _rapport_coulage_pour_periode(periode)
    lignes_mkt = [l for l in rapport_complet.get('lignes', []) if l['marketeur'].pk == mkt.pk]
    rapport    = {**rapport_complet, 'lignes': lignes_mkt}
    societe    = Societe.get_instance()
    contenu    = _xlsx_coulage_repartition(rapport, societe, marketeur_filtre=mkt)

    nom = f"coulage_repartition_{mkt.sigle or 'mkt'}_{periode.mois:02d}_{periode.annee}.xlsx"
    response = HttpResponse(
        content=contenu,
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    )
    response['Content-Disposition'] = f'attachment; filename="{nom}"'
    return response


def _xlsx_coulage_repartition(rapport, societe, marketeur_filtre=None):
    import io, openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment
    from openpyxl.utils import get_column_letter

    if not rapport:
        buf = io.BytesIO()
        openpyxl.Workbook().save(buf)
        buf.seek(0)
        return buf.read()

    periode  = rapport.get('periode')
    produits = rapport.get('produits', [])
    lignes   = rapport.get('lignes', [])
    totaux   = rapport.get('totaux', {})

    FIELDS  = ['brut_entree', 'coul_entree', 'entree_nette', 'sortie',
               'base_qp_coul', 'coef_qp_coul', 'qp_coul', 'volume_sorti']
    SHDR    = ['Brut Entrée', 'Coul.Entrée', 'Entrée Nette', 'Sortie',
               'Base QP', 'Coef QP', 'QP Coul.', 'Vol.Sorti']

    n_cols    = 1 + len(produits) * len(FIELDS)
    last_col  = get_column_letter(n_cols)

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Coulage Répartition"

    ws.merge_cells(f'A1:{last_col}1')
    ws['A1'] = societe.raison_sociale if societe else 'SGDS'
    ws['A1'].font = Font(bold=True, size=14)
    ws['A1'].alignment = Alignment(horizontal='center')

    ws.merge_cells(f'A2:{last_col}2')
    suffix_mkt = (f" — {marketeur_filtre.sigle or marketeur_filtre.raison_sociale}"
                  if marketeur_filtre else "")
    ws['A2'] = f"COULAGE RÉPARTITION — {periode}{suffix_mkt}"
    ws['A2'].font = Font(bold=True, size=12)
    ws['A2'].alignment = Alignment(horizontal='center')

    BLEU  = PatternFill(fill_type='solid', fgColor='1F4E79')
    BLEU2 = PatternFill(fill_type='solid', fgColor='2E75B6')
    VERT  = PatternFill(fill_type='solid', fgColor='E2EFDA')
    ZEBRA = PatternFill(fill_type='solid', fgColor='EBF3FB')

    row = 4
    # En-tête produits (rang 1)
    c = ws.cell(row=row, column=1, value='Marketeur')
    c.font = Font(bold=True, color='FFFFFF')
    c.fill = BLEU
    ws.column_dimensions['A'].width = 22

    prod_col_start = {}
    col = 2
    for p in produits:
        prod_col_start[p.pk] = col
        end_col = col + len(FIELDS) - 1
        ws.merge_cells(start_row=row, start_column=col, end_row=row, end_column=end_col)
        c = ws.cell(row=row, column=col, value=p.nom.upper())
        c.font = Font(bold=True, color='FFFFFF')
        c.fill = BLEU
        c.alignment = Alignment(horizontal='center')
        col += len(FIELDS)
    row += 1

    # Sous-colonnes (rang 2)
    ws.cell(row=row, column=1).fill = BLEU2
    col = 2
    for p in produits:
        for sh in SHDR:
            c = ws.cell(row=row, column=col, value=sh)
            c.font = Font(bold=True, color='FFFFFF', size=8)
            c.fill = BLEU2
            c.alignment = Alignment(horizontal='center', wrap_text=True)
            ws.column_dimensions[get_column_letter(col)].width = 13
            col += 1
    ws.row_dimensions[row].height = 28
    row += 1

    def _f(v):
        return float(v) if v is not None else 0.0

    for i, ligne in enumerate(lignes):
        mkt = ligne['marketeur']
        c = ws.cell(row=row, column=1, value=mkt.sigle or mkt.raison_sociale)
        if i % 2 == 0:
            c.fill = ZEBRA
        for p in produits:
            pp   = ligne.get('par_produit', {}).get(p.pk, {})
            col  = prod_col_start[p.pk]
            for fi, field in enumerate(FIELDS):
                cell = ws.cell(row=row, column=col+fi, value=_f(pp.get(field)))
                cell.number_format = '#,##0.00' if field != 'coef_qp_coul' else '0.000000'
                cell.alignment = Alignment(horizontal='right')
                if i % 2 == 0:
                    cell.fill = ZEBRA
        row += 1

    # Totaux
    c = ws.cell(row=row, column=1, value='TOTAUX')
    c.font = Font(bold=True)
    c.fill = VERT
    for p in produits:
        tp  = totaux.get('par_produit', {}).get(p.pk, {})
        col = prod_col_start[p.pk]
        for fi, field in enumerate(FIELDS):
            cell = ws.cell(row=row, column=col+fi, value=_f(tp.get(field)))
            cell.font = Font(bold=True)
            cell.fill = VERT
            cell.number_format = '#,##0.00' if field != 'coef_qp_coul' else '0.000000'
            cell.alignment = Alignment(horizontal='right')

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf.read()


# ═════════════════════════════════════════════════════════════
#  ÉTAT 5 — STOCK MENSUEL FORMAT A  (admin + marketeur)
# ═════════════════════════════════════════════════════════════

def _calculer_stock_mensuel_a(periode, marketeur=None):
    """
    Par produit × marketeur :
      Stock Départ, Récept SD/AC (AMB+15C), Perte/Gain réception,
      Total Entrées Nettes, Sorties, Stock Comptable,
      P/G Physique, Ratio, Stock Fermeture.
    Quand marketeur=None → mode TM (tous marketeurs).
    """
    from SGDS.models import Produit, StockOuverture, Mouvement, Marketeur as MktModel

    produits = list(Produit.objects.filter(statut='ACTIF').order_by('nom'))

    if marketeur:
        marketeurs = [marketeur]
    else:
        mkt_ids = (
            Mouvement.objects
            .filter(date_mouvement__range=(periode.date_debut, periode.date_fin))
            .values_list('marketeur_id', flat=True).distinct()
        )
        marketeurs = list(MktModel.objects.filter(pk__in=mkt_ids).order_by('raison_sociale'))

    periode_suiv = periode.periode_suivante()
    sf_physique  = {}
    if periode_suiv:
        for so in StockOuverture.objects.filter(periode=periode_suiv).select_related('produit'):
            sf_physique[so.produit_id] = {
                'amb': _D(so.volume_ambiant),
                '15c': _D(so.volume_15c),
            }

    lignes_par_produit = {}
    for produit in produits:
        lignes_mkt = []
        tot = {k: _Z for k in [
            'stock_debut_amb', 'stock_debut_15c',
            'rec_sd_amb', 'rec_sd_15c', 'rec_ac_amb', 'rec_ac_15c',
            'pg_rec_amb', 'pg_rec_15c',
            'entrees_nettes_amb', 'entrees_nettes_15c',
            'sorties_amb', 'sorties_15c',
            'stock_comptable_amb', 'stock_comptable_15c',
        ]}

        for mkt in marketeurs:
            mvts = list(
                Mouvement.objects.filter(
                    produit=produit, marketeur=mkt,
                    date_mouvement__range=(periode.date_debut, periode.date_fin),
                )
            )

            # Stock départ — mode TM : 0 par ligne marketeur (total = StockOuverture dépôt, fixé après la boucle)
            # mode par marketeur : cumul historique (mouvements + inventaire initial + cessions)
            if not marketeur:
                # En mode TM on n'affecte pas le stock de départ ici, il sera calculé au niveau totaux
                sd_amb = sd_15c = _Z
            else:
                from SGDS.models import InventaireInitialMarketeur
                from django.db.models import Sum as _Sum
                # Mouvements antérieurs à la période (ENTREE, SORTIE, CESSION émise)
                mvts_avant = list(Mouvement.objects.filter(
                    produit=produit, marketeur=mkt,
                    date_mouvement__lt=periode.date_debut,
                ))
                sd_amb = sum(
                    (_D(m.volume_ambiant_recu)       if m.type_mouvement == 'ENTREE'  else
                     -_D(m.volume_ambiant_sortie)    if m.type_mouvement == 'SORTIE'  else
                     -_D(m.cession_volume_ambiant)   if m.type_mouvement == 'CESSION' else _Z)
                    for m in mvts_avant
                )
                sd_15c = sum(
                    (_D(m.volume_15c_recu)       if m.type_mouvement == 'ENTREE'  else
                     -_D(m.volume_15c_sortie)    if m.type_mouvement == 'SORTIE'  else
                     -_D(m.cession_volume_15c)   if m.type_mouvement == 'CESSION' else _Z)
                    for m in mvts_avant
                )
                # Cessions REÇUES par ce marketeur avant la période
                cess_recues_avant = Mouvement.objects.filter(
                    produit=produit,
                    type_mouvement='CESSION',
                    cession_marketeur_destinataire=mkt,
                    date_mouvement__lt=periode.date_debut,
                )
                for m in cess_recues_avant:
                    sd_amb += _D(m.cession_volume_ambiant)
                    sd_15c += _D(m.cession_volume_15c)
                # Ajouter l'inventaire initial du marketeur pour ce produit
                inv_agg = (
                    InventaireInitialMarketeur.objects
                    .filter(marketeur=mkt, produit=produit)
                    .aggregate(v_amb=_Sum('volume_ambiant'), v_15c=_Sum('volume_15c'))
                )
                sd_amb += _D(inv_agg['v_amb'] or 0)
                sd_15c += _D(inv_agg['v_15c'] or 0)

            rec_sd_amb = rec_sd_15c = rec_ac_amb = rec_ac_15c = _Z
            pg_amb = pg_15c = _Z

            for m in mvts:
                if m.type_mouvement == 'ENTREE':
                    v_amb = _D(m.volume_ambiant_recu)
                    v_15c = _D(m.volume_15c_recu)
                    if m.regime_douanier == 'SOUS_DOUANE':
                        rec_sd_amb += v_amb
                        rec_sd_15c += v_15c
                    else:
                        rec_ac_amb += v_amb
                        rec_ac_15c += v_15c
                    pg_amb += _D(m.perte_gain_reception)
                    pg_15c += _D(m.perte_gain_15c)

            tot_rec_amb = rec_sd_amb + rec_ac_amb
            tot_rec_15c = rec_sd_15c + rec_ac_15c
            en_nettes_amb = tot_rec_amb + pg_amb
            en_nettes_15c = tot_rec_15c + pg_15c

            sor_amb = sum(_D(m.volume_ambiant_sortie) for m in mvts if m.type_mouvement == 'SORTIE')
            sor_15c = sum(_D(m.volume_15c_sortie)     for m in mvts if m.type_mouvement == 'SORTIE')

            stk_c_amb = sd_amb + en_nettes_amb - sor_amb
            stk_c_15c = sd_15c + en_nettes_15c - sor_15c

            ligne = {
                'marketeur':          mkt,
                'stock_debut_amb':    sd_amb,
                'stock_debut_15c':    sd_15c,
                'rec_sd_amb':         rec_sd_amb,
                'rec_sd_15c':         rec_sd_15c,
                'rec_ac_amb':         rec_ac_amb,
                'rec_ac_15c':         rec_ac_15c,
                'pg_rec_amb':         pg_amb,
                'pg_rec_15c':         pg_15c,
                'entrees_nettes_amb': en_nettes_amb,
                'entrees_nettes_15c': en_nettes_15c,
                'sorties_amb':        sor_amb,
                'sorties_15c':        sor_15c,
                'stock_comptable_amb': stk_c_amb,
                'stock_comptable_15c': stk_c_15c,
            }
            lignes_mkt.append(ligne)

            for k in tot.keys():
                tot[k] += ligne.get(k, _Z)

        # En mode TM : le stock de départ total = StockOuverture global du dépôt
        if not marketeur:
            try:
                so_global = StockOuverture.objects.get(periode=periode, produit=produit)
                tot['stock_debut_amb'] = _D(so_global.volume_ambiant)
                tot['stock_debut_15c'] = _D(so_global.volume_15c)
            except StockOuverture.DoesNotExist:
                pass  # reste à 0

        sf      = sf_physique.get(produit.pk, {})
        sf_amb  = sf.get('amb')
        sf_15c  = sf.get('15c')
        # Stock comptable total = stock départ + entrées nettes - sorties
        tot['stock_comptable_amb'] = tot['stock_debut_amb'] + tot['entrees_nettes_amb'] - tot['sorties_amb']
        tot['stock_comptable_15c'] = tot['stock_debut_15c'] + tot['entrees_nettes_15c'] - tot['sorties_15c']
        pg_phys = (sf_amb - tot['stock_comptable_amb']) if sf_amb is not None else None
        ratio   = ((pg_phys / tot['entrees_nettes_amb'] * 100)
                   if pg_phys is not None and tot['entrees_nettes_amb'] else None)

        lignes_par_produit[produit.pk] = {
            'produit':    produit,
            'lignes':     lignes_mkt,
            'totaux':     tot,
            'sf_amb':     sf_amb,
            'sf_15c':     sf_15c,
            'pg_phys_amb': pg_phys,
            'ratio':       ratio,
        }

    return {
        'periode':             periode,
        'produits':            produits,
        'marketeurs':          marketeurs,
        'lignes_par_produit':  lignes_par_produit,
        'is_tm':               marketeur is None,
    }


@login_required
def etat_stock_mensuel_a(request):
    from SGDS.models import Societe, Marketeur as MktModel
    if request.user.is_marketeur_role:
        messages.error(request, "Accès non autorisé.")
        return redirect('client_dashboard')

    periodes   = _periodes_disponibles()
    periode    = _get_periode(request)
    marketeurs = list(MktModel.objects.filter(statut='ACTIF').order_by('raison_sociale'))
    marketeur  = _get_marketeur_optionnel(request)
    rapport    = _calculer_stock_mensuel_a(periode, marketeur) if periode else {}
    societe    = Societe.get_instance()

    return render(request, 'Etat/mensuel/stock_mensuel_a.html', {
        'periodes':      periodes,
        'periode':       periode,
        'rapport':       rapport,
        'marketeurs':    marketeurs,
        'marketeur_sel': marketeur,
        'societe':       societe,
    })


@login_required
def etat_stock_mensuel_a_export(request):
    from SGDS.models import Societe
    from django.http import HttpResponse
    if request.user.is_marketeur_role:
        return redirect('client_dashboard')

    periode   = _get_periode(request)
    if not periode:
        messages.warning(request, "Aucune période disponible.")
        return redirect('etat_mensuel_stock_a')
    marketeur = _get_marketeur_optionnel(request)
    rapport   = _calculer_stock_mensuel_a(periode, marketeur)
    societe   = Societe.get_instance()
    contenu   = _xlsx_stock_mensuel_a(rapport, societe)

    suffix = f"_{marketeur.sigle or 'mkt'}" if marketeur else "_TM"
    nom = f"stock_mensuel_A_{periode.mois:02d}_{periode.annee}{suffix}.xlsx"
    response = HttpResponse(
        content=contenu,
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    )
    response['Content-Disposition'] = f'attachment; filename="{nom}"'
    return response


@marketeur_required
def etat_stock_mensuel_a_marketeur(request):
    from SGDS.models import Societe
    periodes = _periodes_disponibles()
    periode  = _get_periode(request)
    mkt      = request.user.marketeur
    rapport  = _calculer_stock_mensuel_a(periode, mkt) if periode else {}
    societe  = Societe.get_instance()

    return render(request, 'Espace_Marketeur/mensuel/stock_mensuel_a.html', {
        'periodes':  periodes,
        'periode':   periode,
        'rapport':   rapport,
        'societe':   societe,
        'marketeur': mkt,
    })


@marketeur_required
def etat_stock_mensuel_a_marketeur_export(request):
    from SGDS.models import Societe
    from django.http import HttpResponse
    periode = _get_periode(request)
    if not periode:
        return redirect('client_mensuel_stock_a')
    mkt     = request.user.marketeur
    rapport = _calculer_stock_mensuel_a(periode, mkt)
    societe = Societe.get_instance()
    contenu = _xlsx_stock_mensuel_a(rapport, societe)

    nom = f"stock_mensuel_A_{mkt.sigle or 'mkt'}_{periode.mois:02d}_{periode.annee}.xlsx"
    response = HttpResponse(
        content=contenu,
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    )
    response['Content-Disposition'] = f'attachment; filename="{nom}"'
    return response


def _xlsx_stock_mensuel_a(rapport, societe):
    import io, openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment
    from openpyxl.utils import get_column_letter

    COLS = [
        'Marketeur',
        'Stk Départ AMB', 'Stk Départ 15C',
        'Récept SD AMB', 'Récept SD 15C',
        'Récept AC AMB', 'Récept AC 15C',
        'P/G Récept AMB',
        'Tot.Entrées Nettes AMB', 'Tot.Entrées Nettes 15C',
        'Sorties AMB', 'Sorties 15C',
        'Stk Comptable AMB', 'Stk Comptable 15C',
        'P/G Physique AMB', 'Ratio %',
        'Stk Fermeture AMB', 'Stk Fermeture 15C',
    ]
    KEYS = [
        None,
        'stock_debut_amb', 'stock_debut_15c',
        'rec_sd_amb', 'rec_sd_15c',
        'rec_ac_amb', 'rec_ac_15c',
        'pg_rec_amb',
        'entrees_nettes_amb', 'entrees_nettes_15c',
        'sorties_amb', 'sorties_15c',
        'stock_comptable_amb', 'stock_comptable_15c',
        None, None, None, None,
    ]

    BLEU  = PatternFill(fill_type='solid', fgColor='1F4E79')
    VERT  = PatternFill(fill_type='solid', fgColor='E2EFDA')
    TITRE = PatternFill(fill_type='solid', fgColor='BDD7EE')
    ZEBRA = PatternFill(fill_type='solid', fgColor='EBF3FB')

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Stock Mensuel A"

    periode = rapport.get('periode')
    n       = len(COLS)
    ws.merge_cells(f'A1:{get_column_letter(n)}1')
    ws['A1'] = societe.raison_sociale if societe else 'SGDS'
    ws['A1'].font = Font(bold=True, size=14)
    ws['A1'].alignment = Alignment(horizontal='center')

    ws.merge_cells(f'A2:{get_column_letter(n)}2')
    ws['A2'] = f"ÉTAT STOCK MENSUEL — FORMAT A — {periode}"
    ws['A2'].font = Font(bold=True, size=12)
    ws['A2'].alignment = Alignment(horizontal='center')

    row = 4
    for ci, h in enumerate(COLS, 1):
        c = ws.cell(row=row, column=ci, value=h)
        c.font = Font(bold=True, color='FFFFFF', size=8)
        c.fill = BLEU
        c.alignment = Alignment(horizontal='center', wrap_text=True)
        ws.column_dimensions[get_column_letter(ci)].width = 13
    ws.column_dimensions['A'].width = 22
    ws.row_dimensions[row].height = 35
    row += 1

    def _f(v):
        return float(v) if v is not None else ''

    for produit in rapport.get('produits', []):
        info = rapport.get('lignes_par_produit', {}).get(produit.pk)
        if not info:
            continue

        ws.merge_cells(f'A{row}:{get_column_letter(n)}{row}')
        c = ws.cell(row=row, column=1, value=produit.nom.upper())
        c.font = Font(bold=True, size=11, color='1F4E79')
        c.fill = TITRE
        row += 1

        for i, ligne in enumerate(info['lignes']):
            mkt  = ligne['marketeur']
            fill = ZEBRA if i % 2 == 0 else None
            vals = [mkt.sigle or mkt.raison_sociale]
            for key in KEYS[1:]:
                vals.append(_f(ligne.get(key)) if key else '')
            for ci, v in enumerate(vals, 1):
                c = ws.cell(row=row, column=ci, value=v)
                if fill:
                    c.fill = fill
                if isinstance(v, float):
                    c.number_format = '#,##0.00'
                    c.alignment = Alignment(horizontal='right')
            row += 1

        # Ligne totaux
        tot = info['totaux']
        tot_vals = ['TOTAUX']
        for key in KEYS[1:13]:
            tot_vals.append(_f(tot.get(key, _Z)) if key else '')
        tot_vals += [
            _f(info['pg_phys_amb']),
            f"{float(info['ratio']):.4f}%" if info['ratio'] is not None else '',
            _f(info['sf_amb']),
            _f(info['sf_15c']),
        ]
        for ci, v in enumerate(tot_vals, 1):
            c = ws.cell(row=row, column=ci, value=v)
            c.font = Font(bold=True)
            c.fill = VERT
            if isinstance(v, float):
                c.number_format = '#,##0.00'
                c.alignment = Alignment(horizontal='right')
        row += 2

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf.read()


# ═════════════════════════════════════════════════════════════
#  ÉTAT 6 — STOCK MENSUEL FORMAT B  (simplifié AMB — admin + mkt)
# ═════════════════════════════════════════════════════════════

def _calculer_stock_mensuel_b(periode, marketeur=None):
    """
    Format pivot exact du fichier Excel "STOCK AMB" :
      Lignes   = statistiques (Ouverture, Entrees, Sorties, Comptable, P/G, Ratio, Fermeture)
      Colonnes = produits actifs
    V AMB uniquement.
    marketeur=None => Tous marketeurs (stock global depuis StockOuverture)
    marketeur=<obj> => filtre par ce marketeur
    """
    from SGDS.models import Produit, StockOuverture, Mouvement

    produits = list(Produit.objects.filter(statut='ACTIF').order_by('nom'))

    # Stock fermeture physique = StockOuverture de la periode suivante
    periode_suiv = periode.periode_suivante()
    sf_physique  = {}
    if periode_suiv:
        for so in StockOuverture.objects.filter(periode=periode_suiv).select_related('produit'):
            sf_physique[so.produit_id] = _D(so.volume_ambiant)

    stk_ouv_vals      = []
    cumul_ent_vals    = []
    cumul_sor_vals    = []
    stk_cpt_vals      = []
    pertes_gains_vals = []
    ratios_vals       = []
    stk_ferm_vals     = []

    for produit in produits:
        if marketeur is None:
            # TM : stock global depuis StockOuverture
            try:
                so  = StockOuverture.objects.get(periode=periode, produit=produit)
                ouv = _D(so.volume_ambiant)
            except StockOuverture.DoesNotExist:
                ouv = _Z
            mvts_qs = Mouvement.objects.filter(
                produit=produit,
                date_mouvement__range=(periode.date_debut, periode.date_fin),
            )
        else:
            # Marketeur specifique : recalcul depuis historique
            from SGDS.models import InventaireInitialMarketeur
            from django.db.models import Sum as _Sum
            mvts_avant = list(Mouvement.objects.filter(
                produit=produit, marketeur=marketeur,
                date_mouvement__lt=periode.date_debut,
            ))
            ouv = sum(
                (_D(m.volume_ambiant_recu)      if m.type_mouvement == 'ENTREE'  else
                 -_D(m.volume_ambiant_sortie)   if m.type_mouvement == 'SORTIE'  else
                 -_D(m.cession_volume_ambiant)  if m.type_mouvement == 'CESSION' else _Z)
                for m in mvts_avant
            )
            # Cessions REÇUES par ce marketeur avant la période
            cess_recues_avant = Mouvement.objects.filter(
                produit=produit,
                type_mouvement='CESSION',
                cession_marketeur_destinataire=marketeur,
                date_mouvement__lt=periode.date_debut,
            )
            for m in cess_recues_avant:
                ouv += _D(m.cession_volume_ambiant)
            # Ajouter l'inventaire initial du marketeur pour ce produit
            inv_agg = (
                InventaireInitialMarketeur.objects
                .filter(marketeur=marketeur, produit=produit)
                .aggregate(v_amb=_Sum('volume_ambiant'))
            )
            ouv += _D(inv_agg['v_amb'] or 0)
            mvts_qs = Mouvement.objects.filter(
                produit=produit, marketeur=marketeur,
                date_mouvement__range=(periode.date_debut, periode.date_fin),
            )

        mvts = list(mvts_qs)
        ent  = sum(_D(m.volume_ambiant_recu)   for m in mvts if m.type_mouvement == 'ENTREE')
        sor  = sum(_D(m.volume_ambiant_sortie) for m in mvts if m.type_mouvement == 'SORTIE')
        cpt  = ouv + ent - sor

        sf    = sf_physique.get(produit.pk)
        pg    = (sf - cpt) if sf is not None else None
        ratio = (float(pg) / float(ent) * 100) if (pg is not None and ent) else None

        stk_ouv_vals.append(ouv)
        cumul_ent_vals.append(ent)
        cumul_sor_vals.append(sor)
        stk_cpt_vals.append(cpt)
        pertes_gains_vals.append(pg)
        ratios_vals.append(ratio)
        stk_ferm_vals.append(sf)

    return {
        'periode':       periode,
        'produits':      produits,
        'date_ouv':      periode.date_debut,
        'date_ferm':     periode.date_fin,
        'stk_ouverture': stk_ouv_vals,
        'cumul_entrees': cumul_ent_vals,
        'cumul_sorties': cumul_sor_vals,
        'stk_comptable': stk_cpt_vals,
        'pertes_gains':  pertes_gains_vals,
        'ratios':        ratios_vals,
        'stk_fermeture': stk_ferm_vals,
    }


@login_required
def etat_stock_mensuel_b(request):
    from SGDS.models import Societe, Marketeur as MktModel
    if request.user.is_marketeur_role:
        messages.error(request, "Accès non autorisé.")
        return redirect('client_dashboard')

    periodes   = _periodes_disponibles()
    periode    = _get_periode(request)
    marketeurs = list(MktModel.objects.filter(statut='ACTIF').order_by('raison_sociale'))
    marketeur  = _get_marketeur_optionnel(request)
    rapport    = _calculer_stock_mensuel_b(periode, marketeur) if periode else {}
    societe    = Societe.get_instance()

    return render(request, 'Etat/mensuel/stock_mensuel_b.html', {
        'periodes':      periodes,
        'periode':       periode,
        'rapport':       rapport,
        'marketeurs':    marketeurs,
        'marketeur_sel': marketeur,
        'societe':       societe,
    })


@login_required
def etat_stock_mensuel_b_export(request):
    from SGDS.models import Societe
    from django.http import HttpResponse
    if request.user.is_marketeur_role:
        return redirect('client_dashboard')

    periode   = _get_periode(request)
    if not periode:
        messages.warning(request, "Aucune période disponible.")
        return redirect('etat_mensuel_stock_b')
    marketeur = _get_marketeur_optionnel(request)
    rapport   = _calculer_stock_mensuel_b(periode, marketeur)
    societe   = Societe.get_instance()
    contenu   = _xlsx_stock_mensuel_b(rapport, societe)

    suffix = f"_{marketeur.sigle or 'mkt'}" if marketeur else "_TM"
    nom = f"stock_mensuel_B_{periode.mois:02d}_{periode.annee}{suffix}.xlsx"
    response = HttpResponse(
        content=contenu,
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    )
    response['Content-Disposition'] = f'attachment; filename="{nom}"'
    return response


@marketeur_required
def etat_stock_mensuel_b_marketeur(request):
    from SGDS.models import Societe
    periodes = _periodes_disponibles()
    periode  = _get_periode(request)
    mkt      = request.user.marketeur
    rapport  = _calculer_stock_mensuel_b(periode, mkt) if periode else {}
    societe  = Societe.get_instance()

    return render(request, 'Espace_Marketeur/mensuel/stock_mensuel_b.html', {
        'periodes':  periodes,
        'periode':   periode,
        'rapport':   rapport,
        'societe':   societe,
        'marketeur': mkt,
    })


@marketeur_required
def etat_stock_mensuel_b_marketeur_export(request):
    from SGDS.models import Societe
    from django.http import HttpResponse
    periode = _get_periode(request)
    if not periode:
        return redirect('client_mensuel_stock_b')
    mkt     = request.user.marketeur
    rapport = _calculer_stock_mensuel_b(periode, mkt)
    societe = Societe.get_instance()
    contenu = _xlsx_stock_mensuel_b(rapport, societe)

    nom = f"stock_mensuel_B_{mkt.sigle or 'mkt'}_{periode.mois:02d}_{periode.annee}.xlsx"
    response = HttpResponse(
        content=contenu,
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    )
    response['Content-Disposition'] = f'attachment; filename="{nom}"'
    return response


def _xlsx_stock_mensuel_b(rapport, societe):
    """
    Export pivot format B: lignes = statistiques, colonnes = produits.
    Correspond au format exact du classeur Excel STOCK AMB.
    """
    import io, openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from openpyxl.utils import get_column_letter

    NAVY   = PatternFill(fill_type='solid', fgColor='1B3A6B')
    BLUE2  = PatternFill(fill_type='solid', fgColor='BDD7EE')
    OUV    = PatternFill(fill_type='solid', fgColor='EEF2FF')
    ENT    = PatternFill(fill_type='solid', fgColor='F0FDF4')
    SOR    = PatternFill(fill_type='solid', fgColor='FFF7ED')
    CPT    = PatternFill(fill_type='solid', fgColor='EFF6FF')
    PG     = PatternFill(fill_type='solid', fgColor='FEF2F2')
    RAT    = PatternFill(fill_type='solid', fgColor='FAFAFA')
    FERM   = PatternFill(fill_type='solid', fgColor='F0FDF4')
    WHITE  = Font(bold=True, color='FFFFFF')
    NAVY_F = Font(bold=True, color='1B3A6B')
    RED_F  = Font(bold=True, color='DC2626')
    GRN_F  = Font(bold=True, color='16A34A')
    BOLD   = Font(bold=True)
    CENTER = Alignment(horizontal='center', vertical='center')
    RIGHT  = Alignment(horizontal='right', vertical='center')
    LEFT   = Alignment(horizontal='left', vertical='center')

    periode  = rapport.get('periode')
    produits = rapport.get('produits', [])
    n_prod   = len(produits)
    n_cols   = 1 + n_prod  # label col + one col per product

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Stock Mensuel B"

    last_col = get_column_letter(n_cols)

    # Row 1: company name
    ws.merge_cells(f'A1:{last_col}1')
    c = ws['A1']
    c.value = societe.raison_sociale if societe else 'SGDS'
    c.font = Font(bold=True, size=14, color='1B3A6B')
    c.alignment = CENTER

    # Row 2: title
    ws.merge_cells(f'A2:{last_col}2')
    c = ws['A2']
    c.value = f"ETAT STOCK MENSUEL - FORMAT B (AMB) - {periode}"
    c.font = Font(bold=True, size=12)
    c.alignment = CENTER

    # Row 3: blank
    row = 4

    # Header row
    c = ws.cell(row=row, column=1, value='DESIGNATION')
    c.font = WHITE; c.fill = NAVY; c.alignment = CENTER
    ws.column_dimensions['A'].width = 28

    for i, prod in enumerate(produits, 2):
        c = ws.cell(row=row, column=i, value=prod.nom.upper())
        c.font = WHITE; c.fill = NAVY; c.alignment = CENTER
        ws.column_dimensions[get_column_letter(i)].width = 18

    row += 1

    def _f(v):
        return float(v) if v is not None else None

    STAT_ROWS = [
        ('STOCKS OUVERTURE (L)',  'stk_ouverture', OUV,  NAVY_F),
        ('CUMULS ENTREES (L)',    'cumul_entrees',  ENT,  BOLD),
        ('CUMULS SORTIES (L)',    'cumul_sorties',  SOR,  BOLD),
        ('STOCKS COMPTABLE (L)',  'stk_comptable',  CPT,  NAVY_F),
        ('PERTES OU GAINS (L)',   'pertes_gains',   PG,   None),
        ('RATIO (%)',             'ratios',         RAT,  None),
        ('STOCKS FERMETURE (L)',  'stk_fermeture',  FERM, Font(bold=True, color='16A34A')),
    ]

    for label, key, fill, label_font in STAT_ROWS:
        c = ws.cell(row=row, column=1, value=label)
        c.fill = fill
        c.alignment = LEFT
        if label_font:
            c.font = label_font
        else:
            c.font = BOLD

        vals = rapport.get(key, [])
        for i, v in enumerate(vals, 2):
            num = _f(v)
            c2 = ws.cell(row=row, column=i)
            c2.fill = fill
            c2.alignment = RIGHT
            if num is None:
                c2.value = ''
            elif key == 'ratios':
                c2.value = num
                c2.number_format = '0.0000'
                if num < 0:
                    c2.font = RED_F
                elif num > 0:
                    c2.font = Font(bold=True, color='16A34A')
            elif key == 'pertes_gains':
                c2.value = num
                c2.number_format = '#,##0.00'
                if num < 0:
                    c2.font = RED_F
                elif num > 0:
                    c2.font = Font(bold=True, color='16A34A')
            else:
                c2.value = num
                c2.number_format = '#,##0.00'
        row += 1

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf.read()


# ═════════════════════════════════════════════════════════════
#  ÉTAT 7 — FRAIS DE PASSAGE MENSUEL  (admin + marketeur)
# ═════════════════════════════════════════════════════════════

def _filtrer_rapport_frais_marketeur(rapport_complet, mkt):
    """Filtre un rapport frais_passage pour ne garder que les lignes d'un marketeur."""
    modes_filtres = []
    for mode_data in rapport_complet.get('modes', []):
        lignes_mkt = [l for l in mode_data['lignes'] if l['marketeur'].pk == mkt.pk]
        if lignes_mkt:
            modes_filtres.append({**mode_data, 'lignes': lignes_mkt})

    produits  = rapport_complet.get('produits', [])
    tot_vols  = {p.id: _Z for p in produits}
    tot_vol_g = _Z
    tot_mont  = _Z
    for md in modes_filtres:
        for l in md['lignes']:
            for pid, v in l['volumes_par_produit'].items():
                tot_vols[pid] = tot_vols.get(pid, _Z) + _D(v)
            tot_vol_g += _D(l['volume_global'])
            tot_mont  += _D(l['montant'])

    return {
        **rapport_complet,
        'modes': modes_filtres,
        'total_general': {
            'volumes_par_produit': tot_vols,
            'volume_global':       tot_vol_g,
            'montant':             tot_mont,
        },
    }


@login_required
def etat_frais_passage_mensuel(request):
    from SGDS.models import Societe
    from SGDS.services.frais_passage import calculer_frais_passage
    if request.user.is_marketeur_role:
        messages.error(request, "Accès non autorisé.")
        return redirect('client_dashboard')

    periodes = _periodes_disponibles()
    periode  = _get_periode(request)
    societe  = Societe.get_instance()
    rapport  = calculer_frais_passage(periode) if periode else None

    return render(request, 'Etat/mensuel/frais_passage.html', {
        'periodes': periodes,
        'periode':  periode,
        'rapport':  rapport,
        'societe':  societe,
    })


@login_required
def etat_frais_passage_mensuel_export(request):
    from SGDS.models import Societe
    from SGDS.services.frais_passage import calculer_frais_passage
    from SGDS.services.export_excel import exporter_frais_passage_xlsx
    from django.http import HttpResponse
    if request.user.is_marketeur_role:
        return redirect('client_dashboard')

    periode = _get_periode(request)
    if not periode:
        messages.warning(request, "Aucune période disponible.")
        return redirect('etat_mensuel_frais_passage')

    rapport = calculer_frais_passage(periode)
    contenu = exporter_frais_passage_xlsx(rapport)

    nom = f"frais_passage_{periode.mois:02d}_{periode.annee}.xlsx"
    response = HttpResponse(
        content=contenu,
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    )
    response['Content-Disposition'] = f'attachment; filename="{nom}"'
    return response



@marketeur_required
def etat_frais_passage_mensuel_marketeur(request):
    from SGDS.models import Societe
    from SGDS.services.frais_passage import calculer_frais_passage
    periodes        = _periodes_disponibles()
    periode         = _get_periode(request)
    societe         = Societe.get_instance()
    mkt             = request.user.marketeur
    rapport         = None

    if periode:
        rapport_complet = calculer_frais_passage(periode)
        rapport         = _filtrer_rapport_frais_marketeur(rapport_complet, mkt)

    return render(request, 'Espace_Marketeur/mensuel/frais_passage.html', {
        'periodes':  periodes,
        'periode':   periode,
        'rapport':   rapport,
        'societe':   societe,
        'marketeur': mkt,
    })


@marketeur_required
def etat_frais_passage_mensuel_marketeur_export(request):
    from SGDS.models import Societe
    from SGDS.services.frais_passage import calculer_frais_passage
    from SGDS.services.export_excel import exporter_frais_passage_xlsx
    from django.http import HttpResponse

    periode = _get_periode(request)
    if not periode:
        return redirect('client_mensuel_frais_passage')

    mkt             = request.user.marketeur
    rapport_complet = calculer_frais_passage(periode)
    rapport         = _filtrer_rapport_frais_marketeur(rapport_complet, mkt)
    contenu         = exporter_frais_passage_xlsx(rapport)

    nom = f"frais_passage_{mkt.sigle or 'mkt'}_{periode.mois:02d}_{periode.annee}.xlsx"
    response = HttpResponse(
        content=contenu,
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    )
    response['Content-Disposition'] = f'attachment; filename="{nom}"'
    return response
