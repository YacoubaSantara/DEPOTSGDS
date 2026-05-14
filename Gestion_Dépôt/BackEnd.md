# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# ⚠️ Toujours utiliser le Python du venv, pas le Python système
# Navigate to Django project root first
cd "Gestion_Dépôt"

# Run development server
"E:/Projet Site/SANKE/SGDS/env/Scripts/python.exe" manage.py runserver

# Apply migrations
"E:/Projet Site/SANKE/SGDS/env/Scripts/python.exe" manage.py migrate

# Create new migrations after model changes
"E:/Projet Site/SANKE/SGDS/env/Scripts/python.exe" manage.py makemigrations

# Open Django shell
"E:/Projet Site/SANKE/SGDS/env/Scripts/python.exe" manage.py shell

# Run tests
"E:/Projet Site/SANKE/SGDS/env/Scripts/python.exe" manage.py test SGDS

# Collect static files
"E:/Projet Site/SANKE/SGDS/env/Scripts/python.exe" manage.py collectstatic

# Create superuser
"E:/Projet Site/SANKE/SGDS/env/Scripts/python.exe" manage.py createsuperuser

# Activer l'environnement virtuel (PowerShell)
& "E:/Projet Site/SANKE/SGDS/env/Scripts/Activate.ps1"
```

## Architecture Overview

**Django 6.0.3** project for warehouse/depot management ("Système de Gestion de Dépôt SANKE"). The working Django project root is `Gestion_Dépôt/`.

### Project Layout

```
Gestion_Dépôt/
├── Gestion_Dépôt/        # Project config (settings.py, urls.py)
├── accounts/             # App authentification & utilisateurs
│   ├── models.py         # UtilisateurSGDS (AbstractUser custom)
│   ├── views.py          # Vues auth uniquement (connexion, deconnexion) — CRUD utilisateurs supprimé
│   ├── forms.py          # Formulaires utilisateurs (création, modification, profil)
│   ├── admin.py          # UtilisateurSGDSAdmin (Role/RolePermission supprimés — n'existaient pas)
│   ├── urls.py           # Routes /auth/ uniquement (/utilisateurs/ géré par SGDS.users)
│   └── migrations/
│       └── 0001_initial.py
├── SGDS/                 # App métier principale (dépôt, flotte, jaugeage)
│   ├── models.py         # Tous les modèles métier (incl. PeriodeComptable, ClotureCoulage*, Produit.prix_passage)
│   ├── petroleum_calc.py # Calculs API MPMS (density_at_15c, vcf_to_15c) — FIGÉ, validé
│   ├── views/            # Package vues (prend le dessus sur views.py)
│   │   ├── __init__.py   # Vues CRUD + imports centralisés de coulage.py et periode.py
│   │   ├── coulage.py    # CBVs coulage + suivi évolution + frais passage + exports Excel
│   │   └── periode.py    # CBVs ListePeriodesView + OuvrirPeriodeView
│   ├── views.py          # Fichier hérité — shadowed par le package views/, ignoré par Python
│   ├── forms.py          # Formulaires métier (incl. ProduitForm.prix_passage)
│   ├── admin.py          # Admin pour tous les modèles (incl. ClotureCoulageProduitInline)
│   ├── urls.py           # Routes métier + périodes + coulage + suivi + frais passage
│   ├── apps.py           # SgdsConfig.ready() charge signals.py
│   ├── signals.py        # post_save/post_delete MesureCuve+JaugeageJour → recalcul stocks
│   ├── users/            # Sous-app RBAC + Audit Trail + SSO
│   │   ├── __init__.py
│   │   ├── apps.py           # UsersConfig.ready() charge signals
│   │   ├── models.py         # Role(TextChoices) + UserProfile (OneToOne→AUTH_USER_MODEL) + AuditLog
│   │   ├── managers.py       # creer_utilisateur() — crée User + UserProfile atomiquement
│   │   ├── middleware.py     # AuditContextMiddleware + get_current_user() + get_current_request()
│   │   ├── sync_permissionsignals.py        # Audit trail complet (CREATE/UPDATE/DELETE + login/logout)
│   │   ├── permissions.py    # Helpers fonctionnels : is_superadmin, can_write, can_close_period…
│   │   ├── decorators.py     # @role_required + CBV Mixins (SuperAdminRequired, CanWriteMixin…)
│   │   ├── adapters.py       # SGDSSocialAccountAdapter — refuse emails non pré-enregistrés (SSO)
│   │   ├── views.py          # 6 CBVs : Liste, Detail, Creer, Modifier, MonProfil, AuditLog
│   │   ├── urls.py           # 6 routes : /utilisateurs/ /mon-profil/ /audit/
│   │   ├── admin.py          # UserProfileAdmin + AuditLogAdmin (immuable)
│   │   ├── migrations/
│   │   │   └── __init__.py
│   │   ├── templatetags/
│   │   │   └── user_tags.py  # role_badge (inclusion_tag) + action_icon + has_role (simple_tag)
│   │   └── tests/
│   │       ├── __init__.py
│   │       ├── test_permissions.py   # 11 tests droits par rôle + vues HTTP
│   │       ├── test_audit.py         # 8 tests CREATE/UPDATE/DELETE/login/logout loggés
│   │       └── test_sso.py           # 3 tests adapter SSO (email inconnu/existant/vide)
│   ├── services/         # Services métier (pas d'__init__.py requis)
│   │   ├── periode_comptable.py   # Cycle vie PeriodeComptable (ouvrir, cloturer, vérifier)
│   │   ├── recalcul_stock.py      # Recalcul Cuve.niveau_actuel + Produit.stock_actuel
│   │   ├── ecart_jaugeages.py     # Calcul écart physique/comptable entre 2 jaugeages
│   │   ├── coulage_repartition.py # calculer_repartition_coulage() + figer_cloture_coulage()
│   │   ├── suivi_evolution.py     # calculer_suivi_evolution(periode, produit) → tableau journalier par cuve
│   │   ├── frais_passage.py       # calculer_frais_passage(periode) → facturation par mode règlement
│   │   └── export_excel.py        # exporter_coulage_xlsx / exporter_suivi_xlsx / exporter_frais_passage_xlsx
│   ├── templatetags/     # Template tags custom
│   │   ├── __init__.py
│   │   ├── jaugeage_extras.py   # Filtres fmt_vol, fmt_density, fmt_vcf, fmt_temp, fmt_mm, or_tiret ; tag jaugeage_total_v15
│   │   ├── periode_tags.py      # Tags bandeau_periode + periode_indicateur
│   │   └── coulage_tags.py      # Filtres lookup(dict, key) + lookup_id(dict, obj) pour accès dict en template
│   ├── tests/
│   │   ├── __init__.py
│   │   └── test_workflow_periode.py  # 21 tests : workflow période, recalcul stock, écart jaugeages
│   ├── tests_coulage.py  # Tests : TestCoefficients, TestFigerCloture, TestVerrouillage, TestSuiviEvolution (4), TestFraisPassage (4)
│   └── migrations/
│       ├── 0001_initial.py                                          # Marketeur, Camion, Chauffeur, Famille, Produit, Cuve
│       ├── 0002_jaugeagejour_parametrejaugeagecuve_mesurecuve.py    # ParametreJaugeageCuve, JaugeageJour, MesureCuve
│       ├── 0003_auto_...                                            # (éventuelles migrations intermédiaires)
│       ├── 0005_mouvement.py                                        # Modèle Mouvement (création initiale)
│       ├── 0006_numero_enregistrement_auto.py                       # ALTER FIELD — editable=False sur numero_enregistrement
│       ├── 0007_attribuer_numeros_mouvements.py                     # Migration données — numeros conformes aux enregistrements existants
│       ├── 0008_suppr_acquittement_montant_droits.py                # REMOVE FIELD acquittement_montant_droits
│       ├── 0009_ajout_ecart_densite_15c.py                         # ADD FIELD ecart_densite_15c
│       └── 0014_produit_prix_passage.py                             # ADD FIELD prix_passage (DecimalField 10,4 nullable) sur Produit
├── templates/            # Global templates
│   ├── base.html         # Base layout (sidebar + topbar + footer utilisateur)
│   ├── admin/
│   │   └── jaugeage_change_list.html  # Template admin custom (bouton "Créer nouveau jaugeage")
│   ├── Auth/             # Templates d'authentification
│   │   ├── login.html           # Page de connexion (standalone, no base.html)
│   │   └── logout_confirm.html  # Confirmation déconnexion
│   ├── users/            # Templates gestion utilisateurs RBAC (minuscule)
│   │   ├── liste.html              # Liste utilisateurs + stat strip 5 rôles + filtres
│   │   ├── detail.html             # Détail utilisateur + 30 dernières actions audit
│   │   ├── creer.html              # Création : grille rôle cliquable + barre force mdp JS
│   │   ├── modifier.html           # Édition : toggles actif, grille rôle pré-sélectionnée
│   │   ├── mon_profil.html         # Profil courant : upload photo + changement mdp dépliable
│   │   ├── audit_log.html          # Journal d'audit : lignes expandables + diff avant/après
│   │   └── partials/
│   │       └── role_badge.html     # Badge rôle RBAC inline (utilisé par templatetag role_badge)
│   ├── Marketeur/        # Marketeur CRUD templates
│   ├── Camion/           # Camion citerne CRUD templates
│   ├── Chauffeur/        # Chauffeur CRUD templates
│   ├── Famille/          # Famille de produits CRUD templates
│   ├── Produit/          # Produit CRUD templates
│   ├── Cuve/             # Cuve de stockage CRUD templates
│   ├── ParametreJaugeage/  # Paramètres jaugeage CRUD templates
│   ├── Jaugeage/         # Module jaugeage — interfaces RJJ complètes
│   │   ├── jaugeage_list.html         # Liste avec colonne Vol.@15°C, lignes cliquables, bouton rapport
│   │   ├── jaugeage_form.html         # Création / édition en-tête jaugeage
│   │   ├── jaugeage_saisie.html       # Saisie (layout colonne-par-cuve, groupé par produit, calculs JS live)
│   │   ├── jaugeage_detail.html       # Vue lecture + boutons hero lisibles + tfoot sous-totaux volumes
│   │   ├── jaugeage_rapport.html      # Rapport A4 paysage impression/PDF (standalone, @media print)
│   │   └── jaugeage_confirm_delete.html
│   ├── mouvements/       # Module mouvements pétroliers
│   │   ├── liste.html                 # Liste filtrée + N° enregistrement monospace + badges types/régimes
│   │   ├── detail.html                # Fiche lecture seule — hero navy, sections par type, calculs affichés ; dark mode : .dcheader-* classes
│   │   ├── saisie.html                # Saisie unifiée (création + édition) — 4 types, calculs auto, JS conditionnel, {% localize off %} ; dark mode : .fcheader-* classes
│   │   └── confirmer_suppression.html # Confirmation suppression avec résumé mouvement
│   ├── periode/          # Module périodes comptables
│   │   ├── liste.html                 # Tableau périodes + bouton ouvrir dynamique
│   │   └── ouvrir_confirm.html        # Confirmation ouverture + sélecteur première période
│   ├── coulage/          # Module coulage mensuel
│   │   ├── liste_periodes.html        # Liste périodes avec statut coulage
│   │   └── repartition.html           # Tableau dynamique colonnes/produits + KPI + modal clôture (display:none)
│   └── includes/         # Composants réutilisables
│       ├── bandeau_periode.html       # Alerte rouge pleine largeur si pas de période ouverte
│       └── periode_indicateur.html    # Badge dropdown topbar (vert=ouvert, rouge=absent)
├── media/                # Uploaded files (logos, photos, documents)
└── manage.py
```

### Models

#### App `accounts`

##### UtilisateurSGDS *(custom AbstractUser — AUTH_USER_MODEL)*
Modèle utilisateur personnalisé héritant de `AbstractUser`. Défini dans `accounts/models.py`.

- Champs hérités : `username`, `password`, `first_name`, `last_name`, `email`, `is_staff`, `is_active`, `is_superuser`, `date_joined`, `last_login`
- **Champs supplémentaires** :
  - `role` — CharField(choices) : `ADMIN` / `OPERATEUR` / `MARKETEUR` (défaut: `OPERATEUR`)
  - `telephone` — CharField nullable
  - `photo` — ImageField(`users/photos/`), nullable
  - `marketeur` — OneToOneField(`'SGDS.Marketeur'`, nullable, `related_name='compte_utilisateur'`) — FK cross-app vers SGDS
- **Properties** :
  - `is_admin_role` → `True` si `role == 'ADMIN'` ou `is_superuser`
  - `is_marketeur_role` → `True` si `role == 'MARKETEUR'`
  - `initiales` → ex. `"JD"` (first_name[0] + last_name[0], ou username[:2])
  - `nom_complet` → `get_full_name()` ou `username`
- **Migration** : `accounts/migrations/0001_initial.py`

---

#### App `SGDS`

##### Marketeur
Représente une société de distribution/marketing.
- Identification : raison_sociale (unique), sigle, forme_juridique (SARL/SA/SAS/SNC/EI/EURL/GIE/COOP/AUTRE), RCCM, NIF, IFU, capital_social, logo (ImageField)
- Coordonnées : adresse, quartier, ville, pays (défaut: Mali), BP, téléphones, email, site_web
- Représentant légal : nom, prénom, fonction, téléphone, email
- Banque : banque, numero_compte, code_swift
- Statut : ACTIF / INACTIF / SUSPENDU / BLACKLIST (défaut: ACTIF)

##### Camion (citerne)
Représente un camion citerne du parc.
- Identification : immatriculation (unique), marque, modele, annee_fabrication, couleur, N° châssis, N° moteur
- Citerne : capacite_totale (litres), nombre_compartiments, type_produit (Carburant/HUILE/MIXTE/AUTRE)
- Documents : date_mise_en_circulation, carte_grise (FileField)
- Assurance : compagnie_assurance, numero_police_assurance, date_expiration_assurance
- Technique : date_derniere_revision, date_prochaine_revision, kilometrage
- Lien : marketeur (FK → Marketeur, nullable, SET_NULL)
- Statut : EN_SERVICE / HORS_SERVICE / EN_MAINTENANCE / RETIRE (défaut: EN_SERVICE)

##### Chauffeur
Représente un chauffeur de camion citerne.
- Identité : nom, prenom, date_naissance, lieu_naissance, nationalite (défaut: Malien(ne)), photo (ImageField)
- Contact : telephone, telephone2, email, adresse
- Permis : numero_permis (unique), categorie_permis (B/C/D/CE/C1E/AUTRE), date_obtention_permis, date_expiration_permis
- Professionnel : numero_employe (**auto-généré**, format `EMP-YYYY-NNN`, incrémenté à chaque création, champ readonly dans le formulaire), date_embauche
- Liens : marketeur (FK → Marketeur, nullable), camion (FK → Camion, nullable) — les deux optionnels (SET_NULL)
- Statut : ACTIF / INACTIF / SUSPENDU (défaut: ACTIF)
- Classmethod : `Chauffeur.get_next_numero()` — retourne le prochain numéro disponible pour l'année en cours

##### Famille
Représente une famille / catégorie de produits pétroliers.
- nom (unique), code (unique, court ex: HYD)
- description, couleur (hex parmi 8 choix prédéfinis, pour identification visuelle)
- Statut : ACTIF / INACTIF (défaut: ACTIF)
- Property : `nb_produits` — nombre de produits rattachés

##### Produit
Représente un produit stocké dans le dépôt.
- Identification : nom (unique), code (unique, ex: GSL-50)
- famille (FK → Famille, PROTECT — impossible de supprimer une famille ayant des produits)
- description, unite_mesure (LITRE/M3/KG/TONNE/BARIL, défaut: LITRE)
- prix_unitaire (FCFA, optionnel), seuil_alerte (stock minimum, optionnel)
- **`prix_passage`** — DecimalField(max_digits=10, decimal_places=4, nullable) — Frais de passage spécifique à ce produit (FCFA/L). Si `null`, le tarif global de `ParametresCoulage` est appliqué. Permet d'anticiper des tarifs différenciés par produit.
- **`stock_actuel`** — DecimalField(max_digits=14, decimal_places=2, défaut: 0) — Stock total en litres, mis à jour automatiquement après chaque signal `MesureCuve`/`LigneMouvement`.
- **`date_maj_stock`** — DateTimeField(nullable) — Horodatage de la dernière mise à jour automatique du stock.
- Statut : ACTIF / INACTIF / DISCONTINUE (défaut: ACTIF)
- Property : `nb_cuves` — nombre de cuves stockant ce produit
- Classmethod : `Produit.mettre_a_jour_stocks(jaugeage)` — met à jour `stock_actuel` de chaque produit à partir des mesures du jaugeage donné (`volume_ambiant_depot`). Appelé après validation d'un jaugeage.

##### Cuve
Représente un réservoir/cuve de stockage dans le dépôt.
- Identification : numero (unique, ex: CUV-001), designation
- produit (FK → Produit, nullable, SET_NULL — une cuve peut être vide/non affectée)
- Capacité : capacite_totale (litres), niveau_actuel (litres, défaut: 0)
- Caractéristiques : type_cuve (AERIENNE/SOUTERRAINE/SEMI_ENTERREE), materiau (ACIER/INOX/FIBRE_VERRE/BETON/AUTRE)
- localisation (emplacement physique dans le dépôt)
- Dates : date_installation, date_derniere_inspection, date_prochaine_inspection
- Statut : ACTIVE / INACTIVE / EN_MAINTENANCE / HORS_SERVICE (défaut: ACTIVE)
- Properties : `taux_remplissage` (%), `disponible` (litres restants)

##### ParametreJaugeageCuve *(nouveau)*
Paramètres métrologiques d'une cuve, mis à jour uniquement lors d'un re-jaugeage officiel.
- **Relation** : OneToOneField → Cuve (`related_name='parametre_jaugeage'`, CASCADE)
- **Caractéristiques physiques** :
  - `hauteur_totale_temoin` — HTT en mm (ex: 12981)
  - `hauteur_min_livraison` — Hml en mm (défaut: 2000)
  - `correction_creux` — correction systématique du creux mesuré en mm (défaut: 4)
  - `remplissage_maxi` — volume maximum autorisé en exploitation (litres)
- **Certificat de jaugeage officiel** :
  - `v_a` — V(A) volume certificat à la hauteur décimale (litres)
  - `v_mn` — V/mn volume par millimètre (litres/mm)
  - `reference_certificat`, `date_certificat`, `organisme_certificateur`, `date_prochain_jaugeage`
- `is_pompe` — BooleanField (True pour cuves P GO, P SP — index pompe)
- `notes`, `date_creation`, `date_modification`

##### JaugeageJour *(nouveau)*
En-tête d'un jaugeage journalier. Plusieurs jaugeages par jour autorisés.
- `date_jaugeage`, `type_jaugeage` (AVR/APR/J), `heure_jaugeage`
- `depot` (défaut: 'SGDS SANKE'), `type_depot`, `temperature_reference` (défaut: 15.0°C)
- `operateur`, `notes`
- **Workflow de validation** :
  - `est_valide` — BooleanField (défaut: False) — indique si le jaugeage a été officiellement validé
  - `date_validation` — DateTimeField(nullable) — horodatage de la validation
  - `valide_par` — FK → `settings.AUTH_USER_MODEL` (nullable, SET_NULL, `related_name='jaugeages_valides'`) — utilisateur ayant validé
- **Contrainte unique** : `(date_jaugeage, type_jaugeage, heure_jaugeage)`
- **Ordering** : `-date_jaugeage, -heure_jaugeage, -date_creation`
- **Classmethod** : `JaugeageJour.dernier()` — retourne le dernier jaugeage
- **Classmethod** : `JaugeageJour.creer_nouveau_jaugeage(date, type, heure, operateur)` — crée un jaugeage en pré-remplissant les `MesureCuve` depuis le jaugeage précédent. Si aucun précédent, crée des mesures vides pour toutes les cuves ayant un `parametre_jaugeage`.

##### MesureCuve *(nouveau)*
Mesures saisies pour une cuve lors d'un jaugeage. Une ligne = 1 cuve × 1 jaugeage.
- **Relations** : `jaugeage` (FK → JaugeageJour, CASCADE, `related_name='mesures'`), `cuve` (FK → Cuve, CASCADE, `related_name='mesures'`)
- **Contrainte unique** : `(jaugeage, cuve)`
- **Saisies — Hauteur** : `creux_mesure` (mm, nullable)
- **`v_a_saisi`** — DecimalField(max_digits=12, decimal_places=2, nullable) — Volume V(A) lu dans le cahier de jaugeage pour la hauteur décimale du jour. Permet à l'opérateur de saisir manuellement le V(A) plutôt qu'utiliser celui du paramètre de cuve. **Prioritaire sur `ParametreJaugeageCuve.v_a`** dans le calcul de `volume_ambiant_bac`.
- **Saisies — Températures** : `t1`, `t2`, `t3` (prises sur le bac), `temperature_obs` (°C sur densité)
- **Saisies — Densité** : `densite_moyenne`, `densite_15c`, `facteur_vcf`
- **Saisies — Volumes additionnels** : `volume_additionnel`, `volume_tuyauterie`, `volume_eau` (litres, défaut: 0)
- **Properties calculées** (formules CONV_ADAMA / RJJ) :

| Property | Formule | Description |
|----------|---------|-------------|
| `creux_corrige` | `creux_mesure - correction_creux` | CONV_ADAMA C8 |
| `hauteur_produit` | `HTT - creux_corrige` | CONV_ADAMA C40 |
| `hauteur_decimal` | `hauteur_produit arrondi dizaine inférieure` | CONV_ADAMA C41 |
| `surplus` | `hauteur_produit % 10` | CONV_ADAMA C43 |
| `volume_ambiant_bac` | `(v_a_saisi ?? V(A)) + V/mn × surplus` — priorité à `v_a_saisi` si renseigné | CONV_ADAMA C47 |
| `temperature_moyenne` | `(t1 + t2 + t3) / 3` | CONV_ADAMA C55 |
| `volume_physique` | `vol_ambiant_bac + vol_tuyauterie - vol_eau` | RJJ E28 |
| `volume_ambiant_depot` | `vol_ambiant_bac + vol_additionnel` | RJJ E31 |
| `volume_standard_15c` | `vol_ambiant_depot × Vcf` | RJJ E41 |
| `volume_disponible` | `remplissage_maxi - vol_ambiant_depot` | RJJ J7 |

---

##### Mouvement *(nouveau)*
Enregistre les mouvements pétroliers du dépôt : entrées, sorties, cessions inter-marketeurs et acquittements douaniers.

**Champs communs à tous les types :**
- `numero_enregistrement` — CharField unique, `editable=False`, auto-généré à la création. Format : `ENT-2026-0001` (préfixe par type + année + séquence à 4 chiffres zero-padded). Jamais régénéré après création.
- `type_mouvement` — CharField(choices) : `ENTREE` / `SORTIE` / `CESSION` / `ACQUITTEMENT`
- `regime_douanier` — CharField(choices) : `ACQUITTE` / `SOUS_DOUANE`. ACQUITTEMENT force toujours `ACQUITTE`.
- `date_mouvement` — DateField (date du mouvement physique)
- `marketeur` — FK → Marketeur (PROTECT)
- `produit` — FK → Produit (PROTECT)
- `cuve` — FK → Cuve (nullable, SET_NULL)
- `camion` — FK → Camion (nullable, SET_NULL)
- `chauffeur` — FK → Chauffeur (nullable, SET_NULL)
- `collaborateur` — CharField(max_length=150, nullable) — nom du saisisseur, **auto-rempli** depuis `request.user.get_full_name() or request.user.username` à la création (non modifiable via formulaire)
- `notes`, `date_saisie` (auto_now_add), `date_modification` (auto_now)

**Champs ENTREE (provenance & BL) :**
- `provenance`, `bl_expediteur`, `bl_client`, `date_chargement`, `date_dechargement`
- `volume_ambiant_expediteur`, `volume_15c_expediteur` (volumes BL expéditeur)
- `densite_15c_expediteur`, `temperature_chargement`
- `volume_ambiant_recu`, `temperature_reception`, `temperature_labo`, `densite_observee_labo`

**Champs ENTREE calculés automatiquement (via `save()` + petroleum_calc.py) :**

| Champ | Formule | Colonne Excel |
|-------|---------|---------------|
| `densite_15c_calculee` | `density_at_15c(densite_observee_labo, temperature_labo)` | — |
| `ecart_densite_15c` | `(densite_15c_calculee − densite_15c_expediteur) / 1000` | AH |
| `coefficient_conversion_15c` | `vcf_to_15c(densite_15c_calculee, temperature_reception)` | — |
| `volume_15c_recu` | `volume_ambiant_recu × coefficient_conversion_15c` | — |
| `perte_gain_reception` | `volume_ambiant_recu − volume_ambiant_expediteur` | — |
| `perte_gain_15c` | `volume_15c_recu − volume_15c_expediteur` | — |
| `poids_kg` | `volume_15c_recu × densite_15c_calculee / 1000` | — |

> `ecart_densite_15c` — alerte visuelle si `|écart| > 0.001` (rouge + ⚠ dans le template).

**Champs SORTIE :**
- `reference_client_externe`, `destination`, `code_destination`
- `date_permis`, `numero_permis_sortie`, `numero_s`, `numero_c`, `mode_reglement`
- `volume_ambiant_sortie`, `densite_15c_sortie`, `temperature_sortie`
- Calculés : `coefficient_conversion_sortie`, `volume_15c_sortie`, `poids_sortie_kg`

**Champs CESSION :**
- `cession_marketeur_destinataire` (FK → Marketeur), `cession_volume_ambiant`, `cession_volume_15c`, `cession_motif`

**Champs ACQUITTEMENT :**
- `acquittement_volume_ambiant`, `acquittement_volume_15c`
- `acquittement_reference_declaration`, `acquittement_date_declaration`

**Génération du numéro d'enregistrement :**
- Classmethod `generer_numero(cls, type_mouvement, annee)` — ordonnancement lexicographique sur séquence paddée, cherche le MAX des numéros existants pour type+année.
- `save()` override — si `not self.pk and not self.numero_enregistrement` : boucle `transaction.atomic()` + retry sur `IntegrityError` (max 5 tentatives) pour sécurité race condition.
- Préfixes : `ENTREE`→`ENT`, `SORTIE`→`SOR`, `CESSION`→`CES`, `ACQUITTEMENT`→`ACQ`.

**Property :**
- `volume_principal` — retourne le volume principal selon le type (utile pour l'admin et l'affichage liste).

---

##### LigneMouvement *(nouveau)*
Détail d'un mouvement par cuve. Un `Mouvement` (en-tête) peut avoir N `LigneMouvement` (une par cuve affectée). Remplace progressivement `Mouvement.cuve` (FK simple dépréciée).

- `mouvement` — FK → Mouvement (CASCADE, `related_name='lignes'`)
- `cuve` — FK → Cuve (SET_NULL, nullable, `related_name='lignes_mouvement'`)
- `produit` — FK → Produit (PROTECT) — **champ dénormalisé** depuis `mouvement.produit` pour faciliter les agrégats par produit/cuve. Toujours synchronisé via `LigneMouvement.objects.filter(mouvement=m).update(produit=m.produit)` après modification.
- `volume_ambiant` — DecimalField(max_digits=12, decimal_places=2, nullable) — Volume ambiant (L)
- `volume_15c` — DecimalField(max_digits=12, decimal_places=2, nullable) — Volume @15°C (L)
- `ordre` — PositiveSmallIntegerField (défaut: 1) — ordre d'affichage des lignes
- **Ordering** : `['ordre']`
- **Migration** : `0015_lignemouvement.py` + `0016_data_migration_lignes_mouvement.py` (conversion des `Mouvement.cuve` existants)

> `LigneMouvement` est le nouveau modèle multi-cuves. Les signaux `on_ligne_mouvement_changed` (post_save + post_delete) déclenchent le recalcul des stocks à chaque modification d'une ligne.

---

##### StockOuverture *(nouveau)*
Agrégat du stock par produit à l'ouverture d'une période comptable.

- `periode` — FK → PeriodeComptable (CASCADE, `related_name='stocks_ouverture'`)
- `produit` — FK → Produit (PROTECT)
- `volume_ambiant` — DecimalField(max_digits=14, decimal_places=2, défaut: 0)
- `volume_15c` — DecimalField(max_digits=14, decimal_places=2, défaut: 0)
- `calcul_auto` — BooleanField (défaut: True) — si False, valeur saisie manuellement, ne sera pas écrasée
- `date_modification` — DateTimeField(auto_now)
- **Contrainte unique** : `(periode, produit)`

##### StockOuvertureCuve *(nouveau)*
Stock d'ouverture par cuve (granularité plus fine que `StockOuverture`).

- `periode` — FK → PeriodeComptable (CASCADE, `related_name='stocks_ouverture_cuve'`)
- `cuve` — FK → Cuve (PROTECT)
- `volume_ambiant` — DecimalField(max_digits=14, decimal_places=2, défaut: 0)
- `volume_15c` — DecimalField(max_digits=14, decimal_places=2, défaut: 0)
- `calcul_auto` — BooleanField (défaut: True)
- `source_mesure` — FK → MesureCuve (SET_NULL, nullable) — référence à la mesure de jaugeage ayant servi de base
- `date_modification` — DateTimeField(auto_now)
- **Contrainte unique** : `(periode, cuve)`

### Authentication & Sécurité

#### Configuration (`settings.py`)
```python
AUTH_USER_MODEL       = 'accounts.UtilisateurSGDS'   # ← app accounts (plus SGDS)
LOGIN_URL             = '/auth/connexion/'
LOGIN_REDIRECT_URL    = '/chauffeurs/'
LOGOUT_REDIRECT_URL   = '/auth/connexion/'
SESSION_COOKIE_AGE    = 28800   # 8 heures
SESSION_EXPIRE_AT_BROWSER_CLOSE = False

