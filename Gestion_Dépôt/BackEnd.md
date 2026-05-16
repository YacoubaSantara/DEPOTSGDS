# SGDS — Journal des modifications Backend & Mobile

> Dernière mise à jour : 16 mai 2026
> Commit de référence : `f5b4f3d`

---

## Système de notifications automatiques (mai 2026)

### Objectif

Chaque fois qu'un opérateur enregistre un mouvement lié à un marketeur, une notification est créée automatiquement. Elle est visible dans l'espace web du marketeur (cloche dans la barre de navigation) et dans l'application mobile (onglet Notifications + badge).

---

## 1. Backend Django

### `SGDS/models.py`
Ajout du modèle `Notification` :

```python
class Notification(models.Model):
    TYPE_CHOICES = [
        ('ENTREE', 'Entrée'), ('SORTIE', 'Sortie'),
        ('CESSION_EMISE', 'Cession émise'), ('CESSION_RECUE', 'Cession reçue'),
        ('ACQUITTEMENT', 'Acquittement'),
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
```

### `SGDS/migrations/0022_notification_marketeur.py`
Migration créée et appliquée (`python manage.py migrate` → OK).

### `SGDS/signals.py`
Ajout du signal `on_mouvement_created_notif` (séparé du signal existant `on_mouvement_saved`).
Règles de génération :

| Type mouvement | Notifications créées |
|---|---|
| ENTREE | 1 → marketeur du mouvement (`ENTREE`) |
| SORTIE | 1 → marketeur du mouvement (`SORTIE`) |
| CESSION | 2 → marketeur émetteur (`CESSION_EMISE`) + marketeur destinataire (`CESSION_RECUE`) |
| ACQUITTEMENT | 1 → marketeur du mouvement (`ACQUITTEMENT`) |

### `SGDS/context_processors.py` *(nouveau fichier)*
Injecte dans tous les templates :
- `notifs_recentes` — 8 dernières notifications non lues du marketeur connecté
- `notif_count` — nombre de notifications non lues

Enregistré dans `settings.py` → `TEMPLATES[0]['OPTIONS']['context_processors']`.

### `Gestion_Dépôt/settings.py`
- Ajout : `'SGDS.context_processors.notifications_marketeur'` dans les context processors
- Mise à jour `ALLOWED_HOSTS` : `192.168.1.103` → `192.168.1.102`

### `SGDS/views/client.py`
> **Attention** : le projet utilise un **package** `SGDS/views/` (dossier), pas un fichier `views.py`. Toute nouvelle vue doit être ajoutée dans `client.py` et exportée depuis `__init__.py`.

Deux nouvelles vues protégées par `@marketeur_required` :

```python
def notif_marquer_lue(request, notif_id):
    # Marque la notification comme lue, puis redirige vers le détail
    # du mouvement si disponible, sinon vers la page précédente.

def notif_tout_marquer_lu(request):
    # Marque toutes les notifications non lues du marketeur comme lues.
```

### `SGDS/views/__init__.py`
Export des nouvelles vues :
```python
from .client import (
    client_dashboard, client_mouvements,
    notif_marquer_lue, notif_tout_marquer_lu,
)
```

### `SGDS/urls.py`
Deux nouvelles routes :
```python
path('espace/notifications/<int:notif_id>/lue/', views.notif_marquer_lue,      name='notif_marquer_lue'),
path('espace/notifications/tout-lire/',          views.notif_tout_marquer_lu,  name='notif_tout_marquer_lu'),
```

---

## 2. Interface web

### `templates/base.html`
Ajout dans la zone `tb-right` (visible uniquement pour les marketeurs) :
- Cloche avec badge rouge (`notif_count`)
- Panel déroulant listant les 8 dernières notifications non lues
- Clic sur une notification → marque lue + redirige vers le **détail du mouvement** (`mouvement_detail/<pk>`)
- Bouton "Tout marquer lu" (POST vers `notif_tout_marquer_lu`)
- Footer par notification : date à gauche, "Voir le mouvement ›" à droite (si `mouvement_id` présent)
- Script click-away pour fermer le panel au clic extérieur

### `static/css/sgds.css`
Nouvelles classes ajoutées :
`.notif-wrap`, `.notif-bell`, `.notif-badge`, `.notif-panel`, `.notif-panel-header`,
`.notif-list`, `.notif-item`, `.notif-item-icon`, `.notif-item-body`, `.notif-item-titre`,
`.notif-item-msg`, `.notif-item-footer`, `.notif-item-date`, `.notif-item-link`, `.notif-empty`,
variantes de couleur par type (`notif-type-entree`, `notif-type-sortie`, etc.), surcharges dark mode.

