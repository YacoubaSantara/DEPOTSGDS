import os
import mimetypes

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, Http404
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_POST

from SGDS.models import Mouvement, MouvementDocument
from SGDS.forms import MouvementDocumentForm


# ── Helpers permission ────────────────────────────────────────

def _peut_uploader(user):
    return not user.is_marketeur_role


def _peut_supprimer(user):
    if user.is_staff:
        return True
    try:
        return user.profile.role.code in ('SUPERADMIN', 'CHEF_DEPOT')
    except Exception:
        return False


# ── Vues ──────────────────────────────────────────────────────

@login_required
@require_POST
def mouvement_documents_upload(request, mouvement_uuid, mouvement_slug):
    if not _peut_uploader(request.user):
        messages.error(request, "Action non autorisée pour votre rôle.")
        return redirect('mouvement_detail', uuid=doc.mouvement.uuid, slug=doc.mouvement.slug)

    mouvement = get_object_or_404(Mouvement, pk=mouvement_id)
    form = MouvementDocumentForm(request.POST, request.FILES)

    if form.is_valid():
        fichier = form.cleaned_data['fichier']
        doc = form.save(commit=False)
        doc.mouvement = mouvement
        doc.nom_original = fichier.name
        doc.uploader = request.user
        doc.save()

        # Notifier le marketeur du mouvement
        try:
            from SGDS.models import Notification
            Notification.objects.create(
                marketeur=mouvement.marketeur,
                type_notif='DOCUMENT_AJOUTE',
                mouvement=mouvement,
                titre="Nouveau document justificatif",
                message=(
                    f"Un document « {doc.get_type_document_display()} » a été joint "
                    f"au mouvement {mouvement.numero_enregistrement}."
                ),
            )
        except Exception:
            pass

        messages.success(request, f"Document « {doc.nom_original} » joint avec succès.")
    else:
        for errs in form.errors.values():
            for err in errs:
                messages.error(request, err)

    return redirect('mouvement_detail', uuid=doc.mouvement.uuid, slug=doc.mouvement.slug)


@login_required
@require_POST
def mouvement_document_supprimer(request, document_uuid):
    doc = get_object_or_404(
        MouvementDocument.objects.select_related('mouvement'), uuid=document_uuid
    )
    if not _peut_supprimer(request.user):
        messages.error(request, "Suppression réservée au Chef de Dépôt ou Super Administrateur.")
        return redirect('mouvement_detail', uuid=doc.mouvement.uuid, slug=doc.mouvement.slug)

    mouvement_id = doc.mouvement_id
    nom = doc.nom_original
    try:
        if doc.fichier and os.path.exists(doc.fichier.path):
            os.remove(doc.fichier.path)
    except Exception:
        pass
    doc.delete()
    messages.success(request, f"Document « {nom} » supprimé.")
    return redirect('mouvement_detail', uuid=doc.mouvement.uuid, slug=doc.mouvement.slug)


@login_required
def mouvement_document_voir(request, document_uuid):
    doc = get_object_or_404(
        MouvementDocument.objects.select_related('mouvement__marketeur'), uuid=document_uuid
    )

    # Restriction marketeur : seulement ses propres mouvements
    if request.user.is_marketeur_role:
        if (
            not request.user.marketeur
            or doc.mouvement.marketeur_id != request.user.marketeur.pk
        ):
            raise Http404

    try:
        with open(doc.fichier.path, 'rb') as f:
            content = f.read()
    except (FileNotFoundError, ValueError, OSError):
        raise Http404("Fichier introuvable sur le serveur.")

    content_type, _ = mimetypes.guess_type(doc.nom_original)
    content_type = content_type or 'application/octet-stream'

    response = HttpResponse(content, content_type=content_type)
    if content_type == 'application/pdf':
        response['Content-Disposition'] = f'inline; filename="{doc.nom_original}"'
    else:
        response['Content-Disposition'] = f'attachment; filename="{doc.nom_original}"'
    return response
