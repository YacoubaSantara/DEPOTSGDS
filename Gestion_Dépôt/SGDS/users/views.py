from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import Permission
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.generic import (
    CreateView, DetailView, ListView, TemplateView, UpdateView, View,
)

from .decorators import CanManageUsersMixin, CanViewAuditMixin, CanManageRolesMixin
from .managers import creer_utilisateur
from .models import AuditLog, Role, UserProfile
from .permissions import can_manage_roles

User = get_user_model()


# ── Gestion des utilisateurs ───────────────────────────────────────────────────
class ListeUtilisateursView(LoginRequiredMixin, CanManageUsersMixin, ListView):
    model = User
    template_name = 'users/liste.html'
    context_object_name = 'utilisateurs'
    paginate_by = 25

    def get_queryset(self):
        qs = User.objects.select_related('profile__role').order_by('username')
        q = self.request.GET.get('q', '').strip()
        if q:
            qs = qs.filter(
                Q(username__icontains=q) | Q(email__icontains=q) |
                Q(first_name__icontains=q) | Q(last_name__icontains=q)
            )
        role_code = self.request.GET.get('role', '')
        if role_code:
            qs = qs.filter(profile__role__code=role_code)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['roles'] = list(
            Role.objects.all().order_by('-systeme', 'nom').values_list('code', 'nom')
        )
        ctx['role_filtre'] = self.request.GET.get('role', '')
        ctx['q'] = self.request.GET.get('q', '')
        return ctx


class DetailUtilisateurView(LoginRequiredMixin, CanManageUsersMixin, DetailView):
    model = User
    template_name = 'users/detail.html'
    context_object_name = 'utilisateur'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['dernieres_actions'] = (
            AuditLog.objects
            .filter(user=self.object)
            .order_by('-horodatage')[:30]
        )
        return ctx


class CreerUtilisateurView(LoginRequiredMixin, CanManageUsersMixin, CreateView):
    template_name = 'users/creer.html'

    def _roles_qs(self):
        # On retourne les objets complets pour avoir code, nom, couleur, description.
        # LECTEUR exclu : supprimé en migration 0006, remplacé par MARKETEUR pour les clients.
        return Role.objects.exclude(code='LECTEUR').order_by('-systeme', 'nom')

    def _marketeurs_disponibles(self):
        """Marketeurs actifs sans compte utilisateur existant."""
        from SGDS.models import Marketeur
        return Marketeur.objects.filter(
            statut='ACTIF',
            compte_utilisateur__isnull=True,
        ).order_by('raison_sociale')

    def _ctx(self, data=None):
        return {
            'roles':                  self._roles_qs(),
            'marketeurs_disponibles': self._marketeurs_disponibles(),
            'data':                   data or {},
        }

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, self._ctx())

    def post(self, request, *args, **kwargs):
        data = request.POST
        password         = data.get('password', '')
        password_confirm = data.get('password_confirm', '')
        role_code        = data.get('role', '').strip()
        is_marketeur     = (role_code == 'MARKETEUR')
        marketeur_id     = data.get('marketeur_id', '').strip()

        # ── Validations ───────────────────────────────────────
        erreur = None
        if password != password_confirm:
            erreur = "Les mots de passe ne correspondent pas."
        elif len(password) < 8:
            erreur = "Le mot de passe doit faire au moins 8 caractères."
        elif not data.get('username', '').strip():
            erreur = "Le nom d'utilisateur est obligatoire."
        elif not role_code:
            erreur = "Le rôle est obligatoire."
        elif is_marketeur and not marketeur_id:
            erreur = "Vous devez sélectionner un marketeur à lier pour ce rôle."

        if erreur:
            messages.error(request, erreur)
            return render(request, self.template_name, self._ctx(data))

        try:
            if is_marketeur:
                # ── Création d'un compte MARKETEUR ────────────
                from SGDS.models import Marketeur
                from django.db import transaction

                marketeur_obj = Marketeur.objects.get(pk=marketeur_id)

                # Vérifier que ce marketeur n'a pas déjà un compte
                if hasattr(marketeur_obj, 'compte_utilisateur'):
                    raise ValueError(
                        f"Le marketeur « {marketeur_obj.raison_sociale} » a déjà un compte utilisateur."
                    )

                with transaction.atomic():
                    user = User.objects.create_user(
                        username=data['username'].strip(),
                        email=data.get('email', '').strip(),
                        password=password,
                        first_name=data.get('first_name', '').strip(),
                        last_name=data.get('last_name', '').strip(),
                        is_staff=False,
                        is_superuser=False,
                    )
                    # Définir le rôle simple + le lien marketeur
                    user.role      = 'MARKETEUR'
                    user.marketeur = marketeur_obj
                    user.telephone = data.get('telephone', '').strip()
                    user.save(update_fields=['role', 'marketeur', 'telephone'])

                    # Créer un UserProfile sans rôle RBAC (l'accès est géré par
                    # user.is_marketeur_role + @marketeur_required, pas par RBAC)
                    from .models import UserProfile
                    UserProfile.objects.get_or_create(user=user)

            else:
                # ── Création d'un compte interne (RBAC) ───────
                role = Role.objects.get(code=role_code)
                user = creer_utilisateur(
                    username=data['username'].strip(),
                    email=data.get('email', '').strip(),
                    password=password,
                    role=role,
                    prenom=data.get('first_name', '').strip(),
                    nom=data.get('last_name', '').strip(),
                    telephone=data.get('telephone', '').strip(),
                    poste=data.get('poste', '').strip(),
                )

            messages.success(
                request,
                f"Utilisateur « {user.username} » créé avec succès."
                + (f" Lié à {marketeur_obj.raison_sociale}." if is_marketeur else "")
            )
            return redirect('users_detail', pk=user.pk)

        except Exception as e:
            messages.error(request, f"Erreur lors de la création : {e}")
            return render(request, self.template_name, self._ctx(data))