---

## 3. API REST (mobile)

### `api/v1/notifications/` *(nouveau package)*

**`views.py`** — classe `NotificationsView(APIView)` avec `permission_classes = [IsAuthenticated]` :

| Méthode | Corps | Action |
|---|---|---|
| `GET` | — | Retourne `{ count_non_lues, results: [...30 items] }` |
| `PATCH` | `{ "ids": [1, 2, 3] }` | Marque les IDs spécifiés comme lus |
| `PATCH` | `{ "all": true }` | Marque toutes les notifications comme lues |

### `api/v1/urls.py`
```python
path('notifications/', NotificationsView.as_view(), name='api_notifications'),
```

---

## 4. Application mobile (React Native / Expo)

### `sgds-mobile/src/api/notifications.ts` *(nouveau fichier)*
```typescript
export interface NotificationItem {
  id: number;
  type_notif: 'ENTREE' | 'SORTIE' | 'CESSION_EMISE' | 'CESSION_RECUE' | 'ACQUITTEMENT';
  titre: string;
  message: string;
  lue: boolean;
  date_creation: string;
  mouvement_id: number | null;
}

export const notificationsApi = {
  getAll:     () => apiClient.get<NotificationsResponse>('/notifications/'),
  marquerLus: (ids: number[]) => apiClient.patch('/notifications/', { ids }),
  toutLire:   () => apiClient.patch('/notifications/', { all: true }),
};
```

### `sgds-mobile/src/screens/Notifications/NotificationsScreen.tsx` *(nouveau fichier)*
- Rechargement automatique à chaque focus de l'onglet (`useFocusEffect`)
- Pull-to-refresh
- Affichage d'erreur visible + bouton Réessayer (les erreurs réseau ne sont plus silencieuses)
- Marquage optimiste comme lu au tap
- Navigation vers `MouvementDetail` au tap si `mouvement_id` présent :
  `navigation.navigate('Mouvements', { screen: 'MouvementDetail', params: { id } })`
- Bouton "Tout marquer lu"
- `SafeAreaView` importé depuis `react-native-safe-area-context`

### `sgds-mobile/src/navigation/AppNavigator.tsx`
- `Notifications: undefined` ajouté à `TabParams`
- Hook `useNotifCount` : `useEffect` + `setInterval(refresh, 30_000)` pour rafraîchir le badge toutes les 30 s
  *(Note : `useFocusEffect` ne fonctionne pas dans `AppTabs` qui n'est pas un écran enregistré)*
- Onglet `Notifications` avec `tabBarBadge: notifCount > 0 ? notifCount : undefined`

### `sgds-mobile/src/screens/Dashboard/DashboardScreen.tsx`
- `notifCount` chargé via `useFocusEffect` à chaque visite de l'accueil
- Cloche hero câblée : `onPress={() => navigation.navigate('Notifications')}`
- Badge rouge réel (affiche le compte, "9+" si > 9) remplace le point orange statique

### `sgds-mobile/package.json` — mises à jour Expo 54

| Package | Avant | Après |
|---|---|---|
| `expo-print` | `~14.0.1` | `~15.0.8` |
| `expo-sharing` | `~13.0.1` | `~14.0.8` |
| `babel-preset-expo` | `~13.0.0` | `~54.0.10` |

---

## Erreurs rencontrées et corrigées

| Erreur | Cause | Correction |
|---|---|---|
| `SGDS.views` n'a pas l'attribut `notif_marquer_lue` | `SGDS/views/` est un package ; les modifications dans `views.py` (fichier) étaient ignorées par Python | Vues ajoutées dans `SGDS/views/client.py` + export depuis `__init__.py` |
| Badge notifications ne se rafraîchit pas | `useFocusEffect` utilisé dans `AppTabs` qui n'est pas un écran enregistré dans un navigator | Remplacé par `useEffect` + `setInterval` toutes les 30 s |
| Liste notifications vide sans message d'erreur | `catch {}` silencieux masquait toutes les erreurs réseau/auth | Ajout d'un état `erreur` + UI d'erreur visible avec bouton retry |
| Clic notification mobile ne navigue pas | Aucun `useNavigation` dans `NotificationsScreen` | Navigation cross-tab ajoutée vers `MouvementDetail` |
| Clic notification web → retour à la même page | `notif_marquer_lue` redirigeait toujours vers `HTTP_REFERER` | Redirection vers `mouvement_detail/<pk>` si `mouvement_id` présent |
| Avertissement `SafeAreaView` déprécié | Import depuis `react-native` au lieu de `react-native-safe-area-context` dans `NotificationsScreen` | Import corrigé |
