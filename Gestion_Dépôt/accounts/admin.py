from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import UtilisateurSGDS


# ── Utilisateur ───────────────────────────────────────────────────────────────

@admin.register(UtilisateurSGDS)
class UtilisateurSGDSAdmin(UserAdmin):
    list_display    = ('username', 'first_name', 'last_name', 'email', 'role', 'is_active', 'marketeur')
    list_filter     = ('role', 'is_active', 'is_staff')
    search_fields   = ('username', 'first_name', 'last_name', 'email')
    ordering        = ('username',)
    fieldsets = UserAdmin.fieldsets + (
        ('Profil SGDS', {
            'fields': ('role', 'telephone', 'photo', 'marketeur'),
        }),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Profil SGDS', {
            'fields': ('first_name', 'last_name', 'email', 'role', 'telephone', 'marketeur'),
        }),
    )