class ModifierUtilisateurView(LoginRequiredMixin, CanManageUsersMixin, UpdateView):
    model = User
    template_name = 'users/modifier.html'
    fields = ['email', 'first_name', 'last_name', 'is_active']

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['roles'] = Role.objects.exclude(code='LECTEUR').order_by('-systeme', 'nom').values_list('code', 'nom')
        return ctx

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        profil, _ = UserProfile.objects.get_or_create(user=self.object)
        ancien_role = profil.role
        role_code = request.POST.get('role', '')

        if role_code:
            try:
                nouveau_role = Role.objects.get(code=role_code)
                if nouveau_role != ancien_role:
                    profil.role = nouveau_role
                    self.object.is_staff = nouveau_role.code in ('SUPERADMIN', 'CHEF_DEPOT')
                    self.object.is_superuser = (nouveau_role.code == 'SUPERADMIN')
                    self.object.save(update_fields=['is_staff', 'is_superuser'])
                    ancien_nom = ancien_role.nom if ancien_role else 'Aucun'
                    messages.info(request, f"Rôle changé : {ancien_nom} → {nouveau_role.nom}")
            except Role.DoesNotExist:
                pass

        profil.telephone = request.POST.get('telephone', profil.telephone or '').strip()
        profil.poste = request.POST.get('poste', profil.poste or '').strip()
        profil.actif = 'profil_actif' in request.POST
        profil.save()

        return super().post(request, *args, **kwargs)

    def get_success_url(self):
        messages.success(self.request, "Modifications enregistrées.")
        return reverse_lazy('users_detail', kwargs={'pk': self.object.pk})


# ── Mon profil (tout utilisateur) ─────────────────────────────────────────────
class MonProfilView(LoginRequiredMixin, UpdateView):
    template_name = 'users/mon_profil.html'
    fields = ['first_name', 'last_name', 'email']

    def get_object(self):
        return self.request.user

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        profil = getattr(self.object, 'profile', None)
        if profil:
            tel = request.POST.get('telephone', '').strip()
            if tel:
                profil.telephone = tel
            if 'photo' in request.FILES:
                profil.photo = request.FILES['photo']
            profil.save(update_fields=['telephone', 'photo'])

        ancien = request.POST.get('ancien_mot_de_passe', '')
        nouveau = request.POST.get('nouveau_mot_de_passe', '')
        if ancien and nouveau:
            if not self.object.check_password(ancien):
                messages.error(request, "Ancien mot de passe incorrect.")
                return self.get(request, *args, **kwargs)
            if len(nouveau) < 8:
                messages.error(request, "Le nouveau mot de passe doit faire ≥ 8 caractères.")
                return self.get(request, *args, **kwargs)
            self.object.set_password(nouveau)
            self.object.save(update_fields=['password'])
            messages.success(request, "Mot de passe modifié. Reconnectez-vous.")

        return super().post(request, *args, **kwargs)

    def get_success_url(self):
        messages.success(self.request, "Profil mis à jour.")
        return reverse_lazy('users_mon_profil')