INSTALLED_APPS = [
    ...
    'django.contrib.sites',           # requis par allauth (SITE_ID = 1)
    'accounts',                        # ← avant SGDS
    'SGDS',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
    'allauth.socialaccount.providers.microsoft',
    'simple_history',
    'SGDS.users',                      # sous-app RBAC + Audit + SSO
]

MIDDLEWARE = [
    ...
    'allauth.account.middleware.AccountMiddleware',
    'simple_history.middleware.HistoryRequestMiddleware',
    'SGDS.users.middleware.AuditContextMiddleware',
]

# SSO Google + Microsoft
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]
SITE_ID = 1
SOCIALACCOUNT_ADAPTER = 'SGDS.users.adapters.SGDSSocialAccountAdapter'
SOCIALACCOUNT_AUTO_SIGNUP = False   # refuse emails non pré-enregistrés
```

#### Rôles legacy (`UtilisateurSGDS.role`)

| Rôle | Accès |
|------|-------|
| `ADMIN` | Accès total — gère les utilisateurs, toutes les données et configurations |
| `OPERATEUR` | Accès complet aux données (CRUD), sauf la gestion des comptes utilisateurs |
| `MARKETEUR` | Lecture seule — consulte uniquement ses propres données liées |

- Le rôle `ADMIN` s'applique aussi si `is_superuser == True` (propriété `is_admin_role`).
- Toutes les vues write des MARKETEUR sont bloquées par `_deny_marketeur()`.

#### Rôles RBAC (`UserProfile.role`) — nouveau système orthogonal

| Rôle | `peut_ecrire` | `peut_cloturer` | `peut_valider_jaugeage` | `peut_suppr_mouvement` | `peut_gerer_users` | `peut_voir_audit` |
|------|:---:|:---:|:---:|:---:|:---:|:---:|
| `SUPERADMIN` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| `CHEF_DEPOT` | ✅ | ✅ | ✅ | ✅ | ✗ | ✅ |
| `OPERATEUR` | ✅ | ✗ | ✅ | ✗ | ✗ | ✗ |
| `COMPTABLE` | ✗ | ✗ | ✗ | ✗ | ✗ | ✅ |
| `LECTEUR` | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |

Les deux systèmes coexistent : `UtilisateurSGDS.role` (legacy 3 rôles) et `UserProfile.role` (RBAC 5 rôles).

#### Décorateurs et helpers
- `@login_required` — sur toutes les vues (redirige vers `LOGIN_URL`)
- `admin_required` — décorateur custom dans `accounts/views.py`, vérifie `request.user.is_admin_role`
- `_deny_marketeur(request)` — dans `SGDS/views.py`, retourne `True` si `is_marketeur_role` (avec message 403)
- `@role_required(*roles)` — décorateur SGDS.users pour les FBVs RBAC
- CBV Mixins RBAC : `SuperAdminRequiredMixin`, `ChefDepotRequiredMixin`, `CanWriteMixin`, `CanManageUsersMixin`, `CanViewAuditMixin`

#### Formulaires utilisateurs (`accounts/forms.py`)
- `UtilisateurCreationForm(UserCreationForm)` — création par admin
- `UtilisateurModificationForm(ModelForm)` — édition admin (mot de passe optionnel)
- `UtilisateurProfilForm(ModelForm)` — auto-édition non-admin (sans role/marketeur/is_active)

#### Compte admin initial
- Username : `admin` / Password : `Admin@SGDS2025`
- role=`ADMIN`, is_superuser=`True`

#### Créer un utilisateur RBAC (shell)
```python
from SGDS.users.managers import creer_utilisateur
from SGDS.users.models import Role
creer_utilisateur('username', 'email@sgds.ml', 'MotDePasse!', Role.SUPERADMIN, prenom='Prénom', nom='Nom')
```

### URL Structure

#### App `accounts` (`accounts/urls.py`) — auth uniquement

| URL | Vue | Nom |
|-----|-----|-----|
| `/auth/connexion/` | connexion | `connexion` |
| `/auth/deconnexion/` | deconnexion | `deconnexion` |

> Les routes `/utilisateurs/` et dérivées ont été supprimées — remplacées par `SGDS.users`.

#### App `SGDS.users` (`SGDS/users/urls.py`)

| URL | Vue | Nom | Rôle requis |
|-----|-----|-----|-------------|
| `/utilisateurs/` | `ListeUtilisateursView` | `users_liste` | SUPERADMIN / CHEF_DEPOT |
| `/utilisateurs/nouveau/` | `CreerUtilisateurView` | `users_creer` | SUPERADMIN |
| `/utilisateurs/<pk>/` | `DetailUtilisateurView` | `users_detail` | SUPERADMIN / CHEF_DEPOT |
| `/utilisateurs/<pk>/modifier/` | `ModifierUtilisateurView` | `users_modifier` | SUPERADMIN |
| `/mon-profil/` | `MonProfilView` | `users_mon_profil` | Tout utilisateur connecté |
| `/audit/` | `AuditLogView` | `users_audit` | SUPERADMIN / CHEF_DEPOT |

#### App `SGDS` (`SGDS/urls.py`)

| URL | Vue | Nom |
|-----|-----|-----|
| `/marketeurs/` | Liste + filtres | `marketeur_list` |
| `/marketeurs/nouveau/` | Création | `marketeur_create` |
| `/marketeurs/<pk>/` | Détail | `marketeur_detail` |
| `/marketeurs/<pk>/modifier/` | Édition | `marketeur_update` |
| `/marketeurs/<pk>/supprimer/` | Suppression | `marketeur_delete` |
| `/camions/` | Liste + filtres | `camion_list` |
| `/camions/nouveau/` | Création | `camion_create` |
| `/camions/<pk>/` | Détail | `camion_detail` |
| `/camions/<pk>/modifier/` | Édition | `camion_update` |
| `/camions/<pk>/supprimer/` | Suppression | `camion_delete` |
| `/chauffeurs/` | Liste (grille cards) | `chauffeur_list` |
| `/chauffeurs/nouveau/` | Création | `chauffeur_create` |
| `/chauffeurs/<pk>/` | Détail | `chauffeur_detail` |
| `/chauffeurs/<pk>/modifier/` | Édition | `chauffeur_update` |
| `/chauffeurs/<pk>/supprimer/` | Suppression | `chauffeur_delete` |
| `/chauffeurs/<pk>/badge/` | Badge QR imprimable | `chauffeur_badge` |
| `/familles/` | Liste + filtres | `famille_list` |
| `/familles/nouvelle/` | Création | `famille_create` |
| `/familles/<pk>/` | Détail + produits liés | `famille_detail` |
| `/familles/<pk>/modifier/` | Édition | `famille_update` |
| `/familles/<pk>/supprimer/` | Suppression | `famille_delete` |
| `/produits/` | Liste + filtres | `produit_list` |
| `/produits/nouveau/` | Création | `produit_create` |
| `/produits/<pk>/` | Détail + cuves liées | `produit_detail` |
| `/produits/<pk>/modifier/` | Édition | `produit_update` |
| `/produits/<pk>/supprimer/` | Suppression | `produit_delete` |
| `/cuves/` | Liste + filtres | `cuve_list` |
| `/cuves/nouvelle/` | Création | `cuve_create` |
| `/cuves/<pk>/` | Détail + jauge | `cuve_detail` |
| `/cuves/<pk>/modifier/` | Édition | `cuve_update` |
| `/cuves/<pk>/supprimer/` | Suppression | `cuve_delete` |
| `/parametres-jaugeage/` | Liste tous les paramètres | `parametre_list` |
| `/parametres-jaugeage/<pk>/` | Détail | `parametre_detail` |
| `/cuves/<cuve_pk>/parametres-jaugeage/` | Créer/modifier paramètre d'une cuve | `parametre_create_update` |
| `/parametres-jaugeage/<pk>/supprimer/` | Suppression | `parametre_delete` |
| `/jaugeages/` | Liste + filtres + Vol.@15°C | `jaugeage_list` |
| `/jaugeages/nouveau/` | Création (→ redirect saisie) | `jaugeage_create` |
| `/jaugeages/<pk>/` | Détail lecture + tfoot totaux volumes | `jaugeage_detail` |
| `/jaugeages/<pk>/modifier/` | Édition en-tête | `jaugeage_update` |
| `/jaugeages/<pk>/supprimer/` | Suppression | `jaugeage_delete` |
| `/jaugeages/<pk>/saisie/` | Saisie/édition mesures (formset) | `jaugeage_saisie` |
| `/jaugeages/<pk>/rapport/` | Vue A4 impression / export PDF | `jaugeage_rapport` |
| `/parametres-metrologiques/` | Fiche normative API MPMS — lecture seule | `parametres_metrologiques` |
| `/mouvements/` | Liste mouvements + filtres | `mouvement_liste` |
| `/mouvements/nouveau/` | Création mouvement (saisie unifiée) | `mouvement_creer` |
| `/mouvements/calcul-preview/` | `mouvement_calcul_preview` (POST AJAX) | `mouvement_calcul_preview` |
| `/mouvements/<pk>/` | Fiche détail lecture seule | `mouvement_detail` |
| `/mouvements/<pk>/modifier/` | Édition mouvement | `mouvement_modifier` |
| `/mouvements/<pk>/supprimer/` | Suppression (staff only) | `mouvement_supprimer` |
| `/mon-espace/` | Tableau de bord Marketeur (rôle MARKETEUR uniquement) | `client_dashboard` |
| `/mon-espace/mouvements/` | Mes mouvements (rôle MARKETEUR uniquement) | `client_mouvements` |
| `/admin/` | Django admin | — |

#### `Gestion_Dépôt/urls.py` (racine)
```python
path('', include('accounts.urls')),        # auth seulement
path('', include('SGDS.urls')),            # métier
path('accounts/', include('allauth.urls')),# SSO Google / Microsoft
path('', include('SGDS.users.urls')),      # RBAC /utilisateurs/ /mon-profil/ /audit/
```

### Templates & Design

> **Design system migré (2026-05-02)** — Le projet utilise désormais un design system CSS complet dans `static/css/sgds.css`. Les anciennes couleurs hardcodées (`#1E3A5F`, `#E8760A`) et polices (`DM Sans`, `Sora`) ont été remplacées par des variables CSS. Voir la section **"Migration Design System (2026-05-02)"** en bas de ce fichier pour le détail complet.

