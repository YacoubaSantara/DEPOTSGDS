"""
SGDS — Convertisseurs d'URL Django.

Remplace le système HashID par UUID + Slug natifs Django.

Les URLs utilisent désormais le format :
    /mouvements/<uuid>/<slug>/
    ex : /mouvements/a3f8b2c1-9e4d-4f1a-8b3c-2d7e6f901234/ent-2026-0001/

Django fournit nativement les convertisseurs <uuid:...> et <slug:...>,
donc ce fichier n'est plus nécessaire pour les patterns principaux.
Il est conservé pour compatibilité et référence.

Note : <uuid:...> attend un UUID valide (ex: a3f8b2c1-9e4d-4f1a-8b3c-2d7e6f901234)
       <slug:...> accepte [a-zA-Z0-9_-]+
"""

# Ce fichier est conservé mais HashidConverter est désormais retiré.
# Les URLs utilisent les convertisseurs natifs Django :
#   <uuid:uuid>  →  convertisseur intégré Django → python uuid.UUID
#   <slug:slug>  →  convertisseur intégré Django → str

# Aucun register_converter nécessaire dans urls.py pour uuid et slug.
