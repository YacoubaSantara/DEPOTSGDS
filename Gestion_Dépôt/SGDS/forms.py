from django import forms
from django.db.models import Q
from django.forms import inlineformset_factory
from .models import Marketeur, Camion, Chauffeur, Famille, Produit, Cuve, ParametreJaugeageCuve, JaugeageJour, MesureCuve, Mouvement, LigneMouvement, Societe, MouvementDocument, CompartimentCamion


class MarketeurForm(forms.ModelForm):

    class Meta:
        model  = Marketeur
        fields = [
            # Identification
            'raison_sociale', 'sigle', 'forme_juridique', 'capital_social',
            'numero_registre_commerce', 'numero_contribuable', 'numero_ifu',
            'date_creation_societe', 'domaine_activite', 'logo',
            # Coordonnées
            'adresse', 'quartier', 'ville', 'pays', 'boite_postale',
            'telephone', 'telephone2', 'email', 'site_web',
            # Représentant
            'nom_representant', 'prenom_representant', 'fonction_representant',
            'telephone_representant', 'email_representant',
            # Banque
            'banque', 'numero_compte', 'code_swift',
            # Statut
            'statut', 'notes',
        ]
        widgets = {
            'raison_sociale':          forms.TextInput(attrs={'placeholder': 'Ex: MALI DISTRIBUTION SARL'}),
            'sigle':                   forms.TextInput(attrs={'placeholder': 'Ex: BDS'}),
            'capital_social':          forms.NumberInput(attrs={'placeholder': 'Ex: 10000000'}),
            'numero_registre_commerce':forms.TextInput(attrs={'placeholder': 'Ex: ML-BKO-2021-B-00123'}),
            'numero_contribuable':     forms.TextInput(attrs={'placeholder': 'Ex: 00123456Y'}),
            'numero_ifu':              forms.TextInput(attrs={'placeholder': 'Ex: 20211234567'}),
            'date_creation_societe':   forms.DateInput(attrs={'type': 'date'}),
            'domaine_activite':        forms.TextInput(attrs={'placeholder': 'Ex: Distribution de produits alimentaires'}),
            'adresse':                 forms.Textarea(attrs={'rows': 3, 'placeholder': 'Rue, avenue, numéro…'}),
            'quartier':                forms.TextInput(attrs={'placeholder': 'Ex: Secteur 15'}),
            'ville':                   forms.TextInput(attrs={'placeholder': 'Ex: Bamako'}),
            'pays':                    forms.TextInput(attrs={'value': 'Mali'}),
            'boite_postale':           forms.TextInput(attrs={'placeholder': 'Ex: BP 1234'}),
            'telephone':               forms.TextInput(attrs={'placeholder': '+223 20 xx xx xx'}),
            'telephone2':              forms.TextInput(attrs={'placeholder': '+223 70 xx xx xx'}),
            'email':                   forms.EmailInput(attrs={'placeholder': 'contact@societe.ml'}),
            'site_web':                forms.URLInput(attrs={'placeholder': 'https://www.societe.ml'}),
            'nom_representant':        forms.TextInput(attrs={'placeholder': 'Nom de famille'}),
            'prenom_representant':     forms.TextInput(attrs={'placeholder': 'Prénom(s)'}),
            'fonction_representant':   forms.TextInput(attrs={'placeholder': 'Ex: Directeur Général'}),
            'telephone_representant':  forms.TextInput(attrs={'placeholder': '+223 70 xx xx xx'}),
            'email_representant':      forms.EmailInput(attrs={'placeholder': 'representant@societe.ml'}),
            'banque':                  forms.TextInput(attrs={'placeholder': 'Ex: BDM-SA, BMS-SA, Coris Bank…'}),
            'numero_compte':           forms.TextInput(attrs={'placeholder': 'Ex: 000 12345 67890 12'}),
            'code_swift':              forms.TextInput(attrs={'placeholder': 'Ex: BDMAMLBA'}),
            'notes':                   forms.Textarea(attrs={'rows': 4, 'placeholder': 'Informations complémentaires…'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Champs obligatoires — styling
        required = ['raison_sociale', 'forme_juridique', 'adresse', 'ville',
                    'telephone', 'nom_representant', 'prenom_representant']
        for f in self.fields:
            css = 'form-control'
            if f == 'logo':
                css = 'form-control'
            self.fields[f].widget.attrs.update({'class': css})
            if f not in required:
                self.fields[f].required = False
        # Valeur par défaut pays
        if not self.instance.pk:
            self.fields['pays'].initial = 'Mali'


class CamionForm(forms.ModelForm):

    class Meta:
        model  = Camion
        fields = [
            # Identification
            'immatriculation', 'marque', 'modele', 'annee_fabrication', 'couleur',
            'numero_serie_chassis', 'numero_serie_moteur',
            # Citerne
            'capacite_totale', 'nombre_compartiments', 'type_produit',
            # Documents
            'date_mise_en_circulation', 'carte_grise',
            # Assurance
            'compagnie_assurance', 'numero_police_assurance', 'date_expiration_assurance',
            # Technique
            'date_derniere_revision', 'date_prochaine_revision', 'kilometrage',
            # Lien & statut
            'marketeur', 'statut', 'notes',
        ]
        widgets = {
            'immatriculation':          forms.TextInput(attrs={'placeholder': 'Ex: 00 ML 1234 A'}),
            'marque':                   forms.TextInput(attrs={'placeholder': 'Ex: Mercedes-Benz, Scania…'}),
            'modele':                   forms.TextInput(attrs={'placeholder': 'Ex: Actros 2545'}),
            'annee_fabrication':        forms.NumberInput(attrs={'placeholder': 'Ex: 2020'}),
            'couleur':                  forms.TextInput(attrs={'placeholder': 'Ex: Blanc, Gris…'}),
            'numero_serie_chassis':     forms.TextInput(attrs={'placeholder': 'N° châssis'}),
            'numero_serie_moteur':      forms.TextInput(attrs={'placeholder': 'N° moteur'}),
            'capacite_totale':          forms.NumberInput(attrs={'placeholder': 'Ex: 35000'}),
            'nombre_compartiments':     forms.NumberInput(attrs={'placeholder': 'Ex: 5'}),
            'date_mise_en_circulation': forms.DateInput(attrs={'type': 'date'}),
            'compagnie_assurance':      forms.TextInput(attrs={'placeholder': 'Ex: SONAR, UAB…'}),
            'numero_police_assurance':  forms.TextInput(attrs={'placeholder': 'N° police'}),
            'date_expiration_assurance':forms.DateInput(attrs={'type': 'date'}),
            'date_derniere_revision':   forms.DateInput(attrs={'type': 'date'}),
            'date_prochaine_revision':  forms.DateInput(attrs={'type': 'date'}),
            'kilometrage':              forms.NumberInput(attrs={'placeholder': 'Ex: 150000'}),
            'notes':                    forms.Textarea(attrs={'rows': 3, 'placeholder': 'Observations…'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        required = ['immatriculation', 'marque', 'capacite_totale', 'type_produit']
        for f in self.fields:
            self.fields[f].widget.attrs.update({'class': 'form-control'})
            if f not in required:
                self.fields[f].required = False


class ChauffeurForm(forms.ModelForm):

    class Meta:
        model  = Chauffeur
        fields = [
            # Identité
            'nom', 'prenom', 'date_naissance', 'lieu_naissance', 'nationalite', 'photo',
            # Contact
            'telephone', 'telephone2', 'email', 'adresse',
            # Permis
            'numero_permis', 'categorie_permis', 'date_obtention_permis', 'date_expiration_permis',
            # Professionnel
            'numero_employe', 'date_embauche',
            # Liens & statut
            'marketeur', 'camion', 'statut', 'notes',
        ]
        widgets = {
            'nom':                    forms.TextInput(attrs={'placeholder': 'Nom de famille'}),
            'prenom':                 forms.TextInput(attrs={'placeholder': 'Prénom(s)'}),
            'date_naissance':         forms.DateInput(attrs={'type': 'date'}),
            'lieu_naissance':         forms.TextInput(attrs={'placeholder': 'Ex: Bamako'}),
            'nationalite':            forms.TextInput(attrs={'placeholder': 'Ex: Malien(ne)'}),
            'telephone':              forms.TextInput(attrs={'placeholder': '+223 70 xx xx xx'}),
            'telephone2':             forms.TextInput(attrs={'placeholder': '+223 65 xx xx xx'}),
            'email':                  forms.EmailInput(attrs={'placeholder': 'chauffeur@email.com'}),
            'adresse':                forms.Textarea(attrs={'rows': 2, 'placeholder': 'Adresse résidence'}),
            'numero_permis':          forms.TextInput(attrs={'placeholder': 'N° permis de conduire'}),
            'date_obtention_permis':  forms.DateInput(attrs={'type': 'date'}),
            'date_expiration_permis': forms.DateInput(attrs={'type': 'date'}),
            'numero_employe':         forms.TextInput(attrs={
                'readonly': True,
                'style': 'background-color:#e9ecef; cursor:not-allowed; color:#6c757d;',
            }),
            'date_embauche':          forms.DateInput(attrs={'type': 'date'}),
            'notes':                  forms.Textarea(attrs={'rows': 3, 'placeholder': 'Observations…'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        required = ['nom', 'prenom', 'telephone', 'numero_permis', 'categorie_permis']
        for f in self.fields:
            self.fields[f].widget.attrs.update({'class': 'form-control'})
            if f not in required:
                self.fields[f].required = False
        if not self.instance.pk:
            self.fields['nationalite'].initial = 'Malien(ne)'
            from .models import Chauffeur as _Chauffeur
            self.fields['numero_employe'].initial = _Chauffeur.get_next_numero()


# ─────────────────────────────────────────────────────────────
#  FAMILLE
# ─────────────────────────────────────────────────────────────
# ─────────────────────────────────────────────────────────────
#  COMPARTIMENT CAMION
# ─────────────────────────────────────────────────────────────
class CompartimentCamionForm(forms.ModelForm):
    class Meta:
        model  = CompartimentCamion
        fields = ['numero', 'capacite']
        widgets = {
            'numero':   forms.NumberInput(attrs={
                'class': 'form-control form-control-sm',
                'min': '1', 'readonly': True,
            }),
            'capacite': forms.NumberInput(attrs={
                'class': 'form-control form-control-sm',
                'step': '0.01', 'min': '0',
                'placeholder': 'Ex: 5000.00',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['numero'].required   = True
        self.fields['capacite'].required = True


CompartimentCamionFormSet = inlineformset_factory(
    Camion,
    CompartimentCamion,
    form=CompartimentCamionForm,
    fields=['numero', 'capacite'],
    extra=0,
    can_delete=True,
    min_num=0,
    validate_min=False,
)


# ─────────────────────────────────────────────────────────────
#  FAMILLE
# ─────────────────────────────────────────────────────────────
class FamilleForm(forms.ModelForm):

    class Meta:
        model  = Famille
        fields = ['nom', 'code', 'description', 'couleur', 'statut']
        widgets = {
            'nom':         forms.TextInput(attrs={'placeholder': 'Ex: Hydrocarbures liquides'}),
            'code':        forms.TextInput(attrs={'placeholder': 'Ex: HYD'}),
            'description': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Description de la famille…'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        required = ['nom', 'code', 'couleur']
        for f in self.fields:
            self.fields[f].widget.attrs.update({'class': 'form-control'})
            if f not in required:
                self.fields[f].required = False


# ─────────────────────────────────────────────────────────────
#  PRODUIT
# ─────────────────────────────────────────────────────────────
class ProduitForm(forms.ModelForm):

    class Meta:
        model  = Produit
        fields = [
            'nom', 'code', 'famille', 'description',
            'unite_mesure', 'prix_unitaire', 'prix_passage', 'seuil_alerte',
            'statut', 'notes',
        ]
        widgets = {
            'nom':          forms.TextInput(attrs={'placeholder': 'Ex: Gasoil 50 ppm'}),
            'code':         forms.TextInput(attrs={'placeholder': 'Ex: GSL-50'}),
            'description':  forms.Textarea(attrs={'rows': 3, 'placeholder': 'Description du produit…'}),
            'prix_unitaire':forms.NumberInput(attrs={'placeholder': 'Ex: 650'}),
            'prix_passage': forms.NumberInput(attrs={'placeholder': 'Ex: 4.7554', 'step': '0.0001'}),
            'seuil_alerte': forms.NumberInput(attrs={'placeholder': 'Ex: 5000'}),
            'notes':        forms.Textarea(attrs={'rows': 3, 'placeholder': 'Observations…'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        required = ['nom', 'code', 'famille', 'unite_mesure']
        for f in self.fields:
            self.fields[f].widget.attrs.update({'class': 'form-control'})
            if f not in required:
                self.fields[f].required = False


# ─────────────────────────────────────────────────────────────
#  CUVE
# ─────────────────────────────────────────────────────────────
class CuveForm(forms.ModelForm):

    class Meta:
        model  = Cuve
        fields = [
            'numero', 'designation', 'produit',
            'capacite_totale', 'niveau_actuel',
            'type_cuve', 'materiau', 'localisation',
            'date_installation', 'date_derniere_inspection', 'date_prochaine_inspection',
            'statut', 'notes',
        ]
        widgets = {
            'numero':       forms.TextInput(attrs={'placeholder': 'Ex: CUV-001'}),
            'designation':  forms.TextInput(attrs={'placeholder': 'Ex: Cuve gasoil principale'}),
            'capacite_totale': forms.NumberInput(attrs={'placeholder': 'Ex: 50000'}),
            'niveau_actuel':   forms.NumberInput(attrs={'placeholder': 'Ex: 25000'}),
            'localisation': forms.TextInput(attrs={'placeholder': 'Ex: Zone A, Baie 3'}),
            'date_installation':        forms.DateInput(attrs={'type': 'date'}),
            'date_derniere_inspection': forms.DateInput(attrs={'type': 'date'}),
            'date_prochaine_inspection':forms.DateInput(attrs={'type': 'date'}),
            'notes':        forms.Textarea(attrs={'rows': 3, 'placeholder': 'Observations…'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        required = ['numero', 'designation', 'capacite_totale', 'type_cuve', 'materiau']
        for f in self.fields:
            self.fields[f].widget.attrs.update({'class': 'form-control'})
            if f not in required:
                self.fields[f].required = False


# ─────────────────────────────────────────────────────────────
#  PARAMÈTRE DE JAUGEAGE
# ─────────────────────────────────────────────────────────────
class ParametreJaugeageCuveForm(forms.ModelForm):

    class Meta:
        model  = ParametreJaugeageCuve
        fields = [
            'hauteur_totale_temoin', 'hauteur_min_livraison', 'correction_creux', 'remplissage_maxi',
            'v_a', 'v_mn',
            'reference_certificat', 'date_certificat', 'organisme_certificateur', 'date_prochain_jaugeage',
            'is_pompe', 'notes',
        ]
        widgets = {
            'hauteur_totale_temoin':   forms.NumberInput(attrs={'placeholder': 'Ex: 12981'}),
            'hauteur_min_livraison':   forms.NumberInput(attrs={'placeholder': 'Ex: 2000'}),
            'correction_creux':        forms.NumberInput(attrs={'placeholder': 'Ex: 4'}),
            'remplissage_maxi':        forms.NumberInput(attrs={'placeholder': 'Ex: 48000.00'}),
            'v_a':                     forms.NumberInput(attrs={'placeholder': 'Ex: 45230.50', 'step': '0.01'}),
            'v_mn':                    forms.NumberInput(attrs={'placeholder': 'Ex: 38'}),
            'reference_certificat':    forms.TextInput(attrs={'placeholder': 'Ex: CERT-2024-001'}),
            'date_certificat':         forms.DateInput(attrs={'type': 'date'}),
            'organisme_certificateur': forms.TextInput(attrs={'placeholder': 'Ex: DNCC Mali'}),
            'date_prochain_jaugeage':  forms.DateInput(attrs={'type': 'date'}),
            'notes':                   forms.Textarea(attrs={'rows': 3, 'placeholder': 'Observations…'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        required = ['hauteur_totale_temoin', 'remplissage_maxi', 'v_a', 'v_mn']
        for f in self.fields:
            if f == 'is_pompe':
                self.fields[f].widget.attrs.update({'class': 'form-check-input'})
            else:
                self.fields[f].widget.attrs.update({'class': 'form-control'})
            if f not in required:
                self.fields[f].required = False


# ─────────────────────────────────────────────────────────────
#  JAUGEAGE DU JOUR
# ─────────────────────────────────────────────────────────────
class JaugeageJourForm(forms.ModelForm):

    class Meta:
        model  = JaugeageJour
        fields = [
            'date_jaugeage', 'type_jaugeage', 'heure_jaugeage',
            'depot', 'type_depot', 'temperature_reference',
            'operateur', 'notes',
        ]
        widgets = {
            'date_jaugeage':         forms.DateInput(attrs={'type': 'date'}),
            'heure_jaugeage':        forms.TimeInput(attrs={'type': 'time'}),
            'depot':                 forms.TextInput(attrs={'placeholder': 'Ex: SGDS SANKE'}),
            'type_depot':            forms.TextInput(attrs={'placeholder': 'Ex: Dépôt de droit'}),
            'temperature_reference': forms.NumberInput(attrs={'placeholder': '15.0', 'step': '0.1'}),
            'operateur':             forms.TextInput(attrs={'placeholder': 'Nom de l\'opérateur'}),
            'notes':                 forms.Textarea(attrs={'rows': 3, 'placeholder': 'Observations…'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        required = ['date_jaugeage', 'type_jaugeage']
        for f in self.fields:
            self.fields[f].widget.attrs.update({'class': 'form-control'})
            if f not in required:
                self.fields[f].required = False


# ─────────────────────────────────────────────────────────────
#  MESURE CUVE (pour formset dans la saisie)
# ─────────────────────────────────────────────────────────────
class MesureCuveForm(forms.ModelForm):

    class Meta:
        model  = MesureCuve
        fields = [
            'creux_mesure',
            'v_a_saisi',
            't1', 't2', 't3', 'temperature_obs',
            'densite_moyenne', 'densite_15c', 'facteur_vcf',
            'volume_additionnel', 'volume_tuyauterie', 'volume_eau',
        ]
        widgets = {
            'creux_mesure':        forms.NumberInput(attrs={'placeholder': '—', 'step': '1'}),
            'v_a_saisi':           forms.NumberInput(attrs={'placeholder': 'Lire dans le cahier', 'step': '1'}),
            't1':                  forms.NumberInput(attrs={'placeholder': '—', 'step': '0.01'}),
            't2':                  forms.NumberInput(attrs={'placeholder': '—', 'step': '0.01'}),
            't3':                  forms.NumberInput(attrs={'placeholder': '—', 'step': '0.01'}),
            'temperature_obs':     forms.NumberInput(attrs={'placeholder': '—', 'step': '0.01'}),
            'densite_moyenne':     forms.NumberInput(attrs={'placeholder': '—', 'step': '0.01'}),
            'densite_15c':         forms.NumberInput(attrs={'placeholder': '—', 'step': '0.01'}),
            'facteur_vcf':         forms.NumberInput(attrs={'placeholder': '—', 'step': '0.0001'}),
            'volume_additionnel':  forms.NumberInput(attrs={'placeholder': '0', 'step': '1'}),
            'volume_tuyauterie':   forms.NumberInput(attrs={'placeholder': '0', 'step': '1'}),
            'volume_eau':          forms.NumberInput(attrs={'placeholder': '0', 'step': '1'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for f in self.fields:
            self.fields[f].required = False
            self.fields[f].widget.attrs.update({'class': 'form-control form-control-sm'})

    # ── Validation métier ────────────────────────────────────────

    def clean_creux_mesure(self):
        v = self.cleaned_data.get('creux_mesure')
        if v is not None:
            if v < 0:
                raise forms.ValidationError("Le creux mesuré doit être positif.")
            # Vérifier < HTT si les paramètres de jaugeage sont disponibles
            try:
                htt = self.instance.cuve.parametre_jaugeage.hauteur_totale_temoin
                if v >= htt:
                    raise forms.ValidationError(
                        f"Le creux mesuré ({v} mm) doit être inférieur à la HTT ({htt} mm)."
                    )
            except AttributeError:
                pass  # Pas de parametre_jaugeage — on accepte sans validation HTT
        return v

    def clean(self):
        cleaned_data = super().clean()

        # Validation des températures (0–60°C)
        for field in ('t1', 't2', 't3', 'temperature_obs'):
            val = cleaned_data.get(field)
            if val is not None and not (0 <= float(val) <= 60):
                self.add_error(field, "La température doit être entre 0 et 60 °C.")

        # Validation de la densité (600–900 kg/m³)
        densite = cleaned_data.get('densite_moyenne')
        if densite is not None and not (600 <= float(densite) <= 900):
            self.add_error('densite_moyenne', "La densité doit être entre 600 et 900 kg/m³.")

        return cleaned_data


# ─────────────────────────────────────────────────────────────
#  FORMULAIRE MOUVEMENT (entrée/sortie/cession/acquittement)
# ─────────────────────────────────────────────────────────────
class MouvementForm(forms.ModelForm):

    class Meta:
        model  = Mouvement
        # On exclut les champs auto-calculés (remplis dans Mouvement.save)
        # et les timestamps automatiques.
        exclude = [
            'date_saisie',
            'date_modification',
            'collaborateur',       # auto-rempli depuis request.user à la création
            'cuve',                # déprécié — remplacé par LigneMouvement
            # Calculs auto ENTREE
            'densite_15c_calculee',
            'ecart_densite_15c',
            'coefficient_conversion_15c',
            'volume_15c_recu',
            'perte_gain_reception',
            'perte_gain_15c',
            'poids_kg',
            # Calculs auto SORTIE
            'coefficient_conversion_sortie',
            'volume_15c_sortie',
            'poids_sortie_kg',
            # Calculs auto CESSION
            'cession_densite_15c',
            'cession_coefficient_vcf',
            # Calcul auto ACQUITTEMENT (calculé depuis entree_source.coefficient_conversion_15c)
            'acquittement_volume_15c',
        ]
        widgets = {
            # Dates
            'date_mouvement':                   forms.DateInput(attrs={'type': 'date'}),
            'date_chargement':                  forms.DateInput(attrs={'type': 'date'}),
            'date_dechargement':                forms.DateInput(attrs={'type': 'date'}),
            'date_permis':                      forms.DateInput(attrs={'type': 'date'}),
            'acquittement_date_declaration':    forms.DateInput(attrs={'type': 'date'}),
            'acquittement_date_paiement':       forms.DateInput(attrs={'type': 'date'}),
            'cession_date_autorisation':        forms.DateInput(attrs={'type': 'date'}),
            # Heures ENTREE
            'heure_arrivee':                    forms.TimeInput(attrs={'type': 'time'}),
            'heure_depotage':                   forms.TimeInput(attrs={'type': 'time'}),
            'heure_fin':                        forms.TimeInput(attrs={'type': 'time'}),
            # Textes longs
            'notes':                            forms.Textarea(attrs={'rows': 3}),
            'cession_motif':                    forms.TextInput(),
            'compartiments_charges':            forms.TextInput(attrs={'placeholder': 'Ex: C1=5000L, C2=8000L, C3=7000L'}),
            # Volumes & densités — step adapté
            'volume_ambiant_expediteur':        forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
            'volume_15c_expediteur':            forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
            'densite_15c_expediteur':           forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
            'temperature_chargement':           forms.NumberInput(attrs={'step': '0.01'}),
            'volume_ambiant_recu':              forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
            'temperature_reception':            forms.NumberInput(attrs={'step': '0.01'}),
            'temperature_labo':                 forms.NumberInput(attrs={'step': '0.01'}),
            'densite_observee_labo':            forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
            'volume_ambiant_sortie':            forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
            'densite_15c_sortie':               forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
            'densite_observee_sortie':          forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
            'temperature_sortie':               forms.NumberInput(attrs={'step': '0.01'}),
            'cession_volume_ambiant':           forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
            'cession_volume_15c':               forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
            'cession_densite_observee':         forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
            'cession_temperature':              forms.NumberInput(attrs={'step': '0.01'}),
            'acquittement_volume_ambiant':      forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Tous les champs sont optionnels par défaut —
        # la validation conditionnelle est faite dans clean()
        for name in self.fields:
            self.fields[name].required = False
            self.fields[name].widget.attrs.update({'class': 'form-control'})
        # Champs toujours obligatoires
        for name in ('type_mouvement', 'produit', 'regime_douanier', 'date_mouvement', 'marketeur'):
            self.fields[name].required = True

        # Filtres sur les selects pour améliorer l'UX
        self.fields['produit'].queryset = Produit.objects.filter(statut='ACTIF').order_by('nom')
        self.fields['marketeur'].queryset = Marketeur.objects.filter(statut='ACTIF').order_by('raison_sociale')
        self.fields['cession_marketeur_destinataire'].queryset = Marketeur.objects.filter(statut='ACTIF').order_by('raison_sociale')
        self.fields['camion'].queryset = Camion.objects.select_related('marketeur').filter(statut='EN_SERVICE').order_by('immatriculation')
        self.fields['chauffeur'].queryset = Chauffeur.objects.filter(statut='ACTIF').order_by('nom', 'prenom')
        self.fields['cession_cuve'].queryset = Cuve.objects.select_related('produit').filter(statut='ACTIVE').order_by('numero')
        self.fields['cession_cuve'].required = False

        # ── Filtre entree_source (ACQUITTEMENT) ───────────────
        # Par défaut : toutes les ENTREE SOUS_DOUANE, triées par date décroissante.
        # Si on est en mode édition et que le produit/marketeur sont déjà connus
        # (instance existante), on affine le filtre pour n'afficher que les entrées
        # du même produit et du même marketeur.
        qs_entrees = (
            Mouvement.objects
            .filter(type_mouvement='ENTREE', regime_douanier='SOUS_DOUANE')
            .select_related('produit', 'marketeur', 'cuve')
            .prefetch_related('acquittements', 'lignes__cuve')
            .order_by('-date_mouvement')
        )
        if self.instance and self.instance.pk:
            if self.instance.produit_id:
                qs_entrees = qs_entrees.filter(produit_id=self.instance.produit_id)
            if self.instance.marketeur_id:
                qs_entrees = qs_entrees.filter(marketeur_id=self.instance.marketeur_id)
        self.fields['entree_source'].queryset = qs_entrees
        self.fields['entree_source'].required = False
        self.fields['entree_source'].label = "Entrée Sous douane source (N° BL)"
        self.fields['entree_source'].help_text = (
            "Sélectionnez le mouvement d'ENTREE SOUS_DOUANE correspondant à cet acquittement. "
            "Laissez vide si cet acquittement concerne un stock initial saisi dans l'inventaire."
        )

    def clean(self):
        data = super().clean()
        type_m = data.get('type_mouvement')

        if type_m == 'ENTREE':
            champs_obligatoires = [
                ('camion',               "Le camion est obligatoire pour une entrée."),
                ('volume_ambiant_recu',  "Le volume ambiant reçu est obligatoire pour une entrée."),
                ('temperature_labo',     "La température labo est obligatoire pour le calcul API MPMS."),
                ('densite_observee_labo',"La densité observée labo est obligatoire pour le calcul API MPMS."),
                ('temperature_reception',"La température à la réception est obligatoire pour le calcul Vcf."),
            ]
            for champ, message in champs_obligatoires:
                if not data.get(champ):
                    self.add_error(champ, message)

        elif type_m == 'SORTIE':
            champs_obligatoires = [
                ('camion',               "Le camion est obligatoire pour une sortie."),
                ('volume_ambiant_sortie',"Le volume ambiant sortie est obligatoire."),
                ('densite_15c_sortie',   "La densité @15°C sortie est obligatoire pour le calcul API MPMS."),
                ('temperature_sortie',   "La température sortie est obligatoire pour le calcul Vcf."),
            ]
            for champ, message in champs_obligatoires:
                if not data.get(champ):
                    self.add_error(champ, message)

        elif type_m == 'CESSION':
            champs_obligatoires = [
                ('camion',                          "Le camion est obligatoire pour une cession."),
                ('cession_marketeur_destinataire',  "Le marketeur destinataire est obligatoire."),
                ('cession_volume_ambiant',          "Le volume ambiant cédé est obligatoire."),
            ]
            for champ, message in champs_obligatoires:
                if not data.get(champ):
                    self.add_error(champ, message)
            # Le destinataire doit être différent de la source
            mkt_src = data.get('marketeur')
            mkt_dst = data.get('cession_marketeur_destinataire')
            if mkt_src and mkt_dst and mkt_src == mkt_dst:
                self.add_error('cession_marketeur_destinataire',
                               "Le marketeur destinataire doit être différent du marketeur source.")

        elif type_m == 'ACQUITTEMENT':
            champs_obligatoires = [
                ('acquittement_volume_ambiant',        "Le volume ambiant à acquitter est obligatoire."),
                # acquittement_volume_15c est calculé automatiquement — non obligatoire en saisie
                ('acquittement_reference_declaration', "La référence de déclaration douanière est obligatoire."),
                ('acquittement_date_declaration',      "La date de déclaration douanière est obligatoire."),
            ]
            for champ, message in champs_obligatoires:
                if not data.get(champ):
                    self.add_error(champ, message)
            # Forcer le régime ACQUITTE
            data['regime_douanier'] = 'ACQUITTE'

            # ── Validation de cohérence entree_source ─────────
            entree_source = data.get('entree_source')
            if entree_source:
                produit    = data.get('produit')
                marketeur  = data.get('marketeur')
                # Vérifier que l'entrée source est bien une ENTREE SOUS_DOUANE
                if entree_source.type_mouvement != 'ENTREE' or entree_source.regime_douanier != 'SOUS_DOUANE':
                    self.add_error(
                        'entree_source',
                        "L'entrée source doit être un mouvement d'ENTREE avec le régime SOUS_DOUANE."
                    )
                # Vérifier la cohérence produit
                elif produit and entree_source.produit != produit:
                    self.add_error(
                        'entree_source',
                        f"L'entrée source concerne le produit « {entree_source.produit} » "
                        f"mais le mouvement est saisi pour « {produit} »."
                    )
                # Vérifier la cohérence marketeur
                elif marketeur and entree_source.marketeur != marketeur:
                    self.add_error(
                        'entree_source',
                        f"L'entrée source appartient au marketeur « {entree_source.marketeur} » "
                        f"mais le mouvement est saisi pour « {marketeur} »."
                    )

        return data


# ─────────────────────────────────────────────────────────────
#  FORMULAIRES LIGNES MOUVEMENT (multi-cuves)
# ─────────────────────────────────────────────────────────────

class LigneMouvementForm(forms.ModelForm):
    """Formulaire d'une ligne cuve pour un mouvement (entrée ou sortie multi-cuves)."""

    class Meta:
        model = LigneMouvement
        fields = ['cuve', 'volume_ambiant', 'volume_15c']
        widgets = {
            'volume_ambiant': forms.NumberInput(attrs={'step': '0.01', 'min': '0', 'class': 'form-control'}),
            'volume_15c':     forms.NumberInput(attrs={'step': '0.01', 'min': '0', 'class': 'form-control'}),
        }

    def __init__(self, *args, produit=None, **kwargs):
        super().__init__(*args, **kwargs)
        qs = Cuve.objects.select_related('produit').filter(statut='ACTIVE').order_by('numero')
        if produit:
            qs = qs.filter(produit=produit)
        self.fields['cuve'].queryset = qs
        self.fields['cuve'].required = False
        self.fields['volume_ambiant'].required = False
        self.fields['volume_15c'].required = False
        self.fields['cuve'].widget.attrs.update({'class': 'form-control'})


LigneMouvementFormSet = inlineformset_factory(
    Mouvement,
    LigneMouvement,
    form=LigneMouvementForm,
    fields=['cuve', 'volume_ambiant', 'volume_15c'],
    extra=1,
    can_delete=True,
    min_num=0,
    validate_min=False,
)


class SocieteForm(forms.ModelForm):
    class Meta:
        model  = Societe
        fields = [
            'raison_sociale', 'sigle', 'forme_juridique',
            'numero_contribuable', 'numero_ifu', 'capital_social',
            'logo', 'tampon', 'couleur_principale', 'pied_de_page',
            'adresse', 'ville', 'pays', 'boite_postale',
            'telephone', 'telephone2', 'email', 'site_web',
            'nom_depot', 'type_depot', 'numero_agrement',
            'autorite_tutelle', 'date_creation',
        ]
        widgets = {
            'raison_sociale':      forms.TextInput(attrs={'class': 'form-control'}),
            'sigle':               forms.TextInput(attrs={'class': 'form-control'}),
            'forme_juridique':     forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ex : SARL, SA…'}),
            'numero_contribuable': forms.TextInput(attrs={'class': 'form-control'}),
            'numero_ifu':          forms.TextInput(attrs={'class': 'form-control'}),
            'capital_social':      forms.NumberInput(attrs={'class': 'form-control'}),
            'couleur_principale':  forms.TextInput(attrs={'class': 'form-control', 'type': 'color'}),
            'pied_de_page':        forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'adresse':             forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'ville':               forms.TextInput(attrs={'class': 'form-control'}),
            'pays':                forms.TextInput(attrs={'class': 'form-control'}),
            'boite_postale':       forms.TextInput(attrs={'class': 'form-control'}),
            'telephone':           forms.TextInput(attrs={'class': 'form-control'}),
            'telephone2':          forms.TextInput(attrs={'class': 'form-control'}),
            'email':               forms.EmailInput(attrs={'class': 'form-control'}),
            'site_web':            forms.URLInput(attrs={'class': 'form-control'}),
            'nom_depot':           forms.TextInput(attrs={'class': 'form-control'}),
            'type_depot':          forms.TextInput(attrs={'class': 'form-control'}),
            'numero_agrement':     forms.TextInput(attrs={'class': 'form-control'}),
            'autorite_tutelle':    forms.TextInput(attrs={'class': 'form-control'}),
            'date_creation':       forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }


# ─────────────────────────────────────────────────────────────
#  DOCUMENT JUSTIFICATIF DE MOUVEMENT
# ─────────────────────────────────────────────────────────────
class MouvementDocumentForm(forms.ModelForm):
    _EXTENSIONS = {'.pdf', '.png', '.jpg', '.jpeg'}
    _TAILLE_MAX = 10 * 1024 * 1024  # 10 Mo

    class Meta:
        model = MouvementDocument
        fields = ['fichier', 'type_document', 'description']
        widgets = {
            'fichier': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.png,.jpg,.jpeg',
            }),
            'type_document': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Note optionnelle sur ce document…',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['description'].required = False

    def clean_fichier(self):
        import os
        fichier = self.cleaned_data.get('fichier')
        if not fichier:
            return fichier
        ext = os.path.splitext(fichier.name)[1].lower()
        if ext not in self._EXTENSIONS:
            raise forms.ValidationError(
                f"Format non autorisé « {ext} ». Formats acceptés : PDF, PNG, JPG, JPEG."
            )
        if fichier.size > self._TAILLE_MAX:
            raise forms.ValidationError(
                f"Fichier trop volumineux ({fichier.size / (1024 * 1024):.1f} Mo). Maximum : 10 Mo."
            )
        return fichier

