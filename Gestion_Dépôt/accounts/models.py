from django.db import models
from django.contrib.auth.models import AbstractUser


class UtilisateurSGDS(AbstractUser):

    ROLE_CHOICES = [
        ('ADMIN',     'Administrateur'),
        ('OPERATEUR', 'Opérateur'),
        ('MARKETEUR', 'Marketeur'),
    ]

    role      = models.CharField(
        max_length=20, choices=ROLE_CHOICES, default='OPERATEUR',
        verbose_name="Rôle"
    )
    telephone = models.CharField(
        max_length=20, blank=True, null=True,
        verbose_name="Téléphone"
    )
    photo     = models.ImageField(
        upload_to='users/photos/', blank=True, null=True,
        verbose_name="Photo de profil"
    )
    marketeur = models.OneToOneField(
        'SGDS.Marketeur', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='compte_utilisateur',
        verbose_name="Marketeur lié"
    )

    class Meta:
        verbose_name        = "Utilisateur SGDS"
        verbose_name_plural = "Utilisateurs SGDS"

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.get_role_display()})"

    @property
    def is_admin_role(self):
        return self.role == 'ADMIN' or self.is_superuser

    @property
    def is_marketeur_role(self):
        return self.role == 'MARKETEUR'

    @property
    def nom_role_display(self):
        """
        Retourne le nom du rôle RBAC (UserProfile → Role.nom) si disponible,
        sinon repli sur le rôle simple (ADMIN/OPERATEUR/MARKETEUR).
        Évite l'affichage "Opérateur" pour tous les comptes internes.
        """
        try:
            profil = self.profile  # reverse OneToOne vers UserProfile
            if profil and profil.role_id:
                return profil.role.nom
        except Exception:
            pass
        return self.get_role_display()

    @property
    def initiales(self):
        if self.first_name and self.last_name:
            return f"{self.first_name[0]}{self.last_name[0]}".upper()
        return self.username[:2].upper()

    @property
    def nom_complet(self):
        return self.get_full_name() or self.username
