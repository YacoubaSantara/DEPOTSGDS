from functools import wraps
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, login_not_required
from django.contrib import messages
from django.db.models import Q
from django.conf import settings
from .models import UtilisateurSGDS
from .forms import UtilisateurCreationForm, UtilisateurModificationForm, UtilisateurProfilForm


# ── Décorateur admin ───────────────────────────────────────────
def admin_required(view_func):
    """Accès réservé aux utilisateurs avec rôle ADMIN ou superuser."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(f"{settings.LOGIN_URL}?next={request.path}")
        if not request.user.is_admin_role:
            messages.error(request, "Accès réservé aux administrateurs.")
            return redirect('admin_dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper


# ── Authentification ───────────────────────────────────────────

@login_not_required
def connexion(request):
    """Page de connexion — accessible sans authentification."""
    if request.user.is_authenticated:
        if request.user.is_marketeur_role and request.user.marketeur:
            return redirect('client_dashboard')
        return redirect('admin_dashboard')

    error = None
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')

        if not username or not password:
            error = "Veuillez renseigner votre identifiant et votre mot de passe."
        else:
            user = authenticate(request, username=username, password=password)
            if user is not None:
                if user.is_active:
                    login(request, user)
                    if not request.POST.get('remember_me'):
                        request.session.set_expiry(0)
                    next_url = request.GET.get('next', '')
                    if next_url and next_url.startswith('/') and not next_url.startswith('//'):
                        return redirect(next_url)
                    # Redirection selon le rôle
                    if user.is_marketeur_role and user.marketeur:
                        return redirect('client_dashboard')
                    return redirect('admin_dashboard')
                else:
                    error = "Ce compte est désactivé. Contactez l'administrateur."
            else:
                error = "Identifiant ou mot de passe incorrect."

    return render(request, 'Auth/login.html', {'error': error})


@login_required
def deconnexion(request):
    """Déconnexion — POST uniquement pour prévenir les déconnexions accidentelles."""
    if request.method == 'POST':
        logout(request)
        return redirect('connexion')
    return render(request, 'Auth/logout_confirm.html')


# ── Utilisateurs ───────────────────────────────────────────────

@admin_required
def user_list(request):
    qs   = UtilisateurSGDS.objects.all().order_by('username')
    q    = request.GET.get('q', '').strip()
    role = request.GET.get('role', '')

    if q:
        qs = qs.filter(
            Q(username__icontains=q) | Q(first_name__icontains=q) |
            Q(last_name__icontains=q) | Q(email__icontains=q)
        )
    if role:
        qs = qs.filter(role=role)

    ctx = {
        'utilisateurs': qs,
        'total':        UtilisateurSGDS.objects.count(),
        'nb_admin':     UtilisateurSGDS.objects.filter(role='ADMIN').count(),
        'nb_operateur': UtilisateurSGDS.objects.filter(role='OPERATEUR').count(),
        'nb_marketeur': UtilisateurSGDS.objects.filter(role='MARKETEUR').count(),
        'role_choices': UtilisateurSGDS.ROLE_CHOICES,
        'q':    q,
        'role': role,
    }
    return render(request, 'Users/user_list.html', ctx)


@login_required
def user_detail(request, pk):
    utilisateur = get_object_or_404(UtilisateurSGDS, pk=pk)
    if utilisateur.pk != request.user.pk and not request.user.is_admin_role:
        messages.error(request, "Accès refusé.")
        return redirect('user_detail', pk=request.user.pk)
    return render(request, 'Users/user_detail.html', {'utilisateur': utilisateur})


@admin_required
def user_create(request):
    if request.method == 'POST':
        form = UtilisateurCreationForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            messages.success(request, f'Utilisateur « {user.username} » créé avec succès.')
            return redirect('user_list')
    else:
        form = UtilisateurCreationForm()
    return render(request, 'Users/user_form.html', {'form': form, 'action': 'Nouveau'})


@login_required
def user_update(request, pk):
    utilisateur = get_object_or_404(UtilisateurSGDS, pk=pk)
    is_self_edit = (utilisateur.pk == request.user.pk)

    if not is_self_edit and not request.user.is_admin_role:
        messages.error(request, "Vous ne pouvez modifier que votre propre profil.")
        return redirect('user_detail', pk=request.user.pk)

    FormClass = UtilisateurModificationForm if request.user.is_admin_role else UtilisateurProfilForm

    if request.method == 'POST':
        form = FormClass(request.POST, request.FILES, instance=utilisateur)
        if form.is_valid():
            form.save()
            if is_self_edit:
                messages.success(request, "Votre profil a été mis à jour.")
            else:
                messages.success(request, f'Utilisateur « {utilisateur.username} » modifié avec succès.')
            return redirect('user_detail', pk=pk)
    else:
        form = FormClass(instance=utilisateur)

    return render(request, 'Users/user_form.html', {
        'form':         form,
        'action':       'Mon profil' if is_self_edit and not request.user.is_admin_role else 'Modifier',
        'utilisateur':  utilisateur,
        'is_self_edit': is_self_edit,
    })


@admin_required
def user_delete(request, pk):
    utilisateur = get_object_or_404(UtilisateurSGDS, pk=pk)
    if utilisateur == request.user:
        messages.error(request, "Vous ne pouvez pas supprimer votre propre compte.")
        return redirect('user_list')
    if request.method == 'POST':
        username = utilisateur.username
        utilisateur.delete()
        messages.success(request, f'Utilisateur « {username} » supprimé.')
        return redirect('user_list')
    return render(request, 'Users/user_confirm_delete.html', {'utilisateur': utilisateur})
