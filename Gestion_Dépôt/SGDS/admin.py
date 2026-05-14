from django.contrib import admin
from django.utils.html import format_html
from django.urls import path
from django.shortcuts import redirect
from django.contrib import messages
from .models import (
    Marketeur, Camion, Chauffeur, Famille, Produit, Cuve,
    ParametreJaugeageCuve, JaugeageJour, MesureCuve, Mouvement, LigneMouvement,
    PeriodeComptable, StockOuverture, StockOuvertureCuve,
    ParametresCoulage, ClotureCoulageMensuel, ClotureCoulageProduit, ClotureCoulageLigne,
    InventaireInitialMarketeur,
)


@admin.register(InventaireInitialMarketeur)
class InventaireInitialMarketeurAdmin(admin.ModelAdmin):
    list_display   = ('marketeur', 'produit', 'regime_douanier', 'volume_ambiant', 'volume_15c', 'date_inventaire', 'saisi_par', 'date_modification')
    list_filter    = ('regime_douanier', 'produit', 'marketeur')
    search_fields  = ('marketeur__raison_sociale', 'marketeur__sigle', 'produit__code', 'produit__nom')
    readonly_fields = ('date_creation', 'date_modification')
    autocomplete_fields = []

@admin.register(Marketeur)
class MarketeurAdmin(admin.ModelAdmin):
    list_display   = ('raison_sociale', 'sigle', 'forme_juridique', 'ville', 'telephone', 'statut', 'date_enregistrement')
    list_filter    = ('statut', 'forme_juridique', 'ville')
    search_fields  = ('raison_sociale', 'sigle', 'numero_contribuable', 'telephone', 'email')
    readonly_fields = ('date_enregistrement', 'date_modification')
    fieldsets = (
        ('Identification', {
            'fields': ('raison_sociale', 'sigle', 'forme_juridique', 'capital_social',
                       'numero_registre_commerce', 'numero_contribuable', 'numero_ifu',
                       'date_creation_societe', 'domaine_activite', 'logo')
        }),
        ('Coordonnées', {
            'fields': ('adresse', 'quartier', 'ville', 'pays', 'boite_postale',
                       'telephone', 'telephone2', 'email', 'site_web')
        }),
        ('Représentant légal', {
            'fields': ('nom_representant', 'prenom_representant', 'fonction_representant',
                       'telephone_representant', 'email_representant')
        }),
        ('Informations bancaires', {
            'fields': ('banque', 'numero_compte', 'code_swift'),
            'classes': ('collapse',),
        }),
        ('Statut & Suivi', {
            'fields': ('statut', 'notes', 'date_enregistrement', 'date_modification')
        }),
    )


@admin.register(Camion)
class CamionAdmin(admin.ModelAdmin):
    list_display   = ('immatriculation', 'marque', 'modele', 'type_produit', 'capacite_totale', 'statut', 'marketeur')
    list_filter    = ('statut', 'type_produit', 'marque')
    search_fields  = ('immatriculation', 'marque', 'modele', 'numero_serie_chassis')
    readonly_fields = ('date_enregistrement', 'date_modification')
    fieldsets = (
        ('Identification', {
            'fields': ('immatriculation', 'marque', 'modele', 'annee_fabrication', 'couleur',
                       'numero_serie_chassis', 'numero_serie_moteur')
        }),
        ('Citerne', {
            'fields': ('capacite_totale', 'nombre_compartiments', 'type_produit')
        }),
        ('Documents', {
            'fields': ('date_mise_en_circulation', 'carte_grise')
        }),
        ('Assurance', {
            'fields': ('compagnie_assurance', 'numero_police_assurance', 'date_expiration_assurance'),
            'classes': ('collapse',),
        }),
        ('Technique', {
            'fields': ('date_derniere_revision', 'date_prochaine_revision', 'kilometrage'),
            'classes': ('collapse',),
        }),
        ('Statut & Suivi', {
            'fields': ('marketeur', 'statut', 'notes', 'date_enregistrement', 'date_modification')
        }),
    )


