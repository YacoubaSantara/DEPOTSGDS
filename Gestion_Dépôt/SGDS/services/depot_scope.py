"""
Helpers de scoping multi-dépôt, utilisés par les vues métier (Cuve, Mouvement,
Jaugeage, PeriodeComptable...).

`request.depot` est résolu par DepotContextMiddleware :
- un dépôt précis pour les rôles rattachés à un dépôt fixe (CHEF_DEPOT,
  OPERATEUR, COMPTABLE) ou un SUPERADMIN ayant choisi un dépôt via le switcher.
- None pour un SUPERADMIN en « vue consolidée » (tous dépôts) ou pour un
  MARKETEUR (qui transige avec plusieurs dépôts).

Convention : quand request.depot est None, les listes/lectures ne sont PAS
filtrées (vue consolidée) ; les actions de création exigent un dépôt concret.
"""
from django.contrib import messages
from django.http import Http404
from django.shortcuts import get_object_or_404


def depot_scope(request, queryset):
    """Filtre le queryset par le dépôt actif, sauf en vue consolidée (depot=None)."""
    if request.depot is not None:
        return queryset.filter(depot=request.depot)
    return queryset


def depot_requis(request):
    """
    True (et message d'erreur) si l'action nécessite un dépôt concret —
    bloque la création d'objets dépôt-scopés en vue consolidée SUPERADMIN.
    """
    if request.depot is None:
        messages.error(request, "Choisissez un dépôt actif avant de continuer.")
        return True
    return False


def get_object_or_404_depot(request, klass, **kwargs):
    """
    get_object_or_404 qui refuse (404) l'accès si l'objet n'appartient pas
    au dépôt actif — sauf en vue consolidée (depot=None) où tout est visible.
    """
    obj = get_object_or_404(klass, **kwargs)
    if request.depot is not None and getattr(obj, 'depot_id', None) != request.depot.id:
        raise Http404("Cet élément n'appartient pas au dépôt actif.")
    return obj
