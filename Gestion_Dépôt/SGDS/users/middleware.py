import threading

_thread_locals = threading.local()


def get_current_user():
    return getattr(_thread_locals, 'user', None)


def get_current_request():
    return getattr(_thread_locals, 'request', None)


class DepotContextMiddleware:
    """
    Résout request.depot pour chaque requête :
    - non authentifié ou MARKETEUR → None (les espaces marketeur agrègent
      tous les dépôts, ils ne sont jamais restreints).
    - profile.depots avec un seul dépôt assigné (CHEF_DEPOT/OPERATEUR/COMPTABLE)
      → fixe, pas de switch.
    - profile.depots avec plusieurs dépôts assignés → dépôt actif choisi en
      session (request.session['depot_actif_id']), parmi UNIQUEMENT ses dépôts
      assignés (pas de vue consolidée pour ces rôles).
    - SUPERADMIN sans depot fixe → dépôt actif choisi en session
      (request.session['depot_actif_id']), 'TOUS' pour la vue consolidée,
      ou le premier dépôt actif par défaut.
    Doit être placé APRÈS AuthenticationMiddleware.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.depot = self._resoudre(request)
        return self.get_response(request)

    def _resoudre(self, request):
        from SGDS.models import Depot

        user = getattr(request, 'user', None)
        if not user or not user.is_authenticated:
            return None

        profil = getattr(user, 'profile', None)
        if profil is None:
            return None

        if profil.role and profil.role.code == 'MARKETEUR':
            return None

        if profil.est_superadmin:
            valeur = request.session.get('depot_actif_id')
            if valeur == 'TOUS':
                return None
            if valeur:
                depot = Depot.objects.filter(pk=valeur, statut='ACTIF').first()
                if depot:
                    return depot

            depot = Depot.objects.filter(statut='ACTIF').order_by('nom').first()
            if depot:
                request.session['depot_actif_id'] = str(depot.pk)
            return depot

        mes_depots = profil.depots.filter(statut='ACTIF').order_by('nom')
        if not mes_depots.exists():
            return None
        if mes_depots.count() == 1:
            return mes_depots.first()

        valeur = request.session.get('depot_actif_id')
        if valeur and valeur != 'TOUS':
            depot = mes_depots.filter(pk=valeur).first()
            if depot:
                return depot

        depot = mes_depots.first()
        request.session['depot_actif_id'] = str(depot.pk)
        return depot


class AuditContextMiddleware:
    """
    Stocke la requête courante dans un thread-local pour que les signaux
    d'audit puissent récupérer l'utilisateur, l'IP et le user-agent.
    Doit être placé APRÈS AuthenticationMiddleware.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        _thread_locals.request = request
        _thread_locals.user = getattr(request, 'user', None)
        try:
            response = self.get_response(request)
        finally:
            _thread_locals.request = None
            _thread_locals.user = None
        return response