@admin.register(Chauffeur)
class ChauffeurAdmin(admin.ModelAdmin):
    list_display   = ('nom', 'prenom', 'telephone', 'categorie_permis', 'statut', 'marketeur', 'camion')
    list_filter    = ('statut', 'categorie_permis')
    search_fields  = ('nom', 'prenom', 'telephone', 'numero_permis')
    readonly_fields = ('date_enregistrement', 'date_modification')
    fieldsets = (
        ('Identité', {
            'fields': ('nom', 'prenom', 'date_naissance', 'lieu_naissance', 'nationalite', 'photo')
        }),
        ('Contact', {
            'fields': ('telephone', 'telephone2', 'email', 'adresse')
        }),
        ('Permis de conduire', {
            'fields': ('numero_permis', 'categorie_permis', 'date_obtention_permis', 'date_expiration_permis')
        }),
        ('Professionnel', {
            'fields': ('numero_employe', 'date_embauche'),
            'classes': ('collapse',),
        }),
        ('Affectations', {
            'fields': ('marketeur', 'camion')
        }),
        ('Statut & Suivi', {
            'fields': ('statut', 'notes', 'date_enregistrement', 'date_modification')
        }),
    )


@admin.register(Famille)
class FamilleAdmin(admin.ModelAdmin):
    list_display    = ('nom', 'code', 'couleur', 'statut', 'date_creation')
    list_filter     = ('statut',)
    search_fields   = ('nom', 'code', 'description')
    readonly_fields = ('date_creation', 'date_modification')
    fieldsets = (
        ('Identification', {'fields': ('nom', 'code', 'couleur', 'description')}),
        ('Statut & Suivi', {'fields': ('statut', 'date_creation', 'date_modification')}),
    )


@admin.register(Produit)
class ProduitAdmin(admin.ModelAdmin):
    list_display    = ('nom', 'code', 'famille', 'unite_mesure', 'prix_unitaire', 'statut', 'col_stock_actuel', 'date_maj_stock')
    list_filter     = ('statut', 'famille', 'unite_mesure')
    search_fields   = ('nom', 'code', 'description')
    readonly_fields = ('date_creation', 'date_modification', 'stock_actuel', 'date_maj_stock')
    fieldsets = (
        ('Identification', {'fields': ('nom', 'code', 'famille', 'description')}),
        ('Caractéristiques', {'fields': ('unite_mesure', 'prix_unitaire', 'prix_passage', 'seuil_alerte')}),
        ('Stock (mise à jour automatique)', {
            'fields': ('stock_actuel', 'date_maj_stock'),
            'description': "Mis à jour automatiquement à chaque validation de jaugeage.",
        }),
        ('Statut & Suivi', {'fields': ('statut', 'notes', 'date_creation', 'date_modification')}),
    )

    def col_stock_actuel(self, obj):
        return format_litres(obj.stock_actuel)
    col_stock_actuel.short_description = "Stock actuel"


@admin.register(Cuve)
class CuveAdmin(admin.ModelAdmin):
    list_display    = ('numero', 'designation', 'produit', 'capacite_totale', 'niveau_actuel', 'statut')
    list_filter     = ('statut', 'type_cuve', 'materiau')
    search_fields   = ('numero', 'designation', 'localisation')
    readonly_fields = ('date_enregistrement', 'date_modification')
    fieldsets = (
        ('Identification', {'fields': ('numero', 'designation', 'produit')}),
        ('Capacité & Niveau', {'fields': ('capacite_totale', 'niveau_actuel')}),
        ('Caractéristiques', {'fields': ('type_cuve', 'materiau', 'localisation')}),
        ('Dates', {
            'fields': ('date_installation', 'date_derniere_inspection', 'date_prochaine_inspection'),
            'classes': ('collapse',),
        }),
        ('Statut & Suivi', {'fields': ('statut', 'notes', 'date_enregistrement', 'date_modification')}),
    )

# ─────────────────────────────────────────────────────────────
#  Helper : formate un nombre en litres avec séparateur de milliers
# ─────────────────────────────────────────────────────────────
def format_litres(valeur):
    """Formate 60850 en '60 850 L'"""
    if valeur is None:
        return "—"
    return f"{int(valeur):,} L".replace(",", " ")
 
 
