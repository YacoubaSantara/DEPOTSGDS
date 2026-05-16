
from django.db import models
from django.core.validators import MinValueValidator
from django.conf import settings
from decimal import Decimal
from .import petroleum_calc as pc


class Marketeur(models.Model):

    # --- Choix ---
    FORME_JURIDIQUE_CHOICES = [
        ('SARL', 'SARL - Société à Responsabilité Limitée'),
        ('SA',   'SA - Société Anonyme'),
        ('SAS',  'SAS - Société par Actions Simplifiée'),
        ('SNC',  'SNC - Société en Nom Collectif'),
        ('EI',   'EI - Entreprise Individuelle'),
        ('EURL', 'EURL - Entreprise Unipersonnelle à Responsabilité Limitée'),
        ('GIE',  'GIE - Groupement d\'Intérêt Économique'),
        ('COOP', 'Coopérative'),
        ('AUTRE','Autre'),
    ]

    STATUT_CHOICES = [
        ('ACTIF',     'Actif'),
        ('INACTIF',   'Inactif'),
        ('SUSPENDU',  'Suspendu'),
        ('BLACKLIST',  'Blacklisté'),
    ]

    # --- Identification de la société ---
    raison_sociale        = models.CharField(max_length=200, unique=True, verbose_name="Raison sociale")
    sigle                 = models.CharField(max_length=50,  blank=True, null=True, verbose_name="Sigle / Abréviation")
    forme_juridique       = models.CharField(max_length=10,  choices=FORME_JURIDIQUE_CHOICES, verbose_name="Forme juridique")
    numero_registre_commerce = models.CharField(max_length=100, blank=True, null=True, unique=True, verbose_name="N° Registre de commerce")
    numero_contribuable   = models.CharField(max_length=100, blank=True, null=True, verbose_name="N° Contribuable / NIF")
    numero_ifu            = models.CharField(max_length=100, blank=True, null=True, verbose_name="N° IFU")
    capital_social        = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True, verbose_name="Capital social (FCFA)")
    date_creation_societe = models.DateField(blank=True, null=True, verbose_name="Date de création")
    domaine_activite      = models.CharField(max_length=200, blank=True, null=True, verbose_name="Domaine d'activité")
    logo                  = models.ImageField(upload_to='marketeurs/logos/', blank=True, null=True, verbose_name="Logo")

    # --- Coordonnées ---
    adresse               = models.TextField(verbose_name="Adresse complète")
    quartier              = models.CharField(max_length=100, blank=True, null=True, verbose_name="Quartier / Secteur")
    ville                 = models.CharField(max_length=100, verbose_name="Ville")
    pays                  = models.CharField(max_length=100, default="Mali", verbose_name="Pays")
    boite_postale         = models.CharField(max_length=50,  blank=True, null=True, verbose_name="Boîte postale")
    telephone             = models.CharField(max_length=20,  verbose_name="Téléphone principal")
    telephone2            = models.CharField(max_length=20,  blank=True, null=True, verbose_name="Téléphone secondaire")
    email                 = models.EmailField(blank=True, null=True, verbose_name="Email")
    site_web              = models.URLField(blank=True, null=True, verbose_name="Site web")

    # --- Représentant légal ---
    nom_representant      = models.CharField(max_length=100, verbose_name="Nom du représentant")
    prenom_representant   = models.CharField(max_length=100, verbose_name="Prénom du représentant")
    fonction_representant = models.CharField(max_length=100, blank=True, null=True, verbose_name="Fonction")
    telephone_representant = models.CharField(max_length=20, blank=True, null=True, verbose_name="Tél. représentant")
    email_representant    = models.EmailField(blank=True, null=True, verbose_name="Email représentant")

    # --- Informations bancaires ---
    banque                = models.CharField(max_length=150, blank=True, null=True, verbose_name="Banque")
    numero_compte         = models.CharField(max_length=50,  blank=True, null=True, verbose_name="N° Compte bancaire")
    code_swift            = models.CharField(max_length=20,  blank=True, null=True, verbose_name="Code SWIFT / BIC")

    # --- Statut & suivi ---
    statut                = models.CharField(max_length=20, choices=STATUT_CHOICES, default='ACTIF', verbose_name="Statut")
    notes                 = models.TextField(blank=True, null=True, verbose_name="Notes / Observations")
    date_enregistrement   = models.DateTimeField(auto_now_add=True, verbose_name="Date d'enregistrement")
    date_modification     = models.DateTimeField(auto_now=True, verbose_name="Dernière modification")

    class Meta:
        verbose_name        = "Marketeur"
        verbose_name_plural = "Marketeurs"
        ordering            = ['raison_sociale']

    def __str__(self):
        return f"{self.raison_sociale} ({self.sigle or self.forme_juridique})"

    @property
    def representant_complet(self):
        return f"{self.prenom_representant} {self.nom_representant}"


# ─────────────────────────────────────────────────────────────
#  CAMION CITERNE
# ─────────────────────────────────────────────────────────────
class Camion(models.Model):

    STATUT_CHOICES = [
        ('EN_SERVICE',    'En service'),
        ('HORS_SERVICE',  'Hors service'),
        ('EN_MAINTENANCE','En maintenance'),
        ('RETIRE',        'Retiré'),
    ]

    TYPE_PRODUIT_CHOICES = [
        ('Carburant', 'Carburant'),
        ('HUILE',    'Huile'),
        ('MIXTE',    'Mixte'),
        ('AUTRE',    'Autre'),
    ]

    # --- Identification ---
    immatriculation       = models.CharField(max_length=30, unique=True, verbose_name="Immatriculation")
    marque                = models.CharField(max_length=100, verbose_name="Marque")
    modele                = models.CharField(max_length=100, blank=True, null=True, verbose_name="Modèle")
    annee_fabrication     = models.PositiveIntegerField(blank=True, null=True, verbose_name="Année de fabrication")
    couleur               = models.CharField(max_length=50, blank=True, null=True, verbose_name="Couleur")
    numero_serie_chassis  = models.CharField(max_length=100, blank=True, null=True, verbose_name="N° Série châssis")
    numero_serie_moteur   = models.CharField(max_length=100, blank=True, null=True, verbose_name="N° Série moteur")

    # --- Citerne ---
    capacite_totale       = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Capacité totale (litres)")
    nombre_compartiments  = models.PositiveIntegerField(default=1, verbose_name="Nombre de compartiments")
    type_produit          = models.CharField(max_length=20, choices=TYPE_PRODUIT_CHOICES, verbose_name="Type de produit")

    # --- Documents ---
    date_mise_en_circulation = models.DateField(blank=True, null=True, verbose_name="Date de mise en circulation")
    carte_grise           = models.FileField(upload_to='camions/documents/', blank=True, null=True, verbose_name="Carte grise")

    # --- Assurance ---
    compagnie_assurance        = models.CharField(max_length=150, blank=True, null=True, verbose_name="Compagnie d'assurance")
    numero_police_assurance    = models.CharField(max_length=100, blank=True, null=True, verbose_name="N° Police assurance")
    date_expiration_assurance  = models.DateField(blank=True, null=True, verbose_name="Expiration assurance")

    # --- Technique ---
    date_derniere_revision     = models.DateField(blank=True, null=True, verbose_name="Dernière révision")
    date_prochaine_revision    = models.DateField(blank=True, null=True, verbose_name="Prochaine révision")
    kilometrage                = models.PositiveIntegerField(blank=True, null=True, verbose_name="Kilométrage (km)")

    # --- Lien marketeur (optionnel) ---
    marketeur = models.ForeignKey(
        'Marketeur', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='camions',
        verbose_name="Marketeur"
    )

    # --- Statut & suivi ---
    statut              = models.CharField(max_length=20, choices=STATUT_CHOICES, default='EN_SERVICE', verbose_name="Statut")
    notes               = models.TextField(blank=True, null=True, verbose_name="Notes")
    date_enregistrement = models.DateTimeField(auto_now_add=True, verbose_name="Date d'enregistrement")
    date_modification   = models.DateTimeField(auto_now=True, verbose_name="Dernière modification")

    class Meta:
        verbose_name        = "Camion citerne"
        verbose_name_plural = "Camions citernes"
        ordering            = ['immatriculation']

    def __str__(self):
        return f"{self.immatriculation} — {self.marque} ({self.capacite_totale} L)"


