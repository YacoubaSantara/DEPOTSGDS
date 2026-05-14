from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.db.models import Q
from .models import UtilisateurSGDS
from SGDS.models import Marketeur


class UtilisateurCreationForm(UserCreationForm):

    class Meta(UserCreationForm.Meta):
        model  = UtilisateurSGDS
        fields = [
            'username', 'first_name', 'last_name', 'email',
            'role', 'telephone', 'photo', 'marketeur', 'is_active',
        ]
        widgets = {
            'username':   forms.TextInput(attrs={'placeholder': 'Identifiant de connexion'}),
            'first_name': forms.TextInput(attrs={'placeholder': 'Prénom(s)'}),
            'last_name':  forms.TextInput(attrs={'placeholder': 'Nom de famille'}),
            'email':      forms.EmailInput(attrs={'placeholder': 'adresse@email.ml'}),
            'telephone':  forms.TextInput(attrs={'placeholder': '+223 70 xx xx xx'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for f in self.fields:
            self.fields[f].widget.attrs.update({'class': 'form-control'})
        self.fields['first_name'].required = True
        self.fields['last_name'].required  = True
        self.fields['email'].required      = False
        self.fields['telephone'].required  = False
        self.fields['photo'].required      = False
        self.fields['marketeur'].required  = False
        self.fields['marketeur'].queryset  = Marketeur.objects.filter(
            compte_utilisateur__isnull=True, statut='ACTIF'
        )
        self.fields['marketeur'].empty_label = "— Aucun —"


class UtilisateurModificationForm(forms.ModelForm):

    nouveau_mot_de_passe = forms.CharField(
        required=False,
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Laisser vide pour ne pas changer'}),
        label="Nouveau mot de passe",
    )
    confirmer_mot_de_passe = forms.CharField(
        required=False,
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirmer le nouveau mot de passe'}),
        label="Confirmer le mot de passe",
    )

    class Meta:
        model  = UtilisateurSGDS
        fields = [
            'username', 'first_name', 'last_name', 'email',
            'role', 'telephone', 'photo', 'marketeur', 'is_active',
        ]
        widgets = {
            'username':   forms.TextInput(attrs={'placeholder': 'Identifiant de connexion'}),
            'first_name': forms.TextInput(attrs={'placeholder': 'Prénom(s)'}),
            'last_name':  forms.TextInput(attrs={'placeholder': 'Nom de famille'}),
            'email':      forms.EmailInput(attrs={'placeholder': 'adresse@email.ml'}),
            'telephone':  forms.TextInput(attrs={'placeholder': '+223 70 xx xx xx'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        instance = kwargs.get('instance')
        for f in self.fields:
            self.fields[f].widget.attrs.update({'class': 'form-control'})
        self.fields['first_name'].required = True
        self.fields['last_name'].required  = True
        self.fields['email'].required      = False
        self.fields['telephone'].required  = False
        self.fields['photo'].required      = False
        self.fields['marketeur'].required  = False
        current_pk = instance.marketeur_id if instance else None
        self.fields['marketeur'].queryset = Marketeur.objects.filter(
            statut='ACTIF'
        ).filter(
            Q(compte_utilisateur__isnull=True) | Q(pk=current_pk)
        )
        self.fields['marketeur'].empty_label = "— Aucun —"

    def clean(self):
        cleaned_data = super().clean()
        pwd1 = cleaned_data.get('nouveau_mot_de_passe')
        pwd2 = cleaned_data.get('confirmer_mot_de_passe')
        if pwd1 or pwd2:
            if pwd1 != pwd2:
                self.add_error('confirmer_mot_de_passe', "Les mots de passe ne correspondent pas.")
            elif len(pwd1) < 8:
                self.add_error('nouveau_mot_de_passe', "Le mot de passe doit contenir au moins 8 caractères.")
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        pwd = self.cleaned_data.get('nouveau_mot_de_passe')
        if pwd:
            user.set_password(pwd)
        if commit:
            user.save()
        return user


class UtilisateurProfilForm(forms.ModelForm):
    """Formulaire de profil personnel — sans les champs réservés à l'admin."""

    nouveau_mot_de_passe = forms.CharField(
        required=False,
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Laisser vide pour ne pas changer'}),
        label="Nouveau mot de passe",
    )
    confirmer_mot_de_passe = forms.CharField(
        required=False,
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirmer le nouveau mot de passe'}),
        label="Confirmer le mot de passe",
    )

    class Meta:
        model  = UtilisateurSGDS
        fields = ['first_name', 'last_name', 'email', 'telephone', 'photo']
        widgets = {
            'first_name': forms.TextInput(attrs={'placeholder': 'Prénom(s)'}),
            'last_name':  forms.TextInput(attrs={'placeholder': 'Nom de famille'}),
            'email':      forms.EmailInput(attrs={'placeholder': 'adresse@email.ml'}),
            'telephone':  forms.TextInput(attrs={'placeholder': '+223 70 xx xx xx'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for f in self.fields:
            self.fields[f].widget.attrs.update({'class': 'form-control'})
        self.fields['first_name'].required = True
        self.fields['last_name'].required  = True
        self.fields['email'].required      = False
        self.fields['telephone'].required  = False
        self.fields['photo'].required      = False

    def clean(self):
        cleaned_data = super().clean()
        pwd1 = cleaned_data.get('nouveau_mot_de_passe')
        pwd2 = cleaned_data.get('confirmer_mot_de_passe')
        if pwd1 or pwd2:
            if pwd1 != pwd2:
                self.add_error('confirmer_mot_de_passe', "Les mots de passe ne correspondent pas.")
            elif len(pwd1) < 8:
                self.add_error('nouveau_mot_de_passe', "Le mot de passe doit contenir au moins 8 caractères.")
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        pwd = self.cleaned_data.get('nouveau_mot_de_passe')
        if pwd:
            user.set_password(pwd)
        if commit:
            user.save()
        return user
