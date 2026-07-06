/**
 * Navigation principale — SGDS Mobile
 *
 * Structure :
 *   RootStack
 *   ├── AuthStack  (si non connecté)
 *   │    └── LoginScreen
 *   └── AppTabs   (si connecté)
 *        ├── Dashboard
 *        ├── Mouvements
 *        │    ├── MouvementsList
 *        │    └── MouvementDetail
 *        ├── États
 *        │    ├── EtatsMenu
 *        │    ├── CarteStock
 *        │    ├── RecapMouvements
 *        │    ├── StockOuverture
 *        │    ├── Stock15
 *        │    ├── FraisPassage
 *        │    └── Coulage
 *        ├── Flotte
 *        │    ├── FlotteMenu
 *        │    ├── CamionsList / CamionDetail / CamionForm
 *        │    └── ChauffeursList / ChauffeurDetail / ChauffeurForm
 *        └── Profil
 */
import React, { useState, useCallback } from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { Ionicons } from '@expo/vector-icons';
import { View, ActivityIndicator, StyleSheet } from 'react-native';

import { useAuth } from '../context/AuthContext';
import { Colors } from '../constants/colors';

// Écrans
import { LoginScreen }            from '../screens/Auth/LoginScreen';
import { DashboardScreen }        from '../screens/Dashboard/DashboardScreen';
import { MouvementsScreen }       from '../screens/Mouvements/MouvementsScreen';
import { MouvementDetailScreen }  from '../screens/Mouvements/MouvementDetailScreen';
import { EtatsMenuScreen }        from '../screens/Etats/EtatsMenuScreen';
import { CarteStockScreen }       from '../screens/Etats/CarteStockScreen';
import { RecapMouvementsScreen }  from '../screens/Etats/RecapMouvementsScreen';
import { StockOuvertureScreen }   from '../screens/Etats/StockOuvertureScreen';
import { Stock15Screen }          from '../screens/Etats/Stock15Screen';
import { FraisPassageScreen }     from '../screens/Etats/FraisPassageScreen';
import { CoulageScreen }          from '../screens/Etats/CoulageScreen';
import { ProfilScreen }                   from '../screens/Profil/ProfilScreen';
import { ConditionsUtilisationScreen }    from '../screens/Profil/ConditionsUtilisationScreen';
import { SecurityScreen }                from '../screens/Profil/SecurityScreen';
import { EditProfilScreen }              from '../screens/Profil/EditProfilScreen';
import { NotificationsScreen }           from '../screens/Notifications/NotificationsScreen';
import { notificationsApi }      from '../api/notifications';
import { FlotteMenuScreen }        from '../screens/Flotte/FlotteMenuScreen';
import { CamionsListScreen }       from '../screens/Flotte/CamionsListScreen';
import { CamionDetailScreen }      from '../screens/Flotte/CamionDetailScreen';
import { CamionFormScreen }        from '../screens/Flotte/CamionFormScreen';
import { ChauffeursListScreen }    from '../screens/Flotte/ChauffeursListScreen';
import { ChauffeurDetailScreen }   from '../screens/Flotte/ChauffeurDetailScreen';
import { ChauffeurFormScreen }     from '../screens/Flotte/ChauffeurFormScreen';

// ── Types navigation ──────────────────────────────────────────────

export type AuthStackParams = {
  Login: undefined;
};

export type MouvementsStackParams = {
  MouvementsList:  undefined;
  MouvementDetail: { id: number };
};

export type EtatsStackParams = {
  EtatsMenu:        undefined;
  CarteStock:       { produitId?: number; produitNom?: string; produitSigle?: string } | undefined;
  RecapMouvements:  undefined;
  StockOuverture:   undefined;
  Stock15:          undefined;
  FraisPassage:     undefined;
  Coulage:          undefined;
};

export type ProfilStackParams = {
  ProfilMain:             undefined;
  ConditionsUtilisation:  undefined;
  Securite:               undefined;
  ModifierProfil:         undefined;
};

export type FlotteStackParams = {
  FlotteMenu:       undefined;
  CamionsList:      undefined;
  CamionDetail:     { id: number };
  CamionForm:       { id?: number };
  ChauffeursList:   undefined;
  ChauffeurDetail:  { id: number };
  ChauffeurForm:    { id?: number };
};

export type TabParams = {
  Dashboard:     undefined;
  Mouvements:    undefined;
  Etats:         undefined;
  Flotte:        undefined;
  Notifications: undefined;
  Profil:        undefined;
};

// ── Stacks / Tabs ─────────────────────────────────────────────────

const AuthStack   = createNativeStackNavigator<AuthStackParams>();
const Tab         = createBottomTabNavigator<TabParams>();
const MvtStack    = createNativeStackNavigator<MouvementsStackParams>();
const EtatsStack  = createNativeStackNavigator<EtatsStackParams>();
const ProfilStack = createNativeStackNavigator<ProfilStackParams>();
const FlotteStack = createNativeStackNavigator<FlotteStackParams>();

// ── Hook badge notifications ──────────────────────────────────────

function useNotifCount() {
  const [count, setCount] = useState(0);

  const refresh = useCallback(async () => {
    try {
      const res = await notificationsApi.getAll();
      setCount(res.data.count_non_lues);
    } catch {
      // silencieux — hors ligne ou non-marketeur
    }
  }, []);

  // useEffect (pas useFocusEffect) car AppTabs n'est pas un screen
  React.useEffect(() => {
    refresh();
    const timer = setInterval(refresh, 30_000); // rafraîchit toutes les 30s
    return () => clearInterval(timer);
  }, [refresh]);

  return { count, refresh };
}

