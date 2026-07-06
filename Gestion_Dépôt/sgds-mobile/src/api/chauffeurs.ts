import apiClient from './client';

export interface Chauffeur {
  id: number;
  uuid: string;
  nom: string;
  prenom: string;
  telephone: string;
  telephone2: string | null;
  email: string | null;
  numero_permis: string;
  categorie_permis: string;
  numero_employe: string | null;
  statut: 'ACTIF' | 'INACTIF' | 'SUSPENDU';
  camion: number | null;
  camion_immatriculation: string | null;
  date_embauche: string | null;
  notes: string | null;
}

export interface ChauffeurFilters {
  q?: string;
  statut?: string;
}

export interface ChauffeurInput {
  nom: string;
  prenom: string;
  telephone: string;
  telephone2?: string;
  email?: string;
  numero_permis: string;
  categorie_permis: string;
  statut: string;
  camion?: number | null;
  date_embauche?: string;
  notes?: string;
}

export const chauffeursApi = {
  list: (filters: ChauffeurFilters = {}) =>
    apiClient.get<Chauffeur[]>('/chauffeurs/', { params: filters }),

  detail: (id: number) =>
    apiClient.get<Chauffeur>(`/chauffeurs/${id}/`),

  create: (data: ChauffeurInput) =>
    apiClient.post<Chauffeur>('/chauffeurs/', data),

  update: (id: number, data: Partial<ChauffeurInput>) =>
    apiClient.patch<Chauffeur>(`/chauffeurs/${id}/`, data),

  delete: (id: number) =>
    apiClient.delete(`/chauffeurs/${id}/`),
};