# ─────────────────────────────────────────────────────────────
#  CHAUFFEUR
# ─────────────────────────────────────────────────────────────
class Chauffeur(models.Model):

    STATUT_CHOICES = [
        ('ACTIF',    'Actif'),
        ('INACTIF',  'Inactif'),
        ('SUSPENDU', 'Suspendu'),
    ]

    CATEGORIE_PERMIS_CHOICES = [
        ('B',   'B'),
        ('C',   'C'),
        ('D',   'D'),
        ('CE',  'CE'),
        ('C1E', 'C1E'),
        ('AUTRE','Autre'),
    ]

    # --- Identité ---
    nom             = models.CharField(max_length=100, verbose_name="Nom")
    prenom          = models.CharField(max_length=100, verbose_name="Prénom(s)")
    date_naissance  = models.DateField(blank=True, null=True, verbose_name="Date de naissance")
    lieu_naissance  = models.CharField(max_length=150, blank=True, null=True, verbose_name="Lieu de naissance")
    nationalite     = models.CharField(max_length=100, default="Malien(ne)", verbose_name="Nationalité")
    photo           = models.ImageField(upload_to='chauffeurs/photos/', blank=True, null=True, verbose_name="Photo")

    # --- Contact ---
    telephone  = models.CharField(max_length=20, verbose_name="Téléphone")
    telephone2 = models.CharField(max_length=20, blank=True, null=True, verbose_name="Téléphone 2")
    email      = models.EmailField(blank=True, null=True, verbose_name="Email")
    adresse    = models.TextField(blank=True, null=True, verbose_name="Adresse")

    # --- Permis ---
    numero_permis          = models.CharField(max_length=50, unique=True, verbose_name="N° Permis de conduire")
    categorie_permis       = models.CharField(max_length=10, choices=CATEGORIE_PERMIS_CHOICES, verbose_name="Catégorie permis")
    date_obtention_permis  = models.DateField(blank=True, null=True, verbose_name="Date d'obtention")
    date_expiration_permis = models.DateField(blank=True, null=True, verbose_name="Date d'expiration")

    # --- Professionnel ---
    numero_employe = models.CharField(max_length=50, blank=True, null=True, verbose_name="N° Employé")
    date_embauche  = models.DateField(blank=True, null=True, verbose_name="Date d'embauche")

    # --- Liens (optionnels) ---
    marketeur = models.ForeignKey(
        'Marketeur', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='chauffeurs',
        verbose_name="Marketeur"
    )
    camion = models.ForeignKey(
        'Camion', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='chauffeurs',
        verbose_name="Camion assigné"
    )

    # --- Statut & suivi ---
    statut              = models.CharField(max_length=20, choices=STATUT_CHOICES, default='ACTIF', verbose_name="Statut")
    notes               = models.TextField(blank=True, null=True, verbose_name="Notes")
    date_enregistrement = models.DateTimeField(auto_now_add=True, verbose_name="Date d'enregistrement")
    date_modification   = models.DateTimeField(auto_now=True, verbose_name="Dernière modification")

    class Meta:
        verbose_name        = "Chauffeur"
        verbose_name_plural = "Chauffeurs"
        ordering            = ['nom', 'prenom']

    def __str__(self):
        return f"{self.prenom} {self.nom}"

    @property
    def nom_complet(self):
        return f"{self.prenom} {self.nom}"

    @classmethod
    def get_next_numero(cls):
        from datetime import date
        year = date.today().year
        prefix = f"EMP-{year}-"
        last = (
            cls.objects
            .filter(numero_employe__startswith=prefix)
            .order_by('numero_employe')
            .last()
        )
        if last and last.numero_employe:
            try:
                n = int(last.numero_employe.split('-')[-1]) + 1
            except (ValueError, IndexError):
                n = 1
        else:
            n = 1
        return f"{prefix}{n:03d}"


# ─────────────────────────────────────────────────────────────
#  FAMILLE DE PRODUITS
# ─────────────────────────────────────────────────────────────
class Famille(models.Model):

    STATUT_CHOICES = [
        ('ACTIF',   'Actif'),
        ('INACTIF', 'Inactif'),
    ]

    COULEUR_CHOICES = [
        ('#3B82F6', 'Bleu'),
        ('#10B981', 'Vert'),
        ('#F59E0B', 'Amber'),
        ('#EF4444', 'Rouge'),
        ('#8B5CF6', 'Violet'),
        ('#EC4899', 'Rose'),
        ('#06B6D4', 'Cyan'),
        ('#E8760A', 'Orange'),
    ]

    nom         = models.CharField(max_length=150, unique=True, verbose_name="Nom de la famille")
    code        = models.CharField(max_length=20, unique=True, verbose_name="Code")
    description = models.TextField(blank=True, null=True, verbose_name="Description")
    couleur     = models.CharField(max_length=10, choices=COULEUR_CHOICES, default='#3B82F6', verbose_name="Couleur d'identification")
    statut      = models.CharField(max_length=10, choices=STATUT_CHOICES, default='ACTIF', verbose_name="Statut")

    date_creation     = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    date_modification = models.DateTimeField(auto_now=True, verbose_name="Dernière modification")

    class Meta:
        verbose_name        = "Famille de produits"
        verbose_name_plural = "Familles de produits"
        ordering            = ['nom']

    def __str__(self):
        return f"{self.nom} ({self.code})"

    @property
    def nb_produits(self):
        return self.produits.count()


# ─────────────────────────────────────────────────────────────
#  PRODUIT
# ─────────────────────────────────────────────────────────────
class Produit(models.Model):

    STATUT_CHOICES = [
        ('ACTIF',       'Actif'),
        ('INACTIF',     'Inactif'),
        ('DISCONTINUE', 'Discontinué'),
    ]

    UNITE_MESURE_CHOICES = [
        ('LITRE',  'Litre (L)'),
        ('M3',     'Mètre cube (m³)'),
        ('KG',     'Kilogramme (kg)'),
        ('TONNE',  'Tonne (t)'),
        ('BARIL',  'Baril'),
    ]

    nom          = models.CharField(max_length=200, unique=True, verbose_name="Nom du produit")
    code         = models.CharField(max_length=30, unique=True, verbose_name="Code produit")
    famille      = models.ForeignKey(
        'Famille', on_delete=models.PROTECT,
        related_name='produits', verbose_name="Famille"
    )
    description  = models.TextField(blank=True, null=True, verbose_name="Description")
    unite_mesure = models.CharField(max_length=10, choices=UNITE_MESURE_CHOICES, default='LITRE', verbose_name="Unité de mesure")
    prix_unitaire= models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True, verbose_name="Prix unitaire (FCFA)")
    prix_passage = models.DecimalField(
        max_digits=10, decimal_places=4,
        blank=True, null=True,
        verbose_name="Frais de passage (FCFA/L)",
        help_text="Tarif spécifique à ce produit. Laissez vide pour utiliser le tarif global (ParametresCoulage).",
    )
    seuil_alerte = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True, verbose_name="Seuil d'alerte (stock min)")
    statut       = models.CharField(max_length=15, choices=STATUT_CHOICES, default='ACTIF', verbose_name="Statut")
    notes        = models.TextField(blank=True, null=True, verbose_name="Notes")

    stock_actuel = models.DecimalField(
        max_digits=14, decimal_places=2, default=0,
        verbose_name="Stock actuel (L)",
        help_text="Mis à jour automatiquement après validation du jaugeage"
    )
    date_maj_stock = models.DateTimeField(
        blank=True, null=True,
        verbose_name="Dernière mise à jour du stock"
    )

    date_creation     = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    date_modification = models.DateTimeField(auto_now=True, verbose_name="Dernière modification")

    class Meta:
        verbose_name        = "Produit"
        verbose_name_plural = "Produits"
        ordering            = ['famille', 'nom']

    def __str__(self):
        return f"{self.nom} ({self.code})"

    @property
    def nb_cuves(self):
        return self.cuves.count()

    @classmethod
    def mettre_a_jour_stocks(cls, jaugeage):
        """
        Met à jour stock_actuel de chaque produit à partir des mesures
        du jaugeage donné (volume_ambiant_depot = stock physique réel).
        Appelé automatiquement après chaque validation de jaugeage.
        """
        from django.utils import timezone

        for produit in cls.objects.all():
            mesures = jaugeage.mesures.filter(
                cuve__produit=produit
            ).select_related('cuve__parametre_jaugeage')
            total = 0
            for mesure in mesures:
                v = mesure.volume_ambiant_depot
                if v is not None:
                    total += float(v)

            produit.stock_actuel = total
            produit.date_maj_stock = timezone.now()
            produit.save(update_fields=['stock_actuel', 'date_maj_stock'])


# ─────────────────────────────────────────────────────────────
#  CUVE
# ─────────────────────────────────────────────────────────────
class Cuve(models.Model):

    STATUT_CHOICES = [
        ('ACTIVE',         'Active'),
        ('INACTIVE',       'Inactive'),
        ('EN_MAINTENANCE', 'En maintenance'),
        ('HORS_SERVICE',   'Hors service'),
    ]

    TYPE_CUVE_CHOICES = [
        ('AERIENNE',      'Aérienne'),
        ('SOUTERRAINE',   'Souterraine'),
        ('SEMI_ENTERREE', 'Semi-enterrée'),
    ]

    MATERIAU_CHOICES = [
        ('ACIER',       'Acier'),
        ('INOX',        'Acier inoxydable'),
        ('FIBRE_VERRE', 'Fibre de verre'),
        ('BETON',       'Béton'),
        ('AUTRE',       'Autre'),
    ]

    # --- Identification ---
    numero      = models.CharField(max_length=50, unique=True, verbose_name="Numéro de cuve")
    designation = models.CharField(max_length=200, verbose_name="Désignation")
    produit     = models.ForeignKey(
        'Produit', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='cuves',
        verbose_name="Produit stocké"
    )

    # --- Capacité & niveau ---
    capacite_totale = models.DecimalField(
        max_digits=12, decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name="Capacité totale (litres)"
    )
    niveau_actuel   = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        validators=[MinValueValidator(0)],
        verbose_name="Niveau actuel (litres)"
    )

    # --- Caractéristiques ---
    type_cuve   = models.CharField(max_length=20, choices=TYPE_CUVE_CHOICES, default='AERIENNE', verbose_name="Type de cuve")
    materiau    = models.CharField(max_length=20, choices=MATERIAU_CHOICES, default='ACIER', verbose_name="Matériau")
    localisation= models.CharField(max_length=200, blank=True, null=True, verbose_name="Localisation / Emplacement")

    # --- Dates ---
    date_installation       = models.DateField(blank=True, null=True, verbose_name="Date d'installation")
    date_derniere_inspection= models.DateField(blank=True, null=True, verbose_name="Dernière inspection")
    date_prochaine_inspection=models.DateField(blank=True, null=True, verbose_name="Prochaine inspection")

    # --- Statut & suivi ---
    statut            = models.CharField(max_length=20, choices=STATUT_CHOICES, default='ACTIVE', verbose_name="Statut")
    notes             = models.TextField(blank=True, null=True, verbose_name="Notes / Observations")
    date_enregistrement= models.DateTimeField(auto_now_add=True, verbose_name="Date d'enregistrement")
    date_modification  = models.DateTimeField(auto_now=True, verbose_name="Dernière modification")

    class Meta:
        verbose_name        = "Cuve"
        verbose_name_plural = "Cuves"
        ordering            = ['numero']

    def __str__(self):
        return f"{self.numero} — {self.designation}"

    @property
    def taux_remplissage(self):
        if self.capacite_totale and self.capacite_totale > 0:
            return round((self.niveau_actuel / self.capacite_totale) * 100, 1)
        return 0

    @property
    def disponible(self):
        return self.capacite_totale - self.niveau_actuel