# ─────────────────────────────────────────────────────────────
#  ADMIN : ParametreJaugeageCuve
# ─────────────────────────────────────────────────────────────
@admin.register(ParametreJaugeageCuve)
class ParametreJaugeageCuveAdmin(admin.ModelAdmin):
    list_display = (
        'cuve',
        'hauteur_totale_temoin',
        'remplissage_maxi_format',
        'v_a',
        'v_mn',
        'is_pompe',
        'date_modification',
    )
    list_filter = ('is_pompe', 'cuve__produit')
    search_fields = ('cuve__numero', 'cuve__designation', 'reference_certificat')
    readonly_fields = ('date_creation', 'date_modification')
 
    fieldsets = (
        ("Cuve", {
            'fields': ('cuve', 'is_pompe'),
        }),
        ("Caractéristiques physiques", {
            'fields': (
                'hauteur_totale_temoin',
                'hauteur_min_livraison',
                'correction_creux',
                'remplissage_maxi',
            ),
        }),
        ("Certificat de jaugeage", {
            'fields': (
                'v_a',
                'v_mn',
                'reference_certificat',
                'date_certificat',
                'organisme_certificateur',
                'date_prochain_jaugeage',
            ),
        }),
        ("Suivi", {
            'fields': ('notes', 'date_creation', 'date_modification'),
            'classes': ('collapse',),
        }),
    )
 
    def remplissage_maxi_format(self, obj):
        return format_litres(obj.remplissage_maxi)
    remplissage_maxi_format.short_description = "Remplissage maxi"
 
 
# ─────────────────────────────────────────────────────────────
#  INLINE : MesureCuve dans JaugeageJour
#  Permet de saisir toutes les mesures depuis l'écran du jaugeage
# ─────────────────────────────────────────────────────────────
class MesureCuveInline(admin.TabularInline):
    model = MesureCuve
    extra = 0  # pas de ligne vide supplémentaire
    can_delete = False
 
    fields = (
        'cuve',
        'creux_mesure',
        't1', 't2', 't3',
        'temperature_obs',
        'densite_moyenne',
        'densite_15c',
        'facteur_vcf',
        'volume_additionnel',
        'volume_tuyauterie',
        'volume_eau',
        'apercu_volume_disponible',
    )
    readonly_fields = ('apercu_volume_disponible',)
 
    def apercu_volume_disponible(self, obj):
        """Affiche le volume disponible calculé en temps réel."""
        if obj.pk is None:
            return "—"
        v = obj.volume_disponible
        if v is None:
            return format_html('<span style="color:#999;">en attente saisie</span>')
        if v < 0:
            return format_html('<span style="color:red;font-weight:bold;">{}</span>', format_litres(v))
        return format_html('<span style="color:green;">{}</span>', format_litres(v))
    apercu_volume_disponible.short_description = "Vol. dispo"
 
 
# ─────────────────────────────────────────────────────────────
#  ADMIN : JaugeageJour
# ─────────────────────────────────────────────────────────────
@admin.register(JaugeageJour)
class JaugeageJourAdmin(admin.ModelAdmin):
    list_display = (
        'date_jaugeage',
        'heure_jaugeage',
        'type_jaugeage',
        'operateur',
        'depot',
        'nb_mesures',
        'date_creation',
    )
    list_filter = ('type_jaugeage', 'date_jaugeage', 'depot')
    search_fields = ('operateur', 'notes')
    date_hierarchy = 'date_jaugeage'
    readonly_fields = ('date_creation', 'date_modification')
    ordering = ('-date_jaugeage', '-heure_jaugeage')
 
    fieldsets = (
        ("Identification", {
            'fields': (
                'date_jaugeage',
                'heure_jaugeage',
                'type_jaugeage',
                'operateur',
            ),
        }),
        ("Dépôt", {
            'fields': ('depot', 'type_depot', 'temperature_reference'),
        }),
        ("Notes", {
            'fields': ('notes',),
        }),
        ("Suivi", {
            'fields': ('date_creation', 'date_modification'),
            'classes': ('collapse',),
        }),
    )
 
    inlines = [MesureCuveInline]
 
    def nb_mesures(self, obj):
        n = obj.mesures.count()
        return f"{n} cuve(s)"
    nb_mesures.short_description = "Mesures"
 
    # ───── Bouton "Créer un nouveau jaugeage" en haut de la liste ─────
    change_list_template = "admin/jaugeage_change_list.html"
 
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                'creer-nouveau/',
                self.admin_site.admin_view(self.creer_nouveau_view),
                name='jaugeage_creer_nouveau',
            ),
        ]
        return custom_urls + urls
 
    def creer_nouveau_view(self, request):
        """
        Crée un nouveau jaugeage en pré-remplissant avec les valeurs
        du dernier jaugeage. Redirige vers l'édition du nouveau jaugeage.
        """
        from datetime import date, datetime
        try:
            nouveau = JaugeageJour.creer_nouveau_jaugeage(
                date_jaugeage=date.today(),
                type_jaugeage='J',
                heure_jaugeage=datetime.now().time().replace(microsecond=0),
                operateur=request.user.get_full_name() or request.user.username,
            )
            messages.success(
                request,
                f"Nouveau jaugeage créé : {nouveau}. "
                "Les valeurs ont été pré-remplies depuis le dernier jaugeage."
            )
            return redirect(f'../{nouveau.pk}/change/')
        except Exception as e:
            messages.error(request, f"Erreur : {e}")
            return redirect('..')
 
 
