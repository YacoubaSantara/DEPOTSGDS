"""
Vues mouvements pour l'API mobile.

Endpoints :
  GET  /api/v1/mouvements/                        → liste paginée
  GET  /api/v1/mouvements/{id}/                   → détail complet
  GET  /api/v1/mouvements/{id}/bordereau.pdf/     → bordereau officiel PDF (même format que le web)
  GET  /api/v1/mouvements/{id}/documents/         → liste documents
  POST /api/v1/mouvements/{id}/documents/         → upload document
  GET  /api/v1/documents/{id}/                    → détail document
"""
from decimal import Decimal

from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.parsers import MultiPartParser, FormParser
from django.shortcuts import get_object_or_404

from api.v1.permissions import HasVoirMouvement, HasVoirDetailMouvement
from SGDS.models import Mouvement, MouvementDocument
from .serializers import MouvementListSerializer, MouvementDetailSerializer


LABELS_TYPE = {
    'ENTREE':       'Entrée',
    'SORTIE':       'Sortie',
    'CESSION':      'Cession',
    'ACQUITTEMENT': 'Acquittement',
}
LABELS_REGIME = {
    'ACQUITTE':    'Acquitté',
    'SOUS_DOUANE': 'Sous douane',
}

PAGE_SIZE = 20


def _volume_amb(m):
    t = m.type_mouvement
    if t == 'ENTREE':        return m.volume_ambiant_recu
    if t == 'SORTIE':        return m.volume_ambiant_sortie
    if t == 'CESSION':       return m.cession_volume_ambiant
    if t == 'ACQUITTEMENT':  return m.acquittement_volume_ambiant
    return None


def _volume_15c(m):
    t = m.type_mouvement
    if t == 'ENTREE':        return m.volume_15c_recu
    if t == 'SORTIE':        return m.volume_15c_sortie
    if t == 'CESSION':       return m.cession_volume_15c
    if t == 'ACQUITTEMENT':  return m.acquittement_volume_15c
    return None


def _serialize_list(m):
    return {
        'id':               m.pk,
        'reference':        m.numero_enregistrement or '',
        'type':             m.type_mouvement,
        'produit_id':       m.produit_id,
        'produit':          m.produit.nom,
        'produit_sigle':    getattr(m.produit, 'sigle', '') or m.produit.nom[:4].upper(),
        'regime':           LABELS_REGIME.get(m.regime_douanier, m.regime_douanier),
        'date':             m.date_saisie,       # DateTimeField → inclut la date ET l'heure
        'quantite_ambiant': _volume_amb(m) or 0,
        'quantite_15':      _volume_15c(m) or 0,
        'observation':      m.notes or '',
    }


def _serialize_detail(m):
    d = _serialize_list(m)
    d.update({
        'provenance':                      m.provenance,
        'bl_expediteur':                   m.bl_expediteur,
        'bl_client':                       m.bl_client,
        'date_chargement':                 m.date_chargement,
        'date_dechargement':               m.date_dechargement,
        'volume_ambiant_expediteur':       m.volume_ambiant_expediteur,
        'volume_ambiant_recu':             m.volume_ambiant_recu,
        'volume_15c_recu':                 m.volume_15c_recu,
        'perte_gain_reception':            m.perte_gain_reception,
        'camion_immatriculation':          m.camion.immatriculation if m.camion else None,
        'chauffeur_nom':                   f"{m.chauffeur.prenom} {m.chauffeur.nom}" if m.chauffeur else None,
        'destination':                     m.destination,
        'numero_permis_sortie':            m.numero_permis_sortie,
        'volume_ambiant_sortie':           m.volume_ambiant_sortie,
        'volume_15c_sortie':               m.volume_15c_sortie,
        'mode_reglement':                  m.mode_reglement,
        'cession_destinataire':            m.cession_marketeur_destinataire.raison_sociale if m.cession_marketeur_destinataire else None,
        'cession_volume_ambiant':          m.cession_volume_ambiant,
        'cession_volume_15c':              m.cession_volume_15c,
        'cession_motif':                   m.cession_motif,
        'acquittement_volume_ambiant':     m.acquittement_volume_ambiant,
        'acquittement_reference_declaration': m.acquittement_reference_declaration,
        'acquittement_date_declaration':   m.acquittement_date_declaration,
    })
    return d


