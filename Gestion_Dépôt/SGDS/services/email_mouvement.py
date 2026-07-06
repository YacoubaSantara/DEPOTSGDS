"""
Envoi immédiat (PDF en pièce jointe) de l'email d'un mouvement, via le
gabarit générique SGDS.models.ModeleEmailMouvement. Le PDF joint est
littéralement le même bordereau que celui produit par le bouton "Imprimer"
de l'écran mouvement (templates/mouvements/bordereau_*.html, rendu via
Chromium headless — Playwright — pour une fidélité visuelle complète, le
CSS de ces templates n'étant pas interprétable par xhtml2pdf).
"""

_BORDEREAU_TEMPLATES = {
    'ENTREE':       'mouvements/bordereau_entree.html',
    'SORTIE':       'mouvements/bordereau_sortie.html',
    'CESSION':      'mouvements/bordereau_cession.html',
    'ACQUITTEMENT': 'mouvements/bordereau_acquittement.html',
}


def envoyer_email_mouvement(marketeur, mouvement, config, *, email_override=None):
    """Construit et envoie l'email du mouvement. Lève en cas d'échec —
    l'appelant best-effort (SGDS/signals.py) capture l'exception."""
    from django.core.mail import EmailMessage
    from SGDS.models import ModeleEmailMouvement, Societe
    from SGDS.services.pdf_browser import render_to_pdf_via_browser
    from SGDS.services.bordereau_email import construire_contexte_bordereau

    email_dest = email_override or marketeur.email or marketeur.email_representant
    if not email_dest:
        raise ValueError("Aucune adresse email renseignée pour ce marketeur.")

    societe = Societe.get_instance()
    gabarit = ModeleEmailMouvement.get_instance()
    sujet, corps = gabarit.rendre(marketeur=marketeur, mouvement=mouvement, societe=societe)

    template = _BORDEREAU_TEMPLATES.get(mouvement.type_mouvement, 'mouvements/bordereau_entree.html')
    contexte = construire_contexte_bordereau(mouvement, societe)
    pdf_bytes = render_to_pdf_via_browser(template, contexte)
    # Cachet virtuel de conformité + protection contre la modification
    from SGDS.services.export_pdf import appliquer_cachet_et_protection
    pdf_bytes = appliquer_cachet_et_protection(pdf_bytes, societe)
    nom_fichier = f"Bordereau_{mouvement.numero_enregistrement or mouvement.pk}.pdf"

    message = EmailMessage(sujet, corps, config.from_email, [email_dest], connection=config.get_connection())
    message.attach(nom_fichier, pdf_bytes, 'application/pdf')
    message.send(fail_silently=False)
