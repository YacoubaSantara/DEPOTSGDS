/**
 * AuthContext — gestion de la session JWT
 *
 * - Persiste les tokens dans expo-secure-store
 * - Expose : user, isLoading, login(), logout()
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
    // Considérer expiré 30 s avant l'heure réelle
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

          // Si l'access token est encore valide → session restaurée directement
          if (!isTokenExpired(access)) {
            setState({ user, accessToken: access, refreshToken: refresh, isLoading: false, isAuthenticated: true });
            return;
          }

          // Access token expiré → tenter un refresh silencieux
          try {
            const res = await axios.post(
              `${API_BASE_URL}/auth/refresh/`,
              { refresh },
              { headers: { 'Content-Type': 'application/json' } },
            );
            const newAccess: string   = res.data.access;
            const newRefresh: string  = res.data.refresh ?? refresh;
            await Promise.all([
              SecureStore.setItemAsync(STORAGE_KEYS.ACCESS_TOKEN,  newAccess),
              SecureStore.setItemAsync(STORAGE_KEYS.REFRESH_TOKEN, newRefresh),
            ]);
            setState({ user, accessToken: newAccess, refreshToken: newRefresh, isLoading: false, isAuthenticated: true });
          } catch {
            // Refresh échoué (token blacklisté ou expiré) → forcer la reconnexion
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
      SecureStore.setItemAsync(STORAGE_KEYS.ACCESS_TOKEN,  access),
      SecureStore.setItemAsync(STORAGE_KEYS.REFRESH_TOKEN, refresh),
      SecureStore.setItemAsync(STORAGE_KEYS.USER,          JSON.stringify(user)),
    ]);

    setState({
      user,
      accessToken:     access,
      refreshToken:    refresh,
      isLoading:       false,
      isAuthenticated: true,
    });
  }, []);

  // ── Logout ────────────────────────────────────────────────
  const logout = useCallback(async () => {
    try {
      const refresh = await SecureStore.getItemAsync(STORAGE_KEYS.REFRESH_TOKEN);
      if (refresh) {
        await authApi.logout(refresh).catch(() => {
          // Ignorer l'erreur réseau — on vide quand même les tokens
        });
      }
    } finally {
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
    <AuthContext.Provider
      value={{
        ...state,
        login,
        logout,
      }}
    >
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