class MouvementListView(APIView):
    """
    GET /api/v1/mouvements/

    Paramètres (query string) :
      - produit      : ID du produit
      - type         : ENTREE | SORTIE | CESSION | ACQUITTEMENT
      - regime       : ACQUITTE | SOUS_DOUANE
      - date_debut   : YYYY-MM-DD
      - date_fin     : YYYY-MM-DD
      - page         : numéro de page (défaut 1)
    """
    authentication_classes = [JWTAuthentication]
    permission_classes     = [HasVoirMouvement]

    def get(self, request):
        marketeur = request.user.marketeur
        qs = (
            Mouvement.objects
            .filter(marketeur=marketeur)
            .select_related('produit', 'camion', 'chauffeur')
            .order_by('-date_mouvement', '-date_saisie')
        )

        # Filtres
        produit_id = request.query_params.get('produit')
        if produit_id:
            qs = qs.filter(produit_id=produit_id)

        type_mv = request.query_params.get('type', '').upper()
        if type_mv in ('ENTREE', 'SORTIE', 'CESSION', 'ACQUITTEMENT'):
            qs = qs.filter(type_mouvement=type_mv)

        regime = request.query_params.get('regime', '').upper()
        if regime in ('ACQUITTE', 'SOUS_DOUANE'):
            qs = qs.filter(regime_douanier=regime)

        date_debut = request.query_params.get('date_debut')
        if date_debut:
            qs = qs.filter(date_mouvement__gte=date_debut)

        date_fin = request.query_params.get('date_fin')
        if date_fin:
            qs = qs.filter(date_mouvement__lte=date_fin)

        # Pagination manuelle
        count = qs.count()
        try:
            page = max(1, int(request.query_params.get('page', 1)))
        except (ValueError, TypeError):
            page = 1
        start = (page - 1) * PAGE_SIZE
        end   = start + PAGE_SIZE
        items = qs[start:end]

        base_url = request.build_absolute_uri(request.path)
        params   = request.query_params.copy()

        def make_url(p):
            params['page'] = p
            return f"{base_url}?{'&'.join(f'{k}={v}' for k, v in params.items())}"

        import math
        total_pages = max(1, math.ceil(count / PAGE_SIZE))
        return Response({
            'count':       count,
            'page':        page,
            'page_size':   PAGE_SIZE,
            'total_pages': total_pages,
            'results':     [_serialize_list(m) for m in items],
        })


class MouvementDetailView(APIView):
    """
    GET /api/v1/mouvements/{id}/

    Retourne le détail complet d'un mouvement.
    L'utilisateur ne peut accéder qu'aux mouvements de son propre marketeur.
    """
    authentication_classes = [JWTAuthentication]
    permission_classes     = [HasVoirDetailMouvement]

    def get(self, request, pk):
        marketeur = request.user.marketeur
        m = get_object_or_404(
            Mouvement.objects.select_related(
                'produit', 'camion', 'chauffeur', 'cession_marketeur_destinataire'
            ),
            pk=pk,
            marketeur=marketeur  # sécurité : seulement ses propres mouvements
        )
        serializer = MouvementDetailSerializer(_serialize_detail(m))
        return Response(serializer.data)


def _serialize_document(doc, request):
    return {
        'id':            doc.pk,
        'type_document': doc.type_document,
        'type_document_label': doc.get_type_document_display(),
        'nom_original':  doc.nom_original,
        'description':   doc.description,
        'date_upload':   doc.date_upload.isoformat(),
        'taille_fichier': doc.taille_fichier,
        'url_fichier':   request.build_absolute_uri(doc.fichier.url),
    }


class MouvementDocumentsView(APIView):
    """
    GET  /api/v1/mouvements/{pk}/documents/ → liste des documents
    POST /api/v1/mouvements/{pk}/documents/ → upload (multipart/form-data)
    """
    authentication_classes = [JWTAuthentication]
    permission_classes     = [HasVoirDetailMouvement]
    parser_classes         = [MultiPartParser, FormParser]

    def get(self, request, pk):
        marketeur = request.user.marketeur
        mouvement = get_object_or_404(Mouvement, pk=pk, marketeur=marketeur)
        docs = MouvementDocument.objects.filter(mouvement=mouvement)
        return Response([_serialize_document(d, request) for d in docs])

    def post(self, request, pk):
        import os
        marketeur = request.user.marketeur
        mouvement = get_object_or_404(Mouvement, pk=pk, marketeur=marketeur)

        fichier = request.FILES.get('fichier')
        type_doc = request.data.get('type_document', '')
        description = request.data.get('description', '')

        if not fichier:
            return Response({'detail': 'Le champ fichier est requis.'}, status=status.HTTP_400_BAD_REQUEST)

        ext = os.path.splitext(fichier.name)[1].lower()
        if ext not in {'.pdf', '.png', '.jpg', '.jpeg'}:
            return Response({'detail': f'Format non autorisé : {ext}.'}, status=status.HTTP_400_BAD_REQUEST)
        if fichier.size > 10 * 1024 * 1024:
            return Response({'detail': 'Fichier trop volumineux (max 10 Mo).'}, status=status.HTTP_400_BAD_REQUEST)

        valid_types = {c[0] for c in MouvementDocument.TYPE_DOC_CHOICES}
        if type_doc not in valid_types:
            return Response({'detail': f'Type invalide. Valeurs : {", ".join(valid_types)}'}, status=status.HTTP_400_BAD_REQUEST)

        doc = MouvementDocument.objects.create(
            mouvement=mouvement,
            fichier=fichier,
            type_document=type_doc,
            nom_original=fichier.name,
            description=description,
            uploader=request.user,
        )
        return Response(_serialize_document(doc, request), status=status.HTTP_201_CREATED)