# ─────────────────────────────────────────────────────────────
#  ADMIN : MesureCuve (vue indépendante, optionnelle)
#  Utile pour voir l'historique des mesures d'une cuve
# ─────────────────────────────────────────────────────────────
@admin.register(MesureCuve)
class MesureCuveAdmin(admin.ModelAdmin):
    list_display = (
        'jaugeage',
        'cuve',
        'creux_mesure',
        'col_hauteur_produit',
        'col_volume_ambiant_bac',
        'col_volume_standard_15c',
        'col_volume_disponible',
    )
    list_filter = ('cuve__produit', 'cuve', 'jaugeage__date_jaugeage')
    search_fields = ('cuve__numero', 'jaugeage__operateur')
    readonly_fields = (
        'date_modification',
        'col_creux_corrige',
        'col_hauteur_produit',
        'col_hauteur_decimal',
        'col_surplus',
        'col_volume_ambiant_bac',
        'col_temperature_moyenne',
        'col_volume_physique',
        'col_volume_ambiant_depot',
        'col_volume_standard_15c',
        'col_volume_disponible',
    )
 
    fieldsets = (
        ("Identification", {
            'fields': ('jaugeage', 'cuve'),
        }),
        ("Saisies — Hauteur", {
            'fields': ('creux_mesure',),
        }),
        ("Saisies — Températures", {
            'fields': ('t1', 't2', 't3', 'temperature_obs'),
        }),
        ("Saisies — Densité", {
            'fields': ('densite_moyenne', 'densite_15c', 'facteur_vcf'),
        }),
        ("Saisies — Volumes additionnels", {
            'fields': ('volume_additionnel', 'volume_tuyauterie', 'volume_eau'),
        }),
        ("⚙ Calculs automatiques (lecture seule)", {
            'fields': (
                'col_creux_corrige',
                'col_hauteur_produit',
                'col_hauteur_decimal',
                'col_surplus',
                'col_temperature_moyenne',
                'col_volume_ambiant_bac',
                'col_volume_physique',
                'col_volume_ambiant_depot',
                'col_volume_standard_15c',
                'col_volume_disponible',
            ),
            'description': "Ces valeurs sont calculées automatiquement à partir des saisies ci-dessus.",
        }),
        ("Suivi", {
            'fields': ('date_modification',),
            'classes': ('collapse',),
        }),
    )
 
    # ─── Affichage des @property en colonne ───
    def col_creux_corrige(self, obj):
        return obj.creux_corrige if obj.creux_corrige is not None else "—"
    col_creux_corrige.short_description = "Creux corrigé (mm)"
 
    def col_hauteur_produit(self, obj):
        return obj.hauteur_produit if obj.hauteur_produit is not None else "—"
    col_hauteur_produit.short_description = "Hauteur produit (mm)"
 
    def col_hauteur_decimal(self, obj):
        return obj.hauteur_decimal if obj.hauteur_decimal is not None else "—"
    col_hauteur_decimal.short_description = "Hauteur décimal (mm)"
 
    def col_surplus(self, obj):
        return obj.surplus if obj.surplus is not None else "—"
    col_surplus.short_description = "Surplus (mm)"
 
    def col_temperature_moyenne(self, obj):
        if obj.temperature_moyenne is None:
            return "—"
        return f"{obj.temperature_moyenne:.2f} °C"
    col_temperature_moyenne.short_description = "T° moyenne"
 
    def col_volume_ambiant_bac(self, obj):
        return format_litres(obj.volume_ambiant_bac)
    col_volume_ambiant_bac.short_description = "Vol. ambiant bac"
 
    def col_volume_physique(self, obj):
        return format_litres(obj.volume_physique)
    col_volume_physique.short_description = "Vol. physique"
 
    def col_volume_ambiant_depot(self, obj):
        return format_litres(obj.volume_ambiant_depot)
    col_volume_ambiant_depot.short_description = "Vol. ambiant dépôt"
 
    def col_volume_standard_15c(self, obj):
        return format_litres(obj.volume_standard_15c)
    col_volume_standard_15c.short_description = "Vol. standard 15°C"
 
    def col_volume_disponible(self, obj):
        v = obj.volume_disponible
        if v is None:
            return "—"
        if v < 0:
            return format_html('<span style="color:red;font-weight:bold;">{}</span>', format_litres(v))
        return format_html('<span style="color:green;">{}</span>', format_litres(v))
    col_volume_disponible.short_description = "Vol. disponible"


