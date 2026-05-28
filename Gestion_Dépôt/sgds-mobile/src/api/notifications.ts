import apiClient from './client';

export interface NotificationItem {
  id:            number;
  type_notif:    'ENTREE' | 'SORTIE' | 'CESSION_EMISE' | 'CESSION_RECUE' | 'ACQUITTEMENT'
                 | 'DOCUMENT_AJOUTE' | 'ETAT_MENSUEL_DISPONIBLE';
  titre:         string;
  message:       string;
  lue:           boolean;
  date_creation: string;
  mouvement_id:  number | null;
  lien:          string | null;
}

export interface NotificationsResponse {
  count_non_lues: number;
  results:        NotificationItem[];
}

export const notificationsApi = {
  getAll:     () => apiClient.get<NotificationsResponse>('/notifications/'),
  marquerLus: (ids: number[]) => apiClient.patch('/notifications/', { ids }),
  toutLire:   () => apiClient.patch('/notifications/', { all: true }),
};