`base.html` : layout sidebar (fond `var(--ink)` + accent `var(--accent)` = `#b8541a`), font **Inter** + **JetBrains Mono** (données numériques), responsive. Design system CSS dans `static/css/sgds.css`, complété par des styles inline dans les templates.

**Navigation conditionnelle selon le rôle** : `{% if request.user.is_marketeur_role %}` → sidebar *Mon Espace* (Mon tableau de bord, Mes mouvements, Ma fiche) ; `{% else %}` → sidebar admin complète. Blocs de navigation ajoutés : `nav_client_dashboard`, `nav_client_mouvements`, `nav_client_fiche`.

Sidebar — sections :
- **Principal** : Tableau de bord (lien `#`), Marketeurs
- **Flotte** : Camions citernes, Chauffeurs
- **Dépôt** : Familles, Produits, Cuves, Jaugeages, Param. Jaugeage, **Mouvements** (`/mouvements/`), **Coulage** (`/coulage/`), **Périodes** (`/periodes/`), Commandes (`#`), Livraisons (`#`)
- **Rapports** : Statistiques (`#`), **Norme API MPMS** (`/parametres-metrologiques/`)
- **Administration** *(visible SUPERADMIN + CHEF_DEPOT uniquement via `{% has_role %}`)* :
  - **Utilisateurs** → `users_liste`
  - **Journal d'audit** → `users_audit`
- **Footer sidebar** : Avatar initiales + nom_complet + rôle legacy + `{% role_badge %}` RBAC + lien `users_mon_profil` + bouton déconnexion (POST form avec CSRF)
- **Topbar** : Breadcrumb (gauche) + **badge dropdown période** (centre-droit) + boutons icônes + lien profil → `users_mon_profil`

Blocs nav disponibles dans base.html : `nav_marketeur`, `nav_camion`, `nav_chauffeur`, `nav_famille`, `nav_produit`, `nav_cuve`, `nav_jaugeage`, `nav_parametre`, `nav_mouvement`, `nav_coulage`, `nav_periode`, `nav_metro`, `nav_users_rbac`, `nav_audit`

Template tags chargés dans base.html : `{% load periode_tags %}{% load user_tags %}`

Pages Camion : tableau avec barre de capacité visuelle, stats cards, hero navy sur le détail.
Pages Chauffeur : grille de cards avec avatar (initiales ou photo), anneau coloré selon statut, card permis stylée sur le détail. Bouton **Badge QR** dans le hero du détail → ouvre `chauffeur_badge.html` dans un nouvel onglet.
- `chauffeur_badge.html` — template **standalone** (n'étend pas `base.html`). Badge ID imprimable (54×85.6mm) : header navy (logo SGDS + tag CHAUFFEUR), avatar/photo, nom, N° employé, permis, téléphone, immatriculation camion citerne assigné, statut, QR code (encode l'URL `/chauffeurs/<pk>/`), footer orange (marketeur). Effet 3D hover + `@media print` pour impression directe. Bouton Imprimer + Retour à la fiche.
Pages Famille : tableau avec point de couleur, prévisualisation live JS dans le formulaire.
Pages Produit : badge famille coloré (couleur héritée de la famille), cuves liées avec mini barre de remplissage sur le détail.
Pages Cuve : barre de remplissage en liste (couleur dynamique vert/orange/rouge), jauge circulaire SVG animée sur le détail, preview interactif dans le formulaire.

Pages Jaugeage :
- `jaugeage_list.html` — stat cards (total, AVR, APR, J) + filtre (date début/fin/type) + tableau avec colonne **Vol. total @15°C** (somme `volume_standard_15c_calcule` de toutes les mesures, calculée en Python dans la vue) + bouton rapport PDF par ligne. Lignes cliquables (`onclick`).
- `jaugeage_form.html` — formulaire création (→ redirect vers saisie) et édition en-tête. Banner info pour la création.
- `jaugeage_saisie.html` — **cœur du RJJ**. Layout **colonne par cuve** : chaque colonne = 1 cuve, chaque ligne = 1 paramètre. Cuves regroupées par produit avec coloration via `famille.couleur`. 3 sections : en-tête cuve (HTT, Rempli.max, V(A), V/mn) / saisie opérateur (inputs) / calculs automatiques (lecture seule). Calculs JS **en temps réel** + calculs Python après save.
  - **Totaux (barre du haut)** : cartes par produit + carte "Vol. ambiant total dépôt" (style orange `.total-card.ambiant`) — affichent la somme de `volume_ambiant_depot` (pas @15°C). Mises à jour en temps réel par JS.
  - **Ligne Vol. ambiant dépôt** : mise en évidence avec classe `.tr-vad` (fond orange `#9a3412`, texte `#fed7aa`) — métrique principale du volume réel ambiant.
  - **Ligne Vol. standard @15°C** : mise en évidence `.tr-v15c` (fond vert `#065f46`).
  - **`<tfoot>`** : ligne de sous-totaux par groupe de produit (`colspan="{{ pg.count }}"` par groupe), style orange cohérent avec `.tr-vad`. Mise à jour JS live via `updateTotaux()`.
  - **Barre d'actions sticky** (`position:sticky;bottom:0`) : toujours visible en bas de l'écran. Bouton "Retour au détail" (`.btn-retour` navy solid) remplace l'ancien "Annuler". Bouton "Enregistrer" orange à droite.
  - **Boutons hero** : `.btn-hero-print` (fond verre blanc 12%, bordure 45%) et `.btn-hero-back` (fond verre 7%) — lisibles sur fond navy.
  - **JS** : `productGroupCounts`, `groupStarts`, `vadByCol[]`, `updateTotaux()` — calcule et pousse les totaux Vol. ambiant dépôt par groupe vers la barre du haut ET le tfoot en temps réel.
- `jaugeage_detail.html` — vue lecture avec hero navy, tableau mesures avec colonnes saisies et calculées.
  - **Boutons hero** : `.btn-hero-print` pour "Imprimer/PDF" et `.btn-hero-edit` pour "Modifier en-tête" (fond verre sur navy — lisibles). "Saisie mesures" reste `btn-primary` orange.
  - **`<tfoot>`** dans le tableau mesures : une ligne "Σ Totaux" avec sous-totaux colorés par colonne — Vol. ambiant bac (vert `#064e3b`), **Vol. ambiant dépôt** (orange `#9a3412`, plus grand — métrique principale), Vol. std @15°C (vert `#065f46`), Vol. disponible (navy `#1e3a5f`). Colonnes saisie (Creux, T1-T3, D, Vcf, H. produit) affichent "—".