# ─────────────────────────────────────────────────────────────
#  ADMIN : Mouvement
# ─────────────────────────────────────────────────────────────
class LigneMouvementInline(admin.TabularInline):
    model = LigneMouvement
    fields = ['cuve', 'produit', 'volume_ambiant', 'volume_15c', 'ordre']
    extra = 1
    autocomplete_fields = []

@admin.register(Mouvement)
class MouvementAdmin(admin.ModelAdmin):
    inlines = [LigneMouvementInline]
    list_display = (
        'numero_enregistrement',
        'date_mouvement',
        'type_mouvement',
        'regime_douanier',
        'marketeur',
        'produit',
        'camion',
        'col_volume_principal',
        'date_saisie',
    )
    list_filter = (
        'type_mouvement',
        'regime_douanier',
        'produit',
        'marketeur',
        'date_mouvement',
    )
    search_fields = (
        'numero_enregistrement',
        'camion__immatriculation',
        'marketeur__raison_sociale',
        'bl_expediteur',
        'numero_permis_sortie',
        'acquittement_reference_declaration',
    )
    date_hierarchy = 'date_mouvement'
    readonly_fields = (
        'numero_enregistrement',   # généré automatiquement, jamais modifiable
        'date_saisie',
        'date_modification',
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
    )

    fieldsets = (
        ('Identification', {
            'fields': (
                'numero_enregistrement',   # lecture seule — généré automatiquement
                'type_mouvement',
                'produit',
                'regime_douanier',
                'date_mouvement',
            ),
        }),
        ('Marketeur', {
            'fields': ('marketeur',),
        }),
        ('Camion & Chauffeur', {
            'fields': ('camion', 'chauffeur'),
        }),
        ('Entrée — Provenance & BL', {
            'fields': (
                'provenance', 'bl_expediteur', 'bl_client',
                'date_chargement', 'date_dechargement',
            ),
            'classes': ('collapse',),
        }),
        ('Entrée — Volumes expéditeur', {
            'fields': (
                'volume_ambiant_expediteur',
                'volume_15c_expediteur',
                'densite_15c_expediteur',
                'temperature_chargement',
            ),
            'classes': ('collapse',),
        }),
        ('Entrée — Réception & Laboratoire', {
            'fields': (
                'volume_ambiant_recu',
                'temperature_reception',
                'temperature_labo',
                'densite_observee_labo',
            ),
            'classes': ('collapse',),
        }),
        ('Sortie — Client & Permis', {
            'fields': (
                'reference_client_externe', 'destination', 'code_destination',
                'date_permis', 'numero_permis_sortie', 'numero_s', 'numero_c',
                'mode_reglement',
            ),
            'classes': ('collapse',),
        }),
        ('Sortie — Volumes', {
            'fields': (
                'volume_ambiant_sortie',
                'densite_15c_sortie',
                'temperature_sortie',
            ),
            'classes': ('collapse',),
        }),
        ('Cession', {
            'fields': (
                'cession_marketeur_destinataire',
                'cession_volume_ambiant',
                'cession_volume_15c',
                'cession_motif',
            ),
            'classes': ('collapse',),
        }),
        ('Acquittement', {
            'fields': (
                'acquittement_volume_ambiant',
                'acquittement_volume_15c',
                'acquittement_reference_declaration',
                'acquittement_date_declaration',
            ),
            'classes': ('collapse',),
        }),
        ('Calculs automatiques (lecture seule)', {
            'fields': (
                'densite_15c_calculee',
                'ecart_densite_15c',
                'coefficient_conversion_15c',
                'volume_15c_recu',
                'perte_gain_reception',
                'perte_gain_15c',
                'poids_kg',
                'coefficient_conversion_sortie',
                'volume_15c_sortie',
                'poids_sortie_kg',
            ),
            'classes': ('collapse',),
            'description': "Ces valeurs sont calculées automatiquement à la sauvegarde via l'algorithme API MPMS.",
        }),
        ('Suivi', {
            'fields': ('collaborateur', 'notes', 'date_saisie', 'date_modification'),
            'classes': ('collapse',),
        }),
    )

    def col_volume_principal(self, obj):
        v = obj.volume_principal
        return format_litres(v)
    col_volume_principal.short_description = "Volume principal (@15°C)"


