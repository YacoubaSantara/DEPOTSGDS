/**
 * Libellés des périodes comptables — les périodes sont PAR DÉPÔT côté
 * serveur : dès que le référentiel couvre plusieurs dépôts, les mois
 * homonymes (« Janvier 2026 » × 2) doivent être distingués par le dépôt.
 * En mono-dépôt, l'affichage reste inchangé (pas de bruit).
 */
import type { Periode } from '../api/etats';

/** Vrai si les périodes couvrent plusieurs dépôts. */
export function plusieursDepots(periodes: Periode[]): boolean {
  return new Set(periodes.map(p => p.depot_id ?? null)).size > 1;
}

/** « Janvier 2026 — Alpha » en multi-dépôt, sinon « Janvier 2026 ». */
export function libellePeriode(p: Periode | null | undefined, multiDepot: boolean): string {
  if (!p) return '';
  return multiDepot && p.depot_nom ? `${p.nom} — ${p.depot_nom}` : p.nom;
}

/** Même règle pour les réponses d'état (periode_nom / periode_depot). */
export function libellePeriodeEtat(
  nom: string | undefined,
  depot: string | undefined,
  multiDepot: boolean,
): string {
  if (!nom) return '';
  return multiDepot && depot ? `${nom} — ${depot}` : nom;
}
