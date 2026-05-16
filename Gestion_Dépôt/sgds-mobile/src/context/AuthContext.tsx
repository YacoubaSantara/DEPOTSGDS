/**
 * AuthContext — gestion de la session JWT + authentification biométrique
 *
 * - Persiste les tokens dans expo-secure-store
 * - Expose : user, isLoading, login(), logout(), loginWithBiometric()
 * - Vérifie automatiquement la session au démarrage
 */
import React, {
  createContext,
  useContext,
  useState,
  useEffect,
  useCallback,
  ReactNode,
} from 'react';
import axios from 'axios';
import * as SecureStore from 'expo-secure-store';
import * as LocalAuthentication from 'expo-local-authentication';
import { authApi, LoginPayload, UserInfo } from '../api/auth';
import { API_BASE_URL, STORAGE_KEYS } from '../api/client';

/** Retourne true si le token JWT est expiré (ou invalide). */
function isTokenExpired(token: string): boolean {
  try {
    const part = token.split('.')[1];
    if (!part) return true;
    const b64 = part.replace(/-/g, '+').replace(/_/g, '/');
    const padded = b64.padEnd(b64.length + (4 - (b64.length % 4)) % 4, '=');
    const payload: { exp?: number } = JSON.parse(atob(padded));
    return !payload.exp || payload.exp * 1000 < Date.now() + 30_000;
  } catch {
    return true;
  }
}

// ── Types ─────────────────────────────────────────────────────
interface AuthState {
  user: UserInfo | null;
  accessToken: string | null;
  refreshToken: string | null;
  isLoading: boolean;
  isAuthenticated: boolean;
}

interface AuthContextValue extends AuthState {
  login: (payload: LoginPayload) => Promise<void>;
  logout: () => Promise<void>;
  loginWithBiometric: () => Promise<void>;
}

// ── Contexte ──────────────────────────────────────────────────
const AuthContext = createContext<AuthContextValue | undefined>(undefined);

// ── Provider ──────────────────────────────────────────────────
export function AuthProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<AuthState>({
    user:            null,
    accessToken:     null,
    refreshToken:    null,
    isLoading:       true,
    isAuthenticated: false,
  });

  // Restaurer la session au démarrage
  useEffect(() => {
    const restoreSession = async () => {
      try {
        const [access, refresh, userJson] = await Promise.all([
          SecureStore.getItemAsync(STORAGE_KEYS.ACCESS_TOKEN),
          SecureStore.getItemAsync(STORAGE_KEYS.REFRESH_TOKEN),
          SecureStore.getItemAsync(STORAGE_KEYS.USER),
        ]);

        if (access && refresh && userJson) {
          const user: UserInfo = JSON.parse(userJson);

          if (!isTokenExpired(access)) {
            setState({ user, accessToken: access, refreshToken: refresh, isLoading: false, isAuthenticated: true });
            return;
          }

          try {
            const res = await axios.post(
              `${API_BASE_URL}/auth/refresh/`,
              { refresh },
              { headers: { 'Content-Type': 'application/json' } },
            );
            const newAccess: string  = res.data.access;
            const newRefresh: string = res.data.refresh ?? refresh;
            await Promise.all([
              SecureStore.setItemAsync(STORAGE_KEYS.ACCESS_TOKEN,  newAccess),
              SecureStore.setItemAsync(STORAGE_KEYS.REFRESH_TOKEN, newRefresh),
            ]);
            setState({ user, accessToken: newAccess, refreshToken: newRefresh, isLoading: false, isAuthenticated: true });
          } catch {
            await Promise.all([
              SecureStore.deleteItemAsync(STORAGE_KEYS.ACCESS_TOKEN),
              SecureStore.deleteItemAsync(STORAGE_KEYS.REFRESH_TOKEN),
              SecureStore.deleteItemAsync(STORAGE_KEYS.USER),
            ]);
            setState((prev) => ({ ...prev, isLoading: false }));
          }
        } else {
          setState((prev) => ({ ...prev, isLoading: false }));
        }
      } catch {
        setState((prev) => ({ ...prev, isLoading: false }));
      }
    };

    restoreSession();
  }, []);

  // ── Login ─────────────────────────────────────────────────
  const login = useCallback(async (payload: LoginPayload) => {
    const response = await authApi.login(payload);
    const { access, refresh, user } = response.data;

    await Promise.all([
      SecureStore.setItemAsync(STORAGE_KEYS.ACCESS_TOKEN,          access),
      SecureStore.setItemAsync(STORAGE_KEYS.REFRESH_TOKEN,         refresh),
      SecureStore.setItemAsync(STORAGE_KEYS.USER,                  JSON.stringify(user)),
      // Stocke les credentials pour une éventuelle connexion biométrique ultérieure
      SecureStore.setItemAsync(STORAGE_KEYS.BIOMETRIC_CREDENTIALS, JSON.stringify(payload)),
    ]);

    setState({
      user,
      accessToken:     access,
      refreshToken:    refresh,
      isLoading:       false,
      isAuthenticated: true,
    });
  }, []);

  // ── Login biométrique ─────────────────────────────────────
  const loginWithBiometric = useCallback(async () => {
    const hasHardware = await LocalAuthentication.hasHardwareAsync();
    if (!hasHardware) {
      throw new Error('Ce dispositif ne prend pas en charge la biométrie.');
    }

    const isEnrolled = await LocalAuthentication.isEnrolledAsync();
    if (!isEnrolled) {
      throw new Error('Aucune biométrie configurée sur cet appareil.');
    }

    const result = await LocalAuthentication.authenticateAsync({
      promptMessage:         'Se connecter à SGDS',
      cancelLabel:           'Annuler',
      disableDeviceFallback: true,   // pas de fallback PIN — biométrie uniquement
    });

    if (!result.success) {
      if ((result as any).error === 'lockout' || (result as any).error === 'lockoutPermanent') {
        throw new Error('Trop de tentatives. Biométrie temporairement bloquée.');
      }
      throw new Error('Authentification biométrique annulée.');
    }

    const credJson = await SecureStore.getItemAsync(STORAGE_KEYS.BIOMETRIC_CREDENTIALS);
    if (!credJson) {
      throw new Error('Identifiants non trouvés. Reconnectez-vous avec votre mot de passe.');
    }

    const creds: LoginPayload = JSON.parse(credJson);
    await login(creds);
  }, [login]);

  // ── Logout ────────────────────────────────────────────────
  const logout = useCallback(async () => {
    try {
      const refresh = await SecureStore.getItemAsync(STORAGE_KEYS.REFRESH_TOKEN);
      if (refresh) {
        await authApi.logout(refresh).catch(() => {});
      }
    } finally {
      // On supprime les tokens de session mais pas les credentials biométriques
      // pour permettre la reconnexion biométrique après un logout
      await Promise.all([
        SecureStore.deleteItemAsync(STORAGE_KEYS.ACCESS_TOKEN),
        SecureStore.deleteItemAsync(STORAGE_KEYS.REFRESH_TOKEN),
        SecureStore.deleteItemAsync(STORAGE_KEYS.USER),
      ]);

      setState({
        user:            null,
        accessToken:     null,
        refreshToken:    null,
        isLoading:       false,
        isAuthenticated: false,
      });
    }
  }, []);

  return (
    <AuthContext.Provider value={{ ...state, login, logout, loginWithBiometric }}>
      {children}
    </AuthContext.Provider>
  );
}

// ── Hook ──────────────────────────────────────────────────────
export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error('useAuth doit être utilisé à l\'intérieur d\'<AuthProvider>');
  }
  return ctx;
}