# ─────────────────────────────────────────────────────────────
#  PARAMÈTRES DE JAUGEAGE PAR CUVE
# ─────────────────────────────────────────────────────────────
class ParametreJaugeageCuve(models.Model):
    """
    Paramètres métrologiques d'une cuve : caractéristiques physiques
    fixes (HTT, Hml) + données du certificat de jaugeage officiel.
    Une seule ligne par cuve, modifiée uniquement lors du re-jaugeage.
    """
    cuve = models.OneToOneField(
        'Cuve', on_delete=models.CASCADE,
        related_name='parametre_jaugeage',
        verbose_name="Cuve"
    )
 
    # --- Caractéristiques physiques de la cuve ---
    hauteur_totale_temoin = models.IntegerField(
        verbose_name="Hauteur Totale Témoin - HTT (mm)",
        help_text="Hauteur de référence de la cuve en millimètres (ex: 12981)"
    )
    hauteur_min_livraison = models.IntegerField(
        default=2000,
        verbose_name="Hauteur minimale de livraison - Hml (mm)",
    )
    correction_creux = models.IntegerField(
        default=4,
        verbose_name="Correction du creux mesuré (mm)",
        help_text="Correction systématique appliquée au creux mesuré (CONV_ADAMA L2)"
    )
    remplissage_maxi = models.DecimalField(
        max_digits=12, decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name="Remplissage maximum (litres)",
        help_text="Volume maximum autorisé en exploitation"
    )
 
    # --- Certificat de jaugeage officiel ---
    v_a = models.DecimalField(
        max_digits=12, decimal_places=2,
        verbose_name="V(A) - Volume certificat hauteur décimal (litres)",
    )
    v_mn = models.IntegerField(
        verbose_name="V/mn - Volume par millimètre (litres/mm)",
    )
    reference_certificat = models.CharField(
        max_length=100, blank=True, null=True,
        verbose_name="Référence du certificat"
    )
    date_certificat = models.DateField(
        blank=True, null=True, verbose_name="Date du certificat"
    )
    organisme_certificateur = models.CharField(
        max_length=200, blank=True, null=True,
        verbose_name="Organisme certificateur"
    )
    date_prochain_jaugeage = models.DateField(
        blank=True, null=True,
        verbose_name="Date du prochain re-jaugeage"
    )
 
    is_pompe = models.BooleanField(
        default=False,
        verbose_name="Est une pompe (index)",
        help_text="True pour P GO, P SP"
    )
 
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    notes = models.TextField(blank=True, null=True, verbose_name="Notes")
 
    class Meta:
        verbose_name = "Paramètre de jaugeage de cuve"
        verbose_name_plural = "Paramètres de jaugeage des cuves"
 
    def __str__(self):
        return f"Paramètres jaugeage {self.cuve.numero}"
 
 
# ─────────────────────────────────────────────────────────────
#  JAUGEAGE DU JOUR (historique - plusieurs par jour possibles)
# ─────────────────────────────────────────────────────────────
class JaugeageJour(models.Model):
    """
    En-tête d'un jaugeage. Historique conservé.
    Plusieurs jaugeages par jour autorisés (ex: AVR le matin, APR l'après-midi).
    """
    TYPE_CHOICES = [
        ('AVR', 'Avant'),
        ('APR', 'Après'),
        ('J',   'Jaugeage normal'),
    ]
 
    date_jaugeage = models.DateField(verbose_name="Date du jaugeage")
    type_jaugeage = models.CharField(
        max_length=10, choices=TYPE_CHOICES, default='J',
        verbose_name="Type de jaugeage"
    )
    heure_jaugeage = models.TimeField(
        blank=True, null=True,
        verbose_name="Heure du jaugeage",
        help_text="Permet de différencier plusieurs jaugeages le même jour"
    )
    depot = models.CharField(
        max_length=100, default='SGDS SANKE', verbose_name="Dépôt"
    )
    type_depot = models.CharField(
        max_length=50, default='Dépôt de droit', verbose_name="Type de dépôt"
    )
    temperature_reference = models.DecimalField(
        max_digits=4, decimal_places=1, default=Decimal('15.0'),
        verbose_name="Température de référence (°C)"
    )
    operateur = models.CharField(
        max_length=100, blank=True, null=True, verbose_name="Opérateur"
    )
    notes = models.TextField(
        blank=True, null=True, verbose_name="Notes / Observations"
    )

    # ── Workflow de validation ──────────────────────────────────
    est_valide = models.BooleanField(default=False, verbose_name="Validé")
    date_validation = models.DateTimeField(
        blank=True, null=True, verbose_name="Date de validation"
    )
    valide_par = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        blank=True, null=True, related_name='jaugeages_valides',
        verbose_name="Validé par"
    )

    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
 
    class Meta:
        verbose_name = "Jaugeage"
        verbose_name_plural = "Jaugeages"
        ordering = ['-date_jaugeage', '-heure_jaugeage', '-date_creation']
        constraints = [
            models.UniqueConstraint(
                fields=['date_jaugeage', 'type_jaugeage', 'heure_jaugeage'],
                name='unique_jaugeage_date_type_heure'
            )
        ]
 
    def __str__(self):
        heure = f" {self.heure_jaugeage.strftime('%H:%M')}" if self.heure_jaugeage else ""
        return f"Jaugeage du {self.date_jaugeage}{heure} ({self.get_type_jaugeage_display()})"
 
    @classmethod
    def dernier(cls):
        """Retourne le dernier jaugeage enregistré (ou None)."""
        return cls.objects.first()  # ordering descendant déjà appliqué
 
    def clean(self):
        super().clean()
        if not self.date_jaugeage:
            return
        from django.core.exceptions import ValidationError as _VE
        try:
            from SGDS.services.periode_comptable import periode_pour_date
            periode = periode_pour_date(self.date_jaugeage)
        except Exception:
            return
        if periode is None:
            mois_annee = self.date_jaugeage.strftime('%B %Y')
            raise _VE(
                f"Aucune période comptable n'est ouverte pour {mois_annee}. "
                "Demandez à un administrateur d'ouvrir la période avant de créer un jaugeage."
            )
        if periode.statut == 'CLOTUREE':
            raise _VE(
                f"La période {periode} est clôturée. Aucune modification n'est possible."
            )

    def save(self, *args, **kwargs):
        if not kwargs.get('update_fields'):
            self.full_clean()
        super().save(*args, **kwargs)

    @classmethod
    def creer_nouveau_jaugeage(cls, date_jaugeage=None, type_jaugeage='J',
                                heure_jaugeage=None, operateur=None, notes=None):
        """
        Crée un nouveau jaugeage en pré-remplissant les MesureCuve avec les
        valeurs du dernier jaugeage existant.
 
        Usage :
            from datetime import date, time
            nouveau = JaugeageJour.creer_nouveau_jaugeage(
                date_jaugeage=date.today(),
                type_jaugeage='APR',
                heure_jaugeage=time(14, 30),
                operateur='Yacouba'
            )
        """
        from datetime import date as _date
 
        # 1. Créer l'en-tête
        nouveau = cls.objects.create(
            date_jaugeage=date_jaugeage or _date.today(),
            type_jaugeage=type_jaugeage,
            heure_jaugeage=heure_jaugeage,
            operateur=operateur,
            notes=notes,
        )
 
        # 2. Récupérer le dernier jaugeage précédent (s'il existe)
        precedent = cls.objects.exclude(pk=nouveau.pk).first()
 
        if precedent:
            # Copier les mesures du jaugeage précédent
            for ancienne_mesure in precedent.mesures.all():
                MesureCuve.objects.create(
                    jaugeage=nouveau,
                    cuve=ancienne_mesure.cuve,
                    creux_mesure=ancienne_mesure.creux_mesure,
                    t1=ancienne_mesure.t1,
                    t2=ancienne_mesure.t2,
                    t3=ancienne_mesure.t3,
                    temperature_obs=ancienne_mesure.temperature_obs,
                    densite_moyenne=ancienne_mesure.densite_moyenne,
                    densite_15c=ancienne_mesure.densite_15c,
                    facteur_vcf=ancienne_mesure.facteur_vcf,
                    volume_additionnel=ancienne_mesure.volume_additionnel,
                    volume_tuyauterie=ancienne_mesure.volume_tuyauterie,
                    volume_eau=ancienne_mesure.volume_eau,
                )
        else:
            # Pas de précédent : créer des mesures vides
            cuves = Cuve.objects.filter(parametre_jaugeage__isnull=False)
            for cuve in cuves:
                MesureCuve.objects.create(jaugeage=nouveau, cuve=cuve)
 
        return nouveau
 
 
