import apiClient from './client';

export interface MouvementFilters {
  produit?: number;
  type?: string;
  regime?: string;
  date_debut?: string;
  date_fin?: string;
  page?: number;
}

export interface MouvementListItem {
  id: number;
  type: string;
  date: string;
  produit: string;
  produit_sigle: string;
  regime: string;
  quantite_ambiant: number;
  quantite_15: number;
  reference: string;
  observation: string;
}

export interface MouvementsResponse {
  count: number;
  page: number;
  page_size: number;
  total_pages: number;
  results: MouvementListItem[];
}

export interface MouvementDetail extends MouvementListItem {
  // Entrée
  provenance?: string;
  bl_expediteur?: string;
  bl_client?: string;
  date_chargement?: string;
  date_dechargement?: string;
  volume_ambiant_expediteur?: number;
  volume_ambiant_recu?: number;
  volume_15c_recu?: number;
  perte_gain_reception?: number;
  camion_immatriculation?: string;
  chauffeur_nom?: string;
  // Sortie
  destination?: string;
  numero_permis_sortie?: string;
  volume_ambiant_sortie?: number;
  volume_15c_sortie?: number;
  mode_reglement?: string;
  // Cession
  cession_destinataire?: string;
  cession_volume_ambiant?: number;
  cession_volume_15c?: number;
  cession_motif?: string;
  // Acquittement
  acquittement_volume_ambiant?: number;
  acquittement_reference_declaration?: string;
  acquittement_date_declaration?: string;
}

export const mouvementsApi = {
  list: (filters: MouvementFilters = {}) =>
    apiClient.get<MouvementsResponse>('/mouvements/', { params: filters }),

  detail: (id: number) =>
    apiClient.get<MouvementDetail>(`/mouvements/${id}/`),
};
