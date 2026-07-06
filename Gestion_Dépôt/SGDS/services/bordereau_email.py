"""
Construction du contexte des bordereaux (écarts, tolérance, pertes/gains,
stocks avant/après pour les cessions). Source UNIQUE du calcul, partagée par :
  - l'écran d'impression Ctrl+P (views/__init__.py::mouvement_bordereau),
  - le PDF serveur WeasyPrint (views/__init__.py::mouvement_bordereau_pdf),
  - le PDF envoyé par email (services/email_mouvement.py).
Les options d'affichage (show_calc, compact, …) sont passées en overrides —
seule la vue d'impression les lit depuis les paramètres GET.
"""


def construire_contexte_bordereau(mouvement, societe, *,
                                  show_calc=True, show_sigs=True,
                                  show_stamp=False, compact=False,
                                  bw=False, auto_print=False):
    from django.utils import timezone as tz

    m = mouvement

    from django.utils.dateformat import format as django_dateformat

    try:
        from SGDS.services.periode_comptable import periode_pour_date
        periode = periode_pour_date(m.date_mouvement, m.depot)
        periode_label = str(periode) if periode else django_dateformat(m.date_mouvement, 'F Y')
    except Exception:
        periode_label = django_dateformat(m.date_mouvement, 'F Y')

    vol_exp = float(m.volume_ambiant_expediteur or 0)
    vol_recu = float(m.volume_ambiant_recu or 0)
    ecart = vol_recu - vol_exp
    if vol_exp:
        ecart_signe = f"{'+' if ecart >= 0 else ''}{ecart:,.0f}".replace(",", " ")
        ecart_pct = f"{'+' if ecart >= 0 else ''}{(ecart / vol_exp * 100):.2f}"
        tolerance_status = "OK" if abs(ecart / vol_exp) <= 0.005 else "HORS TOLÉRANCE"
    else:
        ecart_signe = "—"
        ecart_pct = "—"
        tolerance_status = "—"

    pg_amb = float(m.perte_gain_reception or 0)
    pg_15c_val = float(m.perte_gain_15c or 0)
    perte_gain_ambiant_signe = (
        f"{'+' if pg_amb >= 0 else ''}{pg_amb:,.0f}".replace(",", " ")
        if m.perte_gain_reception is not None else "—"
    )
    perte_gain_15c_signe = (
        f"{'+' if pg_15c_val >= 0 else ''}{pg_15c_val:,.0f}".replace(",", " ")
        if m.perte_gain_15c is not None else "—"
    )
    poids_volumique = float(m.densite_15c_calculee) if m.densite_15c_calculee else None

    stock_avant_cedant = stock_apres_cedant = None
    stock_avant_cessionnaire = stock_apres_cessionnaire = None
    if m.type_mouvement == 'CESSION' and m.cession_marketeur_destinataire:
        from SGDS.views.etat import _calculer_carte_stock
        _regime = m.regime_douanier
        _produit = m.produit
        _vol_amb = m.cession_volume_ambiant or 0

        try:
            _carte_c = _calculer_carte_stock(m.marketeur, _produit, _regime, depot=m.depot)
            for _l in _carte_c['lignes']:
                # getattr : les lignes synthétiques (quote-part coulage) n'ont pas de pk
                if getattr(_l['mouvement'], 'pk', None) == m.pk and not _l.get('est_cession_recue'):
                    stock_apres_cedant = _l['stock_apres_amb']
                    stock_avant_cedant = stock_apres_cedant + _vol_amb
                    break
        except Exception:
            pass

        try:
            _carte_d = _calculer_carte_stock(m.cession_marketeur_destinataire, _produit, _regime, depot=m.depot)
            for _l in _carte_d['lignes']:
                if getattr(_l['mouvement'], 'pk', None) == m.pk and _l.get('est_cession_recue'):
                    stock_apres_cessionnaire = _l['stock_apres_amb']
                    stock_avant_cessionnaire = stock_apres_cessionnaire - _vol_amb
                    break
        except Exception:
            pass

    stock_avant_total = (
        (stock_avant_cedant or 0) + (stock_avant_cessionnaire or 0)
        if stock_avant_cedant is not None or stock_avant_cessionnaire is not None
        else None
    )
    stock_apres_total = (
        (stock_apres_cedant or 0) + (stock_apres_cessionnaire or 0)
        if stock_apres_cedant is not None or stock_apres_cessionnaire is not None
        else None
    )

    return {
        "mouvement": m,
        "societe": societe,
        "now": tz.now(),
        "periode_label": periode_label,
        "show_calc": show_calc,
        "show_sigs": show_sigs,
        "show_stamp": show_stamp,
        "compact": compact,
        "bw": bw,
        "auto_print": auto_print,
        "ecart_signe": ecart_signe,
        "ecart_pct": ecart_pct,
        "tolerance_status": tolerance_status,
        "perte_gain_ambiant_signe": perte_gain_ambiant_signe,
        "perte_gain_15c_signe": perte_gain_15c_signe,
        "poids_volumique": poids_volumique,
        "statut_acquittement": m.statut_acquittement,
        "stock_avant_cedant": stock_avant_cedant,
        "stock_apres_cedant": stock_apres_cedant,
        "stock_avant_cessionnaire": stock_avant_cessionnaire,
        "stock_apres_cessionnaire": stock_apres_cessionnaire,
        "stock_avant_total": stock_avant_total,
        "stock_apres_total": stock_apres_total,
    }