# ── Journal d'audit ────────────────────────────────────────────────────────────
class AuditLogView(LoginRequiredMixin, CanViewAuditMixin, ListView):
    model = AuditLog
    template_name = 'users/audit_log.html'
    context_object_name = 'logs'
    paginate_by = 50

    def get_queryset(self):
        qs = AuditLog.objects.select_related('user').order_by('-horodatage')
        f = self.request.GET
        if f.get('action'):
            qs = qs.filter(action=f['action'])
        if f.get('objet'):
            qs = qs.filter(objet_type=f['objet'])
        if f.get('user'):
            qs = qs.filter(user_id=f['user'])
        if f.get('date_from'):
            qs = qs.filter(horodatage__date__gte=f['date_from'])
        if f.get('date_to'):
            qs = qs.filter(horodatage__date__lte=f['date_to'])
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['actions_choices'] = AuditLog.Action.choices
        ctx['users_filtres'] = (
            User.objects.filter(audit_logs__isnull=False)
            .distinct().order_by('username')
        )
        ctx['objets_types'] = (
            AuditLog.objects.exclude(objet_type='')
            .values_list('objet_type', flat=True)
            .distinct().order_by('objet_type')
        )
        ctx['filtres'] = {
            'action':    self.request.GET.get('action', ''),
            'objet':     self.request.GET.get('objet', ''),
            'user':      self.request.GET.get('user', ''),
            'date_from': self.request.GET.get('date_from', ''),
            'date_to':   self.request.GET.get('date_to', ''),
        }
        return ctx


# ── Gestion des rôles ──────────────────────────────────────────────────────────
def _construire_groupes_form(codes_coches):
    from .permissions_registry import PERMISSIONS_REGISTRY
    groupes = []
    for cat_code, cat_data in PERMISSIONS_REGISTRY.items():
        perms = [
            {
                'codename': codename,
                'libelle': libelle,
                'cochee': codename in codes_coches,
            }
            for codename, libelle in cat_data['permissions']
        ]
        groupes.append({
            'code': cat_code,
            'libelle': cat_data['libelle'],
            'icone': cat_data['icone'],
            'permissions': perms,
        })
    return groupes


class ListeRolesView(LoginRequiredMixin, CanManageRolesMixin, ListView):
    model = Role
    template_name = 'users/roles_liste.html'
    context_object_name = 'roles'

    def get_queryset(self):
        return Role.objects.annotate(
            nb_users=Count('utilisateurs', distinct=True),
            nb_perms=Count('permissions', distinct=True),
        ).order_by('-systeme', 'nom')


class DetailRoleView(LoginRequiredMixin, CanManageRolesMixin, DetailView):
    model = Role
    template_name = 'users/role_detail.html'
    context_object_name = 'role'

    def get_context_data(self, **kwargs):
        from .permissions_registry import PERMISSIONS_REGISTRY
        ctx = super().get_context_data(**kwargs)

        codes_role = set(self.object.permissions.values_list('codename', flat=True))

        groupes = []
        for cat_code, cat_data in PERMISSIONS_REGISTRY.items():
            perms_data = [
                {
                    'codename': codename,
                    'libelle': libelle,
                    'cochee': codename in codes_role,
                }
                for codename, libelle in cat_data['permissions']
            ]
            groupes.append({
                'code': cat_code,
                'libelle': cat_data['libelle'],
                'icone': cat_data['icone'],
                'permissions': perms_data,
                'nb_cochees': sum(1 for p in perms_data if p['cochee']),
                'nb_total': len(perms_data),
            })

        ctx['groupes'] = groupes
        ctx['utilisateurs'] = self.object.utilisateurs.select_related('user')[:50]
        return ctx