# ─────────────────────────────────────────────────────────────
#  MESURE PAR CUVE (liée à un JaugeageJour précis)
# ─────────────────────────────────────────────────────────────
class MesureCuve(models.Model):
    """
    Mesures saisies pour une cuve lors d'un jaugeage donné.
    Une mesure = 1 cuve × 1 jaugeage.
    """
    jaugeage = models.ForeignKey(
        'JaugeageJour', on_delete=models.CASCADE,
        related_name='mesures',
        verbose_name="Jaugeage"
    )
    cuve = models.ForeignKey(
        'Cuve', on_delete=models.CASCADE,
        related_name='mesures',
        verbose_name="Cuve"
    )
 
    # --- Hauteurs ---
    creux_mesure = models.IntegerField(
        blank=True, null=True,
        verbose_name="Creux mesuré (mm)",
    )

    # --- Volume à la hauteur décimale saisi (pour contrôle) ---
    v_a_saisi = models.DecimalField(
    max_digits=12, decimal_places=2,
    blank=True, null=True,
    verbose_name="V(A) certificat (litres)",
    help_text="Volume lu dans le cahier de jaugeage pour la hauteur décimale du jour"
)
 
    # --- Températures (3 prises sur le bac) ---
    t1 = models.DecimalField(
        max_digits=5, decimal_places=2, blank=True, null=True,
        verbose_name="Température t1 (5/6 h)"
    )
    t2 = models.DecimalField(
        max_digits=5, decimal_places=2, blank=True, null=True,
        verbose_name="Température t2 (1/2 h)"
    )
    t3 = models.DecimalField(
        max_digits=5, decimal_places=2, blank=True, null=True,
        verbose_name="Température t3 (1/6 h)"
    )
    temperature_obs = models.DecimalField(
        max_digits=5, decimal_places=2, blank=True, null=True,
        verbose_name="Température observée sur densité (°C)"
    )
 
    # --- Densité ---
    densite_moyenne = models.DecimalField(
        max_digits=7, decimal_places=2, blank=True, null=True,
        verbose_name="Densité moyenne mesurée"
    )
    densite_15c = models.DecimalField(
        max_digits=7, decimal_places=2, blank=True, null=True,
        verbose_name="Densité standard à 15°C (D15°C)",
    )
    facteur_vcf = models.DecimalField(
        max_digits=6, decimal_places=4, blank=True, null=True,
        verbose_name="Facteur de correction de volume (Vcf)",
    )
 
    # --- Volumes additionnels ---
    volume_additionnel = models.IntegerField(
        default=0, verbose_name="Volume ambiant additionnel (litres)"
    )
    volume_tuyauterie = models.IntegerField(
        default=0, verbose_name="Volume tuyauterie (litres)"
    )
    volume_eau = models.IntegerField(
        default=0, verbose_name="Volume eau (litres)"
    )
 
    date_modification = models.DateTimeField(auto_now=True)
 
    class Meta:
        verbose_name = "Mesure de cuve"
        verbose_name_plural = "Mesures des cuves"
        ordering = ['cuve__numero']
        constraints = [
            models.UniqueConstraint(
                fields=['jaugeage', 'cuve'],
                name='unique_mesure_jaugeage_cuve'
            )
        ]
 
    def __str__(self):
        return f"Mesure {self.cuve.numero} - {self.jaugeage}"
 
    # ─────────────────────────────────────────────────────
    #  PROPRIÉTÉS CALCULÉES (reproduisent toutes les formules)
    # ─────────────────────────────────────────────────────
 
    @property
    def _params(self):
        """Raccourci vers les paramètres de jaugeage de la cuve."""
        return getattr(self.cuve, 'parametre_jaugeage', None)
 
    @property
    def creux_corrige(self):
        """CONV_ADAMA C8 = creux_mesure - correction_creux"""
        if self.creux_mesure is None or self._params is None:
            return None
        return self.creux_mesure - self._params.correction_creux
 
    @property
    def hauteur_produit(self):
        """CONV_ADAMA C40 = HTT - creux_corrige"""
        if self.creux_corrige is None or self._params is None:
            return None
        return self._params.hauteur_totale_temoin - self.creux_corrige
 
    @property
    def hauteur_decimal(self):
        """CONV_ADAMA C41 = hauteur_produit arrondi à la dizaine inférieure"""
        h = self.hauteur_produit
        if h is None:
            return None
        return h - (h % 10)
 
    @property
    def surplus(self):
        """CONV_ADAMA C43 = hauteur_produit % 10"""
        h = self.hauteur_produit
        if h is None:
            return None
        return h % 10
 
    @property
    def volume_ambiant_bac(self):
        if self._params is None:
            return None
        s = self.surplus
        if s is None:
            return None
        # Priorité : V(A) saisi par l'opérateur > V(A) par défaut du paramètre
        va = self.v_a_saisi if self.v_a_saisi is not None else self._params.v_a
        return va + self._params.v_mn * s
 
    @property
    def temperature_moyenne(self):
        """CONV_ADAMA C55 = AVERAGE(t1, t2, t3)"""
        if self.t1 is None or self.t2 is None or self.t3 is None:
            return None
        return (self.t1 + self.t2 + self.t3) / 3
 
    @property
    def volume_physique(self):
        """RJJ E28 = volume_ambiant_bac + volume_tuyauterie - volume_eau"""
        v = self.volume_ambiant_bac
        if v is None:
            return None
        return v + self.volume_tuyauterie - self.volume_eau
 
    @property
    def volume_ambiant_depot(self):
        """RJJ E31 = volume_ambiant_bac + volume_additionnel"""
        v = self.volume_ambiant_bac
        if v is None:
            return None
        return v + self.volume_additionnel
 
    @property
    def volume_standard_15c(self):
        """RJJ E41 = volume_ambiant_depot × Vcf"""
        v = self.volume_ambiant_depot
        if v is None or self.facteur_vcf is None:
            return None
        return v * self.facteur_vcf
 
    @property
    def volume_disponible(self):
        """RJJ J7 = remplissage_maxi - volume_ambiant_depot"""
        v = self.volume_ambiant_depot
        if v is None or self._params is None:
            return None
        return self._params.remplissage_maxi - v

    # ─── Calculs automatiques via petroleum_calc ───

    @property
    def densite_15c_calculee(self):
        """ρ15 calculée via l'algorithme API MPMS (remplace la feuille TRH_15)."""
        if self.densite_moyenne is None or self.temperature_moyenne is None:
            return None
        return pc.density_at_15c(
            observed_density=float(self.densite_moyenne),
            observed_temperature=float(self.temperature_moyenne),
        )

    @property
    def vcf_calcule(self):
        """Vcf calculé (remplace la feuille TVCF_15)."""
        d15 = self.densite_15c_calculee
        if d15 is None or self.temperature_obs is None:
            return None
        return pc.vcf_to_15c(d15, observed_temperature=float(self.temperature_obs))

    @property
    def volume_standard_15c_calcule(self):
        """V@15°C recalculé = volume_ambiant_depot × Vcf."""
        v_amb = self.volume_ambiant_depot
        vcf = self.vcf_calcule
        if v_amb is None or vcf is None:
            return None
        return float(v_amb) * vcf

    def save(self, *args, **kwargs):
        """Auto-remplit densite_15c et facteur_vcf à chaque sauvegarde."""
        if (self.densite_moyenne is not None
                and self.t1 is not None and self.t2 is not None and self.t3 is not None
                and self.temperature_obs is not None):
            d15 = self.densite_15c_calculee
            vcf = self.vcf_calcule
            if d15 is not None:
                self.densite_15c = Decimal(str(d15))
            if vcf is not None:
                self.facteur_vcf = Decimal(str(vcf))
        super().save(*args, **kwargs)
    

