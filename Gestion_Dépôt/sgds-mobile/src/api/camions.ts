import apiClient from './client';

export interface Compartiment {
  id?: number;
  numero: number;
  capacite: number;
}

export interface Camion {
  id: number;
  uuid: string;
  immatriculation: string;
  marque: string;
  modele: string | null;
  capacite_totale: number;
  nombre_compartiments: number;
  type_produit: string;
  statut: 'EN_SERVICE' | 'HORS_SERVICE' | 'EN_MAINTENANCE' | 'RETIRE';
  notes: string | null;
  compartiments: Compartiment[];
  date_enregistrement: string;
  date_modification: string;
}

export interface CamionFilters {
  q?: string;
  statut?: string;
}

export interface CamionInput {
  immatriculation: string;
  marque: string;
  modele?: string;
  capacite_totale: number;
  nombre_compartiments: number;
  type_produit: string;
  statut: string;
  notes?: string;
  compartiments?: Compartiment[];
}

export const camionsApi = {
  list: (filters: CamionFilters = {}) =>
    apiClient.get<Camion[]>('/camions/', { params: filters }),

  detail: (id: number) =>
    apiClient.get<Camion>(`/camions/${id}/`),

  create: (data: CamionInput) =>
    apiClient.post<Camion>('/camions/', data),

  update: (id: number, data: Partial<CamionInput>) =>
    apiClient.patch<Camion>(`/camions/${id}/`, data),

  delete: (id: number) =>
    apiClient.delete(`/camions/${id}/`),
};
