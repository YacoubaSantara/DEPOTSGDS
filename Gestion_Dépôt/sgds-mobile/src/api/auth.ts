import apiClient from './client';

export interface LoginPayload {
  username: string;
  password: string;
}

export interface UserInfo {
  id: number;
  username: string;
  full_name: string;
  marketeur_id: number;
  marketeur_nom: string;
  marketeur_sigle: string;
}

export interface LoginResponse {
  access: string;
  refresh: string;
  user: UserInfo;
}

export const authApi = {
  login: (payload: LoginPayload) =>
    apiClient.post<LoginResponse>('/auth/login/', payload),

  logout: (refresh: string) =>
    apiClient.post('/auth/logout/', { refresh }),

  refresh: (refresh: string) =>
    apiClient.post<{ access: string; refresh?: string }>(
      '/auth/refresh/',
      { refresh },
    ),

  changePassword: (oldPassword: string, newPassword: string) =>
    apiClient.post('/profil/password/', {
      ancien_mot_de_passe:  oldPassword,
      nouveau_mot_de_passe: newPassword,
      confirmation:         newPassword,
    }),
};