# ─────────────────────────────────────────────────────────────
#  MOUVEMENT (entrée, sortie, cession, acquittement)
# ─────────────────────────────────────────────────────────────
class Mouvement(models.Model):
    """
    Modèle unifié de gestion des mouvements de produits pétroliers :
      - ENTREE      : réception d'un camion citerne en provenance d'un dépôt expéditeur
      - SORTIE      : enlèvement par un marketeur / client
      - CESSION     : transfert comptable entre deux marketeurs
      - ACQUITTEMENT: passage du régime SOUS_DOUANE vers ACQUITTE (sans mouvement physique)
    """

    # ── Choix ──────────────────────────────────────────────────
    TYPE_CHOICES = [
        ('ENTREE',        'Entrée'),
        ('SORTIE',        'Sortie'),
        ('CESSION',       'Cession'),
        ('ACQUITTEMENT',  'Acquittement'),
    ]
    REGIME_CHOICES = [
        ('ACQUITTE',    'Acquitté'),
        ('SOUS_DOUANE', 'Sous douane'),
    ]
    MODE_REGLEMENT_CHOICES = [
        ('ESP-IMMEDIAT', 'Espèces (immédiat)'),
        ('VIREMENT',     'Virement bancaire'),
        ('CHEQUE',       'Chèque'),
        ('CREDIT',       'Crédit'),
    ]

    # ── Champs communs ─────────────────────────────────────────
    type_mouvement        = models.CharField(max_length=15, choices=TYPE_CHOICES, verbose_name="Type de mouvement")
    produit               = models.ForeignKey('Produit',   on_delete=models.PROTECT, related_name='mouvements', verbose_name="Produit")
    regime_douanier       = models.CharField(max_length=15, choices=REGIME_CHOICES, verbose_name="Régime douanier")
    numero_enregistrement = models.CharField(
        max_length=100, unique=True, blank=True, null=True,
        editable=False,
        verbose_name="N° d'enregistrement",
        help_text="Généré automatiquement à la création (ex: ENT-2026-0001)"
    )
    date_mouvement        = models.DateField(verbose_name="Date du mouvement")
    camion                = models.ForeignKey('Camion',    on_delete=models.PROTECT,  null=True, blank=True, related_name='mouvements', verbose_name="Camion citerne")
    chauffeur             = models.ForeignKey('Chauffeur', on_delete=models.SET_NULL, null=True, blank=True, related_name='mouvements', verbose_name="Chauffeur")
    marketeur             = models.ForeignKey('Marketeur', on_delete=models.PROTECT,  related_name='mouvements', verbose_name="Marketeur (propriétaire)")
    cuve                  = models.ForeignKey('Cuve',      on_delete=models.SET_NULL, null=True, blank=True, related_name='mouvements', verbose_name="Cuve affectée")
    collaborateur         = models.CharField(max_length=150, blank=True, null=True, verbose_name="Collaborateur (saisie)")
    notes                 = models.TextField(blank=True, null=True, verbose_name="Notes / Observations")
    date_saisie           = models.DateTimeField(auto_now_add=True, verbose_name="Date de saisie")
    date_modification     = models.DateTimeField(auto_now=True, verbose_name="Dernière modification")

    # ── Champs ENTRÉE ──────────────────────────────────────────
    provenance                = models.CharField(max_length=200, blank=True, null=True, verbose_name="Provenance (dépôt expéditeur)")
    bl_expediteur             = models.CharField(max_length=100, blank=True, null=True, verbose_name="N° BL Dépôt Chargeur")
    bl_client                 = models.CharField(max_length=100, blank=True, null=True, verbose_name="N° BL Client")
    date_chargement           = models.DateField(blank=True, null=True, verbose_name="Date de chargement")
    date_dechargement         = models.DateField(blank=True, null=True, verbose_name="Date de déchargement")
    volume_ambiant_expediteur = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True, verbose_name="Volume ambiant expéditeur (L)")
    volume_15c_expediteur     = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True, verbose_name="Volume @15°C expéditeur (L)")
    densite_15c_expediteur    = models.DecimalField(max_digits=7,  decimal_places=2, blank=True, null=True, verbose_name="Densité @15°C expéditeur (kg/m³)")
    temperature_chargement    = models.DecimalField(max_digits=5,  decimal_places=2, blank=True, null=True, verbose_name="Température au chargement (°C)")
    volume_ambiant_recu       = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True, verbose_name="Volume ambiant reçu (L)")
    temperature_reception     = models.DecimalField(max_digits=5,  decimal_places=2, blank=True, null=True, verbose_name="Température à la réception (°C)")
    temperature_labo          = models.DecimalField(max_digits=5,  decimal_places=2, blank=True, null=True, verbose_name="Température labo (°C)")
    densite_observee_labo     = models.DecimalField(max_digits=7,  decimal_places=2, blank=True, null=True, verbose_name="Densité observée labo (kg/m³)")

    # ── Champs calculés ENTRÉE (auto via save) ─────────────────
    densite_15c_calculee      = models.DecimalField(max_digits=7,  decimal_places=2, blank=True, null=True, verbose_name="Densité @15°C calculée (kg/m³)")
    ecart_densite_15c         = models.DecimalField(max_digits=8,  decimal_places=4, blank=True, null=True,
        verbose_name="Écart densité 15°C (calc − expé) / 1000",
        help_text="(D15°C calculée labo − D15°C expéditeur BL) / 1000. Colonne AH Excel ENTREE. Alerte si |écart| > 0.001."
    )
    coefficient_conversion_15c= models.DecimalField(max_digits=8,  decimal_places=4, blank=True, null=True, verbose_name="Coefficient Vcf @15°C")
    volume_15c_recu           = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True, verbose_name="Volume @15°C reçu (L)")
    perte_gain_reception      = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name="Perte / Gain réception (L ambiant)")
    perte_gain_15c            = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name="Perte / Gain @15°C (L)")
    poids_kg                  = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True, verbose_name="Poids (kg)")

    # ── Champs SORTIE ──────────────────────────────────────────
    reference_client_externe    = models.CharField(max_length=100, blank=True, null=True, verbose_name="Référence client externe")
    destination                 = models.CharField(max_length=200, blank=True, null=True, verbose_name="Destination")
    code_destination            = models.CharField(max_length=50,  blank=True, null=True, verbose_name="Code destination")
    date_permis                 = models.DateField(blank=True, null=True, verbose_name="Date du permis douanier")
    numero_permis_sortie        = models.CharField(max_length=100, blank=True, null=True, verbose_name="N° Permis")
    numero_s                    = models.CharField(max_length=100, blank=True, null=True, verbose_name="N° S")
    numero_c                    = models.CharField(max_length=100, blank=True, null=True, verbose_name="N° C")
    volume_ambiant_sortie       = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True, verbose_name="Volume ambiant sortie (L)")
    densite_15c_sortie          = models.DecimalField(max_digits=7,  decimal_places=2, blank=True, null=True, verbose_name="Densité @15°C sortie (kg/m³)")
    temperature_sortie          = models.DecimalField(max_digits=5,  decimal_places=2, blank=True, null=True, verbose_name="Température sortie (°C)")
    coefficient_conversion_sortie = models.DecimalField(max_digits=8, decimal_places=4, blank=True, null=True, verbose_name="Coefficient Vcf sortie")
    volume_15c_sortie           = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True, verbose_name="Volume @15°C sortie (L)")
    poids_sortie_kg             = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True, verbose_name="Poids sortie (kg)")
    mode_reglement              = models.CharField(max_length=20, choices=MODE_REGLEMENT_CHOICES, blank=True, null=True, verbose_name="Mode de règlement")

    # ── Champs CESSION ─────────────────────────────────────────
    cession_marketeur_destinataire = models.ForeignKey(
        'Marketeur', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='cessions_recues',
        verbose_name="Marketeur destinataire (cession)"
    )
    cession_volume_ambiant = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True, verbose_name="Volume ambiant cédé (L)")
    cession_volume_15c     = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True, verbose_name="Volume @15°C cédé (L)")
    cession_motif          = models.CharField(max_length=300, blank=True, null=True, verbose_name="Motif de la cession")

    # ── Champs ACQUITTEMENT ────────────────────────────────────
    acquittement_volume_ambiant          = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True, verbose_name="Volume ambiant à acquitter (L)")
    acquittement_volume_15c              = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True, verbose_name="Volume @15°C à acquitter (L)")
    acquittement_reference_declaration   = models.CharField(max_length=200, blank=True, null=True, verbose_name="Référence déclaration douanière")
    acquittement_date_declaration        = models.DateField(blank=True, null=True, verbose_name="Date de la déclaration douanière")
    entree_source = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='acquittements',
        verbose_name="Entrée source (Sous douane)",
        help_text=(
            "Mouvement d'ENTREE SOUS_DOUANE dont ce mouvement est l'acquittement douanier. "
            "Sélectionner via le N° BL Dépôt Chargeur de l'entrée correspondante."
        ),
        limit_choices_to={'type_mouvement': 'ENTREE', 'regime_douanier': 'SOUS_DOUANE'},
    )


    # ── Meta ───────────────────────────────────────────────────
    class Meta:
        verbose_name        = "Mouvement"
        verbose_name_plural = "Mouvements"
        ordering            = ['-date_mouvement', '-date_saisie']
        indexes = [
            models.Index(fields=['type_mouvement', 'date_mouvement']),
            models.Index(fields=['marketeur', 'date_mouvement']),
            models.Index(fields=['regime_douanier', 'date_mouvement']),
            models.Index(fields=['marketeur', 'regime_douanier', 'produit']),
        ]

    def __str__(self):
        return f"{self.get_type_mouvement_display()} — {self.marketeur} — {self.date_mouvement}"

    # ── Génération automatique du numéro d'enregistrement ────────
    @classmethod
    def generer_numero(cls, type_mouvement, annee=None):
        """
        Génère le prochain numéro disponible pour un type et une année.
        Format : PREFIXE-ANNEE-SEQUENCE  (ex: ENT-2026-0001)
        Le compteur est indépendant par type ET par année.
        Les trous de séquence (suite à des suppressions) sont normaux et voulus.
        """
        from datetime import date as _date
        if annee is None:
            annee = _date.today().year

        PREFIXES = {
            'ENTREE':       'ENT',
            'SORTIE':       'SOR',
            'CESSION':      'CES',
            'ACQUITTEMENT': 'ACQ',
        }
        prefixe = PREFIXES.get(type_mouvement)
        if not prefixe:
            raise ValueError(f"Type de mouvement inconnu : {type_mouvement}")

        debut = f"{prefixe}-{annee}-"

        # Dernier numéro existant pour ce type + cette année (tri lexicographique
        # suffisant grâce au padding 0000)
        dernier = (
            cls.objects
            .filter(numero_enregistrement__startswith=debut)
            .order_by('-numero_enregistrement')
            .first()
        )

        if dernier and dernier.numero_enregistrement:
            try:
                sequence = int(dernier.numero_enregistrement.split('-')[-1]) + 1
            except (ValueError, IndexError):
                sequence = 1
        else:
            sequence = 1

        return f"{debut}{sequence:04d}"

    def _calculer_auto(self):
        """Exécute tous les calculs automatiques selon le type de mouvement."""

        if self.type_mouvement == 'ENTREE':
            # ── SS3 : Données obtenues à la réception ─────────────

            # col. AC — Perte/gain réception = V_amb_reçu − V_amb_expéditeur
            if (self.volume_ambiant_recu is not None
                    and self.volume_ambiant_expediteur is not None):
                self.perte_gain_reception = round(
                    float(self.volume_ambiant_recu) - float(self.volume_ambiant_expediteur), 2
                )

            # col. AG — Densité @15°C calculée via API MPMS TRH_15
            if (self.densite_observee_labo is not None
                    and self.temperature_labo is not None):
                d15 = pc.density_at_15c(
                    float(self.densite_observee_labo),
                    float(self.temperature_labo)
                )
                self.densite_15c_calculee = round(d15, 2)

            # ── SS4 : Contrôle final avant déchargement ───────────

            # col. AH — Écart densité = (D15°C_cal − D15°C_expé) / 1000
            if (self.densite_15c_calculee is not None
                    and self.densite_15c_expediteur is not None):
                self.ecart_densite_15c = round(
                    (float(self.densite_15c_calculee) - float(self.densite_15c_expediteur))
                    / 1000, 4
                )

            # col. AI — Coefficient Vcf @15°C via API MPMS TVCF_15
            # Utilise temperature_RECEPTION (température du produit dans la citerne
            # au moment du déchargement) — colonne AI du classeur Excel.
            if (self.densite_15c_calculee is not None
                    and self.temperature_reception is not None):
                vcf = pc.vcf_to_15c(
                    float(self.densite_15c_calculee),
                    float(self.temperature_reception)
                )
                self.coefficient_conversion_15c = round(vcf, 4)

            # col. AJ — Volume @15°C reçu = V_amb_reçu × Vcf
            if (self.volume_ambiant_recu is not None
                    and self.coefficient_conversion_15c is not None):
                self.volume_15c_recu = round(
                    float(self.volume_ambiant_recu)
                    * float(self.coefficient_conversion_15c), 2
                )

            # col. AK — Perte/gain @15°C = perte_gain_reception × Vcf
            if (self.perte_gain_reception is not None
                    and self.coefficient_conversion_15c is not None):
                self.perte_gain_15c = round(
                    float(self.perte_gain_reception)
                    * float(self.coefficient_conversion_15c), 2
                )

            # col. AL — Poids = V15°C × D15°C_cal / 1000
            if (self.volume_15c_recu is not None
                    and self.densite_15c_calculee is not None):
                self.poids_kg = round(
                    float(self.volume_15c_recu)
                    * float(self.densite_15c_calculee) / 1000, 2
                )

        elif self.type_mouvement == 'SORTIE':
            if (self.densite_15c_sortie is not None
                    and self.temperature_sortie is not None):
                vcf = pc.vcf_to_15c(
                    float(self.densite_15c_sortie),
                    float(self.temperature_sortie)
                )
                self.coefficient_conversion_sortie = round(vcf, 4)

            if (self.volume_ambiant_sortie is not None
                    and self.coefficient_conversion_sortie is not None):
                self.volume_15c_sortie = round(
                    float(self.volume_ambiant_sortie)
                    * float(self.coefficient_conversion_sortie), 2
                )

            if (self.volume_15c_sortie is not None
                    and self.densite_15c_sortie is not None):
                self.poids_sortie_kg = round(
                    float(self.volume_15c_sortie)
                    * float(self.densite_15c_sortie) / 1000, 2
                )

        elif self.type_mouvement == 'ACQUITTEMENT':
            # Forcer le régime douanier — un acquittement est toujours ACQUITTE
            self.regime_douanier = 'ACQUITTE'

        # CESSION : pas de calculs automatiques

    def clean(self):
        """Vérifie qu'une période OUVERTE existe pour la date du mouvement."""
        super().clean()
        if not self.date_mouvement:
            return
        from django.core.exceptions import ValidationError as _VE
        try:
            from SGDS.services.periode_comptable import periode_pour_date
            periode = periode_pour_date(self.date_mouvement)
        except Exception:
            return  # Table pas encore créée (migrations initiales)
        if periode is None:
            mois_annee = self.date_mouvement.strftime('%B %Y')
            raise _VE(
                f"Aucune période comptable n'est ouverte pour {mois_annee}. "
                "Demandez à un administrateur d'ouvrir la période avant de saisir des mouvements."
            )
        if periode.statut == 'CLOTUREE':
            raise _VE(
                f"La période {periode} est clôturée. Aucune modification n'est possible."
            )

    # ── save() override : numéro auto + calculs petroleum_calc ───
    def save(self, *args, **kwargs):
        from django.db import transaction, IntegrityError as _IntegrityError

        # Valider avant sauvegarde (sauf sur update_fields partiel)
        if not kwargs.get('update_fields'):
            self.full_clean()

        if not self.pk and not self.numero_enregistrement:
            # CRÉATION : génération du numéro + calculs dans un bloc atomique
            # pour sécuriser les race conditions sur la séquence.
            annee = self.date_mouvement.year if self.date_mouvement else None
            max_attempts = 5
            for attempt in range(max_attempts):
                try:
                    with transaction.atomic():
                        self.numero_enregistrement = self.__class__.generer_numero(
                            self.type_mouvement, annee
                        )
                        self._calculer_auto()
                        super().save(*args, **kwargs)
                        return
                except _IntegrityError:
                    if attempt == max_attempts - 1:
                        raise
                    continue
        else:
            # MODIFICATION : recalcul des champs auto, numéro inchangé
            self._calculer_auto()
            super().save(*args, **kwargs)

    # ── Propriétés utiles ──────────────────────────────────────
    @property
    def transporteur(self):
        """Marketeur du camion transporteur (None si pas de camion)."""
        return self.camion.marketeur if self.camion else None

    @property
    def immatriculation(self):
        """Immatriculation du camion (None si pas de camion)."""
        return self.camion.immatriculation if self.camion else None

    @property
    def volume_principal(self):
        """Volume principal du mouvement selon son type."""
        if self.type_mouvement == 'ENTREE':
            return self.volume_15c_recu
        elif self.type_mouvement == 'SORTIE':
            return self.volume_15c_sortie
        elif self.type_mouvement == 'CESSION':
            return self.cession_volume_15c
        elif self.type_mouvement == 'ACQUITTEMENT':
            return self.acquittement_volume_15c
        return None

    @property
    def volume_ambiant_principal(self):
        """Volume ambiant principal du mouvement selon son type."""
        if self.type_mouvement == 'ENTREE':
            return self.volume_ambiant_recu
        elif self.type_mouvement == 'SORTIE':
            return self.volume_ambiant_sortie
        elif self.type_mouvement == 'CESSION':
            return self.cession_volume_ambiant
        elif self.type_mouvement == 'ACQUITTEMENT':
            return self.acquittement_volume_ambiant
        return None

    @property
    def volume_acquitte_total(self):
        """
        Pour une ENTREE SOUS_DOUANE : volume ambiant total deja acquitte.
        Somme des acquittement_volume_ambiant de tous les ACQUITTEMENTs lies.
        Retourne None si le mouvement n'est pas une ENTREE SOUS_DOUANE.
        Utilise le cache prefetch si 'acquittements' a ete prefetche.
        """
        if not (self.type_mouvement == 'ENTREE' and self.regime_douanier == 'SOUS_DOUANE'):
            return None
        return sum(
            (acq.acquittement_volume_ambiant or Decimal('0'))
            for acq in self.acquittements.all()
        )

    @property
    def statut_acquittement(self):
        """
        Pour une ENTREE SOUS_DOUANE : statut d'acquittement douanier.
        Valeurs : 'ACQUITTE', 'PARTIEL', 'EN_ATTENTE', ou None si non applicable.
        """
        if not (self.type_mouvement == 'ENTREE' and self.regime_douanier == 'SOUS_DOUANE'):
            return None
        vol_entree = self.volume_ambiant_recu or Decimal('0')
        vol_acquitte = self.volume_acquitte_total or Decimal('0')
        if vol_entree <= 0:
            return 'EN_ATTENTE'
        if vol_acquitte >= vol_entree:
            return 'ACQUITTE'
        elif vol_acquitte > 0:
            return 'PARTIEL'
        return 'EN_ATTENTE'


