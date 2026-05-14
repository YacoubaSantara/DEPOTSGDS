"""
Point d'entrée de l'API SGDS Mobile.
Inclus dans le urls.py principal sous le préfixe /api/
"""
from django.urls import path, include

urlpatterns = [
    path('v1/', include('api.v1.urls')),
]
