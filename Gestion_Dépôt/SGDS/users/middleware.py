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
        request.depots_selectionnables = []
        request.depot = self._resoudre(request)
        return self.get_response(request)

    def _resoudre(self, request):
        user = getattr(request, 'user', None)
        if not user or not user.is_authenticated:
            return None

        profil = getattr(user, 'profile', None)
        if profil is None:
            return None

        # Une seule requête : la liste est matérialisée puis exposée sur la
        # requête pour être réutilisée par depot_indicateur / depot_context
        # sans requête supplémentaire. Vide pour MARKETEUR (jamais restreint).
        selectionnables = list(profil.depots_selectionnables())
        request.depots_selectionnables = selectionnables
        if not selectionnables:
            return None

        valeur = request.session.get('depot_actif_id')

        if valeur == 'TOUS':
            if profil.peut_selectionner_tous:
                return None  # vue consolidée
            valeur = None

        # Dépôt fixe : un seul assigné, pas de switch (hors SUPERADMIN qui
        # garde le choix 'TOUS').
        if len(selectionnables) == 1 and not profil.peut_selectionner_tous:
            return selectionnables[0]

        if valeur:
            depot = next(
                (d for d in selectionnables if str(d.pk) == str(valeur)), None
            )
            if depot:
                return depot

        depot = selectionnables[0]
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