# ─────────────────────────────────────────────────────────────
#  LIGNE MOUVEMENT  (multi-cuves par mouvement)
# ─────────────────────────────────────────────────────────────
class LigneMouvement(models.Model):
    """
    Détail d'un mouvement par cuve.
    Un Mouvement (entête) peut avoir N LigneMouvement (une par cuve affectée).
    Remplace progressivement Mouvement.cuve (FK simple dépréciée).
    """
    mouvement      = models.ForeignKey(
        Mouvement, on_delete=models.CASCADE,
        related_name='lignes', verbose_name="Mouvement"
    )
    cuve           = models.ForeignKey(
        'Cuve', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='lignes_mouvement',
        verbose_name="Cuve"
    )
    produit        = models.ForeignKey(
        'Produit', on_delete=models.PROTECT,
        verbose_name="Produit",
        help_text="Dénormalisé depuis mouvement.produit pour faciliter les agrégats par produit/cuve."
    )
    volume_ambiant = models.DecimalField(
        max_digits=12, decimal_places=2,
        null=True, blank=True, verbose_name="Volume ambiant (L)"
    )
    volume_15c     = models.DecimalField(
        max_digits=12, decimal_places=2,
        null=True, blank=True, verbose_name="Volume @15°C (L)"
    )
    ordre          = models.PositiveSmallIntegerField(
        default=1, verbose_name="Ordre"
    )

    class Meta:
        ordering = ['ordre']
        verbose_name = "Ligne mouvement"
        verbose_name_plural = "Lignes mouvement"

    def __str__(self):
        cuve_str = self.cuve.numero if self.cuve else "sans cuve"
        return f"{self.mouvement.numero_enregistrement} — {cuve_str} : {self.volume_ambiant} L"