function MouvementsStack() {
  return (
    <MvtStack.Navigator screenOptions={{ headerShown: false }}>
      <MvtStack.Screen name="MouvementsList"  component={MouvementsScreen} />
      <MvtStack.Screen name="MouvementDetail" component={MouvementDetailScreen} />
    </MvtStack.Navigator>
  );
}

function ProfilNavigator() {
  return (
    <ProfilStack.Navigator screenOptions={{ headerShown: false }}>
      <ProfilStack.Screen name="ProfilMain"            component={ProfilScreen} />
      <ProfilStack.Screen name="ConditionsUtilisation" component={ConditionsUtilisationScreen} />
      <ProfilStack.Screen name="Securite"             component={SecurityScreen} />
      <ProfilStack.Screen name="ModifierProfil"        component={EditProfilScreen} />
    </ProfilStack.Navigator>
  );
}

function FlotteNavigator() {
  return (
    <FlotteStack.Navigator screenOptions={{ headerShown: false }}>
      <FlotteStack.Screen name="FlotteMenu"      component={FlotteMenuScreen} />
      <FlotteStack.Screen name="CamionsList"     component={CamionsListScreen} />
      <FlotteStack.Screen name="CamionDetail"    component={CamionDetailScreen} />
      <FlotteStack.Screen name="CamionForm"      component={CamionFormScreen} />
      <FlotteStack.Screen name="ChauffeursList"  component={ChauffeursListScreen} />
      <FlotteStack.Screen name="ChauffeurDetail" component={ChauffeurDetailScreen} />
      <FlotteStack.Screen name="ChauffeurForm"   component={ChauffeurFormScreen} />
    </FlotteStack.Navigator>
  );
}

function EtatsNavigator() {
  return (
    <EtatsStack.Navigator screenOptions={{ headerShown: false }}>
      <EtatsStack.Screen name="EtatsMenu"       component={EtatsMenuScreen} />
      <EtatsStack.Screen name="CarteStock"      component={CarteStockScreen} />
      <EtatsStack.Screen name="RecapMouvements" component={RecapMouvementsScreen} />
      <EtatsStack.Screen name="StockOuverture"  component={StockOuvertureScreen} />
      <EtatsStack.Screen name="Stock15"         component={Stock15Screen} />
      <EtatsStack.Screen name="FraisPassage"    component={FraisPassageScreen} />
      <EtatsStack.Screen name="Coulage"         component={CoulageScreen} />
    </EtatsStack.Navigator>
  );
}

function AppTabs() {
  const { count: notifCount } = useNotifCount();

  return (
    <Tab.Navigator
      screenOptions={({ route }) => ({
        headerShown: false,
        tabBarActiveTintColor:   Colors.navy,
        tabBarInactiveTintColor: Colors.slate,
        tabBarStyle: {
          backgroundColor: Colors.white,
          borderTopWidth:  1,
          borderTopColor:  Colors.cloud,
          height: 64,
          paddingBottom: 10,
          paddingTop: 6,
          shadowColor: Colors.ink,
          shadowOffset: { width: 0, height: -2 },
          shadowOpacity: 0.06,
          shadowRadius: 8,
          elevation: 8,
        },
        tabBarLabelStyle: {
          fontSize: 11,
          fontWeight: '700',
          letterSpacing: 0.1,
        },
        tabBarIcon: ({ focused, color, size }) => {
          const icons: Record<string, [string, string]> = {
            Dashboard:     ['grid',             'grid-outline'],
            Mouvements:    ['swap-horizontal',  'swap-horizontal-outline'],
            Etats:         ['bar-chart',        'bar-chart-outline'],
            Flotte:        ['car',              'car-outline'],
            Notifications: ['notifications',    'notifications-outline'],
            Profil:        ['person-circle',    'person-circle-outline'],
          };
          const [active, inactive] = icons[route.name] ?? ['ellipse', 'ellipse-outline'];
          return (
            <Ionicons
              name={(focused ? active : inactive) as any}
              size={focused ? size + 1 : size}
              color={color}
            />
          );
        },
      })}
    >
      <Tab.Screen name="Dashboard"  component={DashboardScreen}  options={{ title: 'Accueil' }} />
      <Tab.Screen name="Mouvements" component={MouvementsStack}  options={{ title: 'Mouvements' }} />
      <Tab.Screen name="Etats"      component={EtatsNavigator}   options={{ title: 'États' }} />
      <Tab.Screen name="Flotte"     component={FlotteNavigator}  options={{ title: 'Flotte' }} />
      <Tab.Screen
        name="Notifications"
        component={NotificationsScreen}
        options={{
          title: 'Notifs',
          tabBarBadge: notifCount > 0 ? notifCount : undefined,
          tabBarBadgeStyle: { backgroundColor: Colors.red, color: Colors.white, fontSize: 10 },
        }}
      />
      <Tab.Screen name="Profil"     component={ProfilNavigator}  options={{ title: 'Profil' }} />
    </Tab.Navigator>
  );
}

// ── Root Navigator ─────────────────────────────────────────────────

export function AppNavigator() {
  const { isLoading, isAuthenticated } = useAuth();

  if (isLoading) {
    return (
      <View style={styles.splash}>
        <ActivityIndicator size="large" color={Colors.primary} />
      </View>
    );
  }

  return (
    <NavigationContainer>
      {isAuthenticated ? (
        <AppTabs />
      ) : (
        <AuthStack.Navigator screenOptions={{ headerShown: false }}>
          <AuthStack.Screen name="Login" component={LoginScreen} />
        </AuthStack.Navigator>
      )}
    </NavigationContainer>
  );
}

const styles = StyleSheet.create({
  splash: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: Colors.navyDeep,
  },
});