# ─────────────────────────────────────────────────────────────
#  ADMIN : Coulage — Périodes, Paramètres, Clôtures
# ─────────────────────────────────────────────────────────────
@admin.register(ParametresCoulage)
class ParametresCoulageAdmin(admin.ModelAdmin):
    list_display = ('date_application', 'prix_unitaire_passage', 'motif_defaut')
    ordering = ('-date_application',)


@admin.register(PeriodeComptable)
class PeriodeComptableAdmin(admin.ModelAdmin):
    list_display  = ('libelle', 'statut', 'date_ouverture', 'date_cloture', 'cloture_par')
    list_filter   = ('statut',)
    ordering      = ('-annee', '-mois')
    readonly_fields = ('statut', 'date_ouverture', 'date_cloture', 'cloture_par')
    # Ouverture/clôture via les vues dédiées uniquement, pas par l'admin direct


@admin.register(StockOuverture)
class StockOuvertureAdmin(admin.ModelAdmin):
    list_display = ('periode', 'produit', 'volume_ambiant', 'calcul_auto')
    list_filter = ('produit', 'calcul_auto')
    ordering = ('-periode__annee', '-periode__mois')


@admin.register(StockOuvertureCuve)
class StockOuvertureCuveAdmin(admin.ModelAdmin):
    list_display = ('periode', 'cuve', 'volume_ambiant', 'calcul_auto')
    list_filter = ('calcul_auto', 'cuve__produit')
    ordering = ('-periode__annee', '-periode__mois')


class ClotureCoulageProduitInline(admin.TabularInline):
    model = ClotureCoulageProduit
    extra = 0
    can_delete = False
    readonly_fields = (
        'produit', 'coefficient', 'pertes_gains', 'cumul_entree', 'cumul_sortie',
    )


class ClotureCoulageLigneInline(admin.TabularInline):
    model = ClotureCoulageLigne
    extra = 0
    can_delete = False
    readonly_fields = (
        'marketeur', 'produit',
        'brut_entree', 'coul_entree', 'entree_nette',
        'sortie', 'base_qp_coul', 'coef_qp_coul', 'qp_coul',
        'volume_sorti', 'motif', 'prix_unitaire', 'montant',
    )


@admin.register(ClotureCoulageMensuel)
class ClotureCoulageMensuelAdmin(admin.ModelAdmin):
    list_display = (
        'periode', 'prix_unitaire_passage', 'col_montant_total', 'date_cloture',
    )
    readonly_fields = (
        'periode', 'prix_unitaire_passage', 'motif', 'date_cloture', 'cloture_par',
    )
    inlines = [ClotureCoulageProduitInline, ClotureCoulageLigneInline]

    def col_montant_total(self, obj):
        t = obj.total_montant
        return f"{int(t):,} FCFA".replace(',', ' ') if t else '—'
    col_montant_total.short_description = "Montant total"
