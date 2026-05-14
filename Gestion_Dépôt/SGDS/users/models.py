from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class RoleSysteme(models.TextChoices):
    """
    Codes des rôles SYSTÈME (constantes). Conservé pour compatibilité
    avec le code applicatif qui teste role.code == 'SUPERADMIN', etc.
    Les rôles dynamiques sont dans la table Role.
    Note : LECTEUR a été supprimé (migration 0006) — utilisez MARKETEUR pour les clients.
    """
    SUPERADMIN = 'SUPERADMIN', 'Super Administrateur'
    CHEF_DEPOT = 'CHEF_DEPOT', 'Chef de Dépôt'
    OPERATEUR  = 'OPERATEUR',  'Opérateur de Saisie'
    COMPTABLE  = 'COMPTABLE',  'Comptable'
    MARKETEUR  = 'MARKETEUR',  'Marketeur (Client)'


class Role(models.Model):
    """
    Rôle dynamique. Les 5 rôles système sont créés à la migration 0003
    et marqués systeme=True (non supprimables, code immutable).
    """
    COULEUR_CHOICES = [
        ('red',    'Rouge'),
        ('orange', 'Orange'),
        ('yellow', 'Jaune'),
        ('green',  'Vert'),
        ('blue',   'Bleu'),
        ('indigo', 'Indigo'),
        ('purple', 'Violet'),
        ('pink',   'Rose'),
        ('gray',   'Gris'),
    ]

    nom = models.CharField(
        max_length=100, unique=True, verbose_name="Nom du rôle",
        help_text="Affiché dans l'interface (ex: 'Chef de Dépôt')",
    )
    code = models.CharField(
        max_length=50, unique=True, verbose_name="Code interne",
        help_text=(
            "Identifiant technique stable (ex: 'CHEF_DEPOT'). "
            "Ne peut pas être modifié après création."
        ),
    )
    description = models.TextField(blank=True, verbose_name="Description")
    systeme = models.BooleanField(
        default=False, verbose_name="Rôle système",
        help_text="Si coché, le rôle ne peut pas être supprimé.",
    )
    couleur = models.CharField(
        max_length=20, default='gray', choices=COULEUR_CHOICES,
        help_text="Couleur du badge dans l'interface.",
    )
    permissions = models.ManyToManyField(
        'auth.Permission', blank=True,
        related_name='roles_sgds', verbose_name="Permissions",
    )
    date_creation     = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    cree_par = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='+',
    )

    class Meta:
        verbose_name        = "Rôle"
        verbose_name_plural = "Rôles"
        ordering            = ['-systeme', 'nom']

    def __str__(self):
        return self.nom

    @property
    def nb_utilisateurs(self):
        return self.utilisateurs.count()

    @property
    def nb_permissions(self):
        return self.permissions.count()

    def save(self, *args, **kwargs):
        if self.pk:
            ancien = Role.objects.filter(pk=self.pk).values('code').first()
            if ancien and ancien['code'] != self.code:
                raise ValueError(
                    f"Le code du rôle ne peut pas être modifié "
                    f"(ancien: {ancien['code']}, nouveau: {self.code})"
                )
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self.systeme:
            raise ValidationError(
                f"Le rôle système '{self.nom}' ne peut pas être supprimé."
            )
        if self.utilisateurs.exists():
            raise ValidationError(
                f"Impossible de supprimer '{self.nom}' : "
                f"{self.utilisateurs.count()} utilisateur(s) lui sont attribué(s)."
            )
        super().delete(*args, **kwargs)


