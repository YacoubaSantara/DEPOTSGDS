import apiClient from './client';

export interface ProfilData {
  id: number;
  username: string;
  full_name: string;
  first_name: string;
  last_name: string;
  email: string;
  telephone: string | null;
  poste: string | null;
  date_joined: string;
  marketeur_id: number | null;
  marketeur_nom: string | null;
  marketeur_sigle: string | null;
  photo_url: string | null;
  total_mouvements: number;
  volume_total_ambiant: number;
  permissions: Record<string, boolean>;
}

export interface UpdateProfilPayload {
  first_name?: string;
  last_name?: string;
  email?: string;
  telephone?: string;
}

export interface ChangePasswordPayload {
  ancien_mot_de_passe: string;
  nouveau_mot_de_passe: string;
  confirmation: string;
}

export const profilApi = {
  get: () => apiClient.get<ProfilData>('/profil/'),

  update: (payload: UpdateProfilPayload) =>
    apiClient.patch<ProfilData>('/profil/', payload),

  changePassword: (payload: ChangePasswordPayload) =>
    apiClient.post('/profil/password/', payload),
};
