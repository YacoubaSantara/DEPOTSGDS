import os
from io import BytesIO
from django.conf import settings
from django.http import HttpResponse
from django.template.loader import get_template


def _link_callback(uri: str, rel: str) -> str:
    """Resout les URLs /media/... et static/... en chemins disque absolus,
    pour que xhtml2pdf puisse charger les <img> (logo societe, etc.)."""
    if uri.startswith(settings.MEDIA_URL):
        path = os.path.join(settings.MEDIA_ROOT, uri.replace(settings.MEDIA_URL, '', 1))
    elif uri.startswith(settings.STATIC_URL) or uri.startswith('/' + settings.STATIC_URL):
        relatif = uri.replace(settings.STATIC_URL, '', 1).lstrip('/')
        for racine in getattr(settings, 'STATICFILES_DIRS', []):
            candidat = os.path.join(racine, relatif)
            if os.path.isfile(candidat):
                path = candidat
                break
        else:
            return uri
    else:
        return uri
    return path


def render_to_pdf_bytes(template_name: str, context: dict) -> bytes:
    from xhtml2pdf import pisa
    template = get_template(template_name)
    html = template.render(context)
    buffer = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html.encode('utf-8')), buffer, encoding='utf-8', link_callback=_link_callback)
    if pdf.err:
        raise RuntimeError('Erreur de génération PDF (xhtml2pdf).')
    return buffer.getvalue()


def render_to_pdf(template_name: str, context: dict, filename: str = 'document.pdf') -> HttpResponse:
    try:
        contenu = render_to_pdf_bytes(template_name, context)
    except RuntimeError:
        return HttpResponse('Erreur de génération PDF.', status=500)
    response = HttpResponse(contenu, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


# ─────────────────────────────────────────────────────────────
#  CACHET VIRTUEL + PROTECTION — PDF envoyés aux marketeurs
# ─────────────────────────────────────────────────────────────

def _calque_cachet(largeur: float, hauteur: float, nom_societe: str, date_str: str) -> BytesIO:
    """Dessine un cachet circulaire semi-transparent au centre d'une page
    vierge de mêmes dimensions, prêt à être fusionné sur chaque page."""
    from reportlab.pdfgen import canvas as rl_canvas
    from reportlab.lib.colors import Color

    buf = BytesIO()
    c = rl_canvas.Canvas(buf, pagesize=(largeur, hauteur))

    encre = Color(0.12, 0.23, 0.37, alpha=0.38)   # bleu marine translucide
    cx, cy = largeur / 2.0, hauteur / 2.0
    rayon = 105

    c.saveState()
    c.translate(cx, cy)
    c.rotate(15)
    c.setStrokeColor(encre)
    c.setFillColor(encre)

    # Double cercle du cachet
    c.setLineWidth(3.2)
    c.circle(0, 0, rayon)
    c.setLineWidth(1.1)
    c.circle(0, 0, rayon - 8)

    # Nom de la société en arc de cercle (haut)
    texte_haut = (nom_societe or 'SGDS').upper()[:34]
    import math
    r_texte = rayon - 24
    angle_total = min(160, max(60, len(texte_haut) * 7))
    angle_debut = 90 + angle_total / 2.0
    c.setFont('Helvetica-Bold', 10.5)
    for i, lettre in enumerate(texte_haut):
        angle = angle_debut - (angle_total * i / max(len(texte_haut) - 1, 1))
        rad = math.radians(angle)
        x, y = r_texte * math.cos(rad), r_texte * math.sin(rad)
        c.saveState()
        c.translate(x, y)
        c.rotate(angle - 90)
        c.drawCentredString(0, 0, lettre)
        c.restoreState()

    # Texte central
    c.setLineWidth(1)
    c.line(-62, 24, 62, 24)
    c.setFont('Helvetica-Bold', 15)
    c.drawCentredString(0, 4, 'CERTIFIÉ')
    c.drawCentredString(0, -14, 'CONFORME')
    c.setLineWidth(1)
    c.line(-62, -26, 62, -26)

    # Date + mention (bas)
    c.setFont('Helvetica-Bold', 9)
    c.drawCentredString(0, -44, f'Le {date_str}')
    c.setFont('Helvetica', 7)
    c.drawCentredString(0, -(rayon - 22), 'CACHET ÉLECTRONIQUE')

    # Étoiles décoratives latérales
    c.setFont('Helvetica-Bold', 12)
    c.drawCentredString(-(rayon - 22), -4, '★')
    c.drawCentredString(rayon - 22, -4, '★')

    c.restoreState()
    c.showPage()
    c.save()
    buf.seek(0)
    return buf


def _mot_de_passe_proprietaire() -> str:
    """Mot de passe propriétaire dérivé de la SECRET_KEY — stable, jamais
    communiqué : le destinataire ouvre le PDF librement mais ne peut pas
    le modifier."""
    import hashlib
    return hashlib.sha256(f'sgds-pdf-protection-{settings.SECRET_KEY}'.encode()).hexdigest()[:32]


def appliquer_cachet_et_protection(pdf_bytes: bytes, societe=None, proteger: bool = True) -> bytes:
    """Appose le cachet virtuel de conformité au centre de chaque page,
    puis protège le PDF (ouverture libre, mais modification / altération
    interdites — seule l'impression reste autorisée).

    Best-effort : en cas d'erreur, retourne le PDF d'origine plutôt que
    de bloquer un envoi."""
    try:
        from pypdf import PdfReader, PdfWriter
        from pypdf.constants import UserAccessPermissions
        from django.utils import timezone

        nom = getattr(societe, 'raison_sociale', None) or 'SGDS'
        date_str = timezone.localtime().strftime('%d/%m/%Y')

        reader = PdfReader(BytesIO(pdf_bytes))
        writer = PdfWriter()

        calques = {}   # cache par dimensions de page
        for page in reader.pages:
            dims = (round(float(page.mediabox.width), 1), round(float(page.mediabox.height), 1))
            if dims not in calques:
                calques[dims] = PdfReader(_calque_cachet(dims[0], dims[1], nom, date_str)).pages[0]
            page.merge_page(calques[dims])
            writer.add_page(page)

        if proteger:
            writer.encrypt(
                user_password='',
                owner_password=_mot_de_passe_proprietaire(),
                permissions_flag=(
                    UserAccessPermissions.PRINT
                    | UserAccessPermissions.PRINT_TO_REPRESENTATION
                    | UserAccessPermissions.EXTRACT_TEXT_AND_GRAPHICS
                ),
                algorithm='AES-256',
            )

        out = BytesIO()
        writer.write(out)
        return out.getvalue()
    except Exception:
        import logging
        logging.getLogger(__name__).exception('Échec cachet/protection PDF — PDF original conservé.')
        return pdf_bytes