# ─────────────────────────────────────────────────────────────
#  CHARGEMENT DES DONNÉES INITIALES
# ─────────────────────────────────────────────────────────────
def charger_donnees_initiales():
    """
    Initialise produits, cuves, paramètres et premier jaugeage pour SGDS SANKE.
 
    Lancement :
        python manage.py shell
        >>> from monapp.models import charger_donnees_initiales
        >>> charger_donnees_initiales()
    """
    # Produits
    super_p, _ = Produit.objects.get_or_create(
        code='SUPER',
        defaults={'nom': 'Essence Super', 'unite_mesure': 'LITRE'}
    )
    gasoil, _ = Produit.objects.get_or_create(
        code='GASOIL',
        defaults={'nom': 'Gas-oil', 'unite_mesure': 'LITRE'}
    )
 
    # Cuves : (numero, produit, HTT, capacite_totale, remplissage_maxi, V(A), V/mn)
    cuves_data = [
        ('RO3', super_p, 12981, 1500000, 1300000,  60294, 139),
        ('RO5', super_p, 12954, 1800000, 1600000,  82779, 165),
        ('RO6', super_p, 12959, 1800000, 1600000,  74753, 165),
        ('RO1', gasoil,  12942, 2000000, 1800000,  88058, 176),
        ('RO2', gasoil,  12959, 6000000, 5800000, 263875, 530),
        ('RO4', gasoil,  12946, 1500000, 1300000,  58748, 132),
    ]
 
    for numero, produit, htt, cap, rmax, va, vmn in cuves_data:
        cuve, _ = Cuve.objects.update_or_create(
            numero=numero,
            defaults={
                'designation': f'Cuve {numero}',
                'produit': produit,
                'capacite_totale': cap,
            }
        )
        ParametreJaugeageCuve.objects.update_or_create(
            cuve=cuve,
            defaults={
                'hauteur_totale_temoin': htt,
                'hauteur_min_livraison': 2000,
                'correction_creux': 4,
                'remplissage_maxi': rmax,
                'v_a': va,
                'v_mn': vmn,
                'is_pompe': False,
            }
        )
 
    # Premier jaugeage si aucun n'existe
    if not JaugeageJour.objects.exists():
        from datetime import date
        premier = JaugeageJour.objects.create(
            date_jaugeage=date.today(),
            type_jaugeage='J',
        )
        for cuve in Cuve.objects.filter(parametre_jaugeage__isnull=False):
            MesureCuve.objects.create(jaugeage=premier, cuve=cuve)
 
    print("Données initiales chargées avec succès.")
    print(f"  - {Produit.objects.count()} produits")
    print(f"  - {Cuve.objects.count()} cuves")
    print(f"  - {ParametreJaugeageCuve.objects.count()} paramètres de jaugeage")
    print(f"  - {JaugeageJour.objects.count()} jaugeage(s) en historique")
    print(f"  - {MesureCuve.objects.count()} mesures au total")


# ─────────────────────────────────────────────────────────────
#  PÉRIODE COMPTABLE (mois de gestion)
# ─────────────────────────────────────────────────────────────
class PeriodeComptable(models.Model):
    STATUT_CHOICES = [
        ('OUVERTE',   'Ouverte'),
        ('CLOTUREE',  'Clôturée'),
    ]

    mois   = models.PositiveIntegerField(verbose_name="Mois")
    annee  = models.PositiveIntegerField(verbose_name="Année")
    statut = models.CharField(
        max_length=10, choices=STATUT_CHOICES, default='OUVERTE',
        verbose_name="Statut"
    )
    date_ouverture = models.DateTimeField(blank=True, null=True, verbose_name="Date d'ouverture")
    date_cloture = models.DateTimeField(blank=True, null=True, verbose_name="Date de clôture")
    cloture_par  = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='periodes_cloturees',
        verbose_name="Clôturée par"
    )
    notes = models.TextField(blank=True, null=True, verbose_name="Notes")

    class Meta:
        verbose_name        = "Période comptable"
        verbose_name_plural = "Périodes comptables"
        ordering            = ['-annee', '-mois']
        constraints = [
            models.UniqueConstraint(fields=['mois', 'annee'], name='unique_periode_mois_annee')
        ]

    def __str__(self):
        return self.libelle

    @property
    def est_ouverte(self):
        return self.statut == 'OUVERTE'

    @property
    def libelle(self):
        import calendar
        noms = [
            '', 'Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin',
            'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre',
        ]
        return f"{noms[self.mois]} {self.annee}"

    @property
    def date_debut(self):
        from datetime import date
        return date(self.annee, self.mois, 1)

    @property
    def date_fin(self):
        import calendar
        from datetime import date
        dernier_jour = calendar.monthrange(self.annee, self.mois)[1]
        return date(self.annee, self.mois, dernier_jour)

    def periode_precedente(self):
        mois, annee = self.mois - 1, self.annee
        if mois == 0:
            mois, annee = 12, annee - 1
        return PeriodeComptable.objects.filter(mois=mois, annee=annee).first()

    def periode_suivante(self):
        mois, annee = self.mois + 1, self.annee
        if mois == 13:
            mois, annee = 1, annee + 1
        return PeriodeComptable.objects.filter(mois=mois, annee=annee).first()


# ─────────────────────────────────────────────────────────────
#  STOCK D'OUVERTURE (agrégat par produit)
# ─────────────────────────────────────────────────────────────
class StockOuverture(models.Model):
    periode      = models.ForeignKey(
        PeriodeComptable, on_delete=models.CASCADE,
        related_name='stocks_ouverture', verbose_name="Période"
    )
    produit      = models.ForeignKey(
        'Produit', on_delete=models.PROTECT, verbose_name="Produit"
    )
    volume_ambiant = models.DecimalField(
        max_digits=14, decimal_places=2, default=0,
        verbose_name="Volume ambiant (L)"
    )
    volume_15c   = models.DecimalField(
        max_digits=14, decimal_places=2, default=0,
        verbose_name="Volume @15°C (L)"
    )
    calcul_auto  = models.BooleanField(
        default=True,
        verbose_name="Calcul automatique",
        help_text="Si False, la valeur a été saisie manuellement et ne sera pas écrasée"
    )
    date_modification = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = "Stock d'ouverture"
        verbose_name_plural = "Stocks d'ouverture"
        constraints = [
            models.UniqueConstraint(fields=['periode', 'produit'], name='unique_stock_ouv_periode_produit')
        ]

    def __str__(self):
        return f"SO {self.produit.code} — {self.periode}"


# ─────────────────────────────────────────────────────────────
#  STOCK D'OUVERTURE PAR CUVE
# ─────────────────────────────────────────────────────────────
class StockOuvertureCuve(models.Model):
    periode        = models.ForeignKey(
        PeriodeComptable, on_delete=models.CASCADE,
        related_name='stocks_ouverture_cuve', verbose_name="Période"
    )
    cuve           = models.ForeignKey(
        'Cuve', on_delete=models.PROTECT, verbose_name="Cuve"
    )
    volume_ambiant = models.DecimalField(
        max_digits=14, decimal_places=2, default=0,
        verbose_name="Volume ambiant (L)"
    )
    volume_15c     = models.DecimalField(
        max_digits=14, decimal_places=2, default=0,
        verbose_name="Volume @15°C (L)"
    )
    calcul_auto    = models.BooleanField(default=True, verbose_name="Calcul automatique")
    source_mesure  = models.ForeignKey(
        'MesureCuve', on_delete=models.SET_NULL,
        null=True, blank=True, verbose_name="Mesure source"
    )
    date_modification = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = "Stock d'ouverture par cuve"
        verbose_name_plural = "Stocks d'ouverture par cuve"
        constraints = [
            models.UniqueConstraint(fields=['periode', 'cuve'], name='unique_stock_ouv_periode_cuve')
        ]

    def __str__(self):
        return f"SO {self.cuve.numero} — {self.periode}"


# ─────────────────────────────────────────────────────────────
#  PARAMÈTRES DE COULAGE (tarif passage, motif)
# ─────────────────────────────────────────────────────────────
class ParametresCoulage(models.Model):
    date_application     = models.DateField(
        unique=True, verbose_name="Date d'application"
    )
    prix_unitaire_passage = models.DecimalField(
        max_digits=10, decimal_places=4,
        verbose_name="Prix unitaire de passage (FCFA/L)"
    )
    motif_defaut         = models.CharField(
        max_length=200, default='Chargement',
        verbose_name="Motif par défaut"
    )

    class Meta:
        verbose_name        = "Paramètres de coulage"
        verbose_name_plural = "Paramètres de coulage"
        ordering            = ['-date_application']

    def __str__(self):
        return f"Paramètres coulage au {self.date_application} — {self.prix_unitaire_passage} FCFA/L"

    @classmethod
    def en_vigueur(cls, date_ref):
        """Retourne les paramètres en vigueur à la date donnée (dernier ≤ date)."""
        return cls.objects.filter(date_application__lte=date_ref).first()


# ─────────────────────────────────────────────────────────────
#  CLÔTURE COULAGE MENSUEL (snapshot)
# ─────────────────────────────────────────────────────────────
class ClotureCoulageMensuel(models.Model):
    periode               = models.OneToOneField(
        PeriodeComptable, on_delete=models.PROTECT,
        related_name='cloture_coulage', verbose_name="Période"
    )
    prix_unitaire_passage = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    motif                 = models.CharField(max_length=200, blank=True, null=True)
    notes                 = models.TextField(blank=True, null=True)
    date_cloture          = models.DateTimeField(auto_now_add=True)
    cloture_par           = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='clotures_coulage',
        verbose_name="Clôturée par"
    )

    class Meta:
        verbose_name        = "Clôture coulage mensuel"
        verbose_name_plural = "Clôtures coulage mensuel"

    def __str__(self):
        return f"Clôture coulage {self.periode}"

    @property
    def total_montant(self):
        from django.db.models import Sum
        r = self.lignes.aggregate(t=Sum('montant'))
        return r['t'] or Decimal('0')

    @property
    def total_volume_sorti(self):
        from django.db.models import Sum
        r = self.lignes.aggregate(t=Sum('volume_sorti'))
        return r['t'] or Decimal('0')


# ─────────────────────────────────────────────────────────────
#  SNAPSHOT COULAGE PAR PRODUIT (coefficient, P/G, cumuls)
# ─────────────────────────────────────────────────────────────
class ClotureCoulageProduit(models.Model):
    """
    Une ligne par produit pour la clôture coulage.
    Stocke coefficient, pertes/gains et cumuls d'entrée/sortie.
    """
    cloture      = models.ForeignKey(
        ClotureCoulageMensuel, on_delete=models.CASCADE,
        related_name='produits_coulage', verbose_name="Clôture"
    )
    produit      = models.ForeignKey(
        'Produit', on_delete=models.PROTECT, verbose_name="Produit"
    )
    coefficient  = models.DecimalField(max_digits=14, decimal_places=8, default=0)
    pertes_gains = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    cumul_entree = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    cumul_sortie = models.DecimalField(max_digits=14, decimal_places=2, default=0)

    class Meta:
        verbose_name        = "Coulage par produit"
        verbose_name_plural = "Coulage par produit"
        constraints = [
            models.UniqueConstraint(
                fields=['cloture', 'produit'], name='unique_cloture_produit'
            )
        ]

    def __str__(self):
        return f"{self.produit} — {self.cloture.periode}"