class CreerRoleView(LoginRequiredMixin, CanManageRolesMixin, View):
    template_name = 'users/role_form.html'

    def get(self, request):
        return render(request, self.template_name, {
            'role': None,
            'groupes': _construire_groupes_form(set()),
            'mode': 'creation',
            'couleurs': Role.COULEUR_CHOICES,
        })

    def post(self, request):
        try:
            code = request.POST.get('code', '').upper().replace(' ', '_').strip()
            if not code or not code.replace('_', '').isalnum():
                messages.error(request, "Le code doit être alphanumérique (lettres + tirets bas).")
                return self.get(request)

            role = Role.objects.create(
                nom=request.POST['nom'].strip(),
                code=code,
                description=request.POST.get('description', '').strip(),
                couleur=request.POST.get('couleur', 'gray'),
                systeme=False,
                cree_par=request.user,
            )
            codes = request.POST.getlist('permissions')
            perms = Permission.objects.filter(codename__in=codes)
            role.permissions.set(perms)

            messages.success(
                request,
                f"Rôle '{role.nom}' créé avec {role.permissions.count()} permission(s)."
            )
            return redirect('roles_detail', pk=role.pk)
        except Exception as e:
            messages.error(request, f"Erreur : {e}")
            return self.get(request)


class ModifierRoleView(LoginRequiredMixin, CanManageRolesMixin, View):
    template_name = 'users/role_form.html'

    def get(self, request, pk):
        role = get_object_or_404(Role, pk=pk)
        codes = set(role.permissions.values_list('codename', flat=True))
        return render(request, self.template_name, {
            'role': role,
            'groupes': _construire_groupes_form(codes),
            'mode': 'modification',
            'couleurs': Role.COULEUR_CHOICES,
        })

    def post(self, request, pk):
        role = get_object_or_404(Role, pk=pk)
        try:
            role.nom = request.POST['nom'].strip()
            role.description = request.POST.get('description', '').strip()
            role.couleur = request.POST.get('couleur', role.couleur)
            role.save()

            codes = request.POST.getlist('permissions')

            # Garde-fou SUPERADMIN
            if role.code == 'SUPERADMIN':
                from .permissions_registry import PERMISSIONS_REGISTRY
                tous_codes = set()
                for cat in PERMISSIONS_REGISTRY.values():
                    tous_codes.update(c for c, _ in cat['permissions'])
                if set(codes) != tous_codes:
                    messages.error(
                        request,
                        "Le rôle SUPERADMIN doit conserver TOUTES les permissions. "
                        "Modifications des permissions annulées."
                    )
                    return redirect('roles_modifier', pk=pk)

            perms = Permission.objects.filter(codename__in=codes)
            role.permissions.set(perms)

            messages.success(request, f"Rôle '{role.nom}' mis à jour.")
            return redirect('roles_detail', pk=role.pk)
        except Exception as e:
            messages.error(request, f"Erreur : {e}")
            return redirect('roles_modifier', pk=pk)


class SupprimerRoleView(LoginRequiredMixin, CanManageRolesMixin, View):
    def post(self, request, pk):
        role = get_object_or_404(Role, pk=pk)
        try:
            nom = role.nom
            role.delete()
            messages.success(request, f"Rôle '{nom}' supprimé.")
            return redirect('roles_liste')
        except Exception as e:
            messages.error(request, str(e))
            return redirect('roles_detail', pk=pk)


class ListePermissionsView(LoginRequiredMixin, CanManageRolesMixin, TemplateView):
    """Vue lecture seule du référentiel des permissions."""
    template_name = 'users/permissions_liste.html'

    def get_context_data(self, **kwargs):
        from .permissions_registry import PERMISSIONS_REGISTRY
        ctx = super().get_context_data(**kwargs)

        groupes = []
        for cat_code, cat_data in PERMISSIONS_REGISTRY.items():
            perms_data = []
            for codename, libelle in cat_data['permissions']:
                perm = Permission.objects.filter(codename=codename).first()
                nb_roles = perm.roles_sgds.count() if perm else 0
                perms_data.append({
                    'codename': codename,
                    'libelle': libelle,
                    'nb_roles': nb_roles,
                    'perm_pk': perm.pk if perm else None,
                })
            groupes.append({
                'code': cat_code,
                'libelle': cat_data['libelle'],
                'icone': cat_data['icone'],
                'permissions': perms_data,
            })
        ctx['groupes'] = groupes
        return ctx