class UserProfile(models.Model):
    """
    Extension OneToOne du User Django (AUTH_USER_MODEL = accounts.UtilisateurSGDS).
    Créé automatiquement via signal post_save sur User.
    Porte le système RBAC dynamique (role FK → Role).
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='profile', verbose_name="Utilisateur",
    )
    role = models.ForeignKey(
        'Role', on_delete=models.PROTECT,
        related_name='utilisateurs', verbose_name="Rôle",
        null=True, blank=True,
        help_text="Rôle RBAC. Défaut : LECTEUR à la création.",
    )
    telephone   = models.CharField(max_length=20, blank=True, null=True)
    poste       = models.CharField(max_length=100, blank=True, null=True,
                                   verbose_name="Fonction")
    photo       = models.ImageField(upload_to='users/photos/', blank=True, null=True)
    actif       = models.BooleanField(default=True, verbose_name="Actif")
    derniere_ip = models.GenericIPAddressField(blank=True, null=True)
    notes_admin = models.TextField(blank=True, null=True)

    date_creation     = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = "Profil utilisateur"
        verbose_name_plural = "Profils utilisateurs"
        ordering            = ['user__username']

    def __str__(self):
        nom_role = self.role.nom if self.role else 'Sans rôle'
        return f"{self.user.get_full_name() or self.user.username} ({nom_role})"

    # ── Helpers code ───────────────────────────────────────────────────────────
    def _has_perm_codename(self, codename):
        if not self.role or not self.actif:
            return False
        return self.role.permissions.filter(codename=codename).exists()

    # ── Properties sémantiques (compatibles avec l'ancien code) ───────────────
    @property
    def est_superadmin(self):
        return bool(self.role and self.role.code == 'SUPERADMIN')

    @property
    def est_chef_depot(self):
        return bool(self.role and self.role.code in ('SUPERADMIN', 'CHEF_DEPOT'))

    @property
    def est_operateur(self):
        return bool(self.role and self.role.code == 'OPERATEUR')

    @property
    def est_comptable(self):
        return bool(self.role and self.role.code == 'COMPTABLE')

    # ── Properties permissions (basées sur la table Role.permissions) ─────────
    @property
    def peut_ecrire(self):
        return any(self._has_perm_codename(c) for c in [
            'ajouter_mouvement', 'ajouter_jaugeage', 'modifier_mouvement',
        ])

    @property
    def peut_cloturer_periode(self):
        return self._has_perm_codename('cloturer_periode')

    @property
    def peut_valider_jaugeage(self):
        return self._has_perm_codename('valider_jaugeage')

    @property
    def peut_supprimer_mouvement(self):
        return self._has_perm_codename('supprimer_mouvement')

    @property
    def peut_gerer_utilisateurs(self):
        return self._has_perm_codename('gerer_utilisateur')

    @property
    def peut_gerer_roles(self):
        return self._has_perm_codename('gerer_role')

    @property
    def peut_voir_audit(self):
        return self._has_perm_codename('voir_audit')

    @property
    def peut_exporter_rapports(self):
        if not self.role or not self.actif:
            return False
        return self.role.permissions.filter(codename__startswith='exporter_').exists()


class AuditLog(models.Model):
    class Action(models.TextChoices):
        CREATE       = 'CREATE',       'Création'
        UPDATE       = 'UPDATE',       'Modification'
        DELETE       = 'DELETE',       'Suppression'
        VIEW         = 'VIEW',         'Consultation'
        LOGIN        = 'LOGIN',        'Connexion'
        LOGOUT       = 'LOGOUT',       'Déconnexion'
        LOGIN_FAILED = 'LOGIN_FAILED', 'Connexion échouée'
        EXPORT       = 'EXPORT',       'Export'
        VALIDATE     = 'VALIDATE',     'Validation'
        CLOSE        = 'CLOSE',        'Clôture'
        OPEN         = 'OPEN',         'Ouverture'

    horodatage = models.DateTimeField(default=timezone.now, db_index=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='audit_logs',
    )
    user_username_snapshot = models.CharField(
        max_length=150, blank=True,
        help_text="Snapshot du username au cas où le user est supprimé",
    )
    action     = models.CharField(max_length=15, choices=Action.choices, db_index=True)
    objet_type = models.CharField(max_length=100, blank=True, db_index=True)
    objet_id   = models.PositiveIntegerField(blank=True, null=True, db_index=True)
    objet_repr = models.CharField(max_length=300, blank=True)
    description = models.CharField(max_length=500, blank=True)

    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.CharField(max_length=300, blank=True)
    source     = models.CharField(
        max_length=10,
        choices=[('WEB', 'Web'), ('ADMIN', 'Admin'), ('SYSTEM', 'Système')],
        default='WEB', db_index=True,
    )
    changements = models.JSONField(
        blank=True, null=True,
        help_text="Dict {champ: {avant, apres}}",
    )

    class Meta:
        verbose_name        = "Entrée d'audit"
        verbose_name_plural = "Journal d'audit"
        ordering            = ['-horodatage']
        indexes = [
            models.Index(fields=['-horodatage', 'action']),
            models.Index(fields=['user', '-horodatage']),
            models.Index(fields=['objet_type', 'objet_id']),
        ]

    def __str__(self):
        who = self.user_username_snapshot or 'système'
        return f"{self.horodatage:%Y-%m-%d %H:%M} {who} {self.action} {self.objet_type}"
