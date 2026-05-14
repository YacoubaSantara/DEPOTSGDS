# SGDS Mobile — Application React Native / Expo

Application mobile pour les Marketeurs du Système de Gestion des Dépôts (SGDS).

## Prérequis

- Node.js 18+
- Expo CLI : `npm install -g expo-cli`
- Android Studio (pour émulateur Android) ou appareil physique

## Installation

```bash
cd sgds-mobile
npm install
```

## Lancer en développement

```bash
npx expo start
```

Puis scanner le QR code avec **Expo Go** sur votre téléphone, ou appuyer sur `a` pour l'émulateur Android.

## Configuration de l'URL du serveur

Modifier le fichier `src/api/client.ts` :

```ts
export const API_BASE_URL = 'http://VOTRE_IP_LOCALE:8000/api/v1';
```

> Remplacer `VOTRE_IP_LOCALE` par l'IP locale de votre PC (ex: `192.168.1.100`).
> Ne pas utiliser `localhost` sur un appareil physique.

## Structure du projet

```
sgds-mobile/
├── App.tsx                    # Point d'entrée
├── src/
│   ├── api/                   # Couche API (axios)
│   │   ├── client.ts          # Instance axios + JWT refresh auto
│   │   ├── auth.ts            # Login / logout
│   │   ├── dashboard.ts       # Dashboard KPIs
│   │   ├── mouvements.ts      # Liste + détail mouvements
│   │   ├── etats.ts           # État de stock
│   │   └── profil.ts          # Profil utilisateur
│   ├── context/
│   │   └── AuthContext.tsx    # Contexte d'authentification JWT
│   ├── navigation/
│   │   └── AppNavigator.tsx   # Navigation principale
│   ├── screens/
│   │   ├── Auth/              # Écran connexion
│   │   ├── Dashboard/         # Tableau de bord + KPIs
│   │   ├── Mouvements/        # Liste + détail mouvements
│   │   ├── Etats/             # État de stock global
│   │   └── Profil/            # Profil + déconnexion
│   ├── components/            # Composants réutilisables
│   ├── constants/colors.ts    # Palette de couleurs SGDS
│   └── utils/format.ts        # Formatage dates / nombres
└── assets/                    # Icônes et images
```

## Build APK Android (production)

```bash
# Installer EAS CLI
npm install -g eas-cli

# Se connecter à Expo
eas login

# Configurer le projet
eas build:configure

# Lancer le build Android
eas build --platform android --profile preview
```