class MouvementBordereauPdfView(APIView):
    """
    GET /api/v1/mouvements/{pk}/bordereau.pdf/

    Retourne le bordereau officiel en PDF (identique à la version web).
    Nécessite WeasyPrint côté serveur.
    Authentification : Bearer JWT.
    """
    authentication_classes = [JWTAuthentication]
    permission_classes     = [HasVoirDetailMouvement]

    def get(self, request, pk):
        from django.http import HttpResponse
        try:
            from weasyprint import HTML, CSS
            from django.template.loader import render_to_string
            from django.contrib.staticfiles import finders
        except ImportError as e:
            return HttpResponse(
                f"WeasyPrint ImportError : {e}",
                status=501,
                content_type="text/plain; charset=utf-8",
            )
        except Exception as e:
            return HttpResponse(
                f"Erreur chargement WeasyPrint : {type(e).__name__} — {e}",
                status=501,
                content_type="text/plain; charset=utf-8",
            )

        from django.utils import timezone as tz
        from SGDS.models import Societe

        marketeur = request.user.marketeur
        mouvement = get_object_or_404(
            Mouvement.objects.select_related(
                "produit", "marketeur", "cuve", "cuve__produit",
                "camion", "chauffeur",
            ).prefetch_related("lignes__cuve__produit"),
            pk=pk,
            marketeur=marketeur,   # sécurité : seulement ses propres mouvements
        )

        societe = Societe.get_instance()

        try:
            from SGDS.services.periode_comptable import periode_pour_date
            periode = periode_pour_date(mouvement.date_mouvement, mouvement.depot)
            periode_label = str(periode) if periode else mouvement.date_mouvement.strftime("%B %Y")
        except Exception:
            periode_label = mouvement.date_mouvement.strftime("%B %Y")

        # Calculs écart expéditeur / reçu
        vol_exp  = float(mouvement.volume_15c_expediteur or 0)
        vol_recu = float(mouvement.volume_15c_recu or 0)
        ecart    = vol_recu - vol_exp
        if vol_exp:
            ecart_signe      = f"{'+' if ecart >= 0 else ''}{ecart:,.0f}".replace(",", " ")
            ecart_pct        = f"{'+' if ecart >= 0 else ''}{(ecart / vol_exp * 100):.2f}"
            tolerance_status = "OK" if abs(ecart / vol_exp) <= 0.005 else "HORS TOLÉRANCE"
        else:
            ecart_signe = ecart_pct = tolerance_status = "—"

        pg_amb  = float(mouvement.perte_gain_reception or 0)
        pg_15c  = float(mouvement.perte_gain_15c or 0) if hasattr(mouvement, 'perte_gain_15c') else 0
        perte_gain_ambiant_signe = (
            f"{'+' if pg_amb >= 0 else ''}{pg_amb:,.0f}".replace(",", " ")
            if mouvement.perte_gain_reception is not None else "—"
        )
        perte_gain_15c_signe = (
            f"{'+' if pg_15c >= 0 else ''}{pg_15c:,.0f}".replace(",", " ")
            if hasattr(mouvement, 'perte_gain_15c') and mouvement.perte_gain_15c is not None else "—"
        )
        poids_volumique = float(mouvement.densite_15c_calculee) if getattr(mouvement, 'densite_15c_calculee', None) else None

        ctx = {
            "mouvement":                  mouvement,
            "societe":                    societe,
            "now":                        tz.now(),
            "periode_label":              periode_label,
            "show_calc":                  True,
            "show_sigs":                  True,
            "show_stamp":                 False,
            "compact":                    False,
            "bw":                         False,
            "auto_print":                 False,
            "ecart_signe":                ecart_signe,
            "ecart_pct":                  ecart_pct,
            "tolerance_status":           tolerance_status,
            "perte_gain_ambiant_signe":   perte_gain_ambiant_signe,
            "perte_gain_15c_signe":       perte_gain_15c_signe,
            "poids_volumique":            poids_volumique,
            "statut_acquittement":        getattr(mouvement, 'statut_acquittement', None),
        }

        try:
            html_string = render_to_string("mouvements/bordereau.html", ctx, request=request)
            css_path    = finders.find("css/bordereau.css")
            pdf_bytes   = HTML(
                string=html_string,
                base_url=request.build_absolute_uri("/"),
            ).write_pdf(
                stylesheets=[CSS(filename=css_path)] if css_path else None,
                presentational_hints=True,
            )
        except Exception as e:
            return HttpResponse(
                f"Erreur génération PDF : {type(e).__name__} — {e}",
                status=500,
                content_type="text/plain; charset=utf-8",
            )

        filename = f"bordereau_{mouvement.numero_enregistrement}.pdf"
        response = HttpResponse(pdf_bytes, content_type="application/pdf")
        response["Content-Disposition"] = f'inline; filename="{filename}"'
        return response


class DocumentDetailView(APIView):
    """GET /api/v1/documents/{pk}/ → détail d'un document (restriction marketeur)"""
    authentication_classes = [JWTAuthentication]
    permission_classes     = [HasVoirDetailMouvement]

    def get(self, request, pk):
        marketeur = request.user.marketeur
        doc = get_object_or_404(
            MouvementDocument.objects.select_related('mouvement'),
            pk=pk,
            mouvement__marketeur=marketeur,
        )
        return Response(_serialize_document(doc, request))