# ─────────────────────────────────────────────────────────────
#  LIGNE COULAGE PAR MARKETEUR × PRODUIT
# ─────────────────────────────────────────────────────────────
class ClotureCoulageLigne(models.Model):
    """Une ligne = 1 clôture × 1 marketeur × 1 produit."""
    cloture   = models.ForeignKey(
        ClotureCoulageMensuel, on_delete=models.CASCADE,
        related_name='lignes', verbose_name="Clôture"
    )
    marketeur = models.ForeignKey(
        'Marketeur', on_delete=models.PROTECT, verbose_name="Marketeur"
    )
    produit   = models.ForeignKey(
        'Produit', on_delete=models.PROTECT, verbose_name="Produit",
        null=True, blank=True
    )

    brut_entree  = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    coul_entree  = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    entree_nette = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    sortie       = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    base_qp_coul = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    coef_qp_coul = models.DecimalField(max_digits=14, decimal_places=8, default=0)
    qp_coul      = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    volume_sorti = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    motif        = models.CharField(max_length=200, blank=True, null=True)
    prix_unitaire= models.DecimalField(max_digits=10, decimal_places=4, default=0)
    montant      = models.DecimalField(max_digits=14, decimal_places=2, default=0)

    class Meta:
        verbose_name        = "Ligne coulage"
        verbose_name_plural = "Lignes coulage"
        constraints = [
            models.UniqueConstraint(
                fields=['cloture', 'marketeur', 'produit'],
                name='unique_cloture_ligne_marketeur_produit'
            )
        ]

    def __str__(self):
        return (
            f"{self.marketeur.sigle or self.marketeur.raison_sociale}"
            f" — {self.produit} — {self.cloture.periode}"
        )




# ─────────────────────────────────────────────────────────────
#  INVENTAIRE INITIAL MARKETEUR
# ─────────────────────────────────────────────────────────────

class InventaireInitialMarketeur(models.Model):
    """
    Stock de départ d'un marketeur pour un produit et un régime douanier donné.
    Saisi une seule fois lors du démarrage du système ou d'un changement
    de période de référence. Intégré automatiquement dans le calcul du
    REPORT de la carte de stock (comme s'il s'était passé avant toute
    saisie de mouvements).
    """

    REGIME_CHOICES = [
        ('SOUS_DOUANE', 'Sous douane'),
        ('ACQUITTE',    'Acquitté'),
    ]

    marketeur       = models.ForeignKey(
        'Marketeur', on_delete=models.CASCADE,
        related_name='inventaires_initiaux', verbose_name="Marketeur"
    )
    produit         = models.ForeignKey(
        'Produit', on_delete=models.PROTECT,
        related_name='inventaires_initiaux', verbose_name="Produit"
    )
    regime_douanier = models.CharField(
        max_length=15, choices=REGIME_CHOICES,
        verbose_name="Régime douanier"
    )
    volume_15c      = models.DecimalField(
        max_digits=14, decimal_places=2, default=0,
        validators=[MinValueValidator(0)],
        verbose_name="Volume @15°C (L)"
    )
    volume_ambiant  = models.DecimalField(
        max_digits=14, decimal_places=2, default=0,
        validators=[MinValueValidator(0)],
        verbose_name="Volume ambiant (L)"
    )
    date_inventaire = models.DateField(
        verbose_name="Date d'inventaire",
        help_text="Date de référence du stock initial (avant tout mouvement)"
    )
    cuves           = models.ManyToManyField(
        'Cuve',
        blank=True,
        related_name='inventaires_initiaux',
        verbose_name="Cuves associées",
        help_text="Cuves dans lesquelles ce stock est physiquement déposé (optionnel)"
    )
    saisi_par       = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='inventaires_initiaux_saisis', verbose_name="Saisi par"
    )
    notes           = models.TextField(
        blank=True, verbose_name="Notes / observations"
    )
    date_creation   = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = "Inventaire initial marketeur"
        verbose_name_plural = "Inventaires initiaux marketeurs"
        constraints = [
            models.UniqueConstraint(
                fields=['marketeur', 'produit', 'regime_douanier'],
                name='unique_inventaire_initial_mktr_prod_regime'
            )
        ]
        ordering = ['marketeur__raison_sociale', 'produit__nom', 'regime_douanier']

    def __str__(self):
        return (
            f"Inventaire {self.marketeur} — {self.produit.code} "
            f"({self.get_regime_douanier_display()}) au {self.date_inventaire}"
        )

# ─────────────────────────────────────────────────────────────
#  SOCIÉTÉ / DÉPÔT (fiche singleton — 1 seule ligne)
# ─────────────────────────────────────────────────────────────
class Societe(models.Model):
    """
    Fiche officielle du dépôt / de la société exploitante.
    SINGLETON : une seule ligne autorisée.
    Utilisée dans les en-têtes des états imprimés et exports Excel.
    """

    # ── Identification ─────────────────────────────────────────
    raison_sociale        = models.CharField(max_length=200, verbose_name="Raison sociale")
    sigle                 = models.CharField(max_length=50, blank=True, null=True, verbose_name="Sigle / Abréviation")
    forme_juridique       = models.CharField(max_length=10, blank=True, null=True, verbose_name="Forme juridique")
    numero_contribuable   = models.CharField(max_length=100, blank=True, null=True, verbose_name="N° Contribuable / NIF")
    numero_ifu            = models.CharField(max_length=100, blank=True, null=True, verbose_name="N° IFU")
    capital_social        = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True, verbose_name="Capital social (FCFA)")

    # ── Logo & visuel ──────────────────────────────────────────
    logo                  = models.ImageField(upload_to='societe/', blank=True, null=True, verbose_name="Logo")
    tampon                = models.ImageField(upload_to='societe/', blank=True, null=True, verbose_name="Tampon / Cachet")
    couleur_principale    = models.CharField(max_length=7, default='#1e3a5f', blank=True, verbose_name="Couleur principale (hex)")
    pied_de_page          = models.TextField(blank=True, null=True, verbose_name="Texte pied de page des états")

    # ── Coordonnées ────────────────────────────────────────────
    adresse               = models.TextField(blank=True, null=True, verbose_name="Adresse complète")
    ville                 = models.CharField(max_length=100, blank=True, null=True, verbose_name="Ville")
    pays                  = models.CharField(max_length=100, default='Mali', verbose_name="Pays")
    boite_postale         = models.CharField(max_length=50, blank=True, null=True, verbose_name="Boîte postale")
    telephone             = models.CharField(max_length=20, blank=True, null=True, verbose_name="Téléphone principal")
    telephone2            = models.CharField(max_length=20, blank=True, null=True, verbose_name="Téléphone secondaire")
    email                 = models.EmailField(blank=True, null=True, verbose_name="Email")
    site_web              = models.URLField(blank=True, null=True, verbose_name="Site web")

    # ── Informations dépôt ─────────────────────────────────────
    nom_depot             = models.CharField(max_length=200, default='SGDS SANKE', verbose_name="Nom du dépôt")
    type_depot            = models.CharField(max_length=100, default='Dépôt de droit', verbose_name="Type de dépôt")
    numero_agrement       = models.CharField(max_length=100, blank=True, null=True, verbose_name="N° Agrément")
    autorite_tutelle      = models.CharField(max_length=200, blank=True, null=True, verbose_name="Autorité de tutelle")
    date_creation         = models.DateField(blank=True, null=True, verbose_name="Date de création")

    # ── Meta ───────────────────────────────────────────────────
    date_modification     = models.DateTimeField(auto_now=True, verbose_name="Dernière modification")

    class Meta:
        verbose_name        = "Société / Dépôt"
        verbose_name_plural = "Société / Dépôt"

    def __str__(self):
        return self.raison_sociale or self.nom_depot

    @classmethod
    def get_instance(cls):
        """
        Retourne la fiche société (crée une instance vide si absente).
        Garantit le singleton.
        """
        obj, _ = cls.objects.get_or_create(
            pk=1,
            defaults={
                'raison_sociale': 'SGDS SANKE',
                'nom_depot':      'SGDS SANKE',
                'ville':          'Bamako',
                'pays':           'Mali',
            }
        )
        return obj

    def save(self, *args, **kwargs):
        """Force pk=1 — singleton strict."""
        self.pk = 1
        super().save(*args, **kwargs)


# ─────────────────────────────────────────────────────────────
#  NOTIFICATION MARKETEUR
# ─────────────────────────────────────────────────────────────

class Notification(models.Model):
    TYPE_CHOICES = [
        ('ENTREE',        'Entrée'),
        ('SORTIE',        'Sortie'),
        ('CESSION_EMISE', 'Cession émise'),
        ('CESSION_RECUE', 'Cession reçue'),
        ('ACQUITTEMENT',  'Acquittement'),
    ]
    marketeur     = models.ForeignKey('Marketeur', on_delete=models.CASCADE, related_name='notifications')
    type_notif    = models.CharField(max_length=20, choices=TYPE_CHOICES)
    titre         = models.CharField(max_length=200)
    message       = models.TextField()
    mouvement     = models.ForeignKey('Mouvement', on_delete=models.CASCADE,
                                      related_name='notifications', null=True, blank=True)
    lue           = models.BooleanField(default=False)
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date_creation']
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'

    def __str__(self):
        return f"[{self.type_notif}] {self.marketeur} — {self.titre}"