- `jaugeage_rapport.html` — **standalone** (n'étend pas base.html). Format A4 paysage (`@page { size: A4 landscape }`). En-tête SGDS SANKÉ avec logo texte navy + métadonnées jaugeage. Tableau colonne-par-cuve avec toutes les lignes (paramètres, saisies, calculs). 3 zones de signature (opérateur, responsable dépôt, marketeur). Boutons Imprimer/Retour masqués à l'impression via `@media print`.
  - **Totaux (boîtes du haut)** : cartes par produit affichant `volume_ambiant_depot` en primaire (valeur orange `#9a3412`) + `volume_standard_15c_calcule` @15°C en secondaire (vert, plus petit). Carte "Vol. ambiant total dépôt" en dégradé orange (`#7c2d12→#9a3412`), identique visuellement à la carte `.total-card.ambiant` de la saisie. Même métriques et même hiérarchie visuelle que `jaugeage_saisie.html`.
  - **Ligne Vol. ambiant dépôt (L)** : mise en évidence orange — label fond `#7c2d12` texte `#fed7aa`, cellules fond `#9a3412` texte `#fed7aa` bordure basse `#ea580c`. Cohérent avec `.tr-vad` de la saisie.
  - **Ligne Vol. standard @15°C (L)** : mise en évidence vert foncé `#065f46` (`.td-data.v15c`).
  - **`<tfoot>`** : ligne "Σ Vol. ambiant" avec sous-totaux `volume_ambiant_depot` par groupe de produit (`colspan="{{ pg.mesures|length }}"`) — style orange `#9a3412`/`#fed7aa`/bordure `#ea580c`, identique au tfoot de la saisie.
- `parametres_metrologiques.html` — étend `base.html`. Bloc `nav_metro`. **Fiche technique normative en lecture seule.** Hero navy avec grille de points décorative + badges. Bandeau ambre d'avertissement (valeurs non modifiables). 3 sections : (1) tableau des 4 plages de densité avec constantes K₀/K₁ colorées par type de produit (orange=Super, bleu=zone ambiguë, vert=Gasoil, gris=Lourd) + note zone ambiguë ; (2) formules TRH_15 / TVCF_15 côte à côte (α₁₅, Vcf, ρ₁₅) + logique de sélection de plage ; (3) fiche normative grille 2 colonnes (code, titre officiel, date, source Excel `J:\OPS\TRH_15.XLS`, statut). Navigation : retour jaugeages + paramètres cuves + lien `/admin/` (ADMIN uniquement). Contexte : `plages` (liste de 4 dicts avec `id`, `label`, `categorie`, `seuil`, `type`, constantes lues depuis `petroleum_calc.py`), `norme` (dict code/titre/date/source/statut/iterations).

Pages Mouvements :
- `liste.html` — stat header (filtre type/régime/produit/marketeur/dates + champ `q` recherche texte). Tableau avec colonne **N° Enregistrement** en tête (monospace `.td-numero`, cliquable → **fiche détail**), badges type (vert=ENTREE, orange=SORTIE, bleu=CESSION, violet=ACQUITTEMENT) et régime (vert clair=ACQUITTE, jaune=SOUS_DOUANE). `colspan=10`. Lignes cliquables → `mouvement_detail`.
- `detail.html` — **fiche lecture seule** d'un mouvement. Hero navy avec N° enregistrement, badges type/régime, métadonnées (date, marketeur, produit, cuve, camion). Boutons hero : **Modifier** (orange → `mouvement_modifier`) + Retour liste + Supprimer (staff). Cards de sections conditionnelles par type : **Données d'entrée** (SS1 Provenance, SS2 BL Expéditeur col.W–AA, SS3 Réception col.AB–AG avec sous-bloc calculé, SS4 Contrôle final col.AH–AL) pour ENTREE ; Données de sortie pour SORTIE ; Données de cession pour CESSION ; Données d'acquittement pour ACQUITTEMENT. Section Notes & Suivi (collaborateur, notes, date saisie, date modif).
- `saisie.html` — template unifié création ET édition.
  - **Mode création** : 4 boutons-cards de sélection de type (ENTREE/SORTIE/CESSION/ACQUITTEMENT) + input caché `type_mouvement`. Bannière info "numéro généré automatiquement".
  - **Mode édition** : Bannière navy en haut avec N° enregistrement + icône cadenas (champ verrouillé). Pas de sélecteur de type. Bouton **"Retour à la fiche"** dans le footer (→ `mouvement_detail`).
  - JS `selectType()` — affiche/masque les sections selon le type sélectionné (`el.style.display = 'block'` pour les sections actives). ACQUITTEMENT force `ACQUITTE` et masque la section camion.
  - JS `onCamionChange()` — lit `data-marketeur` sur `<option>` pour afficher le transporteur en readonly.
  - JS `onProduitChange()` — filtre le `<select>` cuve par `data-produit` sur les options.
  - JS submit handler — désactive les `input/select/textarea` des sections masquées (`display === 'none'`) avant soumission pour éviter d'écraser des champs partagés.
  - Zone **Calculs automatiques** (lecture seule, visible mode édition) : `densite_15c_calculee`, `ecart_densite_15c` (alerte rouge + ⚠ si `|e| > 0.001`), `coefficient_conversion_15c`, `volume_15c_recu`, `perte_gain_reception`, `perte_gain_15c`, `poids_kg`.
  - **Preview AJAX en temps réel (ENTREE & SORTIE)** : appel debounced (600ms) à `mouvement_calcul_preview` à chaque `input` sur les champs déclencheurs. Déclenché aussi au changement de type (clic bouton) et au chargement si valeurs déjà présentes (mode modification).
    - ENTREE : champs déclencheurs = `volume_ambiant_recu`, `volume_ambiant_expediteur`, `temperature_labo`, `densite_observee_labo`, `temperature_reception`, `densite_15c_expediteur`. Spans cibles : `pv-pg-reception`, `pv-densite-15c`, `pv-ecart-densite`, `pv-vcf`, `pv-volume-15c`, `pv-pg-15c`, `pv-poids`.
    - SORTIE : champs déclencheurs = `volume_ambiant_sortie`, `densite_15c_sortie`, `temperature_sortie`. Spans cibles : `pv-sortie-vcf`, `pv-sortie-volume-15c`, `pv-sortie-poids`.
  - **Localization** : `{% load l10n %}{% localize off %}` wrappent l'ensemble du formulaire pour forcer le séparateur décimal `.` (requis par `input[type=number]`) — voir bug ci-dessous.
  - **Comparaisons FK** : `form.X.value|stringformat:"s" == Y.pk|stringformat:"s"` pour les selects et radios (productuit, marketeur, camion, chauffeur, cuve, cession_marketeur_destinataire). La comparaison `int == str` est toujours `False` en Django templates — le `|stringformat:"s"` des deux côtés est obligatoire.
  - **Champs numériques** : `|default_if_none:''` au lieu de `|default:''` pour ne pas masquer les valeurs `Decimal(0)` (zéro est falsy avec `|default`).
- `confirmer_suppression.html` — page de confirmation suppression avec résumé du mouvement (N°, type, date, produit, volume).

Pages Auth :
- `login.html` — template **standalone** (n'étend pas `base.html`). Fond navy `#0A1628`, orbes animés, grille de points. Split card : panneau gauche branding 42% + formulaire droit 58%. Toggle show/hide password, case "Se souvenir de moi".
- `logout_confirm.html` — étend `base.html`. Formulaire POST avec CSRF, bouton Annuler via `javascript:history.back()`.

Pages Utilisateurs RBAC (`templates/users/`) :
- `liste.html` — stat strip 5 chips par rôle RBAC + filter bar (q + role select) + tableau cliquable (avatar initiales, nom, `role_badge`, statut, dernière IP, actions Voir/Modifier). Paginate 25.
- `detail.html` — layout 2 colonnes : hero card navy (photo/avatar, nom, `role_badge`, bouton Modifier) + info card (email/tel/poste/IP/dates) | tableau 30 dernières actions (horodatage, badge action coloré, objet, source).
- `creer.html` — grille 5 cards rôle cliquables (JS `selectRole()`), barre de force mot de passe JS, validation confirmation.
- `modifier.html` — toggles actif/profil_actif, grille rôle pré-sélectionnée.
- `mon_profil.html` — layout 2 colonnes : sidebar hero navy (avatar cliquable → upload photo, role_badge) + form prénom/nom/email/tel + section mot de passe dépliable JS.
- `audit_log.html` — 4 stat chips, filter panel 7 colonnes (action/objet/user/dates), tableau lignes expandables JS `toggleRow()` (détails + table diff avant/après rouge/vert). Paginate 50.
- `partials/role_badge.html` — span badge inline (couleur selon rôle RBAC, rendu par le templatetag `role_badge`).

> Les anciens templates legacy (`user_list.html`, `user_detail.html`, `user_form.html`, `user_confirm_delete.html`) ont été supprimés.

**Template admin custom :**
- `templates/admin/jaugeage_change_list.html` — étend `admin/change_list.html`. Override du bloc `object-tools-items` pour ajouter un bouton orange **"Créer un nouveau jaugeage"** qui appelle la vue `creer-nouveau/` de `JaugeageJourAdmin`.

Statuts — badges :
- Marketeur : green=ACTIF, gray=INACTIF, amber=SUSPENDU, red=BLACKLIST
- Camion : green=EN_SERVICE, amber=EN_MAINTENANCE, red=HORS_SERVICE, gray=RETIRE
- Chauffeur : green=ACTIF, gray=INACTIF, amber=SUSPENDU
- Famille : green=ACTIF, gray=INACTIF
- Produit : green=ACTIF, gray=INACTIF, amber=DISCONTINUE
- Cuve : green=ACTIVE, gray=INACTIVE, amber=EN_MAINTENANCE, red=HORS_SERVICE
- Utilisateur : purple=ADMIN, blue=OPERATEUR, orange=MARKETEUR, green=Actif, gray=Inactif

### Views

Toutes les vues sont **function-based** (pas de CBV). Pattern : list → detail → create → update → delete.

#### `accounts/views.py` — auth uniquement
- `connexion(request)` — login via `authenticate()` + `login()`. Si rôle MARKETEUR → redirige vers `client_dashboard`. Sinon → `LOGIN_REDIRECT_URL`.
- `deconnexion(request)` — `@login_required`, POST uniquement, `logout()` puis redirect.

> Les vues `user_list`, `user_detail`, `user_create`, `user_update`, `user_delete` ont été supprimées — remplacées par `SGDS/users/views.py`.

#### `SGDS/users/views.py` — CBVs RBAC

| Classe | Mixin | Description |
|--------|-------|-------------|
| `ListeUtilisateursView` | `CanManageUsersMixin + ListView` | Liste + filtres q/role. `paginate_by=25` |
| `DetailUtilisateurView` | `CanManageUsersMixin + DetailView` | Détail + 30 dernières actions AuditLog |
| `CreerUtilisateurView` | `SuperAdminRequiredMixin + View` | Validation mdp, appelle `creer_utilisateur()` |
| `ModifierUtilisateurView` | `SuperAdminRequiredMixin + View` | Update rôle + is_staff + is_superuser + profil |
| `MonProfilView` | `LoginRequiredMixin + View` | Upload photo + changement mdp courant utilisateur |
| `AuditLogView` | `CanViewAuditMixin + ListView` | `paginate_by=50`, filtres action/objet/user/dates |

#### `SGDS/views.py`
- `chauffeur_badge(request, pk)` — `@login_required`. Génère un QR code PNG (navy sur blanc, error_correction=H) encodant `request.build_absolute_uri('/chauffeurs/<pk>/')`, le convertit en base64 et le passe au template `chauffeur_badge.html`. Respecte les restrictions MARKETEUR.

**Vues jaugeage :**
- `jaugeage_list(request)` — `@login_required`. Queryset avec `prefetch_related('mesures__cuve__parametre_jaugeage')`. Calcul en Python des volumes totaux @15°C par jaugeage (`sum(m.volume_standard_15c_calcule)`) → passé comme liste de tuples `jaugeages_with_totals = [(jaugeage, total_ou_None), ...]` (dict non utilisable en template Django pour lookup par clé variable).
- `jaugeage_create(request)` — `@login_required`, bloqué MARKETEUR. Appelle `JaugeageJour.creer_nouveau_jaugeage()` → redirige vers `jaugeage_saisie`.
- `jaugeage_detail(request, pk)` — `@login_required`. Vue lecture. `prefetch_related('mesures__cuve', 'mesures__cuve__produit', 'mesures__cuve__produit__famille', 'mesures__cuve__parametre_jaugeage')`. Calcule et passe au template : `total_vab` (somme `volume_ambiant_bac`), `total_vad` (somme `volume_ambiant_depot`), `total_v15c` (somme `volume_standard_15c`), `total_vdispo` (somme `volume_disponible`) — utilisés par le `<tfoot>` du tableau. Zéro requête supplémentaire (itère `jaugeage.mesures.all()` déjà prefetch).
- `jaugeage_update(request, pk)` — `@login_required`, bloqué MARKETEUR. Édition en-tête uniquement.
- `jaugeage_delete(request, pk)` — `@login_required`, bloqué MARKETEUR. Suppression en cascade (toutes les MesureCuve liées).
- `jaugeage_saisie(request, pk)` — `@login_required`, bloqué MARKETEUR. `modelformset_factory(MesureCuve, form=MesureCuveForm, extra=0)`. En POST valide et sauvegarde → redirect vers soi-même pour afficher les calculs mis à jour. Context : `product_groups` (groupes par produit, chaque entrée contient `produit`, `cuves`, `count`, **`total_vad`** = somme `volume_ambiant_depot` du groupe pour le tfoot), `all_cuves` (liste plate `(form, mesure)`), `totaux_groupes` (sommes `volume_ambiant_depot` par groupe), `total_depot` (somme dépôt entier). **Les totaux affichés (barre du haut + tfoot) représentent le `volume_ambiant_depot`, pas le @15°C.**
- `jaugeage_rapport(request, pk)` — `@login_required`. Vue lecture A4. Groupe les mesures par produit (même ordre `cuve__numero` que la saisie). Calcule **deux séries de totaux** alignées sur la saisie : `volume_ambiant_depot` (primaire) et `volume_standard_15c_calcule` (secondaire). Context : `all_mesures` (liste plate), `product_groups` (chaque entrée a `total_vad` = somme `volume_ambiant_depot` du groupe, pour le tfoot), `totaux_groupes` (liste de dicts `{produit, total_vad, total_v15c}`), `total_depot` (somme dépôt `volume_ambiant_depot`), `total_v15c` (somme dépôt `volume_standard_15c_calcule`).
- `parametres_metrologiques(request)` — `@login_required`. Vue **100% lecture, pas de POST, pas de base**. Importe les constantes depuis `.petroleum_calc` (`K_SUPER`, `K_MIDDLE`, `K_HEAVY`, `A_AMB`, `B_AMB`). Construit `plages` (liste 4 dicts) et `norme` (dict référence normative). Rend `Jaugeage/parametres_metrologiques.html`.

**Vues mouvements :**
- `mouvement_liste(request)` — `@login_required`. Filtres : `type_mouvement`, `regime_douanier`, `produit` (pk), `marketeur` (pk), `date_debut`, `date_fin`, `q` (recherche texte sur `numero_enregistrement`, `camion__immatriculation`, `bl_expediteur`, `marketeur__raison_sociale`). Rend `mouvements/liste.html`.
- `mouvement_creer(request)` — `@login_required`, bloqué MARKETEUR. `MouvementForm` + `LigneMouvementFormSet`. Utilise `commit=False` pour auto-assigner `mouvement.collaborateur`. Sauvegarde les lignes du formset : pour chaque ligne avec `cuve` ou `volume_ambiant` non-null, attribue `ligne.produit = mouvement.produit` avant `ligne.save()`. Passe `camions`, `cuves`, `marketeurs` au template. Rend `mouvements/saisie.html` (`mode='creer'`).
- `mouvement_detail(request, pk)` — `@login_required`. Vue **lecture seule**. `select_related` : `marketeur`, `produit`, `camion`, `camion__marketeur`, `chauffeur`, `cession_marketeur_destinataire` + `prefetch_related('lignes__cuve__produit')`. Rend `mouvements/detail.html`.
- `mouvement_modifier(request, pk)` — `@login_required`, bloqué MARKETEUR. `MouvementForm(instance=mouvement)` + `LigneMouvementFormSet(instance=mouvement)`. Traitement formset : DELETE → `ligne.delete()` ; sinon si `cuve` ou `volume_ambiant` → `ligne.produit = mouvement.produit ; ligne.save()`. Après boucle : `LigneMouvement.objects.filter(mouvement=mouvement).update(produit=mouvement.produit)` (synchronisation dénormalisée). Redirect vers `mouvement_detail`. Rend `mouvements/saisie.html` (`mode='modification'`).
- `mouvement_supprimer(request, pk)` — `@login_required`, `request.user.is_staff` only. Rend `mouvements/confirmer_suppression.html`.
- `mouvement_calcul_preview(request)` — `@login_required`, `@require_POST`. **Endpoint AJAX**. Reçoit un JSON avec `type_mouvement` + champs numériques, retourne un `JsonResponse` avec les valeurs calculées via `petroleum_calc`. Aucune sauvegarde. Utilisé par le JS de `saisie.html` pour la preview en temps réel (ENTREE et SORTIE). Défini dans `views/__init__.py` (importé depuis le package, **pas** depuis `views.py`).

**Vues Espace Marketeur (`SGDS/views/client.py`) :**

| Décorateur / Fonction | Description |
|---|---|
| `@marketeur_required` | Refuse l'accès si `not is_marketeur_role or not marketeur`. Redirige vers `connexion` ou `chauffeur_list`. |
| `_calculer_stock_par_produit(mkt)` | Calcule le stock @15°C par produit : Σ ENTREE - Σ SORTIE - Σ CESSION émise + Σ CESSION reçue - Σ ACQUITTEMENT. Retourne uniquement les produits avec activité ou stock non nul. |
| `client_dashboard(request)` | `@marketeur_required`. Tableau de bord du marketeur : stocks par produit, KPI (nb entrées/sorties/cessions, volumes totaux @15°C), 10 derniers mouvements, 6 dernières lignes coulage. Rend `Espace_Marketeur/dashboard.html`. |
| `client_mouvements(request)` | `@marketeur_required`. Liste paginée des mouvements du marketeur connecté. Filtres : type, produit, régime douanier, date_debut, date_fin. Rend `Espace_Marketeur/mouvements.html`. |

#### Restrictions rôle MARKETEUR (SGDS/views.py)
- `marketeur_list` → redirige directement vers `marketeur_detail` de son marketeur lié
- `camion_list` / `chauffeur_list` → filtrés par `marketeur=request.user.marketeur`
- Toutes les vues create/update/delete → bloquées par `_deny_marketeur()`

Filtres disponibles :
- Famille list : `q` (nom/code/description), `statut`
- Produit list : `q` (nom/code/description/famille), `statut`, `famille` (pk)
- Cuve list : `q` (numero/designation/localisation/produit), `statut`, `produit` (pk)

Relations dans les vues :
- `famille_detail` → passe `produits = famille.produits.all()`
- `produit_detail` → passe `cuves = produit.cuves.all()`
- `cuve_list` → utilise `select_related('produit', 'produit__famille')`

Comportements spéciaux :
- `chauffeur_create` → utilise `form.save(commit=False)`, puis assigne `chf.numero_employe = Chauffeur.get_next_numero()` avant `chf.save()`

### Admin (`SGDS/admin.py`)

En plus des admins standards (Marketeur, Camion, Chauffeur, Famille, Produit, Cuve) :

**`ParametreJaugeageCuveAdmin`** — liste : cuve, HTT, remplissage_maxi, V(A), V/mn, is_pompe. Fieldsets : Cuve / Caractéristiques physiques / Certificat de jaugeage / Suivi.

**`JaugeageJourAdmin`** — liste : date, heure, type, opérateur, dépôt, nb_mesures. `date_hierarchy` sur `date_jaugeage`. Inclut `MesureCuveInline` (TabularInline, `extra=0`, `can_delete=False`). Bouton custom **"Créer un nouveau jaugeage"** via `get_urls()` + `change_list_template = "admin/jaugeage_change_list.html"`.

**`MesureCuveAdmin`** — liste : jaugeage, cuve, creux, hauteur_produit, volume_ambiant_bac, volume_standard_15c, volume_disponible. Toutes les colonnes calculées sont en `readonly_fields`. Volume disponible affiché en rouge si négatif.

**`MesureCuveInline`** — utilisé dans `JaugeageJourAdmin`. Champs saisies + colonne calculée `apercu_volume_disponible` (lecture seule, colorée vert/rouge).

**`ClotureCoulageProduitInline`** *(nouveau)* — `TabularInline` dans `ClotureCoulageMensuelAdmin`. Champs : `produit`, `coefficient`, `pertes_gains`, `cumul_entree`, `cumul_sortie`. Tous en `readonly_fields`, `can_delete=False`, `extra=0`. Ajouté à `ClotureCoulageMensuelAdmin.inlines = [ClotureCoulageProduitInline, ClotureCoulageLigneInline]`.

**`MouvementAdmin`** — liste : `numero_enregistrement` (en premier), `date_mouvement`, `type_mouvement`, `regime_douanier`, `marketeur`, `produit`, `camion`, `col_volume_principal`, `date_saisie`. Filtres : type, régime, produit, marketeur, date. `date_hierarchy` sur `date_mouvement`. `search_fields` : numero_enregistrement, camion immatriculation, marketeur raison_sociale, bl_expediteur, numero_permis_sortie, acquittement_reference_declaration. **`inlines = [LigneMouvementInline]`**.

**`LigneMouvementInline(TabularInline)`** *(nouveau)* — `model=LigneMouvement`, `fields=['cuve','produit','volume_ambiant','volume_15c','ordre']`, `extra=1`.
- `readonly_fields` : `numero_enregistrement`, `date_saisie`, `date_modification`, et tous les champs calculés ENTREE (`densite_15c_calculee`, `ecart_densite_15c`, `coefficient_conversion_15c`, `volume_15c_recu`, `perte_gain_reception`, `perte_gain_15c`, `poids_kg`) et SORTIE (`coefficient_conversion_sortie`, `volume_15c_sortie`, `poids_sortie_kg`).
- Fieldsets : Identification / Marketeur & Cuve / Camion & Chauffeur / Entrée-Provenance & BL / Entrée-Volumes expéditeur / Entrée-Réception & Labo / Sortie-Client & Permis / Sortie-Volumes / Cession / Acquittement / **Calculs automatiques (lecture seule)** (contient : `densite_15c_calculee`, `ecart_densite_15c`, `coefficient_conversion_15c`, `volume_15c_recu`, `perte_gain_reception`, `perte_gain_15c`, `poids_kg`, `coefficient_conversion_sortie`, `volume_15c_sortie`, `poids_sortie_kg`) / Suivi.
- `col_volume_principal` — méthode admin qui appelle `obj.volume_principal` et formate en litres.

**`UtilisateurSGDSAdmin`** — dans `accounts/admin.py` (hérite de `UserAdmin`). Fieldsets étendus avec section "Profil SGDS" (role, telephone, photo, marketeur). Les anciens `RoleAdmin` et `RolePermissionAdmin` ont été supprimés (importaient des modèles inexistants).

**`UserProfileAdmin`** — dans `SGDS/users/admin.py`. Liste : user, role RBAC, actif, poste, derniere_ip. Inline dans l'admin utilisateur.

**`AuditLogAdmin`** — dans `SGDS/users/admin.py`. Immuable : `has_add_permission`, `has_change_permission`, `has_delete_permission` retournent tous `False`. Filtres : action, source, objet_type. Date hierarchy sur `horodatage`.

### Forms (`SGDS/forms.py`)

#### `ProduitForm(ModelForm)` *(mis à jour)*
```python
fields = ['nom', 'code', 'famille', 'description', 'unite_mesure',
          'prix_unitaire', 'prix_passage', 'seuil_alerte', 'statut', 'notes']
```
- `prix_passage` : `NumberInput(attrs={'placeholder': 'Ex: 4.7554', 'step': '0.0001'})` — champ optionnel, laissé vide = tarif global `ParametresCoulage`

#### `MesureCuveForm` — validation métier ajoutée

```python
fields = ['creux_mesure','t1','t2','t3','temperature_obs','densite_moyenne',
          'densite_15c','facteur_vcf','volume_additionnel','volume_tuyauterie','volume_eau']
```

- `clean_creux_mesure()` — vérifie ≥ 0 et < HTT (si `instance.cuve.parametre_jaugeage` accessible)
- `clean()` — vérifie t1/t2/t3/temperature_obs ∈ [0, 60] °C et densite_moyenne ∈ [600, 900] kg/m³
- `densite_15c` et `facteur_vcf` restent éditables (auto-écrasés par `save()` si toutes les températures sont renseignées)
- Tous les champs `required=False`

#### `MouvementForm(ModelForm)` *(nouveau)*

```python
exclude = [
    # Timestamps automatiques
    'date_saisie', 'date_modification',
    # Auto-rempli dans la vue (request.user)
    'collaborateur',
    # Calculés automatiquement via save() + petroleum_calc
    'densite_15c_calculee', 'ecart_densite_15c', 'coefficient_conversion_15c',
    'volume_15c_recu', 'perte_gain_reception', 'perte_gain_15c', 'poids_kg',
    'coefficient_conversion_sortie', 'volume_15c_sortie', 'poids_sortie_kg',
]
```

> `numero_enregistrement` a `editable=False` sur le modèle → exclu automatiquement par Django, pas besoin de le lister ici.

- `__init__()` — tous les champs `required=False` par défaut, sauf `type_mouvement`, `produit`, `regime_douanier`, `date_mouvement`, `marketeur`. Querysets filtrés sur statuts actifs.
- `clean()` — validation conditionnelle selon `type_mouvement` :
  - `ENTREE` : `volume_ambiant_recu`, `densite_observee_labo`, `temperature_labo`, `temperature_reception` requis
  - `SORTIE` : `volume_ambiant_sortie`, `destination` requis
  - `CESSION` : `cession_marketeur_destinataire`, `cession_volume_ambiant` requis
  - `ACQUITTEMENT` : `acquittement_volume_ambiant` requis + force `regime_douanier = 'ACQUITTE'`
- `return cleaned_data` en fin de `clean()` (correction bug silencieux `MesureCuveForm` appliquée simultanément)

#### `LigneMouvementForm(ModelForm)` *(nouveau)*

```python
fields = ['cuve', 'volume_ambiant', 'volume_15c']
```

- Widgets `NumberInput` avec `step='0.01'` et `class='form-control'` sur `volume_ambiant` et `volume_15c`
- `__init__()` accepte `produit=None` : filtre le queryset `cuve` sur `produit` si fourni, sinon toutes les cuves `ACTIVE`
- Tous les champs `required=False`

#### `LigneMouvementFormSet` *(nouveau)*

```python
LigneMouvementFormSet = inlineformset_factory(
    Mouvement, LigneMouvement,
    form=LigneMouvementForm,
    fields=['cuve', 'volume_ambiant', 'volume_15c'],
    extra=1, can_delete=True, min_num=0, validate_min=False,
)
```

Inline formset utilisé dans `mouvement_creer` et `mouvement_modifier` pour saisir les lignes multi-cuves d'un mouvement.

### Template Tags (`SGDS/templatetags/`)

#### `coulage_tags.py` *(nouveau)*

Usage : `{% load coulage_tags %}` dans les templates de coulage.

| Filtre | Signature | Description |
|--------|-----------|-------------|
| `lookup` | `dict\|lookup:key` | Accès `dict.get(key)` — pour clés Python simples |
| `lookup_id` | `dict\|lookup_id:obj` | Accès `dict.get(obj.id)` — pour accéder à un dict `{id: valeur}` depuis un objet Django |

**Pourquoi** : Django templates n'autorisent pas `dict[variable_key]`. Ces filtres permettent d'accéder dynamiquement aux dicts `volumes_par_produit`, `pu_par_produit`, etc. dans `suivi_evolution.html` et `frais_passage.html`.

---

#### `jaugeage_extras.py`

Usage : `{% load jaugeage_extras %}` dans les templates.

| Filtre/Tag | Signature | Description |
|---|---|---|
| `fmt_vol` | `value\|fmt_vol` ou `value\|fmt_vol:2` | Entier avec séparateur espace insécable `\u202f` (ex: `1 234 567 L`). Retourne `—` si None. |
| `fmt_density` | `value\|fmt_density` | 2 décimales (ex: `726.45`) |
| `fmt_vcf` | `value\|fmt_vcf` | 4 décimales (ex: `0.9978`) |
| `fmt_temp` | `value\|fmt_temp` | 2 décimales (ex: `32.50`) |
| `fmt_mm` | `value\|fmt_mm` | Entier mm avec séparateur espace (ex: `12 981`) |
| `or_tiret` | `value\|or_tiret` | Retourne `—` si None ou vide |
| `jaugeage_total_v15` | `{% jaugeage_total_v15 jaugeage as var %}` | Somme Python de `volume_standard_15c_calcule` sur toutes les mesures. Retourne `None` si aucune valeur. |

### Database

PostgreSQL (`sgds_depot`, localhost:5432). Credentials hardcodés dans `settings.py` — à déplacer en variables d'environnement avant mise en production.

Migrations :
- `accounts/0001_initial` — modèle UtilisateurSGDS (AbstractUser custom, AUTH_USER_MODEL)
- `SGDS/0001_initial` — modèles Marketeur, Camion, Chauffeur, Famille, Produit, Cuve
- `SGDS/0002_jaugeagejour_parametrejaugeagecuve_mesurecuve` — modèles ParametreJaugeageCuve, JaugeageJour, MesureCuve
- `SGDS/0003_mesurecuve_v_a_saisi` — `ADD FIELD v_a_saisi` (DecimalField 12,2 nullable) sur `MesureCuve`
- `SGDS/0004_jaugeagejour_date_validation_jaugeagejour_est_valide_and_more` — `ADD FIELD est_valide`, `date_validation`, `valide_par` (FK→AUTH_USER_MODEL) sur `JaugeageJour`
- `SGDS/0005_mouvement` — création table `Mouvement` avec tous ses champs
- `SGDS/0006_numero_enregistrement_auto` — `ALTER FIELD numero_enregistrement` (editable=False)
- `SGDS/0007_attribuer_numeros_mouvements` — migration de données : attribue des numéros conformes (`ENT-YYYY-NNNN`) aux enregistrements existants, triés par `date_mouvement, date_saisie, pk`. Saute les enregistrements déjà conformes. Met à jour les compteurs internes pour éviter les doublons. `RunPython`.
- `SGDS/0008_suppr_acquittement_montant_droits` — `REMOVE FIELD acquittement_montant_droits` (vérifié 0 valeurs non-NULL avant suppression)
- `SGDS/0009_ajout_ecart_densite_15c` — `ADD FIELD ecart_densite_15c` (DecimalField max_digits=8, decimal_places=4, nullable)
- `SGDS/0010_ajout_stock_actuel_produit` — `ADD FIELD stock_actuel` (DecimalField 14,2, défaut: 0) + `date_maj_stock` (DateTimeField nullable) sur `Produit`
- `SGDS/0011_coulage_models` — `CreateModel` ParametresCoulage, PeriodeComptable, ClotureCoulageMensuel (v1 avec champs `_go/_super`), StockOuverture, StockOuvertureCuve, ClotureCoulageLigne (v1)
- `SGDS/0012_add_date_ouverture_periode` — `ADD FIELD date_ouverture` (DateTimeField nullable) sur `PeriodeComptable`
- `SGDS/0013_refactor_coulage_par_produit` — Refactoring coulage générique : suppression des champs hardcodés `_go/_super` sur `ClotureCoulageMensuel` et `ClotureCoulageLigne` ; création de `ClotureCoulageProduit` ; ajout FK `produit` sur `ClotureCoulageLigne` ; nouvelle contrainte `unique_cloture_ligne_marketeur_produit`.
- `SGDS/0014_produit_prix_passage` — `ADD FIELD prix_passage` (DecimalField max_digits=10, decimal_places=4, nullable) sur `Produit`
- `SGDS/0015_lignemouvement` — `CreateModel LigneMouvement` (mouvement + cuve + produit + volume_ambiant + volume_15c + ordre)
- `SGDS/0016_data_migration_lignes_mouvement` — Migration de données `RunPython` : convertit les `Mouvement` existants (avec `FK cuve` renseignée) en `LigneMouvement` (1 ligne par mouvement). Reverse disponible.

> **Note importante AUTH_USER_MODEL** : Le modèle est dans `accounts`, pas `SGDS`. `AUTH_USER_MODEL = 'accounts.UtilisateurSGDS'`. La FK cross-app dans `UtilisateurSGDS` vers `Marketeur` utilise la référence `'SGDS.Marketeur'`.

> **Note petroleum_calc** : `SGDS/petroleum_calc.py` est **figé et validé** (6/6 cuves conformes au centième près contre classeur Excel de référence). Ne jamais modifier ce fichier.

### Dépendances Python supplémentaires

```bash
pip install qrcode[pil]          # Génération QR code (chauffeur_badge)
pip install openpyxl             # Export Excel coulage
pip install django-allauth       # SSO Google + Microsoft
pip install django-simple-history# Historique des modèles (HistoryRequestMiddleware)
pip install requests             # Requis par allauth (provider Google/Microsoft)
# Pillow est déjà requis (ImageField) — inclus automatiquement
```

### Modules planifiés (non implémentés)

- Commandes (liens dans la sidebar pointent sur `#`)
- Livraisons (liens dans la sidebar pointent sur `#`)
- Tableau de bord (statistiques globales)

### Modules implémentés (résumé chronologique)

| Module | Migration(s) | Statut |
|--------|-------------|--------|
| Marketeur, Camion, Chauffeur, Famille, Produit, Cuve | `0001_initial` | ✅ |
| ParametreJaugeageCuve, JaugeageJour, MesureCuve | `0002` | ✅ |
| **MesureCuve — saisie V(A) manuelle** (`v_a_saisi`) | `0003` | ✅ |
| **JaugeageJour — workflow validation** (`est_valide`, `date_validation`, `valide_par`) | `0004` | ✅ |
| **Mouvement** (ENTREE/SORTIE/CESSION/ACQUITTEMENT) | `0005` → `0009` | ✅ |
| **Produit — stock temps réel** (`stock_actuel`, `date_maj_stock`) | `0010` | ✅ |
| **PériodeComptable + Coulage + StockOuverture/Cuve** | `0011` → `0013` | ✅ |
| **Suivi Évolution Journalier** (tableau jour×cuve par produit, export Excel) | `—` (calcul live) | ✅ |
| **Frais de Passage** (facturation mode règlement, tarif par produit, export Excel) | `0014_produit_prix_passage` | ✅ |
| **LigneMouvement** (multi-cuves par mouvement, migration données) | `0015` + `0016` | ✅ |
| **Espace Marketeur** (`client_dashboard`, `client_mouvements`, stocks par produit) | `—` (vues + templates) | ✅ |
| **RBAC + Audit Trail + SSO** (UserProfile, AuditLog, allauth, simple_history) | `SGDS/users/migrations/` | ✅ |

---

## Module Périodes Comptables & Coulage

### Modèles (`SGDS/models.py` — nouveaux)

#### PeriodeComptable
Cycle de vie mensuel payroll-like. Aucune création implicite — toujours via `ouvrir_periode()`.

- `mois` (1–12), `annee` (YYYY)
- `statut` — `OUVERTE` / `CLOTUREE` (défaut: `OUVERTE`)
- `date_debut` / `date_fin` — calculés automatiquement dans `save()` (1er et dernier jour du mois)
- `date_ouverture` / `date_cloture` — timestamps horodatés
- `cloture_par` — FK → UtilisateurSGDS (nullable, SET_NULL)
- `libelle` — property : ex. `"Avril 2026"`
- `periode_precedente()` — méthode : retourne la PeriodeComptable du mois M-1 ou None
- **Contrainte unique** : `(mois, annee)`
- **Relation inverse** : `cloture_coulage` → `ClotureCoulageMensuel` (OneToOne, nullable)

#### ClotureCoulageMensuel
Snapshot figé de la répartition du coulage au moment de la clôture.

- `periode` — OneToOneField → PeriodeComptable (`related_name='cloture_coulage'`, CASCADE)
- `motif`, `prix_unitaire_passage` (FCFA/L)
- `total_montant` (Decimal)
- `date_cloture`, `cloture_par` (FK User)
- `notes`
- Relations inverses : `produits_coulage` → `ClotureCoulageProduit`, `lignes` → `ClotureCoulageLigne`

#### ClotureCoulageProduit
Résumé par produit dans le snapshot.

- `cloture` — FK → ClotureCoulageMensuel (`related_name='produits_coulage'`, CASCADE)
- `produit` — FK → Produit (PROTECT)
- `coefficient` (Decimal), `pertes_gains` (Decimal), `cumul_entree`, `cumul_sortie`

#### ClotureCoulageLigne
Détail par marketeur × produit dans le snapshot.

- `cloture` — FK → ClotureCoulageMensuel (`related_name='lignes'`, CASCADE)
- `marketeur` — FK → Marketeur (PROTECT)
- `produit` — FK → Produit (nullable, PROTECT)
- `motif`, `prix_unitaire`, `brut_entree`, `coul_entree`, `entree_nette`, `sortie`
- `base_qp_coul`, `coef_qp_coul`, `qp_coul`, `volume_sorti`, `montant`

---

### Services (`SGDS/services/`)

Nouveau répertoire (pas d'`__init__.py` requis, imports directs).

#### `periode_comptable.py`

| Fonction | Signature | Description |
|----------|-----------|-------------|
| `mois_suivant` | `(mois, annee) → (mois, annee)` | Gère décembre → janvier+1 |
| `periode_pour_date` | `(d: date) → PeriodeComptable\|None` | Retourne la période (tout statut) pour le mois de `d`. NE CRÉE RIEN. |
| `periode_ouverte_pour_date` | `(d: date) → PeriodeComptable\|None` | Retourne la période OUVERTE pour le mois de `d`, ou None |
| `periode_courante_ou_alerte` | `() → PeriodeComptable\|None` | Retourne la période OUVERTE du mois courant — utilisée par le templatetag |
| `verifier_peut_ouvrir_periode` | `(mois, annee) → True \| raise ValidationError` | Vérifie chaîne chronologique stricte : pas de doublons, pas de saut, dernière doit être CLOTUREE |
| `ouvrir_periode` | `(mois, annee, user=None) → PeriodeComptable` | `@transaction.atomic` — crée la période, résout les stocks d'ouverture. Lève `ValidationError` si refusé. |
| `cloturer_periode` | `(periode, user=None, notes=None) → PeriodeComptable` | `@transaction.atomic` — exige ≥1 jaugeage ce mois, appelle `figer_cloture_coulage()`, marque CLOTUREE. N'ouvre PAS la période suivante. |

**Règles métier :**
- Aucun `get_or_create` — création uniquement via `ouvrir_periode()`
- `Mouvement.clean()` et `JaugeageJour.clean()` appellent `periode_ouverte_pour_date(date)` → `ValidationError` si None
- N+1 ne peut ouvrir que si N est CLOTUREE et N+1 = M+1 exactement (pas de saut)
- Première période : exception — tout mois est accepté si aucune période n'existe

#### `recalcul_stock.py`

| Fonction | Description |
|----------|-------------|
| `recalculer_stock_cuve(cuve)` | `Cuve.niveau_actuel` ← `volume_ambiant_depot` de la dernière `MesureCuve` (jaugeage physique) **+ Σ volumes ENTREE postérieurs au jaugeage − Σ volumes SORTIE postérieurs**. 0 si aucune mesure. `save(update_fields=['niveau_actuel'])` |
| `recalculer_stock_produit(produit)` | `Produit.stock_actuel` ← Σ `niveau_actuel` de toutes les cuves du produit. `save(update_fields=['stock_actuel', 'date_maj_stock'])` |
| `recalculer_tous_stocks()` | Boucle générique sur toutes cuves puis tous produits. Appelée après suppression d'un JaugeageJour entier. |

> **Logique de `recalculer_stock_cuve`** :
> 1. Base = `volume_ambiant_depot` de la dernière `MesureCuve` (jaugeage = snapshot physique réel)
> 2. Delta = Σ volumes des `LigneMouvement` **strictement postérieures** à la date du jaugeage :
>    - `ENTREE` → `+ volume_ambiant`
>    - `SORTIE` → `- volume_ambiant`
>    - `CESSION` et `ACQUITTEMENT` → ignorés (pas de mouvement physique)
> 3. `niveau_actuel = base + delta`
>
> Si aucun jaugeage : base = 0, tous les mouvements sont comptés.

#### `suivi_evolution.py` *(nouveau)*

| Fonction | Signature | Description |
|----------|-----------|-------------|
| `calculer_suivi_evolution` | `(periode, produit) → dict` | Tableau journalier par cuve pour un produit sur la période. Retourne `{produit, cuves, jours, kpis}`. |

**Logique :**
- `cuves` = cuves actives stockant le produit
- `jours` = liste de dicts par date (date_debut → date_fin de la période), chaque jour contient :
  - `stock_initial_par_cuve` — stock de la veille (premier jour = `StockOuvertureCuve` ou `MesureCuve` la plus récente avant la période)
  - `entree_brute`, `coulage_reception`, `sortie` — agrégats `Mouvement` du jour
  - `stock_comptable` = stock_initial + entree_nette - sortie
  - `stock_physique` — `volume_ambiant_depot` si jaugeage ce jour, sinon `None`
  - `pg_bac` = stock_physique - stock_comptable (si jaugeage)
  - `pg_cumul` — cumulé sur la période
  - `has_jaugeage` — booléen (ligne mise en évidence dans le template)
- `kpis` : `{total_entree_brute, total_coulage_reception, total_sortie, pg_cumul_total}`

#### `frais_passage.py` *(nouveau)*

| Fonction | Signature | Description |
|----------|-----------|-------------|
| `calculer_frais_passage` | `(periode) → dict` | Facture les frais de passage par mode de règlement et par marketeur. |

**Logique de tarification par produit :**
- `pu_global` = `ParametresCoulage.prix_unitaire_global`
- `pu_par_produit = {p.id: p.prix_passage if p.prix_passage is not None else pu_global}` — chaque produit a son propre tarif
- Montant par ligne = `Σ(volume_produit × pu_par_produit[pid])` (pas `vol_global × pu_unique`)
- `pu_moyen` par ligne = `montant / volume_global` (affiché dans le tableau)

**Structure retournée :**
```python
{
  'periode': periode,
  'parametres': {
    'prix_unitaire_global': pu_global,
    'pu_par_produit': {prod_id: Decimal},  # tarif effectif par produit
    'motif': str,
  },
  'produits': [Produit, ...],
  'modes': [
    {
      'mode': 'ESP-IMMEDIAT',
      'mode_libelle': str,
      'lignes': [{'marketeur', 'volumes_par_produit', 'volume_global', 'motif', 'pu', 'montant'}, ...],
      'sous_totaux': {'volumes_par_produit', 'volume_global', 'montant'},
    }, ...
  ],
  'total_general': {'volumes_par_produit', 'volume_global', 'montant'},
}
```

#### `export_excel.py` *(nouveau)*

| Fonction | Signature | Description |
|----------|-----------|-------------|
| `exporter_coulage_xlsx` | `(rapport) → Workbook` | Export coulage répartition (colonnes dynamiques par produit) |
| `exporter_suivi_xlsx` | `(rapport) → Workbook` | Export suivi évolution journalier (colonnes par cuve) |
| `exporter_frais_passage_xlsx` | `(rapport) → Workbook` | Export frais de passage (colonnes par produit + mode règlement) |

Toutes retournent un `openpyxl.Workbook`. Les vues les sérialisent en `HttpResponse` avec `content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'`.

#### `ecart_jaugeages.py`

| Fonction | Description |
|----------|-------------|
| `calculer_ecart_jaugeages(jaugeage_actuel)` | Retourne `{produit: Decimal}` — vide si pas de jaugeage précédent. Formule : `écart = stock_phys_nouveau - stock_phys_precedent - Σentrees_nettes + Σsorties`. Négatif = perte. |
| `_stocks_physiques_par_produit(jaugeage)` | Somme `volume_ambiant_depot` par produit pour un jaugeage donné |
| `_mouvements_entre(date_debut, date_fin)` | Agrège `{produit: {entree_nette, sortie}}` via FK produit + champs génériques |
| `formatter_ecart_pour_affichage(ecarts)` | Transforme le dict en liste de dicts `{produit_code, produit_nom, ecart, signe, classe_css}` pour le template |

---

### Signaux (`SGDS/signals.py`)

Chargés dans `SgdsConfig.ready()` via `from . import signals`.

| Signal | Déclencheur | Action |
|--------|------------|--------|
| `on_mesure_saved` | `post_save` sur `MesureCuve` | Recalcule `Cuve.niveau_actuel` + `Produit.stock_actuel` |
| `on_mesure_deleted` | `post_delete` sur `MesureCuve` | Idem — **fix bug** : stock ne restait plus figé après suppression |
| `on_jaugeage_deleted` | `post_delete` sur `JaugeageJour` | `recalculer_tous_stocks()` — les mesures étant supprimées en cascade, un recalcul global est nécessaire |
| `on_ligne_mouvement_changed` | `post_save` + `post_delete` sur `LigneMouvement` | Recalcule `Cuve.niveau_actuel` + `Produit.stock_actuel` pour la cuve affectée — déclenché à chaque création/modification/suppression d'une ligne |
| `on_mouvement_saved` | `post_save` sur `Mouvement` | Recalcule les cuves de toutes les lignes du mouvement — couvre les cas où l'entête change (ex: `type_mouvement` ENTREE→SORTIE) sans modification des lignes |

---

### Template Tags (`SGDS/templatetags/periode_tags.py`)

```python
{% load periode_tags %}
```

| Tag | Template inclus | Description |
|-----|----------------|-------------|
| `{% bandeau_periode %}` | `includes/bandeau_periode.html` | Bandeau rouge pleine largeur si aucune période ouverte ce mois. Invisible si période ouverte. Contexte : `periode_ouverte`, `mois_courant`, `request` |
| `{% periode_indicateur %}` | `includes/periode_indicateur.html` | Badge dropdown dans la topbar. Vert `📅 Mois Année` si ouvert, rouge `⚠️ Aucune période` sinon. Contexte : `periode` (ouverte), `derniere` (toute dernière période en base), `request` |

---

### Views (package `SGDS/views/`)

> ⚠️ **Architecture importante** : `SGDS/views/` est un **package Python** (dossier avec `__init__.py`). Il prend le dessus sur l'ancien fichier `SGDS/views.py` (toujours présent mais **ignoré par Python**). Toutes les nouvelles vues doivent aller dans `views/coulage.py` (ou un nouveau sous-module) et être réexportées depuis `views/__init__.py`.

#### `views/periode.py` + `views/coulage.py` — CBVs

| Classe | Fichier | Type | `test_func` | Description |
|--------|---------|------|------------|-------------|
| `ListePeriodesView` | `periode.py` | `LoginRequired + ListView` | — | Liste chronologique des périodes. `paginate_by=24`. Context : `peut_ouvrir_suivante`, `premiere_periode`, `mois_a_ouvrir`, `annee_a_ouvrir` |
| `OuvrirPeriodeView` | `periode.py` | `LoginRequired + UserPassesTest + View` | `is_staff` | GET : confirmation avec mois/annee proposé. POST : appelle `ouvrir_periode()`, messages.success/error |
| `ListePeriodesCoulageView` | `coulage.py` | `LoginRequired + ListView` | — | Liste des périodes avec statut coulage (`select_related('cloture_coulage')`). Context : `produits_actifs_list` (pour le menu déroulant Suivi par produit) |
| `RepartitionCoulageView` | `coulage.py` | `LoginRequired + View` | — | GET : calcul live (`calculer_repartition_coulage`) si OUVERTE, snapshot (`_rapport_depuis_snapshot`) si CLOTUREE. Context : `rapport`, `source` ('LIVE'/'SNAPSHOT'), `peut_cloturer` |
| `ClotureCoulageView` | `coulage.py` | `LoginRequired + UserPassesTest + View` | `is_staff` | POST : appelle `cloturer_periode()`. GET : redirect vers `coulage_detail`. |
| `ExportCoulageExcelView` | `coulage.py` | `LoginRequired + View` | — | GET : génère `.xlsx` via `exporter_coulage_xlsx()`. Fonctionne en LIVE et SNAPSHOT. |
| `SuiviEvolutionView` | `coulage.py` | `LoginRequired + View` | — | GET : appelle `calculer_suivi_evolution(periode, produit)`, rend `coulage/suivi_evolution.html`. Context : `rapport`, `periode`, `produit`, `produits_actifs` (pour le sélecteur). |
| `ExportSuiviExcelView` | `coulage.py` | `LoginRequired + View` | — | GET : génère `.xlsx` via `exporter_suivi_xlsx()`, retourne le fichier en réponse. |
| `FraisPassageView` | `coulage.py` | `LoginRequired + View` | — | GET : appelle `calculer_frais_passage(periode)`, rend `coulage/frais_passage.html`. |
| `ExportFraisPassageExcelView` | `coulage.py` | `LoginRequired + View` | — | GET : génère `.xlsx` via `exporter_frais_passage_xlsx()`, retourne le fichier en réponse. |

**Fonction helper `_rapport_depuis_snapshot(cloture)`** — reconstruit le même dict que `calculer_repartition_coulage()` à partir de `ClotureCoulageMensuel`. Permet à `repartition.html` de fonctionner identiquement en live et snapshot.

---

### URLs (`SGDS/urls.py` — nouvelles routes)

| URL | Vue | Nom |
|-----|-----|-----|
| `/periodes/` | `ListePeriodesView` | `periode_liste` |
| `/periodes/ouvrir/` | `OuvrirPeriodeView` | `periode_ouvrir` |
| `/coulage/` | `ListePeriodesCoulageView` | `coulage_liste` |
| `/coulage/<int:periode_id>/` | `RepartitionCoulageView` | `coulage_detail` |
| `/coulage/<int:periode_id>/cloturer/` | `ClotureCoulageView` | `coulage_cloture` |
| `/coulage/<int:periode_id>/export/` | `ExportCoulageExcelView` | `coulage_export` |
| `/coulage/<int:periode_id>/suivi/<int:produit_id>/` | `SuiviEvolutionView` | `suivi_evolution` |
| `/coulage/<int:periode_id>/suivi/<int:produit_id>/export/` | `ExportSuiviExcelView` | `suivi_export` |
| `/coulage/<int:periode_id>/frais-passage/` | `FraisPassageView` | `frais_passage` |
| `/coulage/<int:periode_id>/frais-passage/export/` | `ExportFraisPassageExcelView` | `frais_passage_export` |

---

### Templates nouveaux

#### `templates/includes/bandeau_periode.html`
Affiché via `{% bandeau_periode %}` dans `base.html` (à l'intérieur de `<main class="main">`, avant `<header class="topbar">`).
- Visible uniquement quand `not periode_ouverte`
- Fond rouge `#dc2626`, texte blanc, lien navy vers `periode_liste` (staff) ou message contactez admin

#### `templates/includes/periode_indicateur.html`
Affiché via `{% periode_indicateur %}` dans la topbar de `base.html`.
- Bouton pill avec dropdown CSS/JS
- **Période ouverte** : pill vert `📅 Mois Année` → dropdown : "Consulter le coulage", "Clôturer la période" (staff uniquement, POST avec confirm JS), "Toutes les périodes"
- **Aucune période** : pill rouge `⚠️ Aucune période` → dropdown : "Clôturer [dernière période]" si elle est OUVERTE (staff), "Toutes les périodes", "Ouvrir une période" (staff)
- Fermeture au clic extérieur via `document.addEventListener('click', ...)`

#### `templates/periode/liste.html`
- Header avec bouton dynamique "Ouvrir [NomMois] [Année]" (visible staff + `peut_ouvrir_suivante`)
- Tableau : Période / Statut (badge vert/gris) / Date ouverture + heure / Date clôture + heure / Montant coulage / Action "Consulter →"
- Pagination 24 par page
- État vide contextuel (message différent staff vs non-staff)

#### `templates/periode/ouvrir_confirm.html`
- Hero card navy, résumé des effets de l'ouverture
- Sélecteur mois/année uniquement pour la première période (`{% if premiere %}`)
- Formulaire POST caché `mois` + `annee`
- Affichage erreurs via `messages`

#### `templates/coulage/liste_periodes.html`
- Liste des périodes avec lien vers `coulage_detail`
- **Mis à jour** : colonne "Actions" (renommée depuis "Action")
- Bouton **"Frais passage"** (teal) par période → `frais_passage`
- Bouton **"Suivi ▾"** (violet) par période → menu déroulant avec lien par produit actif (`suivi_evolution`). JS `toggleSuivi()` + fermeture au clic extérieur.

#### `templates/coulage/suivi_evolution.html` *(nouveau)*
- Sélecteur de produit (dropdown → redirect JS vers `suivi_evolution` du produit choisi)
- 4 KPI cards : Entrées brutes / Coulage réception / Sorties / P/G cumulé
- Tableau journalier colonnes par cuve : Date / Stock initial / Entrée brute / Coulage réception / Sortie / Stock comptable / Stock physique / P/G bac / P/G cumulé
- Lignes jaune sur les jours avec jaugeage (icône ⚖) — classe `row-jaugeage` (dark mode géré via CSS)
- P/G coloré vert (gain) / rouge (perte)
- Bouton "↓ Exporter Excel" → `suivi_export`
- **Dark mode** : `tr.row-jaugeage` → `rgba(202,138,4,.08)` ; `.jaugeage-legend-swatch` → fond ambre semi-transparent

#### `templates/Espace_Marketeur/dashboard.html` *(nouveau)*
- Extends `base.html`, block `nav_client_dashboard` actif
- Header marketeur : logo, statut badge, infos administratives
- Grille KPI : nb_entrees, nb_sorties, nb_cessions, nb produits en stock
- Stocks par produit : cards avec `stock_15c`, volume entrées/sorties
- Tableau des 10 derniers mouvements (type, produit, régime, volume, date)
- Tableau des frais de coulage récents (`ClotureCoulageLigne`)

#### `templates/Espace_Marketeur/mouvements.html` *(nouveau)*
- Extends `base.html`, block `nav_client_mouvements` actif
- Barre de filtres : type de mouvement, produit, régime douanier, date_debut, date_fin
- Tableau des mouvements paginé : N° enregistrement, type, produit, régime, volume @15°C, date

#### `templates/coulage/frais_passage.html` *(nouveau)*
- En-tête : tarif global + badges ambre par produit si `prix_passage` spécifique défini
- Résumé navy dégradé : volumes par produit + montant total
- Sections par mode de règlement (ESP-IMMEDIAT 💵 / VIREMENT 🏦 / CHEQUE 📄 / CREDIT 🕐)
- Tableau marketeurs : colonnes volume par produit + volume global + motif + PU moyen + montant
- Ligne sous-total par mode
- Barre total général en pied de page
- Bouton "↓ Exporter Excel" → `frais_passage_export`
- **Dark mode** : classes `.fp-mode-card`, `.fp-mode-head`, `.fp-row-alt`, `.fp-export-btn`, `.fp-pu-badge` extraites des inline styles — chacune avec un override `[data-theme="dark"]`

#### `templates/Produit/produit_form.html`
- **Mis à jour** : champ `prix_passage` ajouté entre `prix_unitaire` et `seuil_alerte`
- Label : "Frais de passage (FCFA/L) — optionnel"
- Hint : "Laissez vide pour appliquer le tarif global configuré dans les Paramètres de coulage"

#### `templates/Produit/produit_detail.html`
- **Mis à jour** : hero block — affiche `prix_passage` en vert (`#86efac`) si défini
- Info card — affiche `prix_passage` comme badge bleu monospace ou texte gris "Tarif global (ParametresCoulage)"

#### `templates/coulage/repartition.html`
- Tableau dynamique colonnes par produit (Entrée brut/coulage/nette + Sortie + Répartition coulage QP)
- KPI cards par produit (coefficient, P/G) + Volume global sorti + Montant total
- Badge source : "Calcul en temps réel" (vert) ou "Clôturée le..." (gris)
- Export Excel via `coulage_export`
- Bouton "🔒 Clôturer" → modal de confirmation (staff uniquement)
- **Fix modal** : `style="display:none"` au lieu de `class="hidden"` (`.hidden` non défini en CSS → modal s'affichait au chargement)
- Section dépliable `<details>` : méthodologie des coefficients

---

### Modifications `base.html`

1. **`{% load periode_tags %}`** ajouté après `<body>` (chargement du module template tags)
2. **`{% bandeau_periode %}`** placé dans `<main class="main">` avant `<header class="topbar">` — **pas** directement après `<body>` (body a `display:flex`, le bandeau devenait un élément flex côte-à-côte avec la sidebar au lieu de s'étendre en pleine largeur)
3. **`{% periode_indicateur %}`** ajouté dans la topbar à gauche des boutons icônes (`display:flex;align-items:center;gap:8px`)
4. Blocs nav ajoutés : `nav_coulage` (lien Coulage), `nav_periode` (lien Périodes)

---

### Tests (`SGDS/tests/` + `SGDS/tests_coulage.py`)

**`SGDS/tests/__init__.py`** — fichier vide pour faire du répertoire un package Python.

**`SGDS/tests_coulage.py`** — Tests des services coulage (separate du package tests/).

#### `TestSuiviEvolution` *(nouveau — 4 tests)*
- `test_stock_conserve_sans_mouvement` — stock initial reporté tel quel sans mouvement
- `test_stock_baisse_apres_sortie` — stock comptable décrémenté correctement après sortie
- `test_jaugeage_remplace_stock_pour_lendemain` — le `volume_ambiant_depot` du jaugeage devient le stock initial du jour suivant. **Note** : `volume_ambiant_depot` est une `@property` calculée (pas de setter). Pour la forcer en test, passer `v_a_saisi=Decimal('9500')` à `MesureCuve.objects.create()` (formule : `v_a_saisi + v_mn×surplus = v_a_saisi` quand `v_mn=0`).
- `test_pg_cumul_progression` — le P/G cumulé s'accumule correctement sur plusieurs jours

#### `TestFraisPassage` *(nouveau — 4 tests)*
- `test_groupement_par_mode` — les sorties sont groupées par `mode_reglement`
- `test_exclusion_marketeur_sans_sortie` — un marketeur sans sortie ce mois n'apparaît pas
- `test_sous_totaux_coherents` — somme des lignes = sous-total du mode
- `test_total_general_egal_somme_sous_totaux` — total général = somme de tous les sous-totaux

**`SGDS/tests/test_workflow_periode.py`** — 21 tests, tous passants (14.974s).

#### `WorkflowPeriodeTests`
- `test_creation_mouvement_sans_periode_ouverte_refusee` → `ValidationError`
- `test_creation_jaugeage_sans_periode_ouverte_refusee` → `ValidationError`
- `test_ouverture_premiere_periode_ok` → n'importe quel mois si aucune période
- `test_ouverture_periode_quand_precedente_ouverte_refusee` → jan OUVERTE, impossible d'ouvrir fév
- `test_ouverture_periode_non_chronologique_refusee` → jan CLOTUREE, impossible d'ouvrir mars
- `test_ouverture_mois_suivant_apres_cloture_ok` → jan CLOTUREE → fév OK
- `test_creation_mouvement_periode_cloturee_refusee` → CLOTUREE → `ValidationError`
- `test_creation_mouvement_periode_ouverte_ok` → OUVERTE → `clean()` passe
- `test_ouverture_periode_deja_existante_refusee` → doublon → `ValidationError`
- `test_cloture_sans_jaugeage_refusee` → pas de jaugeage → `ValidationError`

#### `RecalculStockTests`
- `test_stock_mis_a_jour_apres_mesure` → creux=500, HTT=5000 → niveau calculé correct
- `test_stock_zero_si_aucune_mesure` → 0 si pas de mesure
- `test_stock_recalcule_apres_suppression_mesure` → suppression → retour à 0
- `test_stock_produit_est_somme_cuves` → 2 cuves → stock = somme
- `test_stock_recalcule_apres_suppression_jaugeage` → suppression jaugeage → stocks = 0
- `test_recalcul_generique_tous_produits` → 3 produits (GO, KERO, FUEL) tous recalculés

#### `EcartJaugeagesTests`
- `test_ecart_vide_si_premier_jaugeage` → `{}` si pas de précédent
- `test_ecart_pertes_detectees` → même volume, pas de mouvements → écart = 0
- `test_ecart_avec_entree_sortie` → entrée=100, sortie=50, même stock phys → écart = -50
- `test_formatter_ecart_pour_affichage` → retourne liste avec `produit_code`, `ecart`, `signe`, `classe_css`
- `test_ecart_generique_produit_non_standard` → produit PETROLE fonctionne correctement

---

### Dépendances supplémentaires

```bash
pip install openpyxl   # Export Excel coulage (ExportCoulageExcelView)
# Version installée : openpyxl 3.1.5
```

---

### Règles architecture critiques

1. **Jamais de `get_or_create` sur `PeriodeComptable`** — création uniquement via `ouvrir_periode()`
2. **Générique** — tous les services bouclent sur `Produit.objects.all()`, jamais de code produit en dur (GASOIL, SUPER, etc.)
3. **`petroleum_calc.py` est figé** — ne jamais modifier, validé contre le classeur Excel de référence
4. **`{% localize off %}`** — obligatoire sur tout template avec `input[type=number]` + `Decimal` en `fr-fr`
5. **`update_fields`** — utilisé systématiquement pour les saves partiels (stocks, statut période)
6. **Clôture ne déclenche pas l'ouverture suivante** — l'utilisateur ouvre manuellement la période suivante depuis `periode_liste` ou le dropdown topbar
7. **`UserProfile` jamais en OneToOne vers `auth.User`** — toujours vers `settings.AUTH_USER_MODEL` (= `accounts.UtilisateurSGDS`)
8. **`AuditLog` est immuable** — admin désactive toute modification/suppression. Ne jamais utiliser `.delete()` sur AuditLog dans le code.
9. **Thread-locals pour l'audit** — `AuditContextMiddleware` est obligatoire dans MIDDLEWARE pour que les signaux d'audit aient accès à l'utilisateur courant et à l'IP. Sans lui, `source='SYSTEM'` et `user=None`.
10. **`accounts/urls.py` ne contient plus que l'auth** — `/utilisateurs/` est exclusivement géré par `SGDS/users/urls.py`

### Localization

- Language: French (`fr-fr`)
- Timezone: `Africa/Bamako`
- Country default: `Mali`
- Nationalité default: `Malien(ne)`
- Indicatif téléphonique : `+223`
- Domaine email : `.ml`
- Banques de référence : BDM-SA, BMS-SA, Coris Bank
- Format RCCM : `ML-BKO-YYYY-B-NNNNN`
- Format immatriculation : `00 ML NNNN A`

#### ⚠️ Bug séparateur décimal — `fr-fr` + `input[type=number]`

Django avec `LANGUAGE_CODE = 'fr-fr'` formate les `Decimal` avec une virgule (ex: `45000,00`). Les navigateurs rejettent ce format pour `input[type=number]` (qui exige un point) et affichent un champ vide.

**Symptôme** : en mode édition, tous les champs numériques (volumes, densités, températures) s'affichent vides même quand la base de données contient les valeurs.

**Fix appliqué** :
- `settings.py` : `USE_L10N = False` + `DECIMAL_SEPARATOR = '.'` + `USE_THOUSAND_SEPARATOR = False` (note : en Django 6.0, `USE_L10N` est ignoré au rendu — la correction réelle est dans le template).
- `templates/mouvements/saisie.html` : `{% load l10n %}` en tête du template + `{% localize off %}...{% endlocalize %}` wrappant l'intégralité du `<form>`. Cela force `.` comme séparateur décimal pour tous les `{{ form.field.value }}` du formulaire.
- **Règle** : tout template contenant des `input[type=number]` avec des valeurs `Decimal` en contexte `fr-fr` DOIT utiliser `{% load l10n %}{% localize off %}` autour du formulaire.

---

---

## Module RBAC + Audit Trail + SSO (`SGDS/users/`)

### Modèles (`SGDS/users/models.py`)

#### `Role(TextChoices)`
```python
SUPERADMIN = 'SUPERADMIN'
CHEF_DEPOT = 'CHEF_DEPOT'
OPERATEUR  = 'OPERATEUR'
COMPTABLE  = 'COMPTABLE'
LECTEUR    = 'LECTEUR'
```

#### `UserProfile`
Extension OneToOne de `settings.AUTH_USER_MODEL` (= `accounts.UtilisateurSGDS`).

- `user` — OneToOneField → `settings.AUTH_USER_MODEL` (`related_name='profile'`, CASCADE)
- `role` — CharField(choices=Role, défaut: `LECTEUR`) — **RBAC 5 rôles, indépendant du `UtilisateurSGDS.role` legacy**
- `telephone`, `poste` — informations professionnelles
- `photo` — ImageField(`users/photos/`, nullable)
- `actif` — BooleanField (contrôle RBAC — un profil inactif perd toutes les permissions)
- `derniere_ip` — GenericIPAddressField (mise à jour par `AuditContextMiddleware`)
- `notes_admin` — TextField nullable (visible admin uniquement)
- **Properties** :
  - `peut_ecrire` → SUPERADMIN / CHEF_DEPOT / OPERATEUR
  - `peut_cloturer_periode` → SUPERADMIN / CHEF_DEPOT
  - `peut_valider_jaugeage` → SUPERADMIN / CHEF_DEPOT / OPERATEUR
  - `peut_supprimer_mouvement` → SUPERADMIN / CHEF_DEPOT
  - `peut_gerer_utilisateurs` → SUPERADMIN seulement
  - `peut_voir_audit` → SUPERADMIN / CHEF_DEPOT / COMPTABLE
  - `peut_exporter` → SUPERADMIN / CHEF_DEPOT / COMPTABLE

#### `AuditLog`
Traçabilité complète, non-supprimable, non-modifiable (admin : `has_*_permission → False`).

- `horodatage` — auto_now_add
- `user` — FK → `settings.AUTH_USER_MODEL` (nullable, SET_NULL — log conservé si user supprimé)
- `user_username_snapshot` — CharField (snapshot au moment du log)
- `action` — CharField(choices) : `CREATE` / `UPDATE` / `DELETE` / `LOGIN` / `LOGOUT` / `LOGIN_FAILED`
- `objet_type`, `objet_id`, `objet_repr` — identification de l'objet modifié
- `description` — résumé lisible
- `ip_address`, `user_agent` — contexte réseau
- `source` — `WEB` / `ADMIN` / `API` / `SYSTEM`
- `changements` — JSONField `{"avant": {...}, "apres": {...}}` — diff avant/après pour UPDATE

---

### Managers (`SGDS/users/managers.py`)

```python
creer_utilisateur(username, email, password, role, prenom='', nom='', **profile_kwargs)
```
Crée `UtilisateurSGDS` + `UserProfile` de façon atomique. Déduit `is_staff=True` si rôle SUPERADMIN ou CHEF_DEPOT.

---

### Middleware (`SGDS/users/middleware.py`)

`AuditContextMiddleware` — stocke la requête courante dans `threading.local()`. Permet aux signaux Django (qui n'ont pas accès à `request`) de connaître l'utilisateur actif et l'IP.

```python
get_current_user()    # → UtilisateurSGDS | None
get_current_request() # → HttpRequest | None
```

---

### Signaux (`SGDS/users/signals.py`)

| Signal | Déclencheur | Action |
|--------|------------|--------|
| `creer_profil_utilisateur` | `post_save` sur AUTH_USER_MODEL (created=True) | Crée automatiquement un `UserProfile` pour tout nouvel utilisateur |
| `capturer_etat_avant` | `pre_save` sur modèles métier | Stocke l'état avant modification dans `_pre_save_state[pk]` |
| `auditer_modification` | `post_save` sur modèles métier | Logue CREATE ou UPDATE avec diff avant/après |
| `auditer_suppression` | `post_delete` sur modèles métier | Logue DELETE |
| `log_login` | `user_logged_in` | Logue LOGIN + met à jour `UserProfile.derniere_ip` |
| `log_logout` | `user_logged_out` | Logue LOGOUT |
| `log_login_failed` | `user_login_failed` | Logue LOGIN_FAILED |

`MODELS_AUDITES` — set de 15 noms de modèles surveillés : `Marketeur`, `Camion`, `Chauffeur`, `Famille`, `Produit`, `Cuve`, `ParametreJaugeageCuve`, `JaugeageJour`, `MesureCuve`, `Mouvement`, `LigneMouvement`, `PeriodeComptable`, `ClotureCoulageMensuel`, `ClotureCoulageProduit`, `ClotureCoulageLigne`.

---

### Template Tags (`SGDS/users/templatetags/user_tags.py`)

Usage : `{% load user_tags %}` dans base.html et les templates users/.

| Tag / Filtre | Signature | Description |
|---|---|---|
| `role_badge` | `{% role_badge user %}` (inclusion_tag) | Rend `users/partials/role_badge.html` — badge span coloré selon rôle RBAC |
| `has_role` | `{% has_role user 'ROLE1' 'ROLE2' as var %}` (simple_tag) | True si `user.profile.role` est dans les rôles donnés ET `profile.actif` |
| `action_icon` | `value\|action_icon` (filter) | Emoji selon type d'action AuditLog |
| `action_badge_style` | `value\|action_badge_style` (filter) | Style CSS inline selon type d'action |

---

### SSO (`SGDS/users/adapters.py`)

`SGDSSocialAccountAdapter(DefaultSocialAccountAdapter)` :
- `pre_social_login()` — si l'email Google/Microsoft n'est pas déjà en base → `ImmediateHttpResponse` (403)
- Si l'email existe → `sociallogin.connect(request, user)` — lie le compte SSO au compte existant
- **Résultat** : seuls les utilisateurs pré-enregistrés peuvent se connecter via SSO

---

### Template Tags — Modifications `base.html`

1. `{% load user_tags %}` ajouté après `{% load periode_tags %}`
2. Section Administration remplacée : logique RBAC avec `{% has_role request.user 'SUPERADMIN' as is_sa %}` + `{% has_role request.user 'SUPERADMIN' 'CHEF_DEPOT' as is_cd %}`
3. Lien profil footer sidebar → `{% url 'users_mon_profil' %}`
4. Lien profil topbar → `{% url 'users_mon_profil' %}`
5. `{% role_badge request.user %}` ajouté dans le footer sidebar après `.user-role`

---

## Correctifs récents (2026-04-21)

### 1. `views/__init__.py` — `mouvement_calcul_preview` manquante

**Problème** : `SGDS/views/` est un package Python (dossier) et `SGDS/views.py` est un fichier. Python charge toujours le package et ignore `views.py`. La vue `mouvement_calcul_preview` était définie uniquement dans `views.py` (ignoré) et absente de `views/__init__.py`.

**Correction** :
- Ajout de `from django.views.decorators.http import require_POST` dans les imports de `views/__init__.py`
- Copie de la fonction `mouvement_calcul_preview` dans `views/__init__.py` (avant les imports de `coulage.py` et `periode.py`)

> ⚠️ **Règle** : toutes les nouvelles vues SGDS doivent être dans `views/__init__.py` (ou un sous-module réexporté). `views.py` est définitivement ignoré.

---

### 2. `services/recalcul_stock.py` — mouvements n'impactaient pas le stock

**Problème** : `recalculer_stock_cuve` ne regardait que la dernière mesure de jaugeage. Les mouvements ENTREE/SORTIE ne modifiaient donc jamais `Cuve.niveau_actuel` ni `Produit.stock_actuel`.

**Correction dans `recalculer_stock_cuve`** :
```
niveau_actuel = dernier_jaugeage_volume
              + Σ(LigneMouvement ENTREE après ce jaugeage)
              − Σ(LigneMouvement SORTIE après ce jaugeage)
```
- Utilise `mouvement__date_mouvement__gt=date_jaugeage` (strictement postérieur) pour éviter le double-comptage avec le jaugeage
- Si aucun jaugeage : base = 0, tous les mouvements comptent
- CESSION et ACQUITTEMENT ignorés (pas de mouvement physique de stock)

---

### 3. `signals.py` — signaux mouvements inactifs

**Problème** : `on_mouvement_changed` était un `pass` vide. Les `LigneMouvement` n'avaient aucun signal.

**Correction** :
- Ajout du signal `on_ligne_mouvement_changed` sur `post_save` + `post_delete` de `LigneMouvement` → recalcule la cuve et le produit de la ligne concernée
- Remplacement de `on_mouvement_changed` par `on_mouvement_saved` sur `post_save` de `Mouvement` → recalcule toutes les cuves des lignes (couvre le cas où `type_mouvement` change sans toucher les lignes)
- Import de `LigneMouvement` ajouté dans `signals.py`

---

### 4. `views/__init__.py` — `mouvement_modifier` restait sur la même page

**Problème** : après modification réussie, la vue faisait `redirect('mouvement_modifier', pk=...)` (retour sur la page d'édition).

**Correction** : redirect vers `mouvement_detail` après sauvegarde.

---

### 5. `templates/base.html` — messages de succès ne disparaissaient pas sur toutes les pages

**Problème** : le script ciblait `.js-alert` mais la plupart des templates (dont `saisie.html`) rendaient leurs propres alertes sans cette classe.

**Correction** : le script cible maintenant `.alert-success` — s'applique automatiquement à **tous** les messages de succès sur **toutes** les pages, sans classe supplémentaire requise.

```javascript
document.querySelectorAll('.alert-success').forEach(function(el){ ... });
```

---

### 6. `templates/mouvements/saisie.html` — preview SORTIE absente, ENTREE améliorée

**Problèmes** :
- La section "Contrôle automatique (API MPMS)" de la SORTIE n'avait pas d'IDs sur ses spans → aucune mise à jour live possible
- Le JS de preview ne gérait que le type ENTREE
- La preview ne se déclenchait pas quand l'utilisateur changeait de type

**Corrections** :
- Ajout d'IDs sur les 3 spans SORTIE : `pv-sortie-vcf`, `pv-sortie-volume-15c`, `pv-sortie-poids`
- Refonte du bloc JS de preview : gestion unifiée ENTREE et SORTIE, champs déclencheurs distincts par type, délai réduit à 600ms
- Déclenchement au clic sur les boutons de type (avec délai 200ms)
- Déclenchement au chargement si `type === 'ENTREE'` ou `type === 'SORTIE'` (mode modification avec valeurs pré-remplies)

---

## Correctifs récents (2026-04-23)

### 1. `services/suivi_evolution.py` — suivi coulage ne reflétait pas un changement de produit

**Problème** : `calculer_suivi_evolution` filtrait les `LigneMouvement` via le champ dénormalisé `LigneMouvement.produit` (`produit=produit`). Quand l'utilisateur modifiait un mouvement et changeait le produit (ex: GASOIL → SUPER), le JS vidait la cuve sélectionnée (via `onProduitChange()`). La ligne était alors sauvegardée avec `cuve=None, produit=SUPER`. Le filtre `cuve__in=cuves` (cuves actives du produit) excluait les lignes sans cuve → les données disparaissaient des deux suivis (ni GASOIL ni SUPER).

**Correction dans `services/suivi_evolution.py`** :
```python
# Avant (champ dénormalisé, potentiellement obsolète)
LigneMouvement.objects.filter(produit=produit, cuve__in=cuves, ...)

# Après (champ autoritatif sur Mouvement)
LigneMouvement.objects.filter(mouvement__produit=produit, cuve__in=cuves, ...)
```
`Mouvement.produit` est toujours à jour lors d'une modification. On ne dépend plus de `LigneMouvement.produit` qui peut être stale.

---

### 2. `views/__init__.py` — `mouvement_modifier` ne synchronisait pas le produit dénormalisé

**Problème** : dans `mouvement_modifier`, après le `form.save()`, le formset traitait uniquement les lignes explicitement soumises avec cuve ou volume. Si la cuve était vidée par le JS (changement de produit), la condition `cuve or volume_ambiant` pouvait échouer pour certaines lignes → `LigneMouvement.produit` restait à l'ancienne valeur (ex: GASOIL) alors que `Mouvement.produit` était à jour (SUPER).

**Correction dans `views/__init__.py` — `mouvement_modifier`** :
```python
# Après la boucle de traitement du formset :
LigneMouvement.objects.filter(mouvement=mouvement).update(produit=mouvement.produit)
```
Force la synchronisation du champ dénormalisé sur toutes les lignes restantes, quelle que soit la façon dont le formset a été soumis.

> ⚠️ **Rappel** : `views.py` est ignoré par Python (shadowed par le package `views/`). Toujours modifier `views/__init__.py`.

---

### 3. `templates/coulage/liste_periodes.html` — dropdown "Suivi ▾" totalement invisible

**Problème** : le `<div>` conteneur du tableau avait `overflow:hidden` (nécessaire pour clipper les coins arrondis de la `<thead>`). Or `overflow:hidden` clippe **aussi** les enfants `position:absolute` qui débordent du conteneur, même quand leur ancêtre positionné (`position:relative`) est différent. Le dropdown `#suivi-<pk>` (position:absolute, top:110%) s'affichait donc en dehors des limites visuelles du div et était tronqué → invisible.

**Correction dans `templates/coulage/liste_periodes.html`** :
- Suppression de `overflow:hidden` sur le conteneur tableau
- Ajout de `border:1px solid #e2e8f0` pour maintenir la délimitation visuelle
- Ajout de `border-top-left-radius:.625rem` / `border-top-right-radius:.625rem` sur le premier et le dernier `<th>` de la `<thead>` pour recréer les coins arrondis (remplace le clipping CSS)

```html
<!-- Avant -->
<div style="...;overflow:hidden;">
  <table>
    <thead>
      <tr>
        <th style="padding:.75rem 1rem;...">Période</th>
        ...
        <th style="padding:.75rem 1rem;...">Actions</th>
      </tr>

<!-- Après -->
<div style="...;border:1px solid #e2e8f0;">   <!-- overflow:hidden supprimé -->
  <table>
    <thead>
      <tr>
        <th style="padding:.75rem 1rem;...;border-top-left-radius:.625rem;">Période</th>
        ...
        <th style="padding:.75rem 1rem;...;border-top-right-radius:.625rem;">Actions</th>
      </tr>
```

---

## Correctifs et ajouts (2026-04-25)

### 1. Refactoring Mouvement → LigneMouvement (multi-cuves)

**Contexte** : un `Mouvement` ne pouvait lier qu'une seule cuve via FK directe. Pour gérer les répartitions sur plusieurs cuves, un modèle `LigneMouvement` a été ajouté.

- **`SGDS/models.py`** : ajout de `LigneMouvement` (FK→Mouvement, FK→Cuve, produit dénormalisé, volume_ambiant, volume_15c, ordre)
- **`SGDS/forms.py`** : `LigneMouvementForm` + `LigneMouvementFormSet` (inlineformset_factory)
- **`SGDS/admin.py`** : `LigneMouvementInline` ajouté à `MouvementAdmin`
- **`SGDS/views/__init__.py`** : `mouvement_creer` et `mouvement_modifier` traitent désormais le formset
- **Migrations** : `0015_lignemouvement` + `0016_data_migration_lignes_mouvement` (RunPython)

### 2. MesureCuve — saisie V(A) manuelle

**Contexte** : l'opérateur doit pouvoir saisir le volume ambiant directement (sans passer par la formule de calcul).

- **`SGDS/models.py`** : ajout `v_a_saisi` (DecimalField nullable) sur `MesureCuve`
- La property `volume_ambiant_bac` retourne `v_a_saisi` en priorité, sinon calcul formule
- **Migration** : `0003_mesurecuve_v_a_saisi`

### 3. Produit — stock en temps réel

- **`SGDS/models.py`** : ajout `stock_actuel` (DecimalField, défaut:0) et `date_maj_stock` (DateTimeField nullable) sur `Produit`
- Classmethod `mettre_a_jour_stocks()` — recalcule `stock_actuel` pour un ou tous les produits via agrégation sur `LigneMouvement`
- Signaux `post_save/post_delete` sur `LigneMouvement` déclenchent `mettre_a_jour_stocks()`
- **Migration** : `0010_ajout_stock_actuel_produit`

### 4. JaugeageJour — workflow de validation

- **`SGDS/models.py`** : ajout `est_valide` (BooleanField, défaut:False), `date_validation` (DateTimeField nullable), `valide_par` (FK→AUTH_USER_MODEL, nullable) sur `JaugeageJour`
- Permet un circuit de validation : saisie → validation par responsable → mesures gelées
- **Migration** : `0004_jaugeagejour_date_validation_jaugeagejour_est_valide_and_more`

### 5. StockOuverture + StockOuvertureCuve

- Nouveaux modèles pour stocker les stocks à l'ouverture de chaque `PeriodeComptable`
- `StockOuverture` : par produit, `StockOuvertureCuve` : par cuve avec référence à `MesureCuve`
- `calcul_auto=False` protège les valeurs saisies manuellement de l'écrasement automatique
- **Migration** : `0011_coulage_models`

### 6. Espace Marketeur

- **Nouveau fichier** `SGDS/views/client.py` : vues réservées au rôle MARKETEUR
- Décorateur `@marketeur_required` (contrôle `is_marketeur_role + marketeur lié`)
- `client_dashboard` : tableau de bord avec stocks calculés, KPIs, derniers mouvements, frais coulage
- `client_mouvements` : liste filtrée des mouvements du marketeur
- **Nouveaux templates** : `Espace_Marketeur/dashboard.html`, `Espace_Marketeur/mouvements.html`
- **`SGDS/urls.py`** : routes `/mon-espace/` et `/mon-espace/mouvements/` ajoutées en tête de fichier

### 7. base.html — sidebar conditionnelle MARKETEUR

- Navigation différenciée : MARKETEUR voit uniquement *Mon Espace* (tableau de bord, mouvements, fiche)
- Staff/admin voit la sidebar complète habituelle
- Blocs ajoutés : `nav_client_dashboard`, `nav_client_mouvements`, `nav_client_fiche`

### 8. accounts/views.py — redirection connexion MARKETEUR

- **Avant** : MARKETEUR redirigé vers `marketeur_detail(pk=...)`
- **Après** : MARKETEUR redirigé vers `client_dashboard` (espace dédié)

---

## Migration Design System (2026-05-02)

### Contexte

Migration CSS-first complète de tous les templates HTML vers un design system unifié. **Règle absolue : aucune modification côté Python** (models.py, views.py, forms.py, urls.py intacts). Seuls les templates HTML et les assets CSS ont été modifiés.

**Direction visuelle** : ERP industriel raffiné — warm neutrals + burnt amber, Inter + JetBrains Mono pour les données numériques.

---

### Fichier CSS principal : `static/css/sgds.css`

#### Variables CSS (design tokens)

```css
--bg:       #f7f6f2   /* fond page (warm off-white) */
--surface:  #fff      /* fond carte / modal */
--ink:      #1a1814   /* texte principal */
--muted:    #6b6660   /* texte secondaire */
--border:   #e4e0d8   /* séparateurs */
--accent:   #b8541a   /* couleur marque (burnt amber) */
--accent-2: #d4703a   /* variante claire accent */
--ok:       #3f7d3a   /* vert succès */
--warn:     #a86b00   /* ambre avertissement */
--err:      #a8331c   /* rouge erreur */
--info:     #2a5b8a   /* bleu information */
```

#### Alias de compatibilité (bridge) — lignes 619–741 de `sgds.css`

Ces alias permettent aux anciens templates utilisant les variables "legacy" de fonctionner automatiquement avec le nouveau design sans réécriture :

```css
--navy:     var(--ink)        /* remplace l'ancien bleu navy #1E3A5F */
--orange:   var(--accent)     /* remplace l'ancien orange #E8760A */
--card:     var(--surface)
--navy-l:   var(--accent)
--orange-l: var(--accent-2)
--text:     var(--ink)
--radius:   10px
--shadow:   0 1px 4px rgba(0,0,0,.07)
```

> **Conséquence** : tout template utilisant `var(--navy)` ou `var(--orange)` affiche automatiquement les bonnes couleurs du nouveau design. Seuls les hexadécimaux hardcodés (`#1E3A5F`, `#E8760A`, etc.) nécessitaient une intervention manuelle.

#### Classes de composants disponibles dans `sgds.css`

| Classe | Usage |
|--------|-------|
| `.ph` / `.ph-title` / `.ph-sub` / `.ph-actions` | En-tête de page (page header) |
| `.card` | Conteneur carte avec fond `var(--surface)` |
| `.tbl` | Table de données standardisée |
| `.kpi-strip` / `.kpi` / `.kpi-label` / `.kpi-val` | Bande de KPIs |
| `.filter-bar` | Barre de filtres (à placer **à l'intérieur** de `.card`) |
| `.bdg` / `.bdg.ok` / `.bdg.warn` / `.bdg.err` / `.bdg.muted` | Badges de statut |
| `.bdg-type.entree` / `.sortie` / `.cession` / `.acquit` | Badges type mouvement |
| `.btn-accent` / `.btn-ghost` / `.btn-sm` | Boutons |
| `.detail-card` / `.detail-card-header` / `.detail-card-body` | Carte détail |
| `.detail-field` / `.detail-label` / `.detail-value` | Champ de détail |
| `.dg-2` / `.dg-3` / `.dg-4` | Grilles auto-fit (2/3/4 colonnes) |
| `.pagination` | Contrôles de pagination |
| `.field` / `.field-label` / `.field-input` | Champs de formulaire |
| `.select` / `.input` | Inputs standardisés |
| `.mono` / `.num` / `.tar` | Utilitaires typographie/alignement |
| `.page-header` / `.page-title` / `.page-subtitle` | Alias bridge → `.ph*` |
| `.btn-primary` / `.btn-secondary` | Alias bridge → `.btn-accent` / `.btn-ghost` |

**Règle de structure critique** : le `.filter-bar` (avec son `<form>`) doit être à l'intérieur du même `.card` que le `<table class="tbl">`. Mettre le filtre en dehors du `.card` casse le rendu visuel.

---

### Polices

| Usage | Police | Variable / Classe |
|-------|--------|-------------------|
| Interface générale | **Inter** (Google Fonts) | `font-family: inherit` — hérite du body |
| Données numériques, codes | **JetBrains Mono** | `font-family: 'JetBrains Mono', monospace` ou classe `.mono` |

- **`Sora`** : supprimée de tous les templates — remplacée par `inherit` (contextes heading/label) ou `'JetBrains Mono',monospace` (contextes numériques)
- **`DM Sans`** : supprimée de tous les templates — remplacée par `inherit`

---

### Templates exclus (intentionnellement non modifiés)

Ces templates ont des styles print-specific qui ne doivent pas être altérés :

| Fichier | Raison |
|---------|--------|
| `templates/partials/_print_css.html` | CSS d'impression A4, couleurs hardcodées pour la fidélité papier |
| `templates/partials/_print_header.html` | En-tête imprimable avec logo et métadonnées |
| `templates/Chauffeur/chauffeur_badge.html` | Badge QR standalone 54×85.6mm, `@media print` dédié |

---

### Templates entièrement réécrits (refonte structurelle)

| Template | Avant | Après |
|----------|-------|-------|
| `templates/periode/liste.html` | Inline styles + `#1E3A5F` | `.ph`, `.card`, `.tbl`, `.bdg ok/muted`, `.pagination` |
| `templates/periode/ouvrir_confirm.html` | Carte custom inline | `.card` centré, header `var(--ink)` + overlay `var(--accent)`, `.select`, `.btn-accent`/`.btn-ghost` |
| `templates/coulage/liste_periodes.html` | Custom styles | `.ph`, `.card`, `.tbl`, `.bdg`, `.pagination`. JS `toggleSuivi()` préservé |
| `templates/coulage/repartition.html` | `#1E3A5F` partout, custom KPI cards | `.ph`, `.kpi-strip`, `.card`, `.tbl`, header `var(--ink)`, modal `var(--surface)`. JS modal préservé |
| `templates/coulage/suivi_evolution.html` | Custom styles + `#1E3A5F` | `.ph`, `.kpi-strip`, `.card` overflow-x:auto, header `var(--ink)` |
| `templates/Users/liste.html` | `<style>` custom `.stat-strip`, `.users-table-wrap` | `.ph`, `.kpi-strip`, `.card`, `.filter-bar`, `.tbl`, `.bdg ok/muted`, `.pagination` |
| `templates/Users/creer.html` | Grand `<style>` custom | Header `var(--ink)` + gradient, `.dg-2`, `.field*`, grille rôles `.role-option` |
| `templates/Users/detail.html` | `<style>` custom `.detail-layout`, `.hero-card` | Grid 2 colonnes, `.card` header `var(--ink)`, `.detail-card*`, `.tbl` audit |
| `templates/Users/mon_profil.html` | Grand `<style>` custom | Grid 2 colonnes, `.card` sidebar + form, `.dg-2`, `.field*`, `.btn-ghost`/`.btn-accent` |
| `templates/Users/audit_log.html` | Grand `<style>` custom | `.ph`, `.kpi-strip`, `.card`, `.filter-bar`, `.tbl` expandable. `extra_head` minimal conservé |
| `templates/Espace_Marketeur/dashboard.html` | Massif `<style>` custom, font Sora | `.card` header marketeur, `.kpi-strip`, grid stock, `.card`/`.tbl` mouvements/coulage |
| `templates/Espace_Marketeur/mouvements.html` | `<style>` custom, `.btn-filter` navy, `.badge-ENTREE` | `.ph`, `.kpi-strip`, `.card`, `.filter-bar`, `.tbl`, `.bdg-type`, `.pagination` |

---

### Templates corrigés par remplacement ciblé (couleurs hardcodées)

Les templates ci-dessous utilisaient déjà les alias bridge (`var(--navy)`, `var(--orange)`) et n'avaient besoin que d'un remplacement des hex hardcodés :

#### Couleurs navies remplacées (`#1E3A5F`, `#2a5285`, `#1d3461`, `#1a3d6b`, `#0e4f8a`, `#1a2744`) → `var(--ink)`

| Template |
|----------|
| `templates/coulage/frais_passage.html` |
| `templates/Societe/detail.html` |
| `templates/Jaugeage/jaugeage_saisie.html` |
| `templates/Jaugeage/jaugeage_rapport.html` |
| `templates/Etat/stock_global.html` |
| `templates/Etat/mensuel/global_depot.html` |
| `templates/Cuve/cuve_form.html` |
| `templates/Cuve/cuve_confirm_delete.html` |
| `templates/Jaugeage/parametres_metrologiques.html` |
| `templates/mouvements/detail.html` |
| `templates/mouvements/saisie.html` |
| `templates/ParametreJaugeage/parametre_form.html` |
| `templates/Users/roles_liste.html` |
| `templates/Users/role_form.html` |
| `templates/Users/permissions_liste.html` |
| `templates/Users/role_detail.html` |

#### Accent orange `#E8760A` → `var(--accent)`

| Template |
|----------|
| `templates/admin/jaugeage_change_list.html` |
| `templates/coulage/frais_passage.html` |
| `templates/Cuve/cuve_confirm_delete.html` |
| `templates/Cuve/cuve_form.html` |
| `templates/Jaugeage/jaugeage_rapport.html` |
| `templates/Jaugeage/parametres_metrologiques.html` |

#### Table header dark slate `background:#334155;color:#fff` → `background:var(--ink);color:#fff`

| Template |
|----------|
| `templates/coulage/frais_passage.html` |

---

### Remplacement polices (bulk PowerShell)

Opérations effectuées sur tous les templates **sauf** les 3 exclus print/badge :

| Avant | Après | Contexte |
|-------|-------|---------|
| `'Sora',sans-serif` | `inherit` | Titres, labels (cascade vers Inter) |
| `'Sora',monospace` | `'JetBrains Mono',monospace` | Valeurs numériques, codes |
| `'DM Sans',sans-serif` | `inherit` | Tous contextes |
| `'DM Sans', sans-serif` | `inherit` | Variante avec espace |

**Templates concernés (liste représentative)** : `Camion/camion_detail.html`, `Camion/camion_list.html`, `Chauffeur/chauffeur_detail.html`, `Chauffeur/chauffeur_list.html`, `Cuve/cuve_form.html`, `Cuve/cuve_confirm_delete.html`, `Etat/stock_global.html`, `Etat/mensuel/*` (8 fichiers), `Espace_Marketeur/carte_stock.html`, `Espace_Marketeur/stock_global.html`, `Espace_Marketeur/mensuel/*` (4 fichiers), `Jaugeage/jaugeage_rapport.html`, `Jaugeage/jaugeage_saisie.html`, `Jaugeage/parametres_metrologiques.html`, `ParametreJaugeage/*` (4 fichiers), `Users/roles_liste.html`, `Users/role_form.html`, `Users/role_detail.html`, `Users/permissions_liste.html`, `Users/partials/role_badge.html`, `Auth/logout_confirm.html`, `Produit/produit_detail.html`, `Users/modifier.html`.

---

### Corrections structurelles filter-bar

Trois templates avaient le filtre **en dehors** du `.card` wrapper, ce qui cassait le rendu. Corrigés en enveloppant le `<form method="get">` (contenant `.filter-bar`) et le `<table class="tbl">` dans un unique `<div class="card">` :

| Template |
|----------|
| `templates/Produit/produit_list.html` |
| `templates/Camion/camion_list.html` |
| `templates/Marketeur/marketeur_list.html` |

---

### Règles de développement UI (post-migration)

1. **Jamais de couleur hardcodée brand** (`#1E3A5F`, `#E8760A`, `#1a2744`...) — toujours utiliser les variables CSS.
2. **Police** : ne pas spécifier `font-family` pour l'interface ; utiliser `inherit`. Pour les nombres, chiffres ou codes : `font-family:'JetBrains Mono',monospace` ou classe `.mono`.
3. **Filter bar inside card** : `<div class="card"><form><div class="filter-bar">...</div></form><table class="tbl">...</table></div>`.
4. **Badges** : `.bdg ok` (vert), `.bdg warn` (ambre), `.bdg err` (rouge), `.bdg muted` (gris). Pour les types mouvements : `.bdg-type entree/sortie/cession/acquit`.
5. **Boutons** : `.btn-accent` (primaire filled), `.btn-ghost` (secondaire outline), `.btn-sm` (petit).
6. **Print templates** : ne jamais modifier `_print_css.html`, `_print_header.html`, `chauffeur_badge.html`.
7. **Aucune modification Python** pour les changements purement visuels.

---

## Dark Mode — Implémentation (2026-05-14)

### Mécanisme

Le dark mode est activé par l'attribut `data-theme="dark"` sur la balise `<html>`. Le toggle est géré côté JS (topbar) et persiste en `localStorage`. Les variables CSS surchargées sont définies dans `static/css/sgds.css` à partir de la ligne ~1198 :

```css
[data-theme="dark"] {
  --bg:          #111110;
  --surface:     #1c1a17;
  --surface-2:   #242118;
  --border:      #2e2b24;
  --border-2:    #3c3830;
  --ink:         #ede9e0;
  --ink-2:       #c8c2b4;
  --muted:       #7a7468;
  --accent:      #d4681f;
  --accent-2:    #e8782a;
  --accent-soft: #2a1808;
  --accent-ink:  #f0a878;   /* remplace var(--navy) pour le texte en dark */
  --ok:          #4cac46;   --ok-soft:   #0d1f0c;
  --warn:        #cc8800;   --warn-soft: #1e1400;
  --err:         #cc4030;   --err-soft:  #220806;
  --info:        #4080b8;   --info-soft: #0a1520;
}
```

**Règle** : ne jamais modifier `sgds.css` pour les overrides dark mode spécifiques à un template. Ajouter un bloc `[data-theme="dark"] { ... }` à la fin du `{% block extra_head %}` de chaque template concerné.

---

### Palette dark utilisée dans les overrides templates

| Usage | Variable light | Variable dark |
|-------|----------------|---------------|
| Texte d'accent (remplace `--navy`) | `var(--navy)` → `var(--ink)` | `var(--accent-ink)` |
| Fond sémantique vert | `#dcfce7` | `var(--ok-soft)` |
| Texte sémantique vert | `#16a34a` | `var(--ok)` |
| Fond sémantique rouge | `#fee2e2` | `var(--err-soft)` |
| Texte sémantique rouge | `#dc2626` | `var(--err)` |
| Fond sémantique ambre | `#fef3c7` | `var(--warn-soft)` |
| Texte sémantique ambre | `#92400e` | `var(--warn)` |
| Fond sémantique bleu | `#dbeafe` | `var(--info-soft)` |
| Texte sémantique bleu | `#1e40af` | `var(--info)` |
| Fond section / surface | `var(--bg)` / `#f1f5f9` | `var(--surface-2)` |
| Hover ligne tableau | `rgba(240,244,248,.4)` | `rgba(255,255,255,.05)` |

---

### Templates avec dark mode implémenté (25 fichiers)

#### `Etat/` (10 templates)

| Template | Éléments corrigés |
|----------|-------------------|
| `Etat/carte_stock_admin.html` | badges, row-*, cumul-chips (`.green/.red/.amber`), `.ch-value`, btn-export-main extrait d'inline |
| `Etat/stock_global.html` | idem + `.badge-sdac`, `.badge-mkt`, `.num-warn` |
| `Etat/mensuel/coulage_repartition.html` | `.source-snapshot`, `.source-realtime`, `.alert-warning`, `tr.total-row` |
| `Etat/mensuel/frais_passage.html` | `.mode-title !important` (override inline style), `tr.sous-total`, `tr.grand-total` |
| `Etat/mensuel/global_depot.html` | `.section-{entree/sortie/cession/acquittement} .section-title`, `.badge-sd`, `.badge-ac`, btn-export-main local |
| `Etat/mensuel/stock_mensuel_a.html` | `tr.total-row`, `tr:nth-child(even)`, `.num-neg`, `.num-pos` |
| `Etat/mensuel/stock_mensuel_b.html` | row-colors pivot, `td.row-label`, `.num-neg/.num-pos` ; inline `style="color:#16a34a"` → `class="num-pos"` |
| `Etat/mensuel/stock_ouverture.html` | `.section-header`, `.total-row`, `.stock-fin-row`, `.physique-row`, `.perte-row`, `.gain-row` |
| `Etat/mensuel/stock_fermeture.html` | idem stock_ouverture |
| `Etat/mensuel/rjj.html` | `.badge-valide`, `.badge-non-valide`, `.clickable-row:hover` |

#### `Espace_Marketeur/` (6 templates)

| Template | Éléments corrigés |
|----------|-------------------|
| `Espace_Marketeur/carte_stock.html` | idem `Etat/carte_stock_admin` + `.regime-tab.active-sd/.active-ac` ; btn-export-main défini localement |
| `Espace_Marketeur/stock_global.html` | idem `Etat/stock_global` sans `.badge-mkt` |
| `Espace_Marketeur/mensuel/coulage_repartition.html` | idem Etat |
| `Espace_Marketeur/mensuel/frais_passage.html` | `.mode-title !important`, `.chip-val` → `var(--accent-ink)` |
| `Espace_Marketeur/mensuel/stock_mensuel_a.html` | idem Etat |
| `Espace_Marketeur/mensuel/stock_mensuel_b.html` | idem Etat |

#### `mouvements/` (2 templates)

| Template | Éléments corrigés |
|----------|-------------------|
| `mouvements/detail.html` | Classes `.dcheader-entree/sortie/cession/acquittement/camion/notes` extraites des `style="background:#..."` inline sur `.detail-card-header`. `.modal-warn-box` (fond orange → `var(--warn-soft)`) et `.modal-type-badge` (fond rouge → `var(--err-soft)`) dans la modale de suppression. |
| `mouvements/saisie.html` | Classes `.fcheader-entree/sortie/cession/acquittement/cuves/camion/notes` extraites des inline styles sur `.form-card-header`. Dark : chaque header devient un tint semi-transparent de sa couleur sémantique. |

#### `coulage/` (2 templates)

| Template | Éléments corrigés |
|----------|-------------------|
| `coulage/frais_passage.html` | Classes `.fp-export-btn`, `.fp-pu-badge`, `.fp-mode-card`, `.fp-mode-head`, `.fp-row-alt` extraites des inline styles omniprésents. Dark : `var(--card)`, `var(--surface-2)`, `var(--warn-soft)`, `var(--ok)`. |
| `coulage/suivi_evolution.html` | `tr.row-jaugeage` extrait (`background:#fefce8` → classe, dark: `rgba(202,138,4,.08) !important`). `.jaugeage-legend-swatch` dark: `rgba(202,138,4,.15)`. |

#### `partials/_print_css.html`

Dark overrides globaux pour `.btn-print-main` (`var(--accent)`) et `.btn-export-main` (`var(--ok)`). La section `@media print` reste inchangée (couleurs fidèles au papier).

---

### Approche et règles dark mode

1. **Jamais modifier `sgds.css`** pour les overrides spécifiques — ajouter dans `{% block extra_head %} <style>` du template.
2. **Patron d'override** : ajouter un bloc `/* ── Dark mode ── */ [data-theme="dark"] { ... }` à la fin du `<style>` dans `{% block extra_head %}`.
3. **Inline styles** : pour les éléments avec `style="background:#hex"`, deux approches selon la complexité :
   - Ajouter une **classe** et utiliser `!important` en dark mode (`[data-theme="dark"] .ma-classe { background: var(...) !important }`)
   - Extraire vers une classe nommée et supprimer l'inline style (préférable quand plusieurs éléments partagent le même style)
4. **Django template conditionnels** : pour `{% if condition %}background:#hex{% endif %}` dans `style=`, ajouter `class="{% if condition %}ma-classe{% endif %}"` et gérer via CSS.
5. **`!important`** : utilisé uniquement pour écraser les inline styles HTML (attribut `style=`). Ne pas l'utiliser pour des overrides purement CSS-to-CSS.
6. **Section `@media print`** dans `_print_css.html` : ne jamais modifier — les couleurs y sont hardcodées intentionnellement pour la fidélité d'impression.

---

## App Mobile — sgds-mobile (Redesign v2.0) — 2026-05-07

### Localisation et commandes

```
Chemin   : Gestion_Dépôt/sgds-mobile/
Démarrer : cd Gestion_Dépôt/sgds-mobile && npx expo start
Tunnel   : npx expo start --tunnel   (réseau local impossible)
```

Stack : **Expo ~54 · React Native 0.81.5 · TypeScript · @react-navigation** (native-stack + bottom-tabs)

---

### Nouveaux packages installés

| Package | Version | Raison |
|---------|---------|--------|
| `expo-linear-gradient` | `~15.0.8` | Gradients hero sur tous les écrans v2 |
| `react-native-svg` | `15.12.1` | Disponible pour futurs graphes SVG |

```bash
# Installation via expo (gère les compatibilités Expo SDK automatiquement)
npx expo install expo-linear-gradient react-native-svg
```

---

### Nouveau système de design tokens — `src/constants/colors.ts`

Fichier entièrement réécrit. Nouvelle palette SGDS v2.0 :

```typescript
export const Colors = {
  // Palette principale
  navy: '#0E2A47',      navyDeep: '#081A2E',   navySoft: '#1B3F66',  navyTint: '#E8EEF6',
  orange: '#E67A2A',    orangeSoft: '#FFE3CC',  orangeDeep: '#B95A14',
  // Neutres
  ink: '#0B1220',       graphite: '#3A4150',   slate: '#6B7589',     silver: '#A8B0BF',
  mist: '#DDE2EC',      cloud: '#EFF2F7',      paper: '#F7F8FB',     white: '#FFFFFF',
  // Statuts
  green: '#1F9D55',     greenSoft: '#D8F3E2',
  red: '#D63B3B',       redSoft: '#FBE0E0',
  // Types mouvements
  entree: '#1F9D55',    sortie: '#D63B3B',
  cession: '#6E47C7',   acquittement: '#1497B8',
  // Aliases legacy (backward compat)
  primary: '#0E2A47',   primaryLight: '#1B3F66', primaryDark: '#081A2E', ...
} as const;

export const Radius = { sm: 8, md: 14, lg: 20, xl: 28, pill: 999 } as const;

export const FontSize = { xs: 10, sm: 12, md: 14, lg: 16, xl: 20, xxl: 26 } as const;
export const Spacing  = { xs: 4, sm: 8, md: 12, lg: 16, xl: 24 } as const;

// Métadonnées visuelles par type de mouvement
export const TypeMeta: Record<string, { label: string; color: string; soft: string; glyph: string }> = {
  ENTREE:        { label: 'Entrée',        color: Colors.entree,        soft: Colors.greenSoft,  glyph: '↓' },
  SORTIE:        { label: 'Sortie',        color: Colors.sortie,        soft: Colors.redSoft,    glyph: '↑' },
  CESSION:       { label: 'Cession',       color: Colors.cession,       soft: '#EDE9FA',         glyph: '⇄' },
  ACQUITTEMENT:  { label: 'Acquittement',  color: Colors.acquittement,  soft: '#D6F0F6',         glyph: '✓' },
};
```

---

### Fichiers modifiés (9 fichiers)

#### 1. `src/screens/Auth/LoginScreen.tsx`

Refonte complète. Structure : `SafeAreaView → KeyboardAvoidingView → ScrollView → [LinearGradient hero | View card]`.

- Hero gradient `navySoft → navy → navyDeep` avec 2 blobs décoratifs, logo badge orange, tagline *"Vos dépôts. En temps réel."*
- Card blanche overlap (`marginTop: -24`, `borderTopRadius: 28`) avec handle pill
- Composant `Field` avec état `focused` (bordure navy au focus, fond cloud → blanc)
- Biometric row statique (toggle visuel sans logique)
- `KeyboardAvoidingView` : `behavior='padding'` iOS / `'height'` Android, hero dans ScrollView pour éviter clipping

#### 2. `src/screens/Dashboard/DashboardScreen.tsx`

Refonte complète. Structure : `SafeAreaView → ScrollView → [LinearGradient hero | KPI grid | stock rows | gauges | activité]`.

- Hero gradient avec blob orange, avatar initiales, pill dépôt, total stock en grand
- KPI grid 2×2 flottant (`marginTop: -64`, `zIndex: 2`) : Entrées / Sorties / Mouvements / Produits
- Stocks par produit : `ProgressRow` avec barre de remplissage colorée (entree/sortie/cession)
- Gauges cuves : `GaugeMini` (track + fill animé-style)
- Activité récente : `ActivityRow` avec badge glyph coloré par `TypeMeta[mvt.type]`
- Types : `DashboardData`, `DernierMouvement` de `../../api/dashboard` — `mvt.reference` affiché (pas de champ `produit_sigle` sur `DernierMouvement`)

#### 3. `src/screens/Mouvements/MouvementsScreen.tsx`

Refonte complète. `FlatList` → `SectionList` groupé par date.

- Header blanc avec searchbar (fond cloud, icône loupe)
- Chips filtre horizontaux défilables : Tous / Entrées / Sorties / Cessions / Acquittements (couleur active par `TypeMeta`)
- Sections par date (titre sticky), vide contextuel
- Filtrage local `useMemo` : search query + chip actif
- Import supprimé : `useNavigation`, `Nav`, `MouvementsStackParams` (navigation déjà dans prop de la stack)

#### 4. `src/screens/Mouvements/MouvementDetailScreen.tsx`

Refonte complète. Header gradient coloré selon `TypeMeta[mvt.type].color`.

- Hero avec glyph badge, type label, volume principal en grand
- Grille 2 colonnes : Vol. ambiant, Vol. 15°C, Densité, Température
- `DetailCard` : référence, régime, produit, marketeur, chauffeur, camion, cuve
- Timeline 3 étapes (Initié → Calculé → Enregistré) avec état actif/inactif

#### 5. `src/screens/Etats/EtatsScreen.tsx`

Refonte complète. Interface : header + segmented control + contenu scrollable.

- Segmented period : `7j / 30j / 3m / 12m` (UI seulement, pas de filtre API)
- Card récap navy gradient : `stock_final_ambiant` principal, sous-titre `stock_final_15`
- Flow cards : `cumul_entrees_ambiant` / `cumul_sorties_ambiant`
- Bar chart : 8 dernières valeurs de `lignes.map(l => l.stock_ambiant)` avec hauteur proportionnelle
- Tableau : colonnes Date / Réf. + stock / Entrée / Sortie sur `lignes` (max 12 lignes)
- Types API corrects : `StockGlobalResponse` → `lignes[]`, `stock_final_ambiant`, `cumul_entrees_ambiant`, `cumul_sorties_ambiant`

#### 6. `src/screens/Profil/ProfilScreen.tsx`

Refonte complète. Hero navy gradient avec avatar orange initiales, orgPill marketeur.

- Stats card flottant (`marginTop: -58`) : `total_mouvements`, `volume_total_ambiant` (formaté `fmtVol`), `marketeur_sigle`
- Sections Coordonnées / Préférences / Application avec `DetailCard` et `PrefRow`
- `PrefRow` : toggle natif (state-driven, position `left: on ? 18 : 2`), trail text, chevron
- Helper `fmtVol(n)` : format compact (M/k) pour volumes

> ⚠️ **API** : `ProfilData` dans `src/api/profil.ts` doit exposer les champs `total_mouvements` (number), `volume_total_ambiant` (number), `marketeur_sigle` (string|null) pour alimenter les stats card.

#### 7. `src/navigation/AppNavigator.tsx`

Tab bar redesignée :

```typescript
tabBarStyle: {
  backgroundColor: Colors.white,
  borderTopWidth: 1, borderTopColor: Colors.cloud,
  height: 64, paddingBottom: 10, paddingTop: 6,
  shadowColor: Colors.ink, shadowOpacity: 0.06, shadowRadius: 8, elevation: 8,
}
tabBarActiveTintColor:   Colors.navy
tabBarInactiveTintColor: Colors.slate
// Splash: Colors.navyDeep
// Label onglet Dashboard: 'Accueil' (était 'Dashboard')
```

#### 8. `src/components/MouvementCard.tsx`

Composant entièrement réécrit. Nouveau layout :

- Cercle badge glyph coloré (`TypeMeta[item.type].soft` / `.color`)
- Corps : label type + heure (`item.reference`) + nom produit
- Bloc droit : volume principal + badge type pastille
- Suppressions : ancienne logique de couleur conditionnelle, `StyleSheet` inline couleurs hardcodées

#### 9. `src/components/LoadingSpinner.tsx` + `src/components/ErrorMessage.tsx`

Composants existants conservés sans modification (utilisés tels quels dans les écrans redesignés).

---

### Architecture préservée

| Élément | Statut |
|---------|--------|
| `src/api/` — tous les modules (`dashboard`, `mouvements`, `etats`, `profil`) | Inchangés |
| `src/context/AuthContext.tsx` | Inchangé |
| `src/navigation/` structure (stacks + tabs) | Inchangée (seul le style tab bar modifié) |
| Types TypeScript des réponses API | Respectés strictement |

---

### Règles de développement mobile (v2.0)

1. **Jamais de couleur hardcodée** — toujours `Colors.*` de `src/constants/colors.ts`
2. **`expo-linear-gradient`** pour tout gradient hero — ne pas utiliser de backgrounds simples pour les sections hero
3. **`TypeMeta[type].color/.soft/.glyph`** pour tout composant affichant un type de mouvement
4. **Types API stricts** — vérifier les interfaces dans `src/api/` avant d'accéder à des propriétés
5. **`LinearGradient` doit être dans un `View` avec `overflow:'hidden'`** si des enfants absolus dépassent
6. **`SafeAreaView edges={['top']}`** — inclure uniquement le top pour laisser la tab bar gérer le bottom

