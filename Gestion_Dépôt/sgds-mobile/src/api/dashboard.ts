import apiClient from './client';

export interface StockProduit {
  produit_id:    number;
  produit_nom:   string;
  produit_sigle: string;
  stock_ambiant: number;
  stock_15:      number;
  sd_ambiant:    number;
  ac_ambiant:    number;
  sd_15:         number;
  ac_15:         number;
  total:         number;
  capacite:      number;
}

export interface DernierMouvement {
  id:               number;
  type:             string;
  date:             string;
  produit:          string;
  quantite_ambiant: number;
  quantite_15:      number;
  reference:        string | null;
}

export interface DashboardData {
  marketeur_nom:       string;
  stocks:              StockProduit[];
  derniers_mouvements: DernierMouvement[];
  total_mouvements:    number;
  total_entrees:       number;
  total_sorties:       number;
  nb_entrees:          number;
  nb_sorties:          number;
  taux_remplissage:    number;
  total_ambiant_hier:  number;
  delta_hier:          number;
}

export const dashboardApi = {
  get: () => apiClient.get<DashboardData>('/dashboard/'),
};
