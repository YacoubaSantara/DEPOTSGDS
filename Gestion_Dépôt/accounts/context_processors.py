def current_periode(request):
    """Injecte la période comptable courante (du dépôt actif) dans tous les templates."""
    from SGDS.services.periode_comptable import periode_courante_ou_alerte
    return {
        'current_periode': periode_courante_ou_alerte(depot=getattr(request, 'depot', None)),
    }
