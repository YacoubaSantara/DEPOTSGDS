import dayjs from 'dayjs';
import 'dayjs/locale/fr';

dayjs.locale('fr');

export function formatDate(date: string): string {
  return dayjs(date).format('DD/MM/YYYY');
}

export function formatDateTime(date: string): string {
  return dayjs(date).format('DD/MM/YYYY HH:mm');
}

export function formatNumber(n: number | null | undefined, decimals = 3): string {
  if (n == null || isNaN(Number(n))) return '0';
  return Number(n).toLocaleString('fr-FR', { maximumFractionDigits: decimals });
}

export function getErrorMessage(error: unknown): string {
  if (!error) return 'Erreur inconnue';
  if (typeof error === 'string') return error;

  // Axios error
  const axiosError = error as {
    response?: { data?: { detail?: string; non_field_errors?: string[] } };
    message?: string;
  };

  if (axiosError.response?.data?.detail) {
    return axiosError.response.data.detail;
  }
  if (axiosError.response?.data?.non_field_errors?.length) {
    return axiosError.response.data.non_field_errors[0];
  }
  if (axiosError.message) {
    if (axiosError.message.includes('Network Error')) {
      return 'Impossible de contacter le serveur. Vérifiez votre connexion.';
    }
    if (axiosError.message.includes('timeout')) {
      return 'Le serveur met trop de temps à répondre.';
    }
    return axiosError.message;
  }
  return 'Une erreur est survenue';
}
