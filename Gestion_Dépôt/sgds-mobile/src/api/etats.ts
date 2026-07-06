import apiClient from './client';

// ── Carte de stock ────────────────────────────────────────────────

export interface StockLigne {
  date: string;
  reference: string;
  type: string;
  entree_ambiant: number;
  entree_15: number;
  sortie_ambiant: number;
  sortie_15: number;
  stock_ambiant: number;
  stock_15: number;
}

export interface StockGlobalResponse {
  marketeur_nom: string;
  produit_id: number | null;
  produit_nom: string;
  produit_sigle: string;
  periode_id: number | null;
  periode_nom: string;
  stock_ouverture_ambiant: number;
  lignes: StockLigne[];
  cumul_entrees_ambiant: number;
  cumul_entrees_15: number;
  cumul_sorties_ambiant: number;
  cumul_sorties_15: number;
  stock_final_ambiant: number;
  stock_final_15: number;
}

export interface StockGlobalFilters {
  produit?: number;
  periode_id?: number;
  date_debut?: string;
  date_fin?: string;
}

// ── Récapitulatif ─────────────────────────────────────────────────

export interface RecapProduit {
  produit_id: number;
  produit_nom: string;
  produit_sigle: string;
  nb_entrees: number;
  volume_entree_ambiant: number;
  volume_entree_15: number;
  nb_sorties: number;
  volume_sortie_ambiant: number;
  nb_cessions: number;
  volume_cession_ambiant: number;
  nb_acquittements: number;
  volume_acquit_ambiant: number;
  stock_ouverture_ambiant: number;
  stock_final_ambiant: number;
}

export interface RecapTotaux {
  nb_mouvements: number;
  nb_entrees: number;
  volume_entree_ambiant: number;
  nb_sorties: number;
  volume_sortie_ambiant: number;
  nb_cessions: number;
  volume_cession_ambiant: number;
  nb_acquittements: number;
  volume_acquit_ambiant: number;
  stock_ouverture_ambiant: number;
  stock_final_ambiant: number;
}

export interface RecapResponse {
  marketeur_nom: string;
  periode_id: number | null;
  periode_nom: string;
  par_produit: RecapProduit[];
  totaux: RecapTotaux;
}

export interface RecapFilters {
  periode_id?: number;
  date_debut?: string;
  date_fin?: string;
}

// ── Stock Ouverture / Fermeture ───────────────────────────────────

export interface StockOuvertureLigne {
  produit_id:      number;
  produit_nom:     string;
  produit_sigle:   string;
  stock_ouverture: number;
  entrees:         number;
  sorties:         number;
  stock_fermeture: number;
}

export interface StockOuvertureResponse {
  marketeur_nom:   string;
  periode_id:      number | null;
  periode_nom:     string;
  lignes:          StockOuvertureLigne[];
  total_ouverture: number;
  total_entrees:   number;
  total_sorties:   number;
  total_fermeture: number;
}

// ── Frais de Passage ──────────────────────────────────────────────

export interface FraisPassageProduit {
  produit_id:    number;
  produit_nom:   string;
  produit_sigle: string;
  prix_passage:  number;
  is_global:     boolean;
}

export interface FraisPassageResponse {
  tarif_global:     number;
  date_application: string;
  periode_id:       number | null;
  periode_nom:      string;
  produits:         FraisPassageProduit[];
}

// ── Coulage des marketeurs ────────────────────────────────────────

export interface CoulageLigne {
  periode_id:    number;
  periode_nom:   string;
  produit_id:    number | null;
  produit_nom:   string;
  produit_sigle: string;
  brut_entree:   number;
  coul_entree:   number;
  entree_nette:  number;
  sortie:        number;
  qp_coul:       number;
  volume_sorti:  number;
  prix_unitaire: number;
  montant:       number;
  motif:         string;
}

export interface CoulageResponse {
  marketeur_nom:      string;
  lignes:             CoulageLigne[];
  total_montant:      number;
  total_volume_sorti: number;
}

// ── Référentiels ──────────────────────────────────────────────────

export interface Produit {
  id: number;
  nom: string;
  sigle: string;
}

export interface Periode {
  id: number;
  annee: number;
  mois: number;
  nom: string;
  statut: string;
}

// ── API calls ─────────────────────────────────────────────────────

export const etatsApi = {
  stockGlobal: (filters: StockGlobalFilters = {}) =>
    apiClient.get<StockGlobalResponse>('/etats/stock-global/', { params: filters }),

  recap: (filters: RecapFilters = {}) =>
    apiClient.get<RecapResponse>('/etats/recap/', { params: filters }),

  stockOuverture: (periodeId?: number) =>
    apiClient.get<StockOuvertureResponse>('/etats/stock-ouverture/', {
      params: periodeId ? { periode_id: periodeId } : {},
    }),

  stock15: (periodeId?: number) =>
    apiClient.get<StockOuvertureResponse>('/etats/stock-15/', {
      params: periodeId ? { periode_id: periodeId } : {},
    }),

  fraisPassage: (periodeId?: number) =>
    apiClient.get<FraisPassageResponse>('/etats/frais-passage/', {
      params: periodeId ? { periode_id: periodeId } : {},
    }),

  coulage: (periodeId?: number) =>
    apiClient.get<CoulageResponse>('/etats/coulage/', {
      params: periodeId ? { periode_id: periodeId } : {},
    }),

  produits: () =>
    apiClient.get<Produit[]>('/etats/produits/'),

  periodes: () =>
    apiClient.get<Periode[]>('/etats/periodes/'),
};
