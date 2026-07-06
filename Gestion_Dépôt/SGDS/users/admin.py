from django.contrib import admin

from .models import AuditLog, Role, UserProfile


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display  = ('nom', 'code', 'systeme', 'couleur', 'nb_utilisateurs',
                     'nb_permissions', 'date_creation')
    list_filter   = ('systeme', 'couleur')
    search_fields = ('nom', 'code', 'description')
    readonly_fields = ('code', 'systeme', 'date_creation', 'date_modification', 'cree_par')
    filter_horizontal = ('permissions',)
    fieldsets = (
        (None, {'fields': ('nom', 'code', 'description', 'couleur', 'systeme')}),
        ('Permissions', {'fields': ('permissions',)}),
        ('Métadonnées', {'fields': ('cree_par', 'date_creation', 'date_modification')}),
    )

    def has_delete_permission(self, request, obj=None):
        if obj and obj.systeme:
            return False
        if obj and obj.utilisateurs.exists():
            return False
        return True


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display  = ('user', 'role', 'liste_depots', 'actif', 'poste', 'telephone',
                     'derniere_ip', 'date_creation')
    list_filter   = ('role', 'depots', 'actif')
    search_fields = ('user__username', 'user__email', 'poste', 'telephone')
    readonly_fields = ('derniere_ip', 'date_creation', 'date_modification')
    filter_horizontal = ('depots',)
    fieldsets = (
        (None, {'fields': ('user', 'role', 'depots', 'actif')}),
        ('Coordonnées', {'fields': ('telephone', 'poste', 'photo')}),
        ('Technique', {'fields': ('derniere_ip', 'notes_admin',
                                  'date_creation', 'date_modification')}),
    )

    @admin.display(description='Depots assignes')
    def liste_depots(self, obj):
        return ", ".join(obj.depots.values_list('code', flat=True)) or '—'


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display  = ('horodatage', 'user_username_snapshot', 'action',
                     'objet_type', 'objet_repr', 'source', 'ip_address')
    list_filter   = ('action', 'source', 'objet_type')
    search_fields = ('user_username_snapshot', 'objet_repr',
                     'description', 'ip_address')
    date_hierarchy = 'horodatage'
    readonly_fields = [f.name for f in AuditLog._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
