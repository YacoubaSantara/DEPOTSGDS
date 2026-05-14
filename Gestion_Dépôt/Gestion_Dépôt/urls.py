from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView
from django.contrib.auth.decorators import login_not_required

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', login_not_required(RedirectView.as_view(pattern_name='connexion')), name='home'),
    path('', include('accounts.urls')),
    path('', include('SGDS.urls')),
    path('accounts/', include('allauth.urls')),
    path('', include('SGDS.users.urls')),
    # API Mobile (/api/v1/...)
    path('api/', include('api.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
