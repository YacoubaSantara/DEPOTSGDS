from django.contrib.auth import get_user_model
from django.db import transaction


@transaction.atomic
def creer_utilisateur(username, email, password, role,
                      prenom='', nom='', is_staff=None, **profile_kwargs):
    """
    Crée un User (UtilisateurSGDS) + UserProfile avec le rôle RBAC donné.

    `role` accepte soit un objet Role, soit un code str ('SUPERADMIN', etc.).

    is_staff auto-déduit du rôle si non fourni :
      SUPERADMIN, CHEF_DEPOT → is_staff=True
      OPERATEUR, COMPTABLE, LECTEUR → is_staff=False
    """
    from .models import Role, UserProfile

    User = get_user_model()

    # Résoudre le rôle si c'est un code string
    if isinstance(role, str):
        role = Role.objects.get(code=role)

    if is_staff is None:
        is_staff = role.code in ('SUPERADMIN', 'CHEF_DEPOT')

    is_superuser = (role.code == 'SUPERADMIN')

    user = User.objects.create_user(
        username=username, email=email, password=password,
        first_name=prenom, last_name=nom,
        is_staff=is_staff, is_superuser=is_superuser,
    )

    # Le signal post_save crée le profil ; on met à jour le rôle ici
    profil, _ = UserProfile.objects.get_or_create(user=user)
    profil.role = role
    for k, v in profile_kwargs.items():
        if hasattr(profil, k):
            setattr(profil, k, v)
    profil.save()

    # Le signal de création a mis en cache sur `user` l'ancien profil (rôle
    # par défaut) via la relation inverse one-to-one : on retourne une
    # instance fraîche pour que user.profile reflète le rôle assigné.
    return User.objects.get(pk=user.pk)
